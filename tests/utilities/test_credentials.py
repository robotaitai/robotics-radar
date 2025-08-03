#!/usr/bin/env python3
"""
Simple test runner to verify Twitter and Telegram credentials.
Run this script to test if your API credentials are working correctly.
"""

import os
import sys
import subprocess

def load_env_vars():
    """Load environment variables from .env file."""
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def run_test(test_file, test_name):
    """Run a specific test file."""
    print(f"\n{'='*60}")
    print(f"🧪 Running {test_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([
            sys.executable, test_file
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Test completed successfully!")
            print(result.stdout)
        else:
            print("❌ Test failed!")
            print(result.stdout)
            print(result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Test timed out!")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def main():
    """Main test runner."""
    print("🤖 Robotics Radar - Credential Tests")
    print("=" * 60)
    
    # Load environment variables
    print("📋 Loading environment variables...")
    load_env_vars()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please create a .env file with your credentials:")
        print("cp env.example .env")
        print("Then edit .env with your actual API keys")
        return False
    
    print("✅ Environment variables loaded")
    
    # Run Twitter API tests
    twitter_success = run_test(
        'tests/test_twitter_api.py',
        'Twitter API Tests'
    )
    
    # Run Telegram bot tests
    telegram_success = run_test(
        'tests/test_telegram_bot.py',
        'Telegram Bot Tests'
    )
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Summary")
    print(f"{'='*60}")
    
    if twitter_success:
        print("✅ Twitter API: Working correctly")
    else:
        print("❌ Twitter API: Issues detected")
    
    if telegram_success:
        print("✅ Telegram Bot: Working correctly")
    else:
        print("❌ Telegram Bot: Issues detected")
    
    if twitter_success and telegram_success:
        print("\n🎉 All credentials are working correctly!")
        print("You're ready to run the Robotics Radar system!")
        return True
    else:
        print("\n⚠️  Some issues detected. Please check your credentials.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 