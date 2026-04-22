"""Core backtesting functionality."""

from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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
