#!/usr/bin/env python3
"""
Run the Telegram scraper to collect real data.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper import TelegramScraper

def main():
    """Run the scraper."""
    print("=" * 60)
    print("Starting Telegram Scraper (REAL DATA)")
    print("=" * 60)
    
    # Check if .env exists
    if not Path(".env").exists():
        print("❌ .env file not found!")
        print("Please create .env with your Telegram credentials:")
        print("  TELEGRAM_API_ID=your_api_id")
        print("  TELEGRAM_API_HASH=your_api_hash")
        print("  TELEGRAM_PHONE=+your_phone_number")
        print("  TELEGRAM_CHANNELS=chemed,lobeliacosmetics,tikvahpharma")
        return
    
    # Create necessary directories
    Path("logs").mkdir(exist_ok=True)
    Path("data/raw/telegram_messages").mkdir(parents=True, exist_ok=True)
    Path("data/raw/images").mkdir(parents=True, exist_ok=True)
    
    # Initialize and run scraper
    try:
        scraper = TelegramScraper()
        print(f"📡 Channels to scrape: {scraper.channels}")
        print("🔄 Starting scraping... (this may take a while)")
        print("   Press Ctrl+C to stop\n")
        
        scraper.run(limit=500)  # Start with 500 messages per channel
        
        print("\n" + "=" * 60)
        print("✅ Scraping completed successfully!")
        print("=" * 60)
        print(f"📁 Data saved in: data/raw/telegram_messages/")
        print(f"🖼️  Images saved in: data/raw/images/")
        
        # Show summary
        data_dir = Path("data/raw/telegram_messages")
        total_files = len(list(data_dir.glob("**/*.json")))
        if total_files > 0:
            print(f"\n📊 Created {total_files} JSON files")
            
            # Show sample
            sample_files = list(data_dir.glob("**/*.json"))[:3]
            for f in sample_files:
                print(f"  - {f}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Scraping interrupted by user")
        print("Partial data has been saved.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()
