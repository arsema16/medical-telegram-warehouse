#!/usr/bin/env python3
"""
Create mock images for YOLO testing.
"""

import os
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def create_mock_image(channel, message_id, category='product'):
    """Create a mock image with simple shapes."""
    # Create a blank image
    img = Image.new('RGB', (640, 480), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw different shapes based on category
    if category == 'product':
        # Draw a pill/bottle shape
        draw.rectangle([200, 150, 440, 330], fill=(100, 150, 200), outline='black')
        draw.ellipse([220, 160, 280, 320], fill=(200, 100, 100), outline='black')
        draw.ellipse([360, 160, 420, 320], fill=(100, 200, 100), outline='black')
    elif category == 'person':
        # Draw a simple person
        draw.ellipse([280, 100, 360, 200], fill=(200, 180, 150), outline='black')  # Head
        draw.rectangle([300, 200, 340, 350], fill=(50, 50, 200), outline='black')   # Body
        draw.line([280, 250, 300, 250], fill='black', width=3)  # Left arm
        draw.line([340, 250, 360, 250], fill='black', width=3)  # Right arm
    else:
        # Random shapes
        for _ in range(random.randint(3, 8)):
            x = random.randint(50, 590)
            y = random.randint(50, 430)
            w = random.randint(30, 120)
            h = random.randint(30, 120)
            draw.rectangle([x, y, x+w, y+h], fill=tuple(random.randint(0, 255) for _ in range(3)))
    
    # Add text
    draw.text((10, 10), f"Channel: {channel}", fill='black')
    draw.text((10, 30), f"Message: {message_id}", fill='black')
    
    # Save image
    img_dir = Path(f"data/raw/images/{channel}")
    img_dir.mkdir(parents=True, exist_ok=True)
    img_path = img_dir / f"{message_id}.jpg"
    img.save(img_path)
    return img_path

def main():
    """Create mock images."""
    print("=" * 60)
    print("Creating Mock Images")
    print("=" * 60)
    
    # Get messages with has_media=1 from database
    import sqlite3
    conn = sqlite3.connect('data/warehouse.db')
    cursor = conn.cursor()
    
    # Get messages that have media flag
    cursor.execute("""
        SELECT message_id, channel_name 
        FROM messages 
        WHERE has_media = 1 
        LIMIT 20
    """)
    messages = cursor.fetchall()
    conn.close()
    
    if not messages:
        print("No messages with media found. Creating some manually...")
        messages = [
            (1001, 'chemed'),
            (1002, 'chemed'),
            (1003, 'lobeliacosmetics'),
            (1004, 'lobeliacosmetics'),
            (1005, 'tikvahpharma'),
            (1006, 'tikvahpharma'),
        ]
    
    categories = ['product', 'person', 'random']
    created = 0
    
    for msg_id, channel in messages:
        # Generate a random category for each image
        category = random.choice(categories)
        
        # Create the image
        img_path = create_mock_image(channel, msg_id, category)
        print(f"✅ Created: {img_path}")
        created += 1
    
    print(f"\n✅ Created {created} mock images")
    print(f"📁 Images saved to: data/raw/images/")

if __name__ == "__main__":
    main()