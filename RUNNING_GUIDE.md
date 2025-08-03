# 🤖 Robotics Radar - Running Guide

## 🚀 Quick Start

### **Manual Running (Recommended for Development/Testing)**
```bash
# Start the system
./scripts/run.sh start

# Stop the system (Ctrl+C or in another terminal)
./scripts/run.sh stop

# Check status
./scripts/status.sh
```

## 📅 Scheduled Running Options

### **Option 1: Business Hours (9 AM - 6 PM, Mon-Fri)**
```bash
./scripts/setup_scheduled_running.sh
# Choose option 1
```

### **Option 2: Daily Morning (8 AM - 10 AM)**
```bash
./scripts/setup_scheduled_running.sh
# Choose option 3
```

### **Option 3: Twice Daily (9 AM and 6 PM)**
```bash
./scripts/setup_scheduled_running.sh
# Choose option 4
```

### **Option 4: Custom Schedule**
```bash
./scripts/setup_scheduled_running.sh
# Choose option 5 and enter your cron schedules
```

## 🕐 When Should It Be Running?

### **🟢 Recommended Schedules:**

1. **Business Hours Only** (9 AM - 6 PM, Mon-Fri)
   - ✅ Get updates during work hours
   - ✅ Save resources on weekends/nights
   - ✅ Perfect for professionals

2. **Daily Morning** (8 AM - 10 AM)
   - ✅ Start your day with robotics news
   - ✅ Minimal resource usage
   - ✅ Great for daily briefings

3. **Twice Daily** (9 AM and 6 PM)
   - ✅ Morning and evening updates
   - ✅ Balanced resource usage
   - ✅ Good for active users

4. **Always On** (Manual start/stop)
   - ✅ Real-time updates every 10 seconds
   - ⚠️ Higher resource usage
   - ✅ Best for development/testing

### **🔴 When NOT to Run:**

- **Weekends** (if you don't need weekend updates)
- **Late Night** (11 PM - 6 AM)
- **Holidays** (if you're not working)
- **Low Battery** (on laptops)

## 📊 What You Get When Running

### **🤖 Telegram Messages**
- **Frequency**: Every 10 seconds (when running)
- **Content**: Top 10 robotics articles
- **Features**: 
  - ⭐⭐⭐⭐⭐ 1-5 star rating system
  - Enhanced summaries
  - Direct article links
  - Author information

### **📈 Analytics Dashboard**
- **URL**: http://localhost:8501
- **Features**:
  - Article statistics
  - Trending topics
  - Author rankings
  - Engagement analytics

### **💾 Database**
- **Storage**: SQLite database (`data/radar.db`)
- **Content**: Articles from 20+ robotics sources
- **History**: Configurable (30-90 days)

## 🛠️ Management Commands

### **Status & Monitoring**
```bash
# Check if system is running
./scripts/status.sh

# View live logs
tail -f logs/scheduler.log

# Check database size
ls -lh data/radar.db
```

### **Data Management**
```bash
# Import 90 days of historical data
python scripts/import_90_days.py

# Clear all data (fresh start)
python -c "from storage.database import DatabaseManager; db = DatabaseManager(); db.clear_all_data()"
```

### **Scheduled Jobs Management**
```bash
# View current cron jobs
crontab -l

# Remove all scheduled jobs
crontab -r

# Edit jobs manually
crontab -e
```

## 🔧 Troubleshooting

### **System Won't Start**
```bash
# Kill all processes
pkill -f "python.*scheduler"
pkill -f "streamlit"

# Check port conflicts
lsof -i :8501

# Restart
./scripts/run.sh start
```

### **No Telegram Messages**
```bash
# Check environment variables
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_ALLOWED_USERS

# Test manual message
python -c "from notifier.telegram_bot import TelegramNotifier; notifier = TelegramNotifier(); notifier.send_top_tweets_sync([])"
```

### **Dashboard Issues**
```bash
# Check if port 8501 is free
lsof -i :8501

# Restart dashboard only
pkill -f "streamlit"
streamlit run analytics/dashboard.py
```

## 📱 Telegram Bot Commands

When the system is running, you can interact with the bot:

- `/start` - Welcome message
- `/help` - Show available commands
- `/stats` - Show system statistics
- `/top` - Get top articles manually

## 💡 Pro Tips

1. **Start Small**: Begin with manual running to test
2. **Monitor Resources**: Check CPU/memory usage
3. **Backup Database**: Copy `data/radar.db` regularly
4. **Customize Feeds**: Edit `config/feeds.yaml` for your interests
5. **Adjust Frequency**: Modify fetch interval in `.env` file

## 🎯 Recommended Setup for Different Users

### **👨‍💻 Developer/Researcher**
- **Schedule**: Business hours (9 AM - 6 PM, Mon-Fri)
- **Dashboard**: Always accessible
- **Notifications**: High frequency (every 10 seconds)

### **📰 News Enthusiast**
- **Schedule**: Twice daily (9 AM and 6 PM)
- **Dashboard**: Check occasionally
- **Notifications**: Moderate frequency

### **🏢 Business Professional**
- **Schedule**: Daily morning (8 AM - 10 AM)
- **Dashboard**: Weekly review
- **Notifications**: Daily digest

### **🎓 Student/Academic**
- **Schedule**: Weekdays only (9 AM - 6 PM)
- **Dashboard**: Research tool
- **Notifications**: As needed

## 🔄 Migration & Updates

### **Updating the System**
```bash
# Pull latest changes
git pull

# Update dependencies
pip install -r requirements.txt

# Restart system
./scripts/run.sh stop
./scripts/run.sh start
```

### **Database Migrations**
```bash
# Run rating system migration
python scripts/migrate_rating_system.py

# Import historical data
python scripts/import_90_days.py
```

---

**🎉 You're all set! Choose the running schedule that works best for you and enjoy your personalized robotics news feed!** 