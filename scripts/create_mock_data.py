#!/usr/bin/env python3
"""
Create mock data for testing.
"""

import json
import random
from pathlib import Path
from datetime import datetime, timedelta

def create_mock_data():
    """Create mock Telegram messages."""
    print("📊 Creating mock data...")
    
    channels = ["chemed", "lobeliacosmetics", "tikvahpharma"]
    products = [
        "Paracetamol 500mg", "Ibuprofen 400mg", "Amoxicillin 250mg",
        "Vitamin C", "Omega-3", "Calcium", "Lotion", "Shampoo",
        "Cream", "Serum", "Antibiotic", "Painkiller", "Antihistamine",
        "Cough Syrup", "Antacid", "Probiotics", "Multivitamin",
        "Eye Drops", "Nasal Spray", "Antifungal Cream"
    ]
    prices = ["50 birr", "100 birr", "200 birr", "75 birr", "150 birr", "300 birr", "25 birr", "500 birr"]
    
    data_dir = Path("data/raw/telegram_messages")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    total_messages = 0
    
    for day in range(7):
        date = (datetime.now() - timedelta(days=day)).date()
        date_str = date.isoformat()
        date_dir = data_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        
        for channel in channels:
            messages = []
            num_messages = random.randint(5, 20)
            
            for i in range(num_messages):
                product = random.choice(products)
                price = random.choice(prices)
                message_date = datetime(
                    date.year, date.month, date.day,
                    random.randint(8, 22),
                    random.randint(0, 59)
                )
                
                msg_type = random.choice(['product', 'price', 'availability', 'promotion'])
                
                if msg_type == 'product':
                    text = f"{product} available now! Price: {price}. Contact us for more info."
                elif msg_type == 'price':
                    text = f"New price for {product}: {price}. Limited time offer!"
                elif msg_type == 'availability':
                    text = f"{product} back in stock! {price} per unit. Hurry up!"
                else:
                    text = f"Special promotion on {product}! Only {price} today!"
                
                msg = {
                    "message_id": random.randint(100000, 999999),
                    "channel_name": channel,
                    "message_date": message_date.isoformat(),
                    "message_text": text,
                    "has_media": random.choice([True, False]),
                    "image_path": f"data/raw/images/{channel}/{random.randint(100000, 999999)}.jpg" if random.choice([True, False]) else None,
                    "views": random.randint(50, 500),
                    "forwards": random.randint(5, 50),
                    "replies": random.randint(0, 20)
                }
                messages.append(msg)
                total_messages += 1
            
            file_path = date_dir / f"{channel}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            
            print(f"  ✅ {channel} - {date_str}: {len(messages)} messages")
    
    print(f"\n✅ Created {total_messages} mock messages")
    print(f"📁 Data saved in: {data_dir}")
    return total_messages

def main():
    """Main function."""
    print("=" * 60)
    print("Creating Mock Data")
    print("=" * 60)
    
    Path("logs").mkdir(exist_ok=True)
    Path("data/raw/images/chemed").mkdir(parents=True, exist_ok=True)
    Path("data/raw/images/lobeliacosmetics").mkdir(parents=True, exist_ok=True)
    Path("data/raw/images/tikvahpharma").mkdir(parents=True, exist_ok=True)
    
    total = create_mock_data()
    
    print("\n" + "=" * 60)
    print("✅ Mock data created successfully!")
    print("=" * 60)
    print("\nNow run:")
    print("  python scripts/load_data_simple.py")

if __name__ == "__main__":
    main()
