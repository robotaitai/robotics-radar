#!/bin/bash

# Smart Publisher Runner for Robotics Radar
# Runs the smart publisher that sends one article every 30 minutes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/smart_publisher.log"
PID_FILE="$PROJECT_ROOT/smart_publisher.pid"
INTERVAL_MINUTES=${2:-30}  # Default 30 minutes, can be overridden

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

# Function to check if publisher is already running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Running
        else
            rm -f "$PID_FILE"  # Clean up stale PID file
        fi
    fi
    return 1  # Not running
}

# Function to start the publisher
start_publisher() {
    if is_running; then
        log_message "${YELLOW}Smart Publisher is already running!${NC}"
        return 1
    fi
    
    log_message "${BLUE}Starting Smart Publisher (interval: ${INTERVAL_MINUTES} minutes)...${NC}"
    
    # Activate virtual environment and start publisher
    cd "$PROJECT_ROOT"
    source test_env/bin/activate
    
    # Start the publisher in background
    nohup python scraper/smart_publisher.py --interval "$INTERVAL_MINUTES" >> "$LOG_FILE" 2>&1 &
    
    # Save PID
    echo $! > "$PID_FILE"
    
    log_message "${GREEN}✅ Smart Publisher started with PID: $(cat "$PID_FILE")${NC}"
    log_message "${BLUE}📊 Check status with: ./scripts/run_smart_publisher.sh status${NC}"
    log_message "${BLUE}📋 View logs with: tail -f $LOG_FILE${NC}"
}

# Function to stop the publisher
stop_publisher() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_message "${YELLOW}Stopping Smart Publisher (PID: $pid)...${NC}"
            kill "$pid"
            rm -f "$PID_FILE"
            log_message "${GREEN}✅ Smart Publisher stopped${NC}"
        else
            log_message "${YELLOW}Smart Publisher not running (stale PID file)${NC}"
            rm -f "$PID_FILE"
        fi
    else
        log_message "${YELLOW}Smart Publisher not running (no PID file)${NC}"
    fi
}

# Function to show status
show_status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        log_message "${GREEN}✅ Smart Publisher is running (PID: $pid)${NC}"
        
        # Show publisher status
        cd "$PROJECT_ROOT"
        source test_env/bin/activate
        python scraper/smart_publisher.py --status
        
        # Show recent logs
        log_message "${BLUE}📋 Recent logs:${NC}"
        tail -n 10 "$LOG_FILE" | sed 's/^/  /'
    else
        log_message "${RED}❌ Smart Publisher is not running${NC}"
    fi
}

# Function to restart the publisher
restart_publisher() {
    log_message "${YELLOW}Restarting Smart Publisher...${NC}"
    stop_publisher
    sleep 2
    start_publisher
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        log_message "${BLUE}📋 Smart Publisher logs:${NC}"
        tail -f "$LOG_FILE"
    else
        log_message "${RED}❌ Log file not found: $LOG_FILE${NC}"
    fi
}

# Main script logic
case "${1:-start}" in
    start)
        start_publisher
        ;;
    stop)
        stop_publisher
        ;;
    restart)
        restart_publisher
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    once)
        log_message "${BLUE}Running one publish cycle...${NC}"
        cd "$PROJECT_ROOT"
        source test_env/bin/activate
        python scraper/smart_publisher.py --once
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|once} [interval_minutes]"
        echo ""
        echo "Commands:"
        echo "  start   - Start the smart publisher (default: 30 min interval)"
        echo "  stop    - Stop the smart publisher"
        echo "  restart - Restart the smart publisher"
        echo "  status  - Show publisher status and recent logs"
        echo "  logs    - Show live logs"
        echo "  once    - Run one publish cycle and exit"
        echo ""
        echo "Examples:"
        echo "  $0 start           # Start with 30 min interval"
        echo "  $0 start 15        # Start with 15 min interval"
        echo "  $0 status          # Check status"
        echo "  $0 logs            # View live logs"
        exit 1
        ;;
esac 