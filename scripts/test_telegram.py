#!/usr/bin/env python3
"""
Test Telegram API credentials.
"""

import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

async def main():
    """Test credentials."""
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    print("=" * 50)
    print("Testing Telegram Credentials")
    print("=" * 50)
    
    # Check if credentials exist
    if not api_id or api_id == 'your_api_id':
        print("❌ API ID not set correctly")
        print("   Current value:", api_id)
        print("   Please update .env with your real API ID")
        return
    
    if not api_hash or api_hash == 'your_api_hash':
        print("❌ API Hash not set correctly")
        print("   Please update .env with your real API Hash")
        return
    
    if not phone or phone == 'your_phone_number':
        print("❌ Phone not set correctly")
        print("   Please update .env with your real phone number")
        return
    
    print(f"✅ API ID: {api_id}")
    print(f"✅ API Hash: {api_hash[:10]}...")
    print(f"✅ Phone: {phone}")
    
    # Test connection
    print("\n🔄 Testing connection to Telegram...")
    
    client = TelegramClient('test_session', int(api_id), api_hash)
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            print("📱 Sending code request to your Telegram...")
            await client.send_code_request(phone)
            code = input("Enter the code sent to your Telegram: ")
            await client.sign_in(phone, code)
        
        me = await client.get_me()
        print(f"\n✅ Successfully connected!")
        print(f"👤 Name: {me.first_name} {me.last_name or ''}")
        print(f"🆔 ID: {me.id}")
        print(f"📱 Phone: {me.phone}")
        
        await client.disconnect()
        print("\n🎉 Your Telegram credentials work perfectly!")
        
    except ValueError as e:
        if "invalid literal for int()" in str(e):
            print("\n❌ API ID must be a number!")
            print("   Check your .env file - remove any quotes around the number")
        await client.disconnect()
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        if "FLOOD_WAIT" in str(e):
            print("   ⏳ Rate limited. Please wait a few minutes.")
        elif "API_ID_INVALID" in str(e):
            print("   ❌ Invalid API ID. Check your .env file.")
        elif "API_HASH_INVALID" in str(e):
            print("   ❌ Invalid API Hash. Check your .env file.")
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
