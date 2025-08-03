#!/usr/bin/env python3
"""
Script to help find your Telegram user ID.
"""

import os
import sys
import asyncio
from telegram import Bot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def find_user_id():
    """Send a message and wait for response to find user ID."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found")
        return
    
    bot = Bot(token=token)
    
    print("🤖 Finding your Telegram User ID")
    print("=" * 40)
    print("1. Make sure you've started the bot: send /start to @RoboticsRadarBot")
    print("2. Send any message to the bot")
    print("3. I'll try to detect your user ID")
    print()
    
    try:
        # Get bot info
        bot_info = await bot.get_me()
        print(f"✅ Bot connected: @{bot_info.username}")
        
        # Get updates to see recent messages
        updates = await bot.get_updates()
        
        if updates:
            print(f"📱 Found {len(updates)} recent messages:")
            for update in updates[-5:]:  # Show last 5
                if update.message:
                    user = update.message.from_user
                    print(f"   User: {user.first_name} (@{user.username}) - ID: {user.id}")
        else:
            print("📱 No recent messages found. Please send a message to the bot first.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(find_user_id()) 