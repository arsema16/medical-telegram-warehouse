#!/usr/bin/env python3
"""
Run the complete pipeline with mock data.
"""

import sys
import subprocess
import sqlite3
from pathlib import Path

def main():
    print("=" * 60)
    print("Medical Telegram Warehouse - Complete Pipeline")
    print("=" * 60)
    
    # Create directories
    Path("logs").mkdir(exist_ok=True)
    Path("data/raw/telegram_messages").mkdir(parents=True, exist_ok=True)
    Path("data/raw/images").mkdir(parents=True, exist_ok=True)
    
    # Step 1: Create mock data
    print("\n📊 Step 1: Creating mock data...")
    subprocess.run([sys.executable, "scripts/create_mock_data.py"])
    
    # Step 2: Load data
    print("\n📊 Step 2: Loading data...")
    subprocess.run([sys.executable, "scripts/load_data_simple.py"])
    
    # Step 3: Verify
    print("\n🔍 Step 3: Verification...")
    conn = sqlite3.connect("data/warehouse.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM messages")
    total = cursor.fetchone()[0]
    print(f"✅ Total messages in database: {total}")
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Pipeline completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
