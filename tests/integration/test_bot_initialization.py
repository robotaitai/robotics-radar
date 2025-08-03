#!/usr/bin/env python3
"""
Test script to check Telegram bot initialization and message sending.
"""

import os
import sys
import asyncio
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from notifier.telegram_bot import TelegramNotifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bot():
    """Test bot initialization and message sending."""
    print("🤖 Testing Telegram Bot Initialization")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Create notifier
    notifier = TelegramNotifier()
    
    print(f"✅ Notifier created")
    print(f"✅ Available: {notifier.is_available()}")
    print(f"✅ Allowed users: {notifier.allowed_users}")
    print(f"✅ Application: {notifier.application}")
    
    if not notifier.application:
        print("❌ Application is None - trying to start bot...")
        try:
            await notifier.start_bot()
            print(f"✅ Bot started, Application: {notifier.application}")
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            return False
    
    # Test sending a simple message
    print("\n📤 Testing message sending...")
    try:
        from telegram import Bot
        bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        
        for user_id in notifier.allowed_users:
            print(f"Sending test message to user {user_id}...")
            await bot.send_message(
                chat_id=user_id,
                text="🤖 Test message from bot initialization test"
            )
            print(f"✅ Message sent to user {user_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending test message: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bot())
    if success:
        print("\n🎉 Bot initialization test completed successfully!")
    else:
        print("\n❌ Bot initialization test failed!")
    sys.exit(0 if success else 1) 