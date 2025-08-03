#!/bin/bash
# Setup script for scheduled running of Robotics Radar

echo "🤖 Robotics Radar - Scheduled Running Setup"
echo "=========================================="

# Function to add cron job
add_cron_job() {
    local schedule="$1"
    local description="$2"
    local command="$3"
    
    # Remove existing job if it exists
    (crontab -l 2>/dev/null | grep -v "$command") | crontab -
    
    # Add new job
    (crontab -l 2>/dev/null; echo "$schedule $command") | crontab -
    
    echo "✅ Added: $description"
    echo "   Schedule: $schedule"
    echo "   Command: $command"
    echo ""
}

# Get the absolute path to the project
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_SCRIPT="$PROJECT_DIR/scripts/run.sh"

echo "📁 Project directory: $PROJECT_DIR"
echo "🚀 Run script: $RUN_SCRIPT"
echo ""

echo "🕐 Choose your running schedule:"
echo "1. Business hours only (9 AM - 6 PM, Mon-Fri)"
echo "2. Weekdays only (9 AM - 6 PM, Mon-Fri)"
echo "3. Daily morning (8 AM - 10 AM)"
echo "4. Twice daily (9 AM and 6 PM)"
echo "5. Custom schedule"
echo "6. Remove all scheduled jobs"
echo ""

read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        echo "🕐 Setting up Business Hours Schedule (9 AM - 6 PM, Mon-Fri)"
        add_cron_job "0 9 * * 1-5" "Start at 9 AM weekdays" "cd $PROJECT_DIR && $RUN_SCRIPT start"
        add_cron_job "0 18 * * 1-5" "Stop at 6 PM weekdays" "cd $PROJECT_DIR && $RUN_SCRIPT stop"
        ;;
    2)
        echo "🕐 Setting up Weekdays Schedule (9 AM - 6 PM, Mon-Fri)"
        add_cron_job "0 9 * * 1-5" "Start at 9 AM weekdays" "cd $PROJECT_DIR && $RUN_SCRIPT start"
        add_cron_job "0 18 * * 1-5" "Stop at 6 PM weekdays" "cd $PROJECT_DIR && $RUN_SCRIPT stop"
        ;;
    3)
        echo "🕐 Setting up Daily Morning Schedule (8 AM - 10 AM)"
        add_cron_job "0 8 * * *" "Start at 8 AM daily" "cd $PROJECT_DIR && $RUN_SCRIPT start"
        add_cron_job "0 10 * * *" "Stop at 10 AM daily" "cd $PROJECT_DIR && $RUN_SCRIPT stop"
        ;;
    4)
        echo "🕐 Setting up Twice Daily Schedule (9 AM and 6 PM)"
        add_cron_job "0 9 * * *" "Start at 9 AM daily" "cd $PROJECT_DIR && $RUN_SCRIPT start"
        add_cron_job "0 18 * * *" "Stop at 6 PM daily" "cd $PROJECT_DIR && $RUN_SCRIPT stop"
        add_cron_job "0 6 * * *" "Start at 6 AM daily" "cd $PROJECT_DIR && $RUN_SCRIPT start"
        add_cron_job "0 21 * * *" "Stop at 9 PM daily" "cd $PROJECT_DIR && $RUN_SCRIPT stop"
        ;;
    5)
        echo "🕐 Custom Schedule Setup"
        echo "Enter cron schedule (e.g., '0 9 * * 1-5' for 9 AM weekdays):"
        read -p "Start schedule: " start_schedule
        read -p "Stop schedule: " stop_schedule
        
        if [[ -n "$start_schedule" && -n "$stop_schedule" ]]; then
            add_cron_job "$start_schedule" "Custom start" "cd $PROJECT_DIR && $RUN_SCRIPT start"
            add_cron_job "$stop_schedule" "Custom stop" "cd $PROJECT_DIR && $RUN_SCRIPT stop"
        else
            echo "❌ Invalid schedule format"
            exit 1
        fi
        ;;
    6)
        echo "🗑️  Removing all scheduled jobs..."
        crontab -r 2>/dev/null || true
        echo "✅ All scheduled jobs removed"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "📊 Current cron jobs:"
echo "===================="
crontab -l 2>/dev/null || echo "No cron jobs found"

echo ""
echo "💡 Tips:"
echo "- Use 'crontab -l' to view current jobs"
echo "- Use 'crontab -r' to remove all jobs"
echo "- Use 'crontab -e' to edit jobs manually"
echo "- Check logs in $PROJECT_DIR/logs/ for any issues"
echo ""
echo "�� Setup complete!" 