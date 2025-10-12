"""Quick Backtest Script - For rapid testing with recent data.

This is a simplified script for quick backtests on recent periods.
Perfect for testing your strategy on the last 30, 60, or 90 days.

Usage:
    python backtest_quick.py AAPL 30     # Last 30 days
    python backtest_quick.py TSLA 60     # Last 60 days
    python backtest_quick.py MSFT 90 50000  # Last 90 days with $50k capital
"""

import asyncio
import sys
from datetime import datetime, timedelta

import sys
from pathlib import Path
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtesting.run import main as run_main


async def quick_backtest():
    """Run a quick backtest with simplified arguments."""
    if len(sys.argv) < 3:
        print("Usage: python backtest_quick.py <SYMBOL> <DAYS> [CAPITAL]")
        print("\nExamples:")
        print("  python backtest_quick.py AAPL 30        # Last 30 days")
        print("  python backtest_quick.py TSLA 60 50000  # Last 60 days with $50k")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    days = int(sys.argv[2])
    capital = float(sys.argv[3]) if len(sys.argv) > 3 else 100000.0
    
    # Calculate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Override sys.argv for the main script
    sys.argv = [
        'run_backtest.py',
        '--symbol', symbol,
        '--start', start_date.strftime('%Y-%m-%d'),
        '--end', end_date.strftime('%Y-%m-%d'),
        '--capital', str(capital)
    ]
    
    print(f"\n🚀 Quick Backtest: {symbol}")
    print(f"📅 Period: Last {days} days")
    print(f"💰 Capital: ${capital:,.2f}\n")
    
    await run_main()


if __name__ == '__main__':
    asyncio.run(quick_backtest())
