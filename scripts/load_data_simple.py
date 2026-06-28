#!/usr/bin/env python3
"""
Simple data loader that works without PostgreSQL.
"""

import json
import sqlite3
from pathlib import Path

def create_sqlite_db():
    """Create SQLite database and load data."""
    print("📊 Creating SQLite database...")
    
    db_path = Path("data/warehouse.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY,
            channel_name TEXT NOT NULL,
            message_date TEXT,
            message_text TEXT,
            has_media INTEGER DEFAULT 0,
            image_path TEXT,
            views INTEGER DEFAULT 0,
            forwards INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            scraped_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_channel_date 
        ON messages (channel_name, message_date)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_views 
        ON messages (views DESC)
    """)
    
    data_dir = Path("data/raw/telegram_messages")
    if not data_dir.exists():
        print("❌ No data found. Run: python scripts/create_mock_data.py")
        conn.close()
        return 0
    
    total_loaded = 0
    json_files = list(data_dir.glob("**/*.json"))
    
    if not json_files:
        print("❌ No JSON files found. Run: python scripts/create_mock_data.py")
        conn.close()
        return 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                messages = json.load(f)
                
            for msg in messages:
                cursor.execute("""
                    INSERT OR REPLACE INTO messages (
                        message_id, channel_name, message_date, message_text,
                        has_media, image_path, views, forwards, replies
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    msg.get('message_id'),
                    msg.get('channel_name'),
                    msg.get('message_date'),
                    msg.get('message_text', ''),
                    1 if msg.get('has_media') else 0,
                    msg.get('image_path'),
                    msg.get('views', 0),
                    msg.get('forwards', 0),
                    msg.get('replies', 0)
                ))
                total_loaded += 1
                
            print(f"  ✅ Loaded {len(messages)} messages from {json_file.name}")
            
        except Exception as e:
            print(f"  ❌ Error loading {json_file}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Total messages loaded: {total_loaded}")
    return total_loaded

def show_summary():
    """Show data summary."""
    db_path = Path("data/warehouse.db")
    if not db_path.exists():
        print("❌ Database not found")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM messages")
    total = cursor.fetchone()[0]
    print(f"\n📊 Total messages: {total}")
    
    if total == 0:
        conn.close()
        return
    
    cursor.execute("""
        SELECT channel_name, COUNT(*) as count, 
               AVG(views) as avg_views,
               SUM(has_media) as with_media
        FROM messages
        GROUP BY channel_name
        ORDER BY count DESC
    """)
    
    print("\n📈 Messages by channel:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} messages, avg views: {row[2]:.0f}, {row[3]} with media")
    
    keywords = ['Paracetamol', 'Ibuprofen', 'Amoxicillin', 'Vitamin', 'Omega', 'Lotion', 'Shampoo']
    
    print("\n🔥 Top product mentions:")
    for keyword in keywords:
        cursor.execute("SELECT COUNT(*) FROM messages WHERE message_text LIKE ?", (f'%{keyword}%',))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"  {keyword}: {count} mentions")
    
    cursor.execute("""
        SELECT channel_name, message_text, views
        FROM messages
        WHERE message_text != ''
        ORDER BY views DESC
        LIMIT 5
    """)
    
    print("\n📊 Most viewed messages:")
    for row in cursor.fetchall():
        text = row[1][:50] + "..." if len(row[1]) > 50 else row[1]
        print(f"  {row[0]}: {text} ({row[2]} views)")
    
    conn.close()

def main():
    """Main function."""
    print("=" * 60)
    print("Simple Data Loader")
    print("=" * 60)
    
    total = create_sqlite_db()
    
    if total > 0:
        show_summary()
        print("\n" + "=" * 60)
        print("✅ Data loaded successfully!")
        print("=" * 60)
        print("\nTo query the data:")
        print("  sqlite3 data/warehouse.db")
        print("  SELECT * FROM messages LIMIT 10;")
    else:
        print("\n❌ No data loaded. Run: python scripts/create_mock_data.py")

if __name__ == "__main__":
    main()
