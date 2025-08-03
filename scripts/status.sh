#!/bin/bash
# Status script for Robotics Radar

echo "🤖 Robotics Radar - Status Check"
echo "==============================="

# Check if scheduler is running
SCHEDULER_PID=$(pgrep -f "python.*scheduler.py" | head -1)
if [[ -n "$SCHEDULER_PID" ]]; then
    echo "✅ Scheduler: Running (PID: $SCHEDULER_PID)"
else
    echo "❌ Scheduler: Not running"
fi

# Check if dashboard is running
DASHBOARD_PID=$(pgrep -f "streamlit.*dashboard.py" | head -1)
if [[ -n "$DASHBOARD_PID" ]]; then
    echo "✅ Dashboard: Running (PID: $DASHBOARD_PID)"
    echo "   URL: http://localhost:8501"
else
    echo "❌ Dashboard: Not running"
fi

# Check if port 8501 is in use
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ Port 8501: In use (dashboard should be accessible)"
else
    echo "❌ Port 8501: Not in use"
fi

# Check cron jobs
echo ""
echo "📅 Scheduled Jobs:"
echo "=================="
if crontab -l 2>/dev/null | grep -q "run.sh"; then
    crontab -l 2>/dev/null | grep "run.sh" | while read -r line; do
        echo "   $line"
    done
else
    echo "   No scheduled jobs found"
fi

# Check recent logs
echo ""
echo "📋 Recent Activity:"
echo "=================="
if [[ -f "logs/scheduler.log" ]]; then
    echo "Scheduler (last 3 lines):"
    tail -3 logs/scheduler.log 2>/dev/null || echo "   No recent logs"
else
    echo "   No scheduler logs found"
fi

echo ""
echo "💡 Quick Commands:"
echo "=================="
echo "   Start: ./scripts/run.sh start"
echo "   Stop:  ./scripts/run.sh stop"
echo "   Setup schedule: ./scripts/setup_scheduled_running.sh"
echo "   View logs: tail -f logs/scheduler.log" 