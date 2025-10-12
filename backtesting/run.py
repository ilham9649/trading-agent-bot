"""Run Backtest - Main entry point for backtesting.

This script provides an easy-to-use interface for running backtests
on your trading agent strategy.

Usage:
    python run_backtest.py --symbol AAPL --start 2024-01-01 --end 2024-10-01
    python run_backtest.py --symbol TSLA --start 2023-06-01 --end 2024-06-01 --capital 50000
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import sys
from pathlib import Path
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtesting.engine import BacktestEngine, BacktestConfig, save_backtest_result
from trading_agent import TradingAgent
from config import Config, ConfigurationError

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('backtesting/backtest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Run backtest on trading agent strategy',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument(
        '--symbol',
        type=str,
        required=True,
        help='Stock symbol to backtest (e.g., AAPL, TSLA, MSFT)'
    )
    
    parser.add_argument(
        '--start',
        type=str,
        required=True,
        help='Start date in YYYY-MM-DD format'
    )
    
    parser.add_argument(
        '--end',
        type=str,
        required=True,
        help='End date in YYYY-MM-DD format'
    )
    
    # Optional arguments
    parser.add_argument(
        '--capital',
        type=float,
        default=100000.0,
        help='Initial capital amount'
    )
    
    parser.add_argument(
        '--commission',
        type=float,
        default=0.001,
        help='Commission percentage per trade (e.g., 0.001 = 0.1%%)'
    )
    
    parser.add_argument(
        '--position-size',
        type=float,
        default=1.0,
        help='Position size as percentage of capital (0.0-1.0)'
    )
    
    parser.add_argument(
        '--min-confidence',
        type=int,
        default=5,
        help='Minimum confidence level to execute trades (0-10)'
    )
    
    parser.add_argument(
    '--output-dir',
    type=str,
    default='./backtesting/results',
    help='Directory to save backtest results'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    return parser.parse_args()


def validate_dates(start_date: str, end_date: str) -> bool:
    """Validate date format and range.
    
    Args:
        start_date: Start date string
        end_date: End date string
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If dates are invalid
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD format. Error: {e}")
    
    if start >= end:
        raise ValueError("Start date must be before end date")
    
    if end > datetime.now():
        raise ValueError("End date cannot be in the future")
    
    # Check minimum duration (at least 5 trading days)
    if (end - start).days < 5:
        raise ValueError("Backtest period must be at least 5 days")
    
    return True


def print_backtest_summary(result):
    """Print a formatted summary of backtest results.
    
    Args:
        result: BacktestResult object
    """
    print("\n" + "="*80)
    print("BACKTEST RESULTS SUMMARY")
    print("="*80)
    
    print(f"\n📊 Configuration:")
    print(f"  Symbol:          {result.config.symbol}")
    print(f"  Period:          {result.config.start_date} to {result.config.end_date}")
    print(f"  Initial Capital: ${result.config.initial_capital:,.2f}")
    print(f"  Commission:      {result.config.commission_pct*100:.2f}%")
    print(f"  Position Size:   {result.config.position_size_pct*100:.0f}%")
    print(f"  Min Confidence:  {result.config.min_confidence}/10")
    
    print(f"\n💰 Performance:")
    print(f"  Final Value:     ${result.final_portfolio_value:,.2f}")
    print(f"  Total Return:    ${result.total_return:,.2f}")
    print(f"  Return %:        {result.total_return_pct:+.2f}%")
    print(f"  Sharpe Ratio:    {result.sharpe_ratio:.2f}")
    print(f"  Max Drawdown:    {result.max_drawdown:.2f}%")
    
    print(f"\n📈 Trading Statistics:")
    print(f"  Total Trades:    {result.total_trades}")
    print(f"  Winning Trades:  {result.winning_trades}")
    print(f"  Losing Trades:   {result.losing_trades}")
    print(f"  Win Rate:        {result.win_rate:.2f}%")
    if result.avg_win > 0:
        print(f"  Average Win:     ${result.avg_win:,.2f}")
    if result.avg_loss < 0:
        print(f"  Average Loss:    ${result.avg_loss:,.2f}")
    print(f"  Total Commission: ${result.total_commission:,.2f}")
    
    # Performance rating
    print(f"\n⭐ Performance Rating:")
    if result.total_return_pct > 20:
        rating = "EXCELLENT 🚀"
    elif result.total_return_pct > 10:
        rating = "GOOD 👍"
    elif result.total_return_pct > 0:
        rating = "POSITIVE ✅"
    elif result.total_return_pct > -10:
        rating = "SLIGHT LOSS ⚠️"
    else:
        rating = "POOR ❌"
    print(f"  {rating}")
    
    print("\n" + "="*80 + "\n")


async def main():
    """Main function."""
    args = parse_arguments()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated")
        
        # Validate dates
        validate_dates(args.start, args.end)
        logger.info(f"Date range validated: {args.start} to {args.end}")
        
        # Create backtest configuration
        backtest_config = BacktestConfig(
            symbol=args.symbol.upper(),
            start_date=args.start,
            end_date=args.end,
            initial_capital=args.capital,
            commission_pct=args.commission,
            position_size_pct=args.position_size,
            min_confidence=args.min_confidence
        )
        
        logger.info(f"Starting backtest for {backtest_config.symbol}")
        logger.info(f"Period: {backtest_config.start_date} to {backtest_config.end_date}")
        logger.info(f"Initial capital: ${backtest_config.initial_capital:,.2f}")
        
        # Initialize trading agent
        trading_agent = TradingAgent(
            Config.GLM_API_KEY,
            Config.FINNHUB_API_KEY,
            Config.OPENAI_API_KEY,
            Config.ALPHA_VANTAGE_API_KEY
        )
        
        # Create and run backtest engine
        engine = BacktestEngine(backtest_config, trading_agent)
        result = await engine.run()
        
        # Print summary
        print_backtest_summary(result)
        
        # Save results
        output_file = save_backtest_result(result, args.output_dir)
        print(f"📁 Detailed results saved to: {output_file}")
        
        # Generate trade log
        trade_log_path = Path(args.output_dir) / f"trades_{args.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        if result.trades:
            import pandas as pd
            trades_df = pd.DataFrame([{
                'date': t.date,
                'symbol': t.symbol,
                'action': t.action,
                'price': t.price,
                'shares': t.shares,
                'value': t.value,
                'commission': t.commission,
                'portfolio_value': t.portfolio_value,
                'confidence': t.confidence
            } for t in result.trades])
            trades_df.to_csv(trade_log_path, index=False)
            print(f"📊 Trade log saved to: {trade_log_path}")
        
        return 0
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n❌ Configuration error:\n{e}")
        print("\nPlease check your .env file and ensure all required variables are set.")
        return 1
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        print(f"\n❌ Error: {e}")
        return 1
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ Unexpected error: {e}")
        print("Check backtest.log for details.")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
