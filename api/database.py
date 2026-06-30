"""
Database connection and query utilities for the API.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from datetime import datetime

from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path("data/warehouse.db")

# Query templates - centralized for maintainability
QUERIES = {
    "stats": """
        SELECT COUNT(*) as total FROM messages
    """,
    "channels": """
        SELECT channel_name, COUNT(*) as count 
        FROM messages 
        GROUP BY channel_name
    """,
    "media_stats": """
        SELECT 
            SUM(has_media) as with_media,
            COUNT(*) - SUM(has_media) as without_media
        FROM messages
    """,
    "avg_views": """
        SELECT AVG(views) as avg_views FROM messages
    """,
    "channel_exists": """
        SELECT COUNT(*) as count FROM messages WHERE channel_name = ?
    """,
    "channel_activity": """
        SELECT 
            date(message_date) as date,
            COUNT(*) as messages,
            AVG(views) as avg_views
        FROM messages
        WHERE channel_name = ?
            AND date(message_date) >= date('now', ?)
        GROUP BY date(message_date)
        ORDER BY date DESC
    """,
    "channel_summary": """
        SELECT 
            COUNT(*) as total_messages,
            AVG(views) as avg_views,
            MAX(views) as max_views,
            SUM(has_media) as media_count
        FROM messages
        WHERE channel_name = ?
    """,
    "top_messages": """
        SELECT 
            message_id,
            message_text,
            views,
            forwards,
            replies
        FROM messages
        WHERE channel_name = ?
        ORDER BY views DESC
        LIMIT 5
    """,
    "search_messages": """
        SELECT 
            message_id,
            channel_name,
            message_date,
            message_text,
            views
        FROM messages
        WHERE message_text LIKE ?
    """,
    "visual_content": """
        SELECT 
            SUM(has_media) as with_media,
            COUNT(*) - SUM(has_media) as without_media,
            AVG(views) as with_media_avg_views,
            AVG(CASE WHEN has_media = 0 THEN views END) as without_media_avg_views
        FROM messages
    """,
    "visual_by_channel": """
        SELECT 
            channel_name,
            COUNT(*) as total_messages,
            SUM(has_media) as with_media,
            ROUND(100.0 * SUM(has_media) / COUNT(*), 2) as media_percentage
        FROM messages
        GROUP BY channel_name
        ORDER BY media_percentage DESC
    """,
    "daily_trends": """
        SELECT 
            date(message_date) as date,
            COUNT(*) as messages,
            AVG(views) as avg_views
        FROM messages
        WHERE date(message_date) >= date('now', ?)
        GROUP BY date(message_date)
        ORDER BY date ASC
    """,
    "image_detections_check": """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='fct_image_detections'
    """,
    "image_analysis": """
        SELECT 
            COUNT(*) as total_images,
            SUM(is_medical) as medical_images,
            category,
            COUNT(*) as count
        FROM fct_image_detections
        GROUP BY category
    """
}


class Database:
    """Database connection and query manager."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        if not self.db_path.exists():
            raise HTTPException(status_code=500, detail="Database not found")
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a query and return results as list of dicts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Execute a query and return a single result."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ============ Specific Query Methods ============
    
    def get_stats(self) -> Dict:
        """Get overall statistics."""
        total = self.execute_one(QUERIES["stats"]) or {"total": 0}
        channels = self.execute_query(QUERIES["channels"])
        media_stats = self.execute_one(QUERIES["media_stats"]) or {"with_media": 0, "without_media": 0}
        avg_views = self.execute_one(QUERIES["avg_views"]) or {"avg_views": 0}
        
        return {
            "total": total.get("total", 0),
            "channels": channels,
            "media_stats": media_stats,
            "avg_views": avg_views.get("avg_views", 0)
        }
    
    def get_channel_activity(self, channel_name: str, days: int) -> Dict:
        """Get channel activity."""
        # Check if channel exists
        exists = self.execute_one(QUERIES["channel_exists"], (channel_name,))
        if not exists or exists.get("count", 0) == 0:
            return {"exists": False}
        
        daily_activity = self.execute_query(
            QUERIES["channel_activity"], 
            (channel_name, f'-{days} days')
        )
        
        summary = self.execute_one(QUERIES["channel_summary"], (channel_name,)) or {}
        top_messages = self.execute_query(QUERIES["top_messages"], (channel_name,))
        
        return {
            "exists": True,
            "daily_activity": daily_activity,
            "summary": summary,
            "top_messages": top_messages
        }
    
    def search_messages(self, query: str, channel: Optional[str] = None, 
                        limit: int = 20, min_views: Optional[int] = None) -> Dict:
        """Search messages."""
        search_query = QUERIES["search_messages"]
        params = [f'%{query}%']
        
        if channel:
            search_query += " AND channel_name = ?"
            params.append(channel)
        
        if min_views:
            search_query += " AND views >= ?"
            params.append(min_views)
        
        search_query += " ORDER BY views DESC LIMIT ?"
        params.append(limit)
        
        results = self.execute_query(search_query, tuple(params))
        return {
            "results": results,
            "count": len(results)
        }
    
    def get_visual_content_stats(self) -> Dict:
        """Get visual content statistics."""
        overall = self.execute_one(QUERIES["visual_content"]) or {}
        by_channel = self.execute_query(QUERIES["visual_by_channel"])
        
        # Media impact
        media_impact = self.execute_query("""
            SELECT 
                CASE WHEN has_media = 1 THEN 'With Media' ELSE 'Without Media' END as media_type,
                AVG(views) as avg_views,
                AVG(forwards) as avg_forwards,
                AVG(replies) as avg_replies,
                AVG(views + forwards + replies) as total_engagement
            FROM messages
            GROUP BY has_media
        """)
        
        return {
            "overall": overall,
            "by_channel": by_channel,
            "media_impact": media_impact
        }
    
    def get_daily_trends(self, days: int, channel: Optional[str] = None) -> Dict:
        """Get daily trends."""
        query = QUERIES["daily_trends"]
        params = [f'-{days} days']
        
        if channel:
            query = query.replace("WHERE date(message_date)", 
                                  f"WHERE channel_name = ? AND date(message_date)")
            params.insert(0, channel)
        
        data = self.execute_query(query, tuple(params))
        return {"data": data}
    
    def get_image_analysis(self) -> Dict:
        """Get image analysis results."""
        check = self.execute_one(QUERIES["image_detections_check"])
        if not check:
            return {"available": False}
        
        results = self.execute_query(QUERIES["image_analysis"])
        total = sum(r.get("count", 0) for r in results) if results else 0
        
        return {
            "available": True,
            "total_images": total,
            "categories": results
        }


# Singleton instance
db = Database()