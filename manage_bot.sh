#!/bin/bash

# Trading Agent Bot Management Script

case "$1" in
    start)
        echo "🤖 Starting Trading Agent Bot..."
        nohup python3 bot.py > bot.log 2>&1 &
        echo "✅ Bot started in background. PID: $!"
        echo "📋 View logs with: tail -f bot.log"
        ;;
    stop)
        echo "🛑 Stopping Trading Agent Bot..."
        pkill -f "python3 bot.py"
        echo "✅ Bot stopped"
        ;;
    restart)
        echo "🔄 Restarting Trading Agent Bot..."
        pkill -f "python3 bot.py"
        sleep 2
        nohup python3 bot.py > bot.log 2>&1 &
        echo "✅ Bot restarted. PID: $!"
        ;;
    status)
        if pgrep -f "python3 bot.py" > /dev/null; then
            echo "✅ Bot is running (PID: $(pgrep -f 'python3 bot.py'))"
        else
            echo "❌ Bot is not running"
        fi
        ;;
    logs)
        echo "📋 Bot logs (last 50 lines):"
        tail -50 bot.log
        ;;
    follow)
        echo "📋 Following bot logs (Ctrl+C to exit):"
        tail -f bot.log
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|follow}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the bot in background"
        echo "  stop    - Stop the bot"
        echo "  restart - Restart the bot"
        echo "  status  - Check if bot is running"
        echo "  logs    - Show recent logs"
        echo "  follow  - Follow logs in real-time"
        exit 1
        ;;
esac