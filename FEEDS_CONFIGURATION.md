# 🤖 Robotics Radar - Feeds Configuration Guide

## 📋 Overview

The Robotics Radar now uses a **unified configuration system** with **profiles** instead of multiple feed files. This makes it easier to switch between different content strategies and maintain configurations.

## 🎯 Available Profiles

### 1. **Frontier** (Default)
- **Focus**: 80% research, 20% industry
- **Goal**: Catch breakthroughs 2-6 months early
- **Sources**: arXiv, AI newsletters, GitHub, HackerNews, Reddit
- **Best for**: Researchers, academics, AI enthusiasts

### 2. **Balanced**
- **Focus**: 50% research, 50% industry
- **Goal**: Good mix for professionals
- **Sources**: Core robotics feeds, some research, some industry
- **Best for**: Industry professionals, balanced coverage

### 3. **Industry**
- **Focus**: 20% research, 80% industry
- **Goal**: Business applications
- **Sources**: Industry news, company blogs, business feeds
- **Best for**: Business users, industry applications

### 4. **Clean**
- **Focus**: Validated feeds only
- **Goal**: Reliable, tested sources
- **Sources**: Only feeds that pass validation tests
- **Best for**: Production environments, reliability

## 🔧 How to Switch Profiles

### Using the Profile Switcher Script
```bash
# Show available profiles
python scripts/switch_profile.py

# Switch to a specific profile
python scripts/switch_profile.py frontier
python scripts/switch_profile.py balanced
python scripts/switch_profile.py industry
python scripts/switch_profile.py clean
```

### Manual Configuration
Edit `config/feeds.yaml` and change the `active_profile` value:
```yaml
active_profile: "frontier"  # Change this to switch profiles
```

## 📊 Profile Comparison

| Profile | Feeds | Research % | Industry % | Best For |
|---------|-------|------------|------------|----------|
| **Frontier** | 22 | 80% | 20% | Researchers, AI enthusiasts |
| **Balanced** | 8 | 50% | 50% | Industry professionals |
| **Industry** | 6 | 20% | 80% | Business users |
| **Clean** | 16 | 60% | 40% | Production environments |

## 🚀 Quick Start

1. **Choose your profile**:
   ```bash
   python scripts/switch_profile.py frontier
   ```

2. **Start the system**:
   ```bash
   ./scripts/run.sh start
   ```

3. **Import historical data**:
   ```bash
   python scripts/import_90_days.py
   ```

## 🔍 Dynamic Source Detection

The system now **automatically detects** which sources are active based on your feed configuration:

- **RSS**: Standard RSS/Atom feeds, blogs, newsletters
- **Reddit**: Reddit subreddits (r/robotics, r/ROS, etc.)
- **HackerNews**: HackerNews robotics/AI discussions
- **GitHub**: GitHub repositories and commits

No more hardcoded source lists!

## 📈 Benefits of the New System

✅ **Single Configuration File**: No more multiple feed files
✅ **Easy Profile Switching**: Change content strategy instantly
✅ **Dynamic Source Detection**: Automatically detects active sources
✅ **Better Organization**: Clear separation of concerns
✅ **Easier Maintenance**: One file to rule them all

## 🛠️ Advanced Configuration

### Adding Custom Feeds
Edit `config/feeds.yaml` and add feeds to any profile:

```yaml
profiles:
  frontier:
    feeds:
      - url: https://your-custom-feed.com/rss
        name: "Your Custom Feed"
        tags: [robotics, custom]
        enabled: true
```

### Custom Scoring Weights
Adjust scoring weights in the configuration:

```yaml
scoring_weights:
  source_bonus:
    arxiv: 30.0
    frontier: 35.0
    # Add your custom weights
```

## 🔄 Migration from Old System

If you were using the old multiple feed files:

1. **Old**: `config/feeds_frontier.yaml` → **New**: Profile "frontier"
2. **Old**: `config/feeds_clean.yaml` → **New**: Profile "clean"
3. **Old**: `config/feeds.yaml` → **New**: Profile "industry"

The new system is backward compatible and includes all your old feeds!

## 💡 Tips

- **Start with Frontier** if you want cutting-edge research
- **Use Balanced** for general professional use
- **Switch to Industry** for business applications
- **Use Clean** for production reliability
- **Run import script** after switching profiles to populate your database

---

**🎉 The new unified system makes Robotics Radar more powerful and easier to use!** 