"""Trading Agent Telegram Bot.

A sophisticated Telegram bot that provides financial recommendations using
AI-powered multi-agent analysis through the TradingAgents framework.

Features:
- Real-time stock analysis using GLM-4.6
- Multi-agent consensus system
- Comprehensive market insights
- Risk assessment and price targets
"""

import logging
import os
from typing import Optional
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from simple_trading_agent import SimpleTradingAgent, TradingAgentError
from config import Config, ConfigurationError
from constants import (
    MAX_ANALYSIS_LENGTH,
    RECOMMENDATION_EMOJIS,
    RECOMMENDATION_HOLD,
    REPORT_SEPARATOR,
    DEFAULT_FILE_ENCODING,
    ANALYSIS_FILE_EXTENSION,
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TradingBot:
    """Main Telegram bot class for financial recommendations.
    
    This bot integrates with the TradingAgents framework to provide
    comprehensive stock analysis through a Telegram interface.
    
    Attributes:
        simple_trading_agent: Instance of SimpleTradingAgent for analysis
        user_sessions: Dictionary to store user session data
    """
    
    def __init__(self) -> None:
        """Initialize the Trading Bot."""
        self.simple_trading_agent = SimpleTradingAgent(
            Config.GLM_API_KEY,
            Config.FINNHUB_API_KEY,
            Config.OPENAI_API_KEY,
            Config.ALPHA_VANTAGE_API_KEY
        )
        self.user_sessions = {}  # Store user preferences and state
        logger.info("TradingBot initialized successfully")
    
    async def start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command.
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        welcome_message = self._get_welcome_message()
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info(f"User {update.effective_user.id} started the bot")
    
    async def help_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /help command.
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        help_text = self._get_help_text()
        await update.message.reply_text(help_text, parse_mode='Markdown')
        logger.info(f"User {update.effective_user.id} requested help")
    
    async def analyze_stock(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /analyze command.
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        user_id = update.effective_user.id
        
        # Validate command arguments
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a stock symbol.\\n"
                "Example: `/analyze AAPL`",
                parse_mode='Markdown'
            )
            return
        
        symbol = context.args[0].upper()
        logger.info(f"User {user_id} requested analysis for {symbol}")
        
        # Send loading message
        loading_msg = await update.message.reply_text(
            self._get_loading_message(symbol)
        )
        
        try:
            # Perform analysis
            analysis = await self.simple_trading_agent.analyze_stock(symbol)
            
            # Check for errors
            if "error" in analysis:
                await loading_msg.edit_text(
                    f"❌ Error analyzing {symbol}: {analysis['error']}"
                )
                logger.error(f"Analysis error for {symbol}: {analysis['error']}")
                return
            
            # Format and send results
            await self._send_analysis_results(
                update,
                loading_msg,
                symbol,
                analysis
            )
            
            logger.info(f"Successfully sent analysis for {symbol} to user {user_id}")
            
        except TradingAgentError as e:
            error_msg = f"❌ Trading agent error for {symbol}: {str(e)}"
            await loading_msg.edit_text(error_msg)
            logger.error(error_msg, exc_info=True)
            
        except Exception as e:
            error_msg = (
                f"❌ An unexpected error occurred while analyzing {symbol}. "
                f"Please try again later."
            )
            await loading_msg.edit_text(error_msg)
            logger.error(
                f"Unexpected error analyzing {symbol}: {e}",
                exc_info=True
            )
    
    async def _send_analysis_results(
        self,
        update: Update,
        loading_msg,
        symbol: str,
        analysis: dict
    ) -> None:
        """Send formatted analysis results to user.
        
        Args:
            update: Telegram update object
            loading_msg: Loading message to edit
            symbol: Stock ticker symbol
            analysis: Analysis results dictionary
        """
        # Format summary for Telegram
        summary = self._format_analysis_summary(analysis)
        
        # Create full analysis file
        full_analysis_text = self._create_full_analysis_text(analysis)
        filename = self._generate_filename(symbol, analysis.get('timestamp', ''))
        
        # Write to temporary file
        temp_file_path = Path(filename)
        try:
            temp_file_path.write_text(
                full_analysis_text,
                encoding=DEFAULT_FILE_ENCODING
            )
            
            # Send summary message
            await loading_msg.edit_text(summary)
            
            # Send full analysis as file
            with open(temp_file_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=filename,
                    caption=f"📄 Full comprehensive analysis for {symbol}"
                )
        finally:
            # Clean up temporary file
            if temp_file_path.exists():
                temp_file_path.unlink()
    
    @staticmethod
    def _get_welcome_message() -> str:
        """Get welcome message for /start command.
        
        Returns:
            Formatted welcome message
        """
        return """
🤖 **Welcome to Trading Agent Bot!**

I provide comprehensive stock analysis using the TradingAgents multi-agent framework powered by GLM-4.6.

**Available Commands:**
/analyze <symbol> - Get detailed stock analysis
/help - Show detailed help

**Example:**
/analyze AAPL
/analyze TSLA
/analyze MSFT

Let's start trading! 📈
"""
    
    @staticmethod
    def _get_help_text() -> str:
        """Get help text for /help command.
        
        Returns:
            Formatted help text
        """
        return """
📚 **Bot Commands:**

/analyze <symbol> - Get comprehensive stock analysis
• Example: `/analyze AAPL`
• Uses TradingAgents multi-agent framework
• Includes technical, fundamental, and sentiment analysis
• Analysis takes 2-3 minutes

/help - Show this help message

**What you get:**
• Current price and price changes
• BUY/SELL/HOLD recommendation with confidence level
• Price target and risk assessment
• Comprehensive AI analysis from multiple specialized agents
• Full detailed report as downloadable file

**Analysis Process:**
1. Multiple AI agents analyze the stock
2. Agents debate and reach consensus
3. Risk assessment is performed
4. Final recommendation is generated

⚠️ **Disclaimer:** This bot provides educational information only. 
Always conduct your own research before making investment decisions.
"""
    
    @staticmethod
    def _get_loading_message(symbol: str) -> str:
        """Get loading message while analysis is in progress.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Formatted loading message
        """
        return (
            f"🔍 **Analyzing {symbol}**\\n\\n"
            f"🤖 Multiple AI agents are working...\\n"
            f"⏱️ This may take 2-3 minutes\\n"
            f"📊 Running comprehensive analysis\\n\\n"
            f"Please wait..."
        )
    
    def _format_analysis_summary(self, analysis: dict) -> str:
        """Format analysis data for Telegram display.
        
        Args:
            analysis: Analysis results dictionary
            
        Returns:
            Formatted summary text suitable for Telegram
        """
        # Extract data with defaults
        symbol = analysis.get('symbol', 'Unknown')
        recommendation = analysis.get('recommendation', RECOMMENDATION_HOLD)
        confidence = analysis.get('confidence', 5)
        reasons = analysis.get('reasons', 'No analysis available')
        price_target = float(analysis.get('price_target', 0))
        risk_level = analysis.get('risk_level', 'MEDIUM')
        current_price = float(analysis.get('current_price', 0))
        price_change = float(analysis.get('price_change', 0))
        
        # Truncate analysis text if needed
        reasons_text = self._truncate_analysis_text(str(reasons))
        
        # Get emoji for recommendation
        rec_emoji = RECOMMENDATION_EMOJIS.get(
            str(recommendation).upper(),
            RECOMMENDATION_EMOJIS[RECOMMENDATION_HOLD]
        )
        
        # Format response
        return f"""
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

📄 See attached file for complete detailed analysis.
"""
    
    @staticmethod
    def _truncate_analysis_text(text: str) -> str:
        """Truncate analysis text to fit Telegram limits.
        
        Args:
            text: Full analysis text
            
        Returns:
            Truncated text if necessary
        """
        if len(text) <= MAX_ANALYSIS_LENGTH:
            return text
        
        # Try to cut at sentence boundary
        truncated = text[:MAX_ANALYSIS_LENGTH]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\\n')
        
        cut_point = max(last_period, last_newline)
        
        # Only use cut point if it's reasonably close to the limit
        if cut_point > MAX_ANALYSIS_LENGTH - 500:
            return text[:cut_point + 1] + "\\n\\n[Continued in attached file...]"
        else:
            return truncated + "...\\n\\n[Continued in attached file...]"
    
    def _create_full_analysis_text(self, analysis: dict) -> str:
        """Create full detailed analysis text for file export.
        
        Args:
            analysis: Analysis results dictionary
            
        Returns:
            Formatted full analysis text
        """
        # Extract data
        symbol = analysis.get('symbol', 'N/A')
        timestamp = analysis.get('timestamp', 'Unknown')
        current_price = float(analysis.get('current_price', 0))
        price_change = float(analysis.get('price_change', 0))
        recommendation = analysis.get('recommendation', 'HOLD')
        confidence = analysis.get('confidence', 5)
        risk_level = analysis.get('risk_level', 'MEDIUM')
        price_target = float(analysis.get('price_target', 0))
        reasons = analysis.get('reasons', 'No analysis available')
        
        # Create comprehensive report
        return f"""
{REPORT_SEPARATOR}
COMPREHENSIVE STOCK ANALYSIS REPORT
{REPORT_SEPARATOR}

Symbol: {symbol}
Generated: {timestamp}
Analysis Type: {analysis.get('analysis_type', 'TRADING_AGENTS')}
Powered by: TradingAgents Multi-Agent Framework + GLM-4.6 (Z.AI)

{REPORT_SEPARATOR}
MARKET DATA
{REPORT_SEPARATOR}

Current Price: ${current_price:.2f}
Price Change: {price_change:+.2f}%
Price Target: ${price_target:.2f}
Target Change: {((price_target / current_price - 1) * 100):+.2f}%

{REPORT_SEPARATOR}
RECOMMENDATION
{REPORT_SEPARATOR}

Action: {recommendation}
Confidence: {confidence}/10
Risk Level: {risk_level}

{REPORT_SEPARATOR}
DETAILED ANALYSIS
{REPORT_SEPARATOR}

{reasons}

{REPORT_SEPARATOR}
DISCLAIMER
{REPORT_SEPARATOR}

This analysis is generated by AI and should not be considered as financial advice.
Always do your own research and consult with a qualified financial advisor before
making investment decisions. Past performance does not guarantee future results.

Generated by Trading Agent Bot using:
- GLM-4.6 (Z.AI) for analysis
- TradingAgents multi-agent framework
- yfinance for market data

{REPORT_SEPARATOR}
END OF REPORT
{REPORT_SEPARATOR}
"""
    
    @staticmethod
    def _generate_filename(symbol: str, timestamp: str) -> str:
        """Generate filename for analysis export.
        
        Args:
            symbol: Stock ticker symbol
            timestamp: Analysis timestamp
            
        Returns:
            Generated filename
        """
        # Extract date from timestamp (YYYY-MM-DD format)
        date_str = timestamp[:10] if timestamp else 'unknown'
        return f"{symbol}_analysis_{date_str}{ANALYSIS_FILE_EXTENSION}"
    
    async def error_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle unexpected errors.
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        logger.error(
            f"Update {update} caused error {context.error}",
            exc_info=context.error
        )
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An unexpected error occurred. Please try again later."
            )


def main() -> None:
    """Main function to run the bot."""
    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated")
        
        if Config.BOT_DEBUG:
            logger.info(Config.get_summary())
        
        # Create bot instance
        bot = TradingBot()
        
        # Create application
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CommandHandler("help", bot.help_command))
        application.add_handler(CommandHandler("analyze", bot.analyze_stock))
        
        # Add error handler
        application.add_error_handler(bot.error_handler)
        
        # Start the bot
        logger.info("Starting Trading Agent Bot...")
        logger.info("Bot is ready to receive commands")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        print(f"❌ Configuration error:\\n{e}")
        print("\\nPlease check your .env file and ensure all required variables are set.")
        print("See .env.example for reference.")
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        print(f"❌ Failed to start bot: {e}")


if __name__ == '__main__':
    main()
