#!/bin/bash
# Example Backtesting Commands
# This script shows various ways to run backtests on your trading agent

echo "======================================"
echo "Trading Agent Backtesting Examples"
echo "======================================"
echo ""

# Make sure scripts are executable
chmod +x run_backtest.py backtest_quick.py visualize_backtest.py

echo "Choose an example to run:"
echo ""
echo "1. Quick 30-day backtest on AAPL"
echo "2. Quick 60-day backtest on TSLA with $50k capital"
echo "3. Full backtest on MSFT (Jan-Oct 2024)"
echo "4. Conservative strategy (high confidence threshold)"
echo "5. Aggressive strategy (low confidence threshold)"
echo "6. Multiple stocks comparison"
echo "7. Exit"
echo ""

read -p "Enter your choice (1-7): " choice

case $choice in
    1)
        echo ""
        echo "Running: Quick 30-day backtest on AAPL..."
        python backtest_quick.py AAPL 30
        ;;
    2)
        echo ""
        echo "Running: Quick 60-day backtest on TSLA with $50,000..."
        python backtest_quick.py TSLA 60 50000
        ;;
    3)
        echo ""
        echo "Running: Full backtest on MSFT (Jan-Oct 2024)..."
        python run_backtest.py --symbol MSFT --start 2024-01-01 --end 2024-10-01
        ;;
    4)
        echo ""
        echo "Running: Conservative strategy (min confidence 7)..."
        python run_backtest.py --symbol AAPL --start 2024-07-01 --end 2024-10-01 --min-confidence 7
        ;;
    5)
        echo ""
        echo "Running: Aggressive strategy (min confidence 3)..."
        python run_backtest.py --symbol AAPL --start 2024-07-01 --end 2024-10-01 --min-confidence 3
        ;;
    6)
        echo ""
        echo "Running: Multiple stocks comparison (last 30 days)..."
        echo ""
        echo "Testing AAPL..."
        python backtest_quick.py AAPL 30
        echo ""
        echo "Testing GOOGL..."
        python backtest_quick.py GOOGL 30
        echo ""
        echo "Testing MSFT..."
        python backtest_quick.py MSFT 30
        echo ""
        echo "Comparison complete! Review the results above."
        ;;
    7)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo "Backtest Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Review the results above"
echo "2. Check backtest_results/ directory for detailed files"
echo "3. Run visualization: python visualize_backtest.py backtest_results/<filename>.json"
echo "4. Check backtest.log for detailed logs"
echo ""
