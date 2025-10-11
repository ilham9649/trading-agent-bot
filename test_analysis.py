#!/usr/bin/env python3
"""Test script to verify trading agent analysis works correctly."""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_agent import TradingAgent
from config import Config

async def test_analysis(symbol: str = "AAPL"):
    """Test stock analysis for a given symbol."""
    print(f"\n{'='*80}")
    print(f"Testing Stock Analysis for {symbol}")
    print(f"{'='*80}\n")
    
    try:
        # Initialize agent
        print("Initializing TradingAgent...")
        agent = TradingAgent(
            Config.GLM_API_KEY,
            Config.FINNHUB_API_KEY,
            Config.OPENAI_API_KEY,
            Config.ALPHA_VANTAGE_API_KEY
        )
        print("✓ TradingAgent initialized successfully\n")
        
        # Run analysis
        print(f"Running analysis for {symbol}...")
        print("(This will take 2-3 minutes)\n")
        
        result = await agent.analyze_stock(symbol)
        
        # Display results
        print(f"\n{'='*80}")
        print("ANALYSIS RESULTS")
        print(f"{'='*80}\n")
        
        if "error" in result:
            print(f"❌ ERROR: {result['error']}")
            return False
        
        print(f"Symbol: {result.get('symbol', 'N/A')}")
        print(f"Timestamp: {result.get('timestamp', 'N/A')}")
        print(f"Current Price: ${result.get('current_price', 0):.2f}")
        print(f"Price Change: {result.get('price_change', 0):+.2f}%")
        print(f"Recommendation: {result.get('recommendation', 'N/A')}")
        print(f"Confidence: {result.get('confidence', 0)}/10")
        print(f"Risk Level: {result.get('risk_level', 'N/A')}")
        print(f"Price Target: ${result.get('price_target', 0):.2f}")
        
        print(f"\n{'='*80}")
        print("ANALYSIS TEXT (First 500 chars)")
        print(f"{'='*80}\n")
        reasons = result.get('reasons', '')
        print(reasons[:500] + "..." if len(reasons) > 500 else reasons)
        
        # Check for the specific errors mentioned
        print(f"\n{'='*80}")
        print("ERROR CHECKS")
        print(f"{'='*80}\n")
        
        reasons_lower = reasons.lower()
        
        if "i apologize for the confusion" in reasons_lower or "future date" in reasons_lower:
            print("❌ FOUND: Future date confusion issue")
            return False
        else:
            print("✓ PASS: No future date confusion")
        
        if "invalid" in reasons_lower and "inputs" in reasons_lower:
            print("❌ FOUND: Invalid inputs error")
            return False
        else:
            print("✓ PASS: No invalid inputs error")
        
        if "let me know how you'd like to proceed" in reasons_lower:
            print("❌ FOUND: Incomplete analysis (asking for direction)")
            return False
        else:
            print("✓ PASS: Analysis is complete")
        
        if len(reasons.strip()) < 100:
            print("❌ FOUND: Analysis text too short (likely incomplete)")
            return False
        else:
            print(f"✓ PASS: Analysis text is substantial ({len(reasons)} chars)")
        
        print(f"\n{'='*80}")
        print("✅ ALL TESTS PASSED!")
        print(f"{'='*80}\n")
        return True
        
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Get symbol from command line or use default
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    
    # Run test
    success = asyncio.run(test_analysis(symbol))
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
