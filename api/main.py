"""
FastAPI application for Medical Telegram Warehouse.
"""

from fastapi import FastAPI, HTTPException, Query
from typing import Optional
import sqlite3
from pathlib import Path
from datetime import datetime
import json
import os

app = FastAPI(
    title="Medical Telegram Warehouse API",
    description="API for querying Telegram medical data",
    version="1.0.0"
)

# Database path
DB_PATH = Path("data/warehouse.db")

def get_db_connection():
    """Get database connection."""
    if not DB_PATH.exists():
        raise HTTPException(status_code=500, detail="Database not found")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Medical Telegram Warehouse API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/api/messages/stats",
            "/api/reports/top-products",
            "/api/channels/{channel_name}/activity",
            "/api/search/messages",
            "/api/reports/visual-content",
            "/api/reports/daily-trends",
            "/api/reports/image-analysis"
        ]
    }

@app.get("/api/messages/stats")
async def get_stats():
    """Get overall statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) as total FROM messages")
        total = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT channel_name, COUNT(*) as count 
            FROM messages 
            GROUP BY channel_name
        """)
        channels = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT 
                SUM(has_media) as with_media,
                COUNT(*) - SUM(has_media) as without_media
            FROM messages
        """)
        media_stats = dict(cursor.fetchone())
        
        cursor.execute("SELECT AVG(views) as avg_views FROM messages")
        avg_views = cursor.fetchone()['avg_views'] or 0
        
        return {
            "total_messages": total,
            "channels": channels,
            "media_stats": media_stats,
            "average_views": round(avg_views, 2),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/reports/top-products")
async def get_top_products(
    limit: int = Query(10, ge=1, le=50),
    channel: Optional[str] = None
):
    """Get top mentioned products."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        products = [
            'Paracetamol', 'Ibuprofen', 'Amoxicillin', 'Vitamin',
            'Omega', 'Lotion', 'Shampoo', 'Cream', 'Serum',
            'Antibiotic', 'Painkiller', 'Multivitamin'
        ]
        
        results = []
        for product in products:
            query = """
                SELECT 
                    COUNT(*) as mentions,
                    AVG(views) as avg_views
                FROM messages
                WHERE message_text LIKE ?
            """
            params = [f'%{product}%']
            
            if channel:
                query += " AND channel_name = ?"
                params.append(channel)
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            if row and row['mentions'] > 0:
                results.append({
                    "product": product,
                    "mentions": row['mentions'],
                    "avg_views": round(row['avg_views'] or 0, 2)
                })
        
        results.sort(key=lambda x: x['mentions'], reverse=True)
        
        return {
            "products": results[:limit],
            "total_products_mentioned": len(results),
            "channel_filter": channel or "All channels",
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/channels/{channel_name}/activity")
async def get_channel_activity(
    channel_name: str,
    days: int = Query(7, ge=1, le=30)
):
    """Get channel activity over time."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT COUNT(*) as count FROM messages WHERE channel_name = ?",
            (channel_name,)
        )
        if cursor.fetchone()['count'] == 0:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        cursor.execute("""
            SELECT 
                date(message_date) as date,
                COUNT(*) as messages,
                AVG(views) as avg_views
            FROM messages
            WHERE channel_name = ?
                AND date(message_date) >= date('now', ?)
            GROUP BY date(message_date)
            ORDER BY date DESC
        """, (channel_name, f'-{days} days'))
        
        daily_activity = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_messages,
                AVG(views) as avg_views,
                MAX(views) as max_views,
                SUM(has_media) as media_count
            FROM messages
            WHERE channel_name = ?
        """, (channel_name,))
        stats = dict(cursor.fetchone())
        
        return {
            "channel": channel_name,
            "period_days": days,
            "summary": {
                "total_messages": stats['total_messages'],
                "avg_views": round(stats['avg_views'] or 0, 2),
                "max_views": stats['max_views'] or 0,
                "media_count": stats['media_count'] or 0
            },
            "daily_activity": daily_activity
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/search/messages")
async def search_messages(
    query: str = Query(..., min_length=1),
    channel: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """Search for messages containing a keyword."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        search_query = """
            SELECT 
                message_id,
                channel_name,
                message_date,
                message_text,
                views
            FROM messages
            WHERE message_text LIKE ?
        """
        params = [f'%{query}%']
        
        if channel:
            search_query += " AND channel_name = ?"
            params.append(channel)
        
        search_query += " ORDER BY views DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(search_query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            "query": query,
            "total_results": len(results),
            "channel_filter": channel or "All channels",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/reports/visual-content")
async def get_visual_content_stats():
    """Get statistics about visual content usage."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                SUM(has_media) as with_media,
                COUNT(*) - SUM(has_media) as without_media,
                AVG(views) as with_media_avg_views,
                AVG(CASE WHEN has_media = 0 THEN views END) as without_media_avg_views
            FROM messages
        """)
        overall = dict(cursor.fetchone())
        
        cursor.execute("""
            SELECT 
                channel_name,
                COUNT(*) as total_messages,
                SUM(has_media) as with_media,
                ROUND(100.0 * SUM(has_media) / COUNT(*), 2) as media_percentage
            FROM messages
            GROUP BY channel_name
            ORDER BY media_percentage DESC
        """)
        by_channel = [dict(row) for row in cursor.fetchall()]
        
        return {
            "overall": {
                "with_media": overall['with_media'] or 0,
                "without_media": overall['without_media'] or 0,
                "avg_views_with_media": round(overall['with_media_avg_views'] or 0, 2),
                "avg_views_without_media": round(overall['without_media_avg_views'] or 0, 2)
            },
            "by_channel": by_channel
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/reports/daily-trends")
async def get_daily_trends(
    days: int = Query(7, ge=1, le=30)
):
    """Get daily posting trends."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                date(message_date) as date,
                COUNT(*) as messages,
                AVG(views) as avg_views
            FROM messages
            WHERE date(message_date) >= date('now', ?)
            GROUP BY date(message_date)
            ORDER BY date ASC
        """, (f'-{days} days',))
        
        daily_data = [dict(row) for row in cursor.fetchall()]
        
        return {
            "period_days": days,
            "data": daily_data,
            "total_messages": sum(d['messages'] for d in daily_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/reports/image-analysis")
async def get_image_analysis():
    """Get image analysis results."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='fct_image_detections'
        """)
        if not cursor.fetchone():
            return {
                "status": "No image detections available",
                "message": "Run YOLO detection first: python scripts/run_yolo.py"
            }
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_images,
                SUM(is_medical) as medical_images,
                category,
                COUNT(*) as count
            FROM fct_image_detections
            GROUP BY category
        """)
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            "total_images": sum(r['count'] for r in results),
            "categories": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)