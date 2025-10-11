import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from trading_agent import TradingAgent
from simple_trading_agent import SimpleTradingAgent
from config import Config
import traceback

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, Config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)

class TradingBot:
    """Main Telegram bot class for financial recommendations"""
    
    def __init__(self):
        self.trading_agent = TradingAgent(Config.OPENAI_API_KEY, Config.FINNHUB_API_KEY)
        self.simple_trading_agent = SimpleTradingAgent(Config.OPENAI_API_KEY, Config.FINNHUB_API_KEY)
        self.user_sessions = {}  # Store user preferences and state
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 **Welcome to Trading Agent Bot!**

I can help you with:
• Stock analysis and recommendations
• Market overview
• Company news and insights
• Technical analysis

**Available Commands:**
/analyze <symbol> - Quick stock analysis (fast)
/analyze_full <symbol> - Full TradingAgents analysis (slow but comprehensive)
/market - Get market overview
/news <symbol> - Get recent company news
/help - Show this help message

**Example:**
/analyze AAPL (quick analysis)
/analyze_full AAPL (full multi-agent analysis)
/market
/news TSLA

Let's start trading! 📈
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📚 **Bot Commands:**

/analyze <symbol> - Quick stock analysis (fast, 10-30 seconds)
• Example: `/analyze AAPL`

/analyze_full <symbol> - Full TradingAgents analysis (comprehensive, 2-5 minutes)
• Example: `/analyze_full AAPL`
• Uses multiple AI agents for deep analysis

/market - Get current market overview
• Shows major indices (S&P 500, Dow Jones, NASDAQ, VIX)

/news <symbol> - Get recent company news
• Example: `/news TSLA`

/help - Show this help message

**Analysis Types:**
• **Quick Analysis**: Basic technical indicators + AI recommendation
• **Full Analysis**: Multi-agent framework with debate, risk assessment, and comprehensive research

⚠️ **Disclaimer:** This bot provides educational information only. Always do your own research before making investment decisions.
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def analyze_stock(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command"""
        if not context.args:
            await update.message.reply_text(
                "Please provide a stock symbol.\nExample: `/analyze AAPL`",
                parse_mode='Markdown'
            )
            return
        
        symbol = context.args[0].upper()
        
        # Send loading message
        loading_msg = await update.message.reply_text(
            f"🔍 Analyzing {symbol}...\nThis may take a moment."
        )
        
        try:
            # Get analysis from trading agent
            analysis = self.trading_agent.analyze_stock(symbol)
            
            if "error" in analysis:
                await loading_msg.edit_text(f"❌ Error: {analysis['error']}")
                return
            
            # Format and send analysis
            response = self._format_analysis(analysis)
            await loading_msg.edit_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in analyze_stock: {e}")
            await loading_msg.edit_text(
                f"❌ An error occurred while analyzing {symbol}. Please try again later."
            )
    
    async def analyze_stock_full(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze_full command - Full TradingAgents analysis"""
        if not context.args:
            await update.message.reply_text(
                "Please provide a stock symbol.\nExample: `/analyze_full AAPL`",
                parse_mode='Markdown'
            )
            return
        
        symbol = context.args[0].upper()
        
        # Send loading message
        loading_msg = await update.message.reply_text(
            f"🔍 **Full Analysis for {symbol}**\n\n"
            f"🤖 Multiple AI agents are analyzing...\n"
            f"⏱️ This may take 2-5 minutes\n"
            f"📊 Running comprehensive research and debate\n\n"
            f"Please wait..."
        )
        
        try:
            # Get TradingAgents analysis
            analysis = await self.simple_trading_agent.analyze_stock(symbol)
            
            if "error" in analysis:
                await loading_msg.edit_text(f"❌ Error: {analysis['error']}")
                return
            
            # Format and send analysis
            response = self._format_enhanced_analysis(analysis)
            await loading_msg.edit_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in analyze_stock_full: {e}")
            await loading_msg.edit_text(
                f"❌ An error occurred during full analysis of {symbol}. Please try again later."
            )
    
    async def market_overview(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /market command"""
        loading_msg = await update.message.reply_text("📊 Getting market overview...")
        
        try:
            market_data = self.trading_agent.get_market_overview()
            
            if "error" in market_data:
                await loading_msg.edit_text(f"❌ Error: {market_data['error']}")
                return
            
            response = self._format_market_overview(market_data)
            await loading_msg.edit_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in market_overview: {e}")
            await loading_msg.edit_text("❌ Error getting market data. Please try again later.")
    
    async def get_news(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /news command"""
        if not context.args:
            await update.message.reply_text(
                "Please provide a stock symbol.\nExample: `/news AAPL`",
                parse_mode='Markdown'
            )
            return
        
        symbol = context.args[0].upper()
        loading_msg = await update.message.reply_text(f"📰 Getting news for {symbol}...")
        
        try:
            news = self.trading_agent.get_company_news(symbol)
            profile = self.trading_agent.get_company_profile(symbol)
            
            if not news:
                await loading_msg.edit_text(f"No recent news found for {symbol}")
                return
            
            response = self._format_news(symbol, news, profile)
            await loading_msg.edit_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in get_news: {e}")
            await loading_msg.edit_text(f"❌ Error getting news for {symbol}. Please try again later.")
    
    def _format_analysis(self, analysis: dict) -> str:
        """Format analysis data for display"""
        data = analysis['analysis']
        rec = analysis['recommendation']
        
        # Determine emoji based on recommendation
        rec_emoji = {
            'BUY': '🟢',
            'SELL': '🔴', 
            'HOLD': '🟡'
        }.get(rec.get('recommendation', 'HOLD'), '🟡')
        
        # Format price change
        price_change = data['price_change_pct']
        change_emoji = '📈' if price_change >= 0 else '📉'
        
        response = f"""
{rec_emoji} **{data['symbol']} Analysis**

**Company:** {data['company_name']}
**Sector:** {data['sector']}
**Market Cap:** ${data['market_cap']:,}

**Price Information:**
• Current: ${data['current_price']} {change_emoji} {price_change:+.2f}%
• MA20: ${data['ma_20']}
• MA50: ${data['ma_50']}

**Volume:** {data['volume']:,} (Avg: {data['avg_volume']:,})

**Recommendation:**
• **Action:** {rec.get('recommendation', 'HOLD')}
• **Confidence:** {rec.get('confidence', 5)}/10
• **Risk Level:** {rec.get('risk_level', 'MEDIUM')}
• **Price Target:** ${rec.get('price_target', data['current_price'])}

**Analysis:**
{rec.get('reasons', 'No analysis available')}

*Analysis generated at {analysis['timestamp'][:19]}*
        """
        return response
    
    def _format_market_overview(self, market_data: dict) -> str:
        """Format market overview for display"""
        data = market_data['market_data']
        
        response = "📊 **Market Overview**\n\n"
        
        index_names = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^IXIC': 'NASDAQ',
            '^VIX': 'VIX (Volatility)'
        }
        
        for index, info in data.items():
            name = index_names.get(index, index)
            change = info['change_pct']
            emoji = '📈' if change >= 0 else '📉'
            response += f"**{name}:** {info['price']} {emoji} {change:+.2f}%\n"
        
        response += f"\n*Updated: {market_data['timestamp'][:19]}*"
        return response
    
    def _format_news(self, symbol: str, news: list, profile: dict) -> str:
        """Format news data for display"""
        company_name = profile.get('name', symbol)
        
        response = f"📰 **Recent News for {symbol}**\n"
        response += f"**Company:** {company_name}\n\n"
        
        for i, article in enumerate(news[:5], 1):  # Show top 5 news
            headline = article.get('headline', 'No headline')
            summary = article.get('summary', '')
            date = article.get('datetime', 0)
            
            # Format date
            if date:
                from datetime import datetime
                try:
                    dt = datetime.fromtimestamp(date / 1000)
                    date_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    date_str = 'Unknown date'
            else:
                date_str = 'Unknown date'
            
            response += f"**{i}. {headline}**\n"
            if summary:
                # Truncate summary if too long
                summary = summary[:200] + "..." if len(summary) > 200 else summary
                response += f"{summary}\n"
            response += f"*{date_str}*\n\n"
        
        return response
    
    def _format_enhanced_analysis(self, analysis: dict) -> str:
        """Format TradingAgents analysis data for display"""
        symbol = analysis.get('symbol', 'Unknown')
        recommendation = analysis.get('recommendation', 'HOLD')
        confidence = analysis.get('confidence', 5)
        reasons = analysis.get('reasons', 'No analysis available')
        price_target = analysis.get('price_target', 0)
        risk_level = analysis.get('risk_level', 'MEDIUM')
        current_price = analysis.get('current_price', 0)
        price_change = analysis.get('price_change', 0)
        
        # Determine emoji based on recommendation
        rec_emoji = {
            'BUY': '🟢',
            'SELL': '🔴', 
            'HOLD': '🟡'
        }.get(recommendation.upper(), '🟡')
        
        # Ensure numeric values for formatting
        try:
            current_price = float(current_price) if current_price else 0
            price_change = float(price_change) if price_change else 0
            price_target = float(price_target) if price_target else 0
        except (ValueError, TypeError):
            current_price = 0
            price_change = 0
            price_target = 0
        
        response = f"""
{rec_emoji} **{symbol} - TradingAgents Analysis**

**📊 Current Price:** ${current_price:.2f} ({price_change:+.2f}%)

**🎯 Recommendation:**
• **Action:** {recommendation}
• **Confidence:** {confidence}/10
• **Risk Level:** {risk_level}
• **Price Target:** ${price_target:.2f}

**🧠 TradingAgents Analysis:**
{reasons}

**⚡ Analysis Type:** {analysis.get('analysis_type', 'TRADING_AGENTS')}
**🕐 Generated:** {analysis.get('timestamp', 'Unknown')[:19]}

*This analysis was generated using the TradingAgents multi-agent framework with specialized analysts, researchers, and risk management teams.*
        """
        return response
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An unexpected error occurred. Please try again later."
            )

def main():
    """Main function to run the bot"""
    try:
        # Validate configuration
        Config.validate()
        
        # Create bot instance
        bot = TradingBot()
        
        # Create application
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CommandHandler("help", bot.help_command))
        application.add_handler(CommandHandler("analyze", bot.analyze_stock))
        application.add_handler(CommandHandler("analyze_full", bot.analyze_stock_full))
        application.add_handler(CommandHandler("market", bot.market_overview))
        application.add_handler(CommandHandler("news", bot.get_news))
        
        # Add error handler
        application.add_error_handler(bot.error_handler)
        
        # Start the bot
        logger.info("Starting Trading Agent Bot...")
        application.run_polling()
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file and ensure all required variables are set.")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ Failed to start bot: {e}")

if __name__ == '__main__':
    main()