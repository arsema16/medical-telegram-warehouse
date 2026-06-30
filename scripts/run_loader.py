#!/usr/bin/env python3
"""
Run the data loader to load data to PostgreSQL.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import DataLoader

def main():
    """Load data to PostgreSQL."""
    print("=" * 60)
    print("Loading Data to PostgreSQL")
    print("=" * 60)
    
    # Check if .env exists
    if not Path(".env").exists():
        print("❌ .env file not found!")
        print("Please create .env with your database credentials:")
        print("  DB_HOST=localhost")
        print("  DB_PORT=5432")
        print("  DB_USER=postgres")
        print("  DB_PASSWORD=postgres")
        print("  DB_NAME=medical_warehouse")
        return
    
    # Check if data exists
    data_dir = Path("data/raw/telegram_messages")
    if not data_dir.exists():
        print("❌ No data found!")
        print("Please run the scraper first:")
        print("  python scripts/run_scraper.py")
        return
    
    json_files = list(data_dir.glob("**/*.json"))
    if not json_files:
        print("❌ No JSON files found!")
        print("Please run the scraper first:")
        print("  python scripts/run_scraper.py")
        return
    
    print(f"📁 Found {len(json_files)} JSON files")
    
    # Initialize and run loader
    try:
        loader = DataLoader()
        print("🔄 Connecting to PostgreSQL...")
        
        # Load all data
        count = loader.load_all()
        
        print("\n" + "=" * 60)
        print("✅ Data loaded successfully!")
        print("=" * 60)
        print(f"📊 Loaded {count} messages to PostgreSQL")
        
        # Verify
        loader.connect()
        with loader.connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM raw.telegram_messages")
            total = cur.fetchone()[0]
            print(f"📊 Total messages in database: {total}")
            
            cur.execute("""
                SELECT channel_name, COUNT(*) 
                FROM raw.telegram_messages 
                GROUP BY channel_name
                ORDER BY COUNT(*) DESC
            """)
            channels = cur.fetchall()
            print("\n📈 Messages per channel:")
            for channel, count in channels:
                print(f"  {channel}: {count} messages")
        
        loader.close()
        
        print("\n📋 Next steps:")
        print("  1. Run dbt: cd medical_warehouse && dbt run")
        print("  2. Test dbt: cd medical_warehouse && dbt test")
        print("  3. Generate docs: cd medical_warehouse && dbt docs generate")
        
    except Exception as e:
        print(f"\n❌ Error loading data: {e}")
        raise

if __name__ == "__main__":
    main()
