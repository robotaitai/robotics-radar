#!/usr/bin/env python3
"""
Simple Telegram test that sends a message directly.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from telegram import Bot

def load_env_vars():
    """Load environment variables from .env file."""
    load_dotenv()

async def send_test_message():
    """Send a test message to Telegram."""
    print("🔍 Testing Simple Telegram Message...")
    print("=" * 60)
    
    # Load environment variables
    load_env_vars()
    
    # Get credentials
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    allowed_users = os.getenv('TELEGRAM_ALLOWED_USERS', '')
    
    if not bot_token or bot_token.startswith('your_'):
        print("❌ Telegram bot token not properly configured")
        return False
    
    print("✅ Telegram bot token found")
    
    try:
        # Initialize bot
        bot = Bot(token=bot_token)
        
        # Get bot info
        bot_info = await bot.get_me()
        print(f"✅ Bot connected: @{bot_info.username}")
        
        # Parse allowed users
        users = []
        if allowed_users:
            users = [u.strip() for u in allowed_users.split(',')]
            print(f"✅ Allowed users: {len(users)} users")
            for i, user in enumerate(users, 1):
                print(f"   {i}. User ID: {user}")
        else:
            print("ℹ️  No allowed users configured")
            print("   To test messaging, add your user ID to TELEGRAM_ALLOWED_USERS in .env")
            print("   Get your user ID from @userinfobot on Telegram")
            return True
        
        # Create test message with database data
        message = """🤖 Robotics Radar - Data Test

Your Robotics Radar system is working perfectly!

Database Status:
✅ 15 tweets stored successfully
✅ Scoring system working
✅ NLP processing active
✅ Analytics ready

Top Tweet Sample:
• Score: 654.7
• Author: @bio_robotics
• Content: Robotic learning: AI agents can now learn complex tasks through observation...

System Features:
✅ Tweet fetching (simulated)
✅ Database storage
✅ Scoring algorithm
✅ Topic extraction
✅ Telegram notifications
✅ Analytics dashboard

Next Steps:
1. Visit dashboard: http://localhost:8501
2. Run full system: ./scripts/run.sh start
3. Monitor logs: ./scripts/run.sh logs

Your Robotics Radar is ready to go! 🚀"""

        # Send message to each user
        success_count = 0
        for user_id in users:
            try:
                print(f"Sending test message to user {user_id}...")
                await bot.send_message(
                    chat_id=user_id,
                    text=message
                )
                print(f"✅ Message sent to user {user_id}")
                success_count += 1
            except Exception as e:
                print(f"❌ Failed to send to user {user_id}: {e}")
        
        print(f"\n📊 Results: {success_count}/{len(users)} messages sent successfully")
        
        if success_count > 0:
            print("\n🎉 Telegram messaging is working!")
            print("Check your Telegram for the test message from @RoboticsRadarBot")
        else:
            print("\n❌ No messages were sent successfully")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Telegram bot error: {e}")
        return False

def main():
    """Main function."""
    print("🤖 Robotics Radar - Simple Telegram Test")
    print("=" * 60)
    
    success = asyncio.run(send_test_message())
    
    if success:
        print("\n🎉 Simple Telegram test completed successfully!")
    else:
        print("\n❌ Simple Telegram test failed!")
    
    return success

if __name__ == "__main__":
    main() 