#!/usr/bin/env python3
"""Wrapper script to run quick backtest from project root.

This is a convenience wrapper that calls the quick backtest script
in the backtesting/ folder.

Usage:
    python backtest_quick.py AAPL 30
    python backtest_quick.py TSLA 60 50000
    
This is equivalent to:
    python backtesting/quick.py AAPL 30
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run quick backtest script from backtesting folder."""
    # Get quick backtest script path
    script_path = Path(__file__).parent / "backtesting" / "scripts" / "quick.py"
    
    if not script_path.exists():
        print(f"Error: Quick backtest script not found at {script_path}")
        print("Make sure you're running from project root directory.")
        return 1
    
    # Pass all arguments to script
    cmd = [sys.executable, str(script_path)] + sys.argv[1:]
    
    # Run backtest
    return subprocess.call(cmd)

if __name__ == '__main__':
    sys.exit(main())
