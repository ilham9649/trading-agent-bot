"""Backtesting module for trading-agent-bot.

This module provides comprehensive backtesting capabilities for trading agent.
All backtest-related code is organized here for clean separation from live trading.

Main components:
- core/: Core backtesting engine with portfolio simulation
- scripts/: CLI entry points for running backtests
- utils/: Helper functions for visualization and metrics
- tests/: Verification and setup testing

Usage:
    From project root:
    python run_backtest.py --symbol AAPL --start 2024-07-01 --end 2024-10-01
    python backtest_quick.py AAPL 30

    Or directly:
    python backtesting/scripts/run.py --symbol AAPL --start 2024-07-01 --end 2024-10-01
    python backtesting/scripts/quick.py AAPL 30
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

# Core exports
from backtesting.core.engine import (
    BacktestEngine,
    BacktestConfig,
    BacktestResult,
    Trade,
    Position,
    PositionSide,
    save_backtest_result,
    update_backtest_index,
)

__all__ = [
    'BacktestEngine',
    'BacktestConfig',
    'BacktestResult',
    'Trade',
    'Position',
    'PositionSide',
    'save_backtest_result',
    'update_backtest_index',
]
