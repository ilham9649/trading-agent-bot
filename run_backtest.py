#!/usr/bin/env python3
"""Wrapper script to run backtest from project root.

This is a convenience wrapper that calls the main backtest script
in the backtesting/ folder.

Usage:
    python run_backtest.py --symbol AAPL --start 2024-07-01 --end 2024-10-01
    
This is equivalent to:
    python backtesting/run.py --symbol AAPL --start 2024-07-01 --end 2024-10-01
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the backtest script from backtesting folder."""
    # Get the backtest script path
    script_path = Path(__file__).parent / "backtesting" / "run.py"
    
    if not script_path.exists():
        print(f"Error: Backtest script not found at {script_path}")
        print("Make sure you're running from the project root directory.")
        return 1
    
    # Pass all arguments to the backtest script
    cmd = [sys.executable, str(script_path)] + sys.argv[1:]
    
    # Run the backtest
    return subprocess.call(cmd)

if __name__ == '__main__':
    sys.exit(main())
