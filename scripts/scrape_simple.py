#!/usr/bin/env python3
"""
Simple scraper that works.
"""

import os
import asyncio
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

async def main():
    """Simple scrape."""
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    channels = ['chemed', 'lobeliacosmetics', 'tikvahpharma']
    
    print("=" * 60)
    print("Simple Telegram Scraper")
    print("=" * 60)
    
    client = TelegramClient('session', api_id, api_hash)
    await client.start(phone=phone)
    
    # Create data directory
    data_dir = Path("data/raw/telegram_messages")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    for channel_name in channels:
        print(f"\n📡 Scraping {channel_name}...")
        
        try:
            entity = await client.get_entity(f'@{channel_name}')
            
            messages = []
            async for msg in client.iter_messages(entity, limit=100):
                # Get replies safely
                replies = 0
                if hasattr(msg, 'replies') and msg.replies:
                    try:
                        replies = msg.replies.replies if hasattr(msg.replies, 'replies') else 0
                    except:
                        replies = 0
                
                msg_data = {
                    "message_id": msg.id,
                    "channel_name": channel_name,
                    "message_date": msg.date.isoformat() if msg.date else None,
                    "message_text": msg.text or "",
                    "has_media": bool(msg.media),
                    "image_path": None,
                    "views": getattr(msg, 'views', 0),
                    "forwards": getattr(msg, 'forwards', 0),
                    "replies": replies,
                }
                messages.append(msg_data)
            
            print(f"  ✅ Scraped {len(messages)} messages")
            
            # Save data
            today = datetime.now().date().isoformat()
            date_dir = data_dir / today
            date_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = date_dir / f"{channel_name}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            
            print(f"  💾 Saved to {file_path}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    await client.disconnect()
    
    print("\n" + "=" * 60)
    print("✅ Scraping complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())