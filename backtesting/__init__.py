"""Backtesting module for trading-agent-bot.

This module provides comprehensive backtesting capabilities for the trading agent.
All backtest-related code is organized here for clean separation from live trading.

Main components:
- engine.py: Core backtesting engine with portfolio simulation
- run.py: Main CLI for running backtests
- quick.py: Quick backtest interface
- visualize.py: Generate charts and reports
- verify.py: Verify date handling and setup

Usage:
    From project root:
    python backtesting/run.py --symbol AAPL --start 2024-07-01 --end 2024-10-01
    python backtesting/quick.py AAPL 30
"""

from pathlib import Path

__version__ = "1.0.0"
__author__ = "Trading Agent Bot"

# Module paths
MODULE_DIR = Path(__file__).parent
RESULTS_DIR = MODULE_DIR / "results"
DOCS_DIR = MODULE_DIR / "docs"

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
