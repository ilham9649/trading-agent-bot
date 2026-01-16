"""Test Backtesting Setup - Verify everything is ready.

This script checks if your backtesting environment is properly configured.
Run this before your first backtest to catch any issues early.

Usage:
    python test_backtest_setup.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def print_status(check_name: str, passed: bool, message: str = ""):
    """Print check status with emoji."""
    status = "✅" if passed else "❌"
    print(f"{status} {check_name}")
    if message:
        print(f"   {message}")


def check_imports():
    """Check if all required packages are installed."""
    print("\n📦 Checking Python packages...")
    
    required_packages = [
        ("telegram", "python-telegram-bot"),
        ("yfinance", "yfinance"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
        ("openai", "openai"),
        ("dotenv", "python-dotenv"),
    ]
    
    all_passed = True
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            print_status(f"{package_name}", True)
        except ImportError:
            print_status(f"{package_name}", False, f"Install with: pip install {package_name}")
            all_passed = False
    
    return all_passed


def check_files():
    """Check if all required files exist."""
    print("\n📄 Checking required files...")
    
    required_files = [
        "bot.py",
        "trading_agent.py",
        "config.py",
        "constants.py",
        "run_backtest.py",
        "backtest_quick.py",
        ".env",
    ]
    
    all_passed = True
    for filename in required_files:
        file_path = Path(filename)
        exists = file_path.exists()
        print_status(filename, exists)
        if not exists:
            all_passed = False
    
    return all_passed


def check_env_vars():
    """Check if required environment variables are set."""
    print("\n🔑 Checking environment variables...")
    
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    required_vars = {
        "GLM_API_KEY": "Z.AI API key for analysis",
        "OPENAI_API_KEY": "OpenAI API key for embeddings",
        "FINNHUB_API_KEY": "Finnhub API key for market data",
    }
    
    optional_vars = {
        "ALPHA_VANTAGE_API_KEY": "Alpha Vantage API key for news (optional)",
    }
    
    all_passed = True
    
    # Check required
    for var, description in required_vars.items():
        value = os.getenv(var)
        is_set = bool(value and len(value) > 0)
        print_status(var, is_set, description if not is_set else "")
        if not is_set:
            all_passed = False
    
    # Check optional
    for var, description in optional_vars.items():
        value = os.getenv(var)
        is_set = bool(value and len(value) > 0)
        print_status(f"{var} (optional)", is_set, description if not is_set else "")
    
    return all_passed


def check_tradingagents():
    """Check if TradingAgents library is available."""
    print("\n🤖 Checking TradingAgents framework...")
    
    trading_agents_path = Path("TradingAgents")
    
    if not trading_agents_path.exists():
        print_status("TradingAgents directory", False, "Run: git clone https://github.com/TauricResearch/TradingAgents.git")
        return False
    
    print_status("TradingAgents directory", True)
    
    # Check key files
    key_files = [
        "TradingAgents/tradingagents/graph/trading_graph.py",
        "TradingAgents/tradingagents/default_config.py",
    ]
    
    all_exist = True
    for file in key_files:
        exists = Path(file).exists()
        if not exists:
            all_exist = False
    
    print_status("TradingAgents files", all_exist)
    
    return all_exist


def test_yfinance():
    """Test if yfinance can fetch data."""
    print("\n📊 Testing market data access...")
    
    try:
        import yfinance as yf
        ticker = yf.Ticker("AAPL")
        hist = ticker.history(period="5d")
        
        if not hist.empty:
            print_status("YFinance data fetch", True, f"Successfully fetched {len(hist)} days of AAPL data")
            return True
        else:
            print_status("YFinance data fetch", False, "No data returned")
            return False
    except Exception as e:
        print_status("YFinance data fetch", False, str(e))
        return False


def check_disk_space():
    """Check available disk space."""
    print("\n💾 Checking disk space...")
    
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        
        free_gb = free // (2**30)  # Convert to GB
        
        if free_gb > 5:
            print_status(f"Disk space ({free_gb} GB free)", True)
            return True
        else:
            print_status(f"Disk space ({free_gb} GB free)", False, "Low disk space, may cause issues")
            return False
    except Exception as e:
        print_status("Disk space check", False, str(e))
        return False


def main():
    """Run all checks."""
    print("="*60)
    print("🧪 BACKTESTING SETUP CHECK")
    print("="*60)
    
    checks = [
        ("Packages", check_imports),
        ("Files", check_files),
        ("Environment", check_env_vars),
        ("TradingAgents", check_tradingagents),
        ("Market Data", test_yfinance),
        ("Disk Space", check_disk_space),
    ]
    
    results = {}
    for check_name, check_func in checks:
        results[check_name] = check_func()
    
    # Summary
    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    
    all_passed = all(results.values())
    required_checks = ["Packages", "Files", "Environment", "TradingAgents"]
    required_passed = all(results.get(c, False) for c in required_checks)
    
    if all_passed:
        print("\n✅ All checks passed! You're ready to backtest.")
        print("\nRun your first backtest:")
        print("  python backtest_quick.py AAPL 30")
    elif required_passed:
        print("\n⚠️  Required checks passed, but some optional checks failed.")
        print("You can proceed, but some features may be limited.")
        print("\nRun your first backtest:")
        print("  python backtest_quick.py AAPL 30")
    else:
        print("\n❌ Some required checks failed. Please fix the issues above.")
        print("\nRequired:")
        for check in required_checks:
            status = "✅" if results.get(check, False) else "❌"
            print(f"  {status} {check}")
    
    print("\n" + "="*60)
    
    return 0 if required_passed else 1


if __name__ == '__main__':
    sys.exit(main())
