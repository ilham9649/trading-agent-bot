# Backtesting Module Documentation

## Overview

The backtesting module provides comprehensive testing capabilities for trading strategies on historical data.

## Directory Structure

```
backtesting/
├── __init__.py           # Module initialization and exports
├── core/                 # Core backtesting logic
│   ├── __init__.py
│   └── engine.py        # Main backtesting engine
├── scripts/              # CLI entry points
│   ├── __init__.py
│   ├── run.py           # Full backtest CLI
│   └── quick.py        # Quick backtest CLI
├── utils/                # Helper utilities
│   ├── __init__.py
│   └── visualize.py    # Visualization and reporting
├── tests/                # Verification and testing
│   ├── __init__.py
│   ├── verify.py       # Date handling verification
│   └── test_setup.py   # Environment setup checks
├── docs/                 # Documentation (this file)
└── results/              # Generated backtest results
```

## Usage

### Quick Backtest (Last N Days)

From project root:
```bash
python backtest_quick.py AAPL 30       # Last 30 days
python backtest_quick.py TSLA 60 50000 # Last 60 days with $50k capital
```

Or directly:
```bash
python backtesting/scripts/quick.py AAPL 30
```

### Full Backtest (Custom Date Range)

From project root:
```bash
python run_backtest.py --symbol AAPL --start 2024-01-01 --end 2024-10-01
python run_backtest.py --symbol TSLA --start 2023-06-01 --end 2024-06-01 --capital 50000
```

Or directly:
```bash
python backtesting/scripts/run.py --symbol AAPL --start 2024-01-01 --end 2024-10-01
```

### Verify Date Handling

```bash
python backtesting/tests/verify.py
```

### Test Setup

```bash
python backtesting/tests/test_setup.py
```

## Command Line Arguments

### Full Backtest (run.py)

- `--symbol`: Stock ticker (e.g., AAPL, TSLA) [required]
- `--start`: Start date in YYYY-MM-DD format [required]
- `--end`: End date in YYYY-MM-DD format [required]
- `--capital`: Initial capital (default: 100000.0)
- `--commission`: Commission percentage (default: 0.001 = 0.1%)
- `--position-size`: Position size as percentage of capital (default: 1.0 = 100%)
- `--min-confidence`: Minimum confidence to execute trades (default: 5)
- `--output-dir`: Directory for results (default: ./backtesting/results)
- `--debug`: Enable debug logging

### Quick Backtest (quick.py)

- `SYMBOL`: Stock ticker [required]
- `DAYS`: Number of days to backtest [required]
- `CAPITAL`: Initial capital (default: 100000.0) [optional]

## Output Files

Each backtest generates:

```
results/
└── YYYYMMDD_HHMMSS_SYMBOL_start_to_end/
    ├── results.json           # Detailed results in JSON
    ├── config.json           # Backtest configuration
    ├── portfolio_value.csv   # Daily portfolio values
    ├── trades_SYMBOL_YYYYMMDD_HHMMSS.csv  # Trade log
    └── SYMBOL_backtest_visualization.png      # Performance charts
```

## Key Features

1. **Historical Date Handling**: Properly uses historical dates for analysis
2. **Portfolio Simulation**: Tracks cash, positions, and P&L
3. **Transaction Costs**: Models commission fees
4. **Performance Metrics**: Sharpe ratio, max drawdown, win rate, etc.
5. **Trade Logging**: Detailed log of all executed trades
6. **Visualization**: Charts for portfolio value, returns, and metrics

## Important Notes

- Backtesting uses historical dates, but LLM knowledge cutoff may affect analysis quality for very recent periods
- Alpha Vantage API is used for historical news data
- Ensure sufficient API credits before running long backtests
- Minimum backtest period is 5 trading days

## Troubleshooting

### API Credit Issues

If you get `Insufficient balance` errors:
1. Check your Z.AI account balance
2. Purchase GLM API credits
3. Use shorter time periods for testing

### Import Errors

If you see import errors:
1. Ensure you're running from project root
2. Check all dependencies are installed: `pip install -r requirements.txt`
3. Verify TradingAgents library is cloned

### Date Format Errors

Always use `YYYY-MM-DD` format for dates:
- Correct: `2024-01-15`
- Incorrect: `01/15/2024`, `15-01-2024`, `Jan 15 2024`
