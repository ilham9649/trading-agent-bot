# Trading Agent Telegram Bot

A sophisticated Telegram bot that provides financial recommendations using AI and real-time market data. The bot uses **GLM-4-32b-0414-128k (Z.AI)** for analysis through the **TradingAgents** multi-agent framework.

## Features

- 🤖 **AI-Powered Analysis**: Uses GLM-4-32b-0414-128k (Z.AI) via TradingAgents multi-agent framework for intelligent stock recommendations
- 📊 **Real-time Data**: Fetches live market data from Yahoo Finance
- 📈 **Multi-Agent System**: Leverages TradingAgents framework for comprehensive analysis
- 🎯 **Comprehensive Reports**: Provides both quick summary and detailed analysis file
- 📄 **Full Analysis Export**: Sends complete untruncated analysis as .txt file
- 🔍 **Deep Thinking**: Uses GLM-4-32b-0414-128k for both deep and quick thinking modes

## Commands

- `/start` - Welcome message and bot introduction
- `/analyze <symbol>` - Get comprehensive stock analysis (e.g., `/analyze AAPL`)
  - Provides summary message + full analysis .txt file
- `/help` - Show all available commands

## Prerequisites

- Python 3.11+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- **Z.AI (GLM) API Key** - Get from [Z.AI Platform](https://api.z.ai/)
- OpenAI API Key (for embeddings only)
- Finnhub API Key
- **Alpha Vantage API Key** - Get from [Alpha Vantage](https://www.alphavantage.co/support/#api-key) (Free tier: 25 calls/day)

## Quick Start

### 1. Clone and Setup

```bash
# Clone the main repository
git clone https://github.com/ilham9649/trading-agent-bot.git
cd trading-agent-bot

# ⚠️ IMPORTANT: Clone TradingAgents library (required - not available via pip)
git clone https://github.com/TauricResearch/TradingAgents.git
```

**Note**: TradingAgents must be cloned locally as it's not available as a standard pip package. The `trading_agent.py` module will automatically add this directory to the Python path.

### 2. Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

Required environment variables:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GLM_API_KEY=your_z_ai_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # For embeddings only
FINNHUB_API_KEY=your_finnhub_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here  # For news data
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install zhipuai
```

### 4. Run the Bot

```bash
python bot.py
```

## Getting API Keys

### 1. Telegram Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Use `/newbot` command
3. Follow instructions to create your bot
4. Copy the bot token

### 2. Z.AI (GLM) API Key
1. Go to [Z.AI Platform](https://api.z.ai/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key

### 3. OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)
   - **Note**: Only used for embeddings, not for chat/analysis

### 4. Finnhub API Key
1. Go to [Finnhub.io](https://finnhub.io/)
2. Sign up for a free account
3. Go to API Keys section
4. Copy your API key

### 5. Alpha Vantage API Key
1. Go to [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Click "Get your free API key today"
3. Fill out the simple form
4. Copy your API key
   - **Free tier**: 25 API calls per day
   - **Note**: Used for news data and financial information in stock analysis

## Configuration

The bot can be configured through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Required |
| `GLM_API_KEY` | Z.AI (GLM) API key for analysis | Required |
| `OPENAI_API_KEY` | OpenAI API key for embeddings | Required |
| `FINNHUB_API_KEY` | Finnhub API key | Required |
| `BOT_DEBUG` | Enable debug mode | `False` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Usage Examples

### Stock Analysis
```
/analyze AAPL
```
Returns:
1. **Summary message** with:
   - Current price and change
   - AI-powered recommendation (BUY/SELL/HOLD)
   - Confidence level and risk assessment
   - Price target
   - Key analysis points

2. **Full analysis .txt file** containing:
   - Complete multi-agent analysis
   - Detailed reasoning from TradingAgents
   - All agent outputs and debates
   - Comprehensive market data

## Architecture

```
trading-agent-bot/
├── bot.py                      # Main Telegram bot
├── trading_agent.py            # TradingAgents integration + GLM-4-32b-0414-128k
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── manage_bot.sh              # Bot management script
├── TradingAgents/             # External library (cloned)
├── eval_results/              # Runtime logs (auto-generated)
├── .env.example              # Environment template
└── README.md                 # This file
```

## How It Works

1. **User sends `/analyze AAPL`**
2. **Bot fetches data** from Yahoo Finance
3. **TradingAgents framework** processes with multiple AI agents:
   - Uses **GLM-4-32b-0414-128k** (Z.AI) for analysis
   - Multi-agent debate and consensus
   - Comprehensive reasoning
4. **Bot returns**:
   - Quick summary message
   - Detailed .txt file with full analysis

## Technical Details

### AI Models
- **Chat/Analysis**: GLM-4-32b-0414-128k via Z.AI API
- **Embeddings**: OpenAI text-embedding-3-small
- **Framework**: TradingAgents multi-agent system

### Data Sources
- **Stock Data**: Yahoo Finance (yfinance)
- **Market Data**: Finnhub API

## Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if all API keys are correctly set
   - Verify bot token is valid
   - Check logs: `tail -f bot.log`

2. **Analysis errors**
   - Ensure GLM_API_KEY is valid and active
   - Check OpenAI API key has sufficient credits (for embeddings)
   - Verify stock symbol exists

3. **Slow responses**
   - Multi-agent analysis takes time (30-60 seconds)
   - This is normal for comprehensive analysis
   - The framework performs multiple LLM calls

### Debug Mode

Enable debug mode for detailed logging:

```env
BOT_DEBUG=True
LOG_LEVEL=DEBUG
```

View logs:
```bash
tail -f bot.log
```

## Security Notes

- Never commit your `.env` file
- Use environment variables for production
- Regularly rotate API keys
- Monitor API usage and costs
- `.env` is already in `.gitignore`

## External Dependencies

This project uses:
- [TradingAgents](https://github.com/TauricResearch/TradingAgents) - Multi-agent trading framework
- [Z.AI](https://api.z.ai/) - GLM-4-32b-0414-128k language model
- [OpenAI](https://platform.openai.com/) - Embeddings
- [yfinance](https://github.com/ranaroussi/yfinance) - Market data

## Disclaimer

⚠️ **Important**: This bot provides educational information only. It is not financial advice. Always do your own research and consult with financial professionals before making investment decisions.

The analysis is generated by AI and should not be solely relied upon for trading decisions. Past performance does not guarantee future results.

## License

This project is for educational purposes. Please ensure compliance with all API terms of service.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs: `tail -f bot.log`
3. Ensure all dependencies are installed
4. Verify API keys are correct and active
5. Ensure TradingAgents is cloned in the project directory
