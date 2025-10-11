#!/bin/bash

################################################################################
# Trading Agent Bot Management Script
################################################################################
# This script provides convenient commands to manage the trading bot lifecycle
# Usage: ./manage_bot.sh {start|stop|restart|status|logs|follow|check}
################################################################################

set -e  # Exit on error

# Configuration
BOT_SCRIPT="bot.py"
BOT_NAME="Trading Agent Bot"
PYTHON_CMD="python3"
LOG_FILE="bot.log"
PID_FILE=".bot.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

################################################################################
# Helper Functions
################################################################################

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_python() {
    if ! command -v $PYTHON_CMD &> /dev/null; then
        print_error "Python3 is not installed or not in PATH"
        exit 1
    fi
}

check_dependencies() {
    print_info "Checking dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        print_warning "requirements.txt not found"
        return 1
    fi
    
    if [ ! -f "$BOT_SCRIPT" ]; then
        print_error "$BOT_SCRIPT not found"
        exit 1
    fi
    
    if [ ! -f ".env" ]; then
        print_warning ".env file not found"
        print_info "Copy .env.example to .env and configure your API keys"
        return 1
    fi
    
    print_success "Dependencies check passed"
    return 0
}

get_bot_pid() {
    pgrep -f "$PYTHON_CMD $BOT_SCRIPT" || echo ""
}

is_bot_running() {
    local pid=$(get_bot_pid)
    [ -n "$pid" ]
}

################################################################################
# Command Functions
################################################################################

cmd_start() {
    print_info "Starting $BOT_NAME..."
    
    check_python
    
    if ! check_dependencies; then
        print_error "Dependency check failed. Please fix the issues above."
        exit 1
    fi
    
    if is_bot_running; then
        local pid=$(get_bot_pid)
        print_warning "$BOT_NAME is already running (PID: $pid)"
        exit 1
    fi
    
    # Start the bot in background
    nohup $PYTHON_CMD $BOT_SCRIPT > $LOG_FILE 2>&1 &
    local pid=$!
    echo $pid > $PID_FILE
    
    # Wait a moment and check if it's running
    sleep 2
    if is_bot_running; then
        print_success "$BOT_NAME started successfully (PID: $pid)"
        print_info "View logs with: ./manage_bot.sh logs"
        print_info "Follow logs with: ./manage_bot.sh follow"
    else
        print_error "$BOT_NAME failed to start. Check logs for details:"
        tail -20 $LOG_FILE
        exit 1
    fi
}

cmd_stop() {
    print_info "Stopping $BOT_NAME..."
    
    if ! is_bot_running; then
        print_warning "$BOT_NAME is not running"
        return 0
    fi
    
    local pid=$(get_bot_pid)
    
    # Try graceful shutdown first
    kill $pid 2>/dev/null || true
    
    # Wait up to 10 seconds for graceful shutdown
    local count=0
    while is_bot_running && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if is_bot_running; then
        print_warning "Forcing shutdown..."
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
    
    if is_bot_running; then
        print_error "Failed to stop $BOT_NAME"
        exit 1
    else
        print_success "$BOT_NAME stopped"
        rm -f $PID_FILE
    fi
}

cmd_restart() {
    print_info "Restarting $BOT_NAME..."
    cmd_stop
    sleep 2
    cmd_start
}

cmd_status() {
    if is_bot_running; then
        local pid=$(get_bot_pid)
        print_success "$BOT_NAME is running (PID: $pid)"
        
        # Show memory usage if ps is available
        if command -v ps &> /dev/null; then
            local mem=$(ps -o rss= -p $pid 2>/dev/null | awk '{print int($1/1024)}')
            if [ -n "$mem" ]; then
                print_info "Memory usage: ${mem}MB"
            fi
        fi
        
        # Show uptime if the log file exists
        if [ -f "$LOG_FILE" ]; then
            local start_time=$(stat -c %Y "$LOG_FILE" 2>/dev/null || stat -f %m "$LOG_FILE" 2>/dev/null)
            if [ -n "$start_time" ]; then
                local current_time=$(date +%s)
                local uptime=$((current_time - start_time))
                local hours=$((uptime / 3600))
                local minutes=$(((uptime % 3600) / 60))
                print_info "Uptime: ${hours}h ${minutes}m"
            fi
        fi
    else
        print_warning "$BOT_NAME is not running"
        exit 1
    fi
}

cmd_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        print_warning "Log file not found: $LOG_FILE"
        exit 1
    fi
    
    local lines=${1:-50}
    print_info "Showing last $lines lines of logs:"
    echo "----------------------------------------"
    tail -n $lines $LOG_FILE
}

cmd_follow() {
    if [ ! -f "$LOG_FILE" ]; then
        print_warning "Log file not found: $LOG_FILE"
        exit 1
    fi
    
    print_info "Following logs (Ctrl+C to exit):"
    echo "----------------------------------------"
    tail -f $LOG_FILE
}

cmd_check() {
    print_info "Running system checks..."
    echo ""
    
    # Check Python
    print_info "Python version:"
    $PYTHON_CMD --version
    echo ""
    
    # Check dependencies
    check_dependencies
    echo ""
    
    # Check bot status
    cmd_status || true
    echo ""
    
    # Check disk space
    print_info "Disk space:"
    df -h . | tail -1
    echo ""
    
    # Check if TradingAgents is present
    if [ -d "TradingAgents" ]; then
        print_success "TradingAgents directory found"
    else
        print_warning "TradingAgents directory not found"
        print_info "Clone it with: git clone https://github.com/TauricResearch/TradingAgents.git"
    fi
    echo ""
    
    print_success "System check complete"
}

cmd_install() {
    print_info "Installing dependencies..."
    
    check_python
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        $PYTHON_CMD -m venv venv
    fi
    
    # Activate and install
    print_info "Installing packages..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install zhipuai  # GLM SDK
    
    print_success "Dependencies installed successfully"
    print_info "Activate the environment with: source venv/bin/activate"
}

################################################################################
# Main Script
################################################################################

case "$1" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    status)
        cmd_status
        ;;
    logs)
        cmd_logs "${2:-50}"
        ;;
    follow)
        cmd_follow
        ;;
    check)
        cmd_check
        ;;
    install)
        cmd_install
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|follow|check|install}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the bot in background"
        echo "  stop     - Stop the bot gracefully"
        echo "  restart  - Restart the bot"
        echo "  status   - Check if bot is running (with stats)"
        echo "  logs     - Show recent logs (default: 50 lines)"
        echo "           Usage: $0 logs [number_of_lines]"
        echo "  follow   - Follow logs in real-time"
        echo "  check    - Run system checks"
        echo "  install  - Install dependencies in virtual environment"
        exit 1
        ;;
esac

exit 0
