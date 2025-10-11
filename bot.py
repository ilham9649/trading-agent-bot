import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
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
        self.simple_trading_agent = SimpleTradingAgent(
            Config.GLM_API_KEY, 
            Config.FINNHUB_API_KEY,
            Config.OPENAI_API_KEY  # For embeddings only
        )
        self.user_sessions = {}  # Store user preferences and state
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 **Welcome to Trading Agent Bot!**

I provide comprehensive stock analysis using the TradingAgents multi-agent framework.

**Available Commands:**
/analyze <symbol> - Get detailed stock analysis
/help - Show this help message

**Example:**
/analyze AAPL
/analyze TSLA
/analyze MSFT

Let's start trading! 📈
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📚 **Bot Commands:**

/analyze <symbol> - Get comprehensive stock analysis
• Example: `/analyze AAPL`
• Uses TradingAgents multi-agent framework
• Includes technical analysis, fundamental analysis, sentiment analysis, and AI recommendations
• Analysis takes 2-3 minutes

/help - Show this help message

**What you get:**
• Current price and price changes
• BUY/SELL/HOLD recommendation with confidence level
• Price target and risk assessment
• Comprehensive AI analysis from multiple specialized agents

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
            f"🔍 **Analyzing {symbol}**\n\n"
            f"🤖 Multiple AI agents are analyzing...\n"
            f"⏱️ This may take 2-3 minutes\n"
            f"📊 Running comprehensive research and debate\n\n"
            f"Please wait..."
        )
        
        try:
            # Get quick analysis from simple trading agent
            analysis = await self.simple_trading_agent.analyze_stock(symbol)
            
            if "error" in analysis:
                await loading_msg.edit_text(f"❌ Error: {analysis['error']}")
                return
            
            # Format and send analysis (no parse_mode to avoid Markdown issues)
            response = self._format_enhanced_analysis(analysis)
            await loading_msg.edit_text(response)
            
        except Exception as e:
            logger.error(f"Error in analyze_stock: {e}")
            await loading_msg.edit_text(
                f"❌ An error occurred while analyzing {symbol}. Please try again later."
            )
    
    
    
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
        
        # Convert reasons to string and truncate smartly if needed
        reasons_text = str(reasons) if reasons else 'No analysis available'
        
        # Telegram limit is 4096 chars, but we need space for the message template
        # Template overhead is ~600 chars, so we can use ~3400 chars for analysis
        max_analysis_length = 3400
        
        if len(reasons_text) > max_analysis_length:
            # Truncate at the last complete sentence before the limit
            truncated = reasons_text[:max_analysis_length]
            last_period = truncated.rfind('.')
            last_newline = truncated.rfind('\n')
            
            # Cut at the last sentence or paragraph boundary
            cut_point = max(last_period, last_newline)
            if cut_point > max_analysis_length - 500:  # If cut point is reasonably close
                reasons_text = reasons_text[:cut_point + 1] + "\n\n[Analysis truncated due to length limit]"
            else:
                reasons_text = truncated + "...\n\n[Analysis truncated due to length limit]"
        
        # Determine emoji based on recommendation
        rec_emoji = {
            'BUY': '🟢',
            'SELL': '🔴', 
            'HOLD': '🟡'
        }.get(str(recommendation).upper() if recommendation else 'HOLD', '🟡')
        
        # Ensure numeric values for formatting
        try:
            current_price = float(current_price) if current_price else 0
            price_change = float(price_change) if price_change else 0
            price_target = float(price_target) if price_target else 0
        except (ValueError, TypeError):
            current_price = 0
            price_change = 0
            price_target = 0
        
        # Simple text formatting without Markdown
        response = f"""
{rec_emoji} {symbol} - TradingAgents Analysis

📊 Current Price: ${current_price:.2f} ({price_change:+.2f}%)

🎯 Recommendation:
• Action: {recommendation}
• Confidence: {confidence}/10
• Risk Level: {risk_level}
• Price Target: ${price_target:.2f}

🧠 TradingAgents Analysis:
{reasons_text}

⚡ Analysis Type: {analysis.get('analysis_type', 'TRADING_AGENTS')}
🕐 Generated: {analysis.get('timestamp', 'Unknown')[:19]}

This analysis was generated using the TradingAgents multi-agent framework.
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