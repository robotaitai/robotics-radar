#!/usr/bin/env python3
"""
Profile switcher for Robotics Radar feeds configuration.
Easily switch between different feed profiles.
"""

import sys
import os
import yaml

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_config():
    """Load the current feeds configuration."""
    feeds_path = "config/feeds.yaml"
    
    if not os.path.exists(feeds_path):
        print(f"❌ Feeds configuration not found at {feeds_path}")
        return None
    
    try:
        with open(feeds_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return None

def save_config(config):
    """Save the configuration back to file."""
    feeds_path = "config/feeds.yaml"
    
    try:
        with open(feeds_path, 'w') as file:
            yaml.dump(config, file, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False

def show_profiles(config):
    """Show available profiles and current selection."""
    profiles = config.get('profiles', {})
    active_profile = config.get('active_profile', 'frontier')
    
    print("📋 Available Profiles:")
    print("=" * 50)
    
    for profile_key, profile_data in profiles.items():
        status = "✅ ACTIVE" if profile_key == active_profile else "  "
        print(f"{status} {profile_key.upper()}")
        print(f"     Name: {profile_data.get('name', 'Unknown')}")
        print(f"     Description: {profile_data.get('description', 'No description')}")
        print(f"     Feeds: {len(profile_data.get('feeds', []))}")
        print()

def switch_profile(profile_name):
    """Switch to the specified profile."""
    config = load_config()
    if not config:
        return False
    
    profiles = config.get('profiles', {})
    
    if profile_name not in profiles:
        print(f"❌ Profile '{profile_name}' not found!")
        print("Available profiles:")
        for key in profiles.keys():
            print(f"  • {key}")
        return False
    
    # Update active profile
    config['active_profile'] = profile_name
    
    # Save configuration
    if save_config(config):
        profile_data = profiles[profile_name]
        print(f"✅ Switched to profile: {profile_data['name']}")
        print(f"📝 {profile_data['description']}")
        print(f"📰 {len(profile_data.get('feeds', []))} feeds enabled")
        return True
    else:
        print("❌ Failed to save configuration")
        return False

def main():
    """Main function."""
    if len(sys.argv) < 2:
        # Show current profiles
        config = load_config()
        if config:
            show_profiles(config)
            print("💡 Usage: python scripts/switch_profile.py <profile_name>")
            print("💡 Example: python scripts/switch_profile.py frontier")
        return
    
    profile_name = sys.argv[1].lower()
    switch_profile(profile_name)

if __name__ == "__main__":
    main() 