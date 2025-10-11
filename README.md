# Trading Agent Telegram Bot

A sophisticated Telegram bot that provides financial recommendations using AI and real-time market data. The bot integrates with OpenAI for intelligent analysis and Finnhub for market data.

## Features

- 🤖 **AI-Powered Analysis**: Uses OpenAI GPT for intelligent stock recommendations
- 📊 **Real-time Data**: Fetches live market data from Finnhub and Yahoo Finance
- 📰 **News Integration**: Provides recent company news and insights
- 📈 **Technical Analysis**: Calculates moving averages and technical indicators
- 🎯 **Market Overview**: Shows major indices and market trends
- 🐳 **Docker Ready**: Easy deployment with Docker and docker-compose

## Commands

- `/start` - Welcome message and bot introduction
- `/analyze <symbol>` - Get detailed stock analysis (e.g., `/analyze AAPL`)
- `/market` - Get current market overview
- `/news <symbol>` - Get recent company news (e.g., `/news TSLA`)
- `/help` - Show all available commands

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (optional)
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- OpenAI API Key
- Finnhub API Key

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd trading-agent
```

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
OPENAI_API_KEY=your_openai_api_key_here
FINNHUB_API_KEY=your_finnhub_api_key_here
```

### 3. Run with Docker (Recommended)

```bash
# Build and start the bot
docker-compose up -d

# View logs
docker-compose logs -f trading-bot

# Stop the bot
docker-compose down
```

### 4. Run Locally (Alternative)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

## Getting API Keys

### 1. Telegram Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Use `/newbot` command
3. Follow instructions to create your bot
4. Copy the bot token

### 2. OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)

### 3. Finnhub API Key
1. Go to [Finnhub.io](https://finnhub.io/)
2. Sign up for a free account
3. Go to API Keys section
4. Copy your API key

## Configuration

The bot can be configured through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Required |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `FINNHUB_API_KEY` | Finnhub API key | Required |
| `BOT_DEBUG` | Enable debug mode | `False` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Usage Examples

### Stock Analysis
```
/analyze AAPL
```
Returns detailed analysis including:
- Current price and change
- Technical indicators (MA20, MA50)
- AI-powered recommendation (BUY/SELL/HOLD)
- Confidence level and risk assessment
- Price target

### Market Overview
```
/market
```
Shows major indices:
- S&P 500
- Dow Jones
- NASDAQ
- VIX (Volatility Index)

### Company News
```
/news TSLA
```
Displays recent company news and headlines.

## Architecture

```
trading-agent/
├── bot.py                 # Main Telegram bot
├── trading_agent.py       # Trading analysis logic
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose setup
├── .env.example        # Environment template
└── README.md           # This file
```

## Monitoring

The bot includes health checks and logging:

```bash
# View real-time logs
docker-compose logs -f trading-bot

# Check bot health
docker-compose ps
```

## Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if all API keys are correctly set
   - Verify bot token is valid
   - Check logs for errors

2. **Analysis errors**
   - Ensure OpenAI API key has sufficient credits
   - Check Finnhub API key is valid
   - Verify stock symbol exists

3. **Docker issues**
   - Ensure Docker is running
   - Check if ports are available
   - Review docker-compose logs

### Debug Mode

Enable debug mode for detailed logging:

```env
BOT_DEBUG=True
LOG_LEVEL=DEBUG
```

## Security Notes

- Never commit your `.env` file
- Use environment variables for production
- Regularly rotate API keys
- Monitor API usage and costs

## Disclaimer

⚠️ **Important**: This bot provides educational information only. It is not financial advice. Always do your own research and consult with financial professionals before making investment decisions.

## License

This project is for educational purposes. Please ensure compliance with all API terms of service.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Ensure all dependencies are installed
4. Verify API keys are correct and active