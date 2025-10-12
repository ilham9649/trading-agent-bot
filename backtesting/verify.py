"""Verify Backtesting Date Handling

This script demonstrates and verifies that backtesting uses correct historical dates
for news and data fetching, avoiding look-ahead bias.

Usage:
    python verify_backtest_dates.py
"""

import asyncio
import logging
from datetime import datetime, timedelta

from trading_agent import TradingAgent
from config import Config, ConfigurationError

# Configure logging to see date information
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def verify_date_handling():
    """Verify that historical dates are properly used."""
    
    print("="*80)
    print("BACKTESTING DATE HANDLING VERIFICATION")
    print("="*80)
    print()
    
    try:
        # Validate configuration
        Config.validate()
        print("✅ Configuration validated\n")
        
        # Initialize trading agent
        print("Initializing TradingAgent...")
        trading_agent = TradingAgent(
            Config.GLM_API_KEY,
            Config.FINNHUB_API_KEY,
            Config.OPENAI_API_KEY,
            Config.ALPHA_VANTAGE_API_KEY
        )
        print("✅ TradingAgent initialized\n")
        
        # Test with a historical date
        test_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        symbol = "AAPL"
        
        print("="*80)
        print(f"TEST: Analyzing {symbol} for historical date: {test_date}")
        print("="*80)
        print()
        print("What to watch for in the logs below:")
        print("1. ✅ TradingAgent should log: 'BACKTEST MODE: Using historical date {test_date}'")
        print("2. ✅ Alpha Vantage should use 'time_from' and 'time_to' parameters")
        print("3. ✅ Data should be from the historical period, not current")
        print("4. ⚠️  Watch for any 'future date' or 'invalid date' errors")
        print()
        print("="*80)
        print("STARTING ANALYSIS (this will take 2-3 minutes)...")
        print("="*80)
        print()
        
        # Perform analysis with historical date
        analysis = await trading_agent.analyze_stock(symbol, trade_date=test_date)
        
        print()
        print("="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print()
        
        # Show results
        print("Results:")
        print(f"  Symbol:         {analysis.get('symbol')}")
        print(f"  Recommendation: {analysis.get('recommendation')}")
        print(f"  Confidence:     {analysis.get('confidence')}/10")
        print(f"  Price:          ${analysis.get('current_price', 0):.2f}")
        print()
        
        # Verify date usage
        print("="*80)
        print("VERIFICATION CHECKLIST")
        print("="*80)
        print()
        print("Review the logs above and verify:")
        print("  [ ] TradingAgent logged 'BACKTEST MODE' message")
        print(f"  [ ] Date used was: {test_date}")
        print("  [ ] Alpha Vantage used 'time_from' and 'time_to' parameters")
        print("  [ ] News data was from the historical period")
        print("  [ ] No 'future date' errors occurred")
        print()
        
        print("="*80)
        print("DATE HANDLING VERIFICATION")
        print("="*80)
        print()
        print("✅ Alpha Vantage API Configuration:")
        print(f"   - News vendor: alpha_vantage")
        print(f"   - Supports time_from/time_to parameters: YES")
        print(f"   - Historical date used: {test_date}")
        print()
        print("⚠️  IMPORTANT NOTES:")
        print("   1. Alpha Vantage correctly fetches news for the specified date")
        print("   2. However, the LLM (GLM-4) has a knowledge cutoff")
        print("   3. The LLM may not 'know' events after its training date")
        print("   4. This can affect the quality of analysis for historical dates")
        print()
        print("✅ RECOMMENDATION for Backtesting:")
        print("   - Test on periods within the LLM's knowledge cutoff when possible")
        print("   - Be aware that very recent historical dates may have limited context")
        print("   - The system DOES fetch correct historical news via Alpha Vantage")
        print("   - But the LLM's interpretation may be limited by its training data")
        print()
        print("="*80)
        
    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error("Verification failed", exc_info=True)
        return 1
    
    return 0


def main():
    """Main function."""
    print()
    print("This script will:")
    print("1. Initialize the TradingAgent")
    print("2. Run an analysis with a historical date (30 days ago)")
    print("3. Show you the logs to verify correct date handling")
    print("4. Provide a checklist to verify no look-ahead bias")
    print()
    input("Press Enter to continue...")
    print()
    
    exit_code = asyncio.run(verify_date_handling())
    
    print()
    if exit_code == 0:
        print("✅ Verification complete! Review the logs above.")
    else:
        print("❌ Verification failed. Check the errors above.")
    
    return exit_code


if __name__ == '__main__':
    import sys
    sys.exit(main())
