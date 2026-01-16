# AGENTS.md - Guide for Coding Agents

## Build/Test Commands

### Main Operations
```bash
# Run the trading bot
python bot.py

# Using the management script (recommended for production)
./manage_bot.sh start      # Start bot in background
./manage_bot.sh stop       # Stop bot
./manage_bot.sh restart    # Restart bot
./manage_bot.sh status     # Check bot status
./manage_bot.sh logs [n]   # Show last n logs (default: 50)
./manage_bot.sh follow     # Follow logs in real-time
./manage_bot.sh check      # Run system checks
./manage_bot.sh install    # Install dependencies in venv
```

### Testing
```bash
# Test trading analysis for a specific stock
python test_analysis.py [symbol]  # Default: AAPL
python test_analysis.py AAPL

# Quick backtest (recent 30 days)
python backtest_quick.py AAPL 30
python backtest_quick.py TSLA 60 50000  # symbol days [capital]

# Full backtest with parameters
python backtest_full.py --symbol AAPL --start 2024-01-01 --end 2024-10-01
python backtest_full.py --symbol TSLA --start 2023-06-01 --end 2024-06-01 --capital 50000
```

### Dependency Management
```bash
pip install -r requirements.txt
pip install zhipuai  # GLM SDK (not in requirements.txt)
```

### Debug Mode
Set in `.env`:
```
BOT_DEBUG=True
LOG_LEVEL=DEBUG
```

## Code Style Guidelines

### Imports
- Standard library imports first, then third-party, then local imports
- Use `from typing import` for type hints (Optional, Dict, List, Tuple, Any, etc.)
- Add TradingAgents to sys.path if needed: `sys.path.insert(0, str(trading_agents_path))`

### Formatting
- Use 4-space indentation (no tabs)
- Maximum line length: Not strictly enforced, but keep reasonable
- Use f-strings for string formatting, not `.format()` or `%` formatting
- Use triple quotes for docstrings

### Type Hints
- **Always use type hints** for function parameters and return values
- Use `Optional[T]` for nullable types
- Use `Final[T]` for constants in constants.py
- Use dataclasses for data structures with `@dataclass` decorator
- Use Enum for fixed sets of values (e.g., PositionSide)

### Naming Conventions
- **Classes**: PascalCase (e.g., `TradingBot`, `BacktestEngine`)
- **Functions/methods**: snake_case (e.g., `analyze_stock`, `get_welcome_message`)
- **Variables**: snake_case (e.g., `current_price`, `trading_agent`)
- **Constants**: UPPER_SNAKE_CASE with Final type (e.g., `MAX_ANALYSIS_LENGTH: Final[int]`)
- **Private methods**: prefix with underscore (e.g., `_get_welcome_message`)
- **Module-level constants**: All caps in constants.py

### Error Handling
- Define custom exceptions (e.g., `class ConfigurationError(Exception)`)
- Use try-except blocks with specific exception types
- Log errors before raising: `logger.error(f"Failed to process: {e}")`
- Return error dicts in async handlers: `{"error": "message"}`

### Documentation
- Module-level docstrings describe purpose and features
- Class docstrings describe purpose and key attributes
- Function docstrings use Google style:
  ```
  """Process stock analysis.

  Args:
      symbol: Stock ticker symbol
      timeframe: Data timeframe period

  Returns:
      dict: Analysis results with recommendation and confidence

  Raises:
      TradingAgentError: If analysis fails
  """
  ```

### Configuration
- All config in `config.py` using the `Config` class
- Load environment variables with `python-dotenv` at module level
- Validate config on startup with `Config.validate()`
- Never log actual API keys - use masking: `key[:4]...key[-4:]`

**Important Constants:**
- `DEFAULT_HISTORY_PERIOD` (`'2d'`): Days of historical price data to fetch for price change calculations (hardcoded in constants.py)
- `DEFAULT_TIMEFRAME` (`'1d'`): Default timeframe for stock data (configurable via `.env` file)
- `MAX_ANALYSIS_LENGTH` (3496): Maximum Telegram message length (4096 - 600 overhead)

### Constants
- All magic numbers/strings go in `constants.py`
- Use `Final` type for constants: `MAX_ANALYSIS_LENGTH: Final[int] = 4096`
- Group related constants together
- Use descriptive names (not `MAX`, use `MAX_ANALYSIS_LENGTH`)

### Async Patterns
- Use `async def` for async functions
- Use `await` for async calls
- Telegram handlers are async: `async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`
- Use `asyncio.run()` for running async from sync code

### Logging
- Configure logging at module level using `Config.LOG_LEVEL`
- Use `logger = logging.getLogger(__name__)` in each module
- Log levels: `logger.debug()`, `logger.info()`, `logger.warning()`, `logger.error()`, `logger.critical()`
- Include context in logs: `logger.info(f"User {user_id} started analysis for {symbol}")`

### Project Structure
```
bot.py                 # Main Telegram bot entry point
trading_agent.py       # TradingAgents integration
config.py             # Configuration management
constants.py          # All constants
backtest_quick.py     # Wrapper for quick backtest
backtest_full.py      # Wrapper for full backtest
test_analysis.py      # Test analysis script
backtesting/          # Backtesting module
  - core/             # Core backtesting components
    - engine.py       # Backtest engine
  - scripts/          # Backtest runner scripts
    - run.py          # Full backtest runner
    - quick.py        # Quick backtest runner
  - utils/            # Utility functions
    - visualize.py    # Visualization tools
  - tests/            # Test files
  - results/          # Backtest results storage
.env                 # Environment variables (not in git)
.env.example         # Template for .env
```

### Telegram Message Formatting

#### HTML Formatting
- All Telegram messages use `parse_mode='HTML'` - **NOT Markdown**
- HTML tags: `<b>` for bold, `<code>` for inline code, `<i>` for italic
- Escape special characters: Use `&lt;` for `<`, `&gt;` for `>`, `&amp;` for `&`
- Example: `<code>/analyze AAPL</code>` displays as `/analyze AAPL`

#### Message Structure
- **Summary Message**: Sent directly to Telegram chat, contains:
  - Current price and change
  - Recommendation (Action, Confidence, Risk Level, Price Target)
  - Brief summary (max 500 chars)
  - Note to see full report in attachment
  
- **Full Report Attachment**: Downloadable `.html` file contains:
  - All market data and recommendation details
  - Complete detailed analysis in formatted HTML with CSS styling
  - **Individual Agent Reports** (with clear separators):
    - Market Analyst
    - Fundamental Analyst
    - News Analyst
    - Sentiment Analyst
    - Risk Analyst
    - Investment Committee
    - Trading Plan
  - Disclaimer
  - Professional formatting with tables, sections, and colored boxes

#### Truncation
- Use `_truncate_analysis_text(text, max_length)` to limit text length
- Default `MAX_ANALYSIS_LENGTH` = 3496 (4096 - 600 overhead)
- Tries to cut at sentence boundary (`.`) or newline (`\n`) for cleaner breaks
- Appends `[See full report in attached file...]` when truncated

### Testing Notes
- No pytest/unittest configured - tests are standalone scripts
- Test files follow `test_*.py` naming (e.g., `test_analysis.py`)
- Manual testing via `python test_analysis.py`
- Add sys.path manipulation at test file start if needed: `sys.path.insert(0, str(Path(__file__).parent))`

### Security
- Never commit `.env` file
- Never log full API keys
- Use environment variables for all secrets
- Validate all user inputs
- Mask sensitive data in logs
