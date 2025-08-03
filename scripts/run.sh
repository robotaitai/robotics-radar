#!/bin/bash

# Robotics Radar Run Script
# This script starts the scheduler and manages the application

set -e  # Exit on any error

echo "🤖 Robotics Radar - Run Script"
echo "=============================="

# Check if virtual environment exists
if [ ! -d "robotics-radar-env" ]; then
    echo "❌ Virtual environment not found. Please run './scripts/install.sh' first"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run './scripts/install.sh' first"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source robotics-radar-env/bin/activate

# Load environment variables
echo "Loading environment variables..."
set -a  # automatically export all variables
source .env
set +a

# Check if required environment variables are set
echo "Checking environment variables..."
required_vars=(
    "TELEGRAM_BOT_TOKEN"
    "TELEGRAM_ALLOWED_USERS"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "your_$(echo $var | tr '[:upper:]' '[:lower:]')_here" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Missing or invalid environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please update the .env file with your actual credentials"
    exit 1
fi

echo "✅ All required environment variables are set"

# Create log directory if it doesn't exist
mkdir -p logs

# Function to handle graceful shutdown
cleanup() {
    echo ""
    echo "🛑 Shutting down Robotics Radar..."
    
    # Kill background processes
    if [ ! -z "$SCHEDULER_PID" ]; then
        echo "Stopping scheduler (PID: $SCHEDULER_PID)..."
        kill $SCHEDULER_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$DASHBOARD_PID" ]; then
        echo "Stopping dashboard (PID: $DASHBOARD_PID)..."
        kill $DASHBOARD_PID 2>/dev/null || true
    fi
    
    echo "✅ Shutdown complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Function to start scheduler
start_scheduler() {
    echo "Starting Robotics Radar scheduler..."
    python scraper/scheduler.py > logs/scheduler.log 2>&1 &
    SCHEDULER_PID=$!
    echo "✅ Scheduler started (PID: $SCHEDULER_PID)"
}

# Function to start dashboard
start_dashboard() {
    echo "Starting analytics dashboard..."
    
    # Kill any existing processes on port 8501
    lsof -ti:8501 | xargs kill -9 2>/dev/null || true
    sleep 2
    
    # Start dashboard in background
    streamlit run analytics/dashboard.py --server.port 8501 --server.headless true > logs/dashboard.log 2>&1 &
    DASHBOARD_PID=$!
    echo "✅ Dashboard started (PID: $DASHBOARD_PID)"
    echo "📊 Dashboard available at: http://localhost:8501"
}

# Function to show status
show_status() {
    echo ""
    echo "📊 Robotics Radar Status:"
    echo "========================="
    
    if [ ! -z "$SCHEDULER_PID" ] && kill -0 $SCHEDULER_PID 2>/dev/null; then
        echo "✅ Scheduler: Running (PID: $SCHEDULER_PID)"
    else
        echo "❌ Scheduler: Not running"
    fi
    
    if [ ! -z "$DASHBOARD_PID" ] && kill -0 $DASHBOARD_PID 2>/dev/null; then
        echo "✅ Dashboard: Running (PID: $DASHBOARD_PID)"
        echo "   URL: http://localhost:8501"
    else
        echo "❌ Dashboard: Not running"
    fi
    
    # Show recent logs
    echo ""
    echo "📋 Recent Logs:"
    echo "==============="
    if [ -f "logs/scheduler.log" ]; then
        echo "Scheduler (last 5 lines):"
        tail -5 logs/scheduler.log
    fi
    
    if [ -f "logs/dashboard.log" ]; then
        echo ""
        echo "Dashboard (last 5 lines):"
        tail -5 logs/dashboard.log
    fi
}

# Function to run once
run_once() {
    echo "Running single fetch cycle..."
    python -c "
import sys
sys.path.append('.')
from scraper.rss_fetcher import RSSFetcher

try:
    fetcher = RSSFetcher()
    fetcher.run_fetch_cycle()
    print('✅ Fetch cycle completed')
except Exception as e:
    print(f'Error in fetch cycle: {e}')
    exit(1)
"
}

# Function to show help
show_help() {
    echo ""
    echo "Robotics Radar - Available Commands:"
    echo "===================================="
    echo "  start     - Start scheduler and dashboard"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  status    - Show current status"
    echo "  once      - Run single fetch cycle"
    echo "  logs      - Show recent logs"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./scripts/run.sh start"
    echo "  ./scripts/run.sh status"
    echo "  ./scripts/run.sh once"
    echo ""
}

# Main script logic
case "${1:-start}" in
    "start")
        echo "🚀 Starting Robotics Radar..."
        start_scheduler
        sleep 2
        start_dashboard
        sleep 2
        show_status
        echo ""
        echo "🎉 Robotics Radar is now running!"
        echo "Press Ctrl+C to stop all services"
        echo ""
        
        # Keep script running (without problematic restart loop)
        echo "💡 System is now running in background mode"
        echo "💡 Use './scripts/run.sh status' to check status"
        echo "💡 Use './scripts/run.sh stop' to stop everything"
        echo ""
        echo "🔄 Press Ctrl+C to stop all services"
        
        # Simple wait loop - no automatic restarts
        while true; do
            sleep 30
            # Just keep the script alive, let the background processes run independently
        done
        ;;
    
    "stop")
        echo "🛑 Stopping Robotics Radar..."
        cleanup
        ;;
    
    "restart")
        echo "🔄 Restarting Robotics Radar..."
        cleanup
        sleep 2
        $0 start
        ;;
    
    "status")
        show_status
        ;;
    
    "once")
        run_once
        ;;
    
    "logs")
        echo "📋 Recent Logs:"
        echo "==============="
        if [ -f "logs/scheduler.log" ]; then
            echo "Scheduler Log:"
            tail -20 logs/scheduler.log
            echo ""
        fi
        
        if [ -f "logs/dashboard.log" ]; then
            echo "Dashboard Log:"
            tail -20 logs/dashboard.log
            echo ""
        fi
        ;;
    
    "help"|"-h"|"--help")
        show_help
        ;;
    
    *)
        echo "❌ Unknown command: $1"
        show_help
        exit 1
        ;;
esac 