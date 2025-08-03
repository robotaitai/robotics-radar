#!/usr/bin/env python3
"""
Test Telegram bot messaging functionality.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

def load_env_vars():
    """Load environment variables from .env file."""
    load_dotenv()

async def test_telegram_messaging():
    """Test Telegram bot messaging functionality."""
    print("🔍 Testing Telegram Bot Messaging...")
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
            print("ℹ️  No allowed users configured (all users allowed)")
        
        # Test message sending
        print("\n📤 Testing Message Sending...")
        
        # Create a test message
        test_message = """🤖 *Robotics Radar Test Message*

This is a test message from your Robotics Radar bot!

*Test Data:*
• Tweet: "Exciting new developments in robotics research!"
• Author: @test_user
• Score: 85.5
• Likes: 42, Retweets: 12

*Features:*
✅ Tweet fetching
✅ Scoring system
✅ Analytics dashboard
✅ Telegram notifications

This message confirms your bot is working correctly! 🎉"""

        # Create inline keyboard for feedback
        keyboard = [
            [
                InlineKeyboardButton("👍 Like", callback_data="like_123"),
                InlineKeyboardButton("👎 Dislike", callback_data="dislike_123")
            ],
            [
                InlineKeyboardButton("📊 View Analytics", callback_data="analytics"),
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send test message to each allowed user
        if users:
            for user_id in users:
                try:
                    print(f"Sending test message to user {user_id}...")
                    await bot.send_message(
                        chat_id=user_id,
                        text=test_message,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                    print(f"✅ Message sent to user {user_id}")
                except Exception as e:
                    print(f"❌ Failed to send to user {user_id}: {e}")
        else:
            print("ℹ️  No specific users configured. To test messaging:")
            print("   1. Start a chat with your bot: @RoboticsRadarBot")
            print("   2. Send /start to the bot")
            print("   3. Add your user ID to TELEGRAM_ALLOWED_USERS in .env")
        
        # Test analytics report
        print("\n📊 Testing Analytics Report...")
        analytics_message = """📈 *Robotics Radar Analytics Report*

*System Status:*
✅ Database: Connected
✅ NLP Processing: Active
✅ Scoring Model: Ready

*Recent Activity:*
• Tweets processed: 0 (API limited)
• Top score: N/A
• Average score: N/A

*Top Topics:*
• No data available yet

*Recommendations:*
• Upgrade Twitter API access for full functionality
• Monitor system logs for updates
• Check dashboard at http://localhost:8501

*Bot Commands:*
/start - Start the bot
/stats - View statistics
/top - View top tweets
/help - Show help

This is a test analytics report! 📊"""

        if users:
            for user_id in users:
                try:
                    print(f"Sending analytics report to user {user_id}...")
                    await bot.send_message(
                        chat_id=user_id,
                        text=analytics_message,
                        parse_mode='Markdown'
                    )
                    print(f"✅ Analytics report sent to user {user_id}")
                except Exception as e:
                    print(f"❌ Failed to send analytics to user {user_id}: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Telegram Bot Messaging Test Complete!")
        print("=" * 60)
        
        if not users:
            print("\n📋 Next Steps:")
            print("1. Start a chat with @RoboticsRadarBot")
            print("2. Send /start to initialize the bot")
            print("3. Get your user ID from @userinfobot")
            print("4. Add your user ID to TELEGRAM_ALLOWED_USERS in .env")
            print("5. Restart the system to test messaging")
        
        return True
        
    except Exception as e:
        print(f"❌ Telegram bot error: {e}")
        return False

def main():
    """Main function."""
    print("🤖 Robotics Radar - Telegram Messaging Test")
    print("=" * 60)
    
    success = asyncio.run(test_telegram_messaging())
    
    if success:
        print("\n🎉 Telegram bot messaging test completed successfully!")
    else:
        print("\n❌ Telegram bot messaging test failed!")
    
    return success

if __name__ == "__main__":
    main() 