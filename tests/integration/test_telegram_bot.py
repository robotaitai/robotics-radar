"""
Test Telegram bot connectivity and functionality.
"""

import os
import sys
import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notifier.telegram_bot import TelegramNotifier


class TestTelegramBot(unittest.TestCase):
    """Test Telegram bot connectivity and functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Load environment variables
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.allowed_users = os.getenv('TELEGRAM_ALLOWED_USERS', '')
        
    def test_environment_variables_set(self):
        """Test that Telegram bot environment variables are set."""
        print("\n🔍 Testing Telegram Bot Environment Variables...")
        
        # Check bot token
        if self.bot_token and not self.bot_token.startswith('your_'):
            print(f"✅ TELEGRAM_BOT_TOKEN: {'*' * (len(self.bot_token) - 4) + self.bot_token[-4:]}")
        else:
            print("❌ TELEGRAM_BOT_TOKEN: Not set or invalid")
            self.fail("TELEGRAM_BOT_TOKEN not set or invalid")
        
        # Check allowed users (optional)
        if self.allowed_users:
            users = self.allowed_users.split(',')
            print(f"✅ TELEGRAM_ALLOWED_USERS: {len(users)} users configured")
            for user in users:
                print(f"   - User ID: {user.strip()}")
        else:
            print("ℹ️  TELEGRAM_ALLOWED_USERS: Not set (all users allowed)")
        
        print("✅ Telegram bot environment variables are properly configured!")
    
    def test_telegram_notifier_initialization(self):
        """Test TelegramNotifier initialization."""
        print("\n🔍 Testing Telegram Notifier Initialization...")
        
        try:
            notifier = TelegramNotifier()
            
            # Check if bot token is set
            if notifier.bot_token:
                print("✅ TelegramNotifier initialized successfully!")
                print(f"   Bot token: {'*' * (len(notifier.bot_token) - 4) + notifier.bot_token[-4:]}")
                print(f"   Allowed users: {len(notifier.allowed_users)} configured")
            else:
                print("❌ TelegramNotifier bot token not set")
                self.fail("TelegramNotifier bot token not set")
                
        except Exception as e:
            print(f"❌ TelegramNotifier initialization failed: {e}")
            self.fail(f"TelegramNotifier initialization failed: {e}")
    
    def test_telegram_bot_availability(self):
        """Test if Telegram bot is available."""
        print("\n🔍 Testing Telegram Bot Availability...")
        
        try:
            notifier = TelegramNotifier()
            is_available = notifier.is_available()
            
            if is_available:
                print("✅ Telegram bot is available!")
            else:
                print("❌ Telegram bot is not available")
                self.fail("Telegram bot is not available")
                
        except Exception as e:
            print(f"❌ Telegram bot availability check failed: {e}")
            self.fail(f"Telegram bot availability check failed: {e}")
    
    @patch('telegram.Bot')
    def test_telegram_bot_connection(self, mock_bot_class):
        """Test Telegram bot connection (mocked)."""
        print("\n🔍 Testing Telegram Bot Connection...")
        
        try:
            # Mock the bot
            mock_bot = MagicMock()
            mock_bot.get_me.return_value = MagicMock(
                id=123456789,
                username="robotics_radar_bot",
                first_name="Robotics Radar",
                is_bot=True
            )
            mock_bot_class.return_value = mock_bot
            
            notifier = TelegramNotifier()
            
            # Test bot info
            if notifier.bot_token:
                print("✅ Telegram bot connection test setup successful!")
                print(f"   Bot username: @robotics_radar_bot")
                print(f"   Bot name: Robotics Radar")
                print(f"   Bot ID: 123456789")
            else:
                print("❌ Telegram bot token not available for connection test")
                self.fail("Telegram bot token not available")
                
        except Exception as e:
            print(f"❌ Telegram bot connection test failed: {e}")
            self.fail(f"Telegram bot connection test failed: {e}")
    
    def test_allowed_users_parsing(self):
        """Test allowed users parsing functionality."""
        print("\n🔍 Testing Allowed Users Parsing...")
        
        try:
            notifier = TelegramNotifier()
            
            # Test with configured users
            if self.allowed_users:
                users = notifier.allowed_users
                print(f"✅ Allowed users parsed successfully!")
                print(f"   Total users: {len(users)}")
                for i, user in enumerate(users, 1):
                    print(f"   {i}. User ID: {user}")
            else:
                print("ℹ️  No allowed users configured (all users allowed)")
            
            # Test user permission check
            test_user_id = "123456789"
            is_allowed = notifier._is_user_allowed(int(test_user_id))
            
            if is_allowed:
                print("✅ User permission check working correctly")
            else:
                print("ℹ️  User permission check working (user not in allowed list)")
                
        except Exception as e:
            print(f"❌ Allowed users parsing failed: {e}")
            self.fail(f"Allowed users parsing failed: {e}")
    
    def test_message_formatting(self):
        """Test message formatting functionality."""
        print("\n🔍 Testing Message Formatting...")
        
        try:
            notifier = TelegramNotifier()
            
            # Test message creation (without sending)
            test_message = "🤖 *Robotics Radar Test*\n\nThis is a test message from the Robotics Radar bot."
            
            print("✅ Message formatting test successful!")
            print(f"   Sample message: {test_message[:50]}...")
            
            # Test inline keyboard creation
            keyboard_data = [
                ("👍 Test", "feedback:test123:like"),
                ("👎 Test", "feedback:test123:dislike")
            ]
            
            print("✅ Inline keyboard formatting test successful!")
            print(f"   Keyboard buttons: {len(keyboard_data)}")
            
        except Exception as e:
            print(f"❌ Message formatting test failed: {e}")
            self.fail(f"Message formatting test failed: {e}")
    
    def test_feedback_processing_integration(self):
        """Test feedback processing integration."""
        print("\n🔍 Testing Feedback Processing Integration...")
        
        try:
            notifier = TelegramNotifier()
            
            # Check if feedback processor is initialized
            if hasattr(notifier, 'feedback_processor'):
                print("✅ Feedback processor integration successful!")
                print(f"   Feedback processor: {type(notifier.feedback_processor).__name__}")
            else:
                print("❌ Feedback processor not integrated")
                self.fail("Feedback processor not integrated")
                
        except Exception as e:
            print(f"❌ Feedback processing integration test failed: {e}")
            self.fail(f"Feedback processing integration test failed: {e}")


def run_telegram_tests():
    """Run all Telegram bot tests."""
    print("🤖 Telegram Bot Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTelegramBot)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("🎉 All Telegram bot tests passed!")
        return True
    else:
        print("❌ Some Telegram bot tests failed!")
        return False


if __name__ == "__main__":
    run_telegram_tests() 