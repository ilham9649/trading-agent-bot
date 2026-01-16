"""Trading Agent Telegram Bot.

A sophisticated Telegram bot that provides financial recommendations using
AI-powered multi-agent analysis through the TradingAgents framework.

Features:
- Real-time stock analysis using GLM-4-32b-0414-128k
- Multi-agent consensus system
- Comprehensive market insights
- Risk assessment and price targets
"""

import logging
import os
from typing import Optional
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from trading_agent import TradingAgent, TradingAgentError
from config import Config, ConfigurationError
from constants import (
    MAX_ANALYSIS_LENGTH,
    RECOMMENDATION_EMOJIS,
    RECOMMENDATION_HOLD,
    REPORT_SEPARATOR,
    DEFAULT_FILE_ENCODING,
    ANALYSIS_FILE_EXTENSION,
    EMOJI_SEARCH,
    EMOJI_ROBOT,
    EMOJI_TIMER,
    EMOJI_CHART,
    EMOJI_ERROR,
    EMOJI_FILE,
    EMOJI_LIGHTNING,
    EMOJI_CLOCK,
    EMOJI_TARGET,
    EMOJI_BRAIN,
    EMOJI_BOOKS,
    EMOJI_WARNING,
    EMOJI_ROCKET,
    EMOJI_CHART_UP,
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
        trading_agent: Instance of TradingAgent for analysis
        user_sessions: Dictionary to store user session data
    """
    
    def __init__(self) -> None:
        """Initialize the Trading Bot."""
        self.trading_agent = TradingAgent(
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
        await update.message.reply_text(welcome_message, parse_mode='HTML')
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
        await update.message.reply_text(help_text, parse_mode='HTML')
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
                f"{EMOJI_ERROR} Please provide a stock symbol.\n"
                f"Example: <code>/analyze AAPL</code>",
                parse_mode='HTML'
            )
            return
        
        symbol = context.args[0].upper()
        logger.info(f"User {user_id} requested analysis for {symbol}")
        
        # Save last analyzed symbol
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {'saved_analyses': [], 'last_symbol': None, 'last_analysis': None}
        self.user_sessions[user_id]['last_symbol'] = symbol
        
        # Send loading message
        loading_msg = await update.message.reply_text(
            self._get_loading_message(symbol),
            parse_mode='HTML'
        )
        
        try:
            # Perform analysis
            analysis = await self.trading_agent.analyze_stock(symbol)
            
            # Check for errors
            if "error" in analysis:
                await loading_msg.edit_text(
                    f"{EMOJI_ERROR} Error analyzing {symbol}: {analysis['error']}"
                )
                logger.error(f"Analysis error for {symbol}: {analysis['error']}")
                return
            
            # Save analysis for agent comparison
            self.user_sessions[user_id]['last_analysis'] = analysis
            
            # Format and send results
            await self._send_analysis_results(
                update,
                loading_msg,
                symbol,
                analysis
            )
            
            logger.info(f"Successfully sent analysis for {symbol} to user {user_id}")
            
        except TradingAgentError as e:
            error_msg = f"{EMOJI_ERROR} Trading agent error for {symbol}: {str(e)}"
            await loading_msg.edit_text(error_msg)
            logger.error(error_msg, exc_info=True)
            
        except Exception as e:
            error_msg = (
                f"{EMOJI_ERROR} An unexpected error occurred while analyzing {symbol}. "
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
            
            # Create keyboard for analysis actions
            keyboard = self._create_analysis_keyboard(symbol)
            
            # Send summary message with keyboard
            await loading_msg.edit_text(summary, parse_mode='HTML', reply_markup=keyboard)
            
            # Send full analysis as file
            with open(temp_file_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=filename,
                    caption=f"{EMOJI_FILE} Full comprehensive analysis for <b>{symbol}</b>",
                    parse_mode='HTML'
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
        return f"""
{EMOJI_ROBOT} <b>Welcome to Trading Agent Bot!</b>

I provide comprehensive stock analysis using the TradingAgents multi-agent framework powered by GLM-4-32b-0414-128k.

<b>Available Commands:</b>
/analyze &lt;symbol&gt; - Get detailed stock analysis
/help - Show detailed help

<b>Example:</b>
<code>/analyze AAPL</code>
<code>/analyze TSLA</code>
<code>/analyze MSFT</code>

Let's start trading! {EMOJI_CHART_UP}
"""
    
    @staticmethod
    def _get_help_text() -> str:
        """Get help text for /help command.
        
        Returns:
            Formatted help text
        """
        return f"""
{EMOJI_BOOKS} <b>Bot Commands:</b>

<b>/analyze &lt;symbol&gt;</b> - Get comprehensive stock analysis
• Example: <code>/analyze AAPL</code>
• Uses TradingAgents multi-agent framework
• Includes technical, fundamental, and sentiment analysis
• Analysis takes 2-3 minutes

<b>/help</b> - Show this help message

<b>What you get:</b>
• Current price and price changes
• BUY/SELL/HOLD recommendation with confidence level
• Price target and risk assessment
• Comprehensive AI analysis from multiple specialized agents
• Full detailed report as downloadable file

<b>Analysis Process:</b>
1. Multiple AI agents analyze the stock
2. Agents debate and reach consensus
3. Risk assessment is performed
4. Final recommendation is generated

{EMOJI_WARNING} <b>Disclaimer:</b> This bot provides educational information only. 
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
            f"{EMOJI_SEARCH} <b>Analyzing {symbol}</b>\n\n"
            f"{EMOJI_ROBOT} Multiple AI agents are working...\n"
            f"{EMOJI_TIMER} This may take 2-3 minutes\n"
            f"{EMOJI_CHART} Running comprehensive analysis\n\n"
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
        
        # Get emoji for recommendation
        rec_emoji = RECOMMENDATION_EMOJIS.get(
            str(recommendation).upper(),
            RECOMMENDATION_EMOJIS[RECOMMENDATION_HOLD]
        )
        
        # Truncate reasons to brief summary (max 500 chars)
        reasons_text = self._truncate_analysis_text(str(reasons), max_length=500)
        
        # Format concise response (summary only)
        return f"""
{rec_emoji} <b>{symbol} - Analysis Summary</b>

{EMOJI_CHART} <b>Current Price:</b> ${current_price:.2f} ({price_change:+.2f}%)

{EMOJI_TARGET} <b>Recommendation:</b>
• <b>Action:</b> <code>{recommendation}</code>
• <b>Confidence:</b> {confidence}/10
• <b>Risk Level:</b> {risk_level}
• <b>Price Target:</b> ${price_target:.2f}

{EMOJI_BRAIN} <b>Summary:</b>
{reasons_text}

{EMOJI_FILE} <b>Full Report:</b> See attached file for detailed multi-agent analysis, individual agent reports, and complete findings.
"""
    
    @staticmethod
    def _truncate_analysis_text(text: str, max_length: Optional[int] = None) -> str:
        """Truncate analysis text to fit limits.
        
        Args:
            text: Full analysis text
            max_length: Maximum length to allow (defaults to MAX_ANALYSIS_LENGTH)
            
        Returns:
            Truncated text if necessary
        """
        if max_length is None:
            max_length = MAX_ANALYSIS_LENGTH
            
        if len(text) <= max_length:
            return text
        
        # Try to cut at sentence boundary
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\\n')
        
        cut_point = max(last_period, last_newline)
        
        # Only use cut point if it's reasonably close to the limit
        threshold = max_length - 500
        if cut_point > threshold:
            return text[:cut_point + 1] + "\\n\\n[See full report in attached file...]"
        else:
            return truncated + "...\\n\\n[See full report in attached file...]"
    
    @staticmethod
    def _format_agent_breakdown(agent_reports: dict) -> str:
        """Format individual agent reports for multi-agent analysis display.
        
        Args:
            agent_reports: Dictionary of agent names to their reports
            
        Returns:
            Formatted multi-agent breakdown text
        """
        if not agent_reports:
            return ""
        
        sections = []
        sections.append("\n" + "=" * 40)
        sections.append("🔍 <b>Individual Agent Analysis:</b>")
        sections.append("=" * 40 + "\n")
        
        # Display each agent's perspective with clear separation
        for idx, (agent_name, report) in enumerate(agent_reports.items(), 1):
            # Truncate very long reports
            if len(report) > 200:
                display_report = report[:200] + "..."
            else:
                display_report = report
            
            sections.append(f"<b>Agent {idx}: {agent_name}</b>")
            sections.append("-" * 40)
            sections.append(f"{display_report}")
            
            # Add separator between agents (except last one)
            if idx < len(agent_reports):
                sections.append("")
        
        sections.append("")
        return "\n".join(sections)
    
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
        agent_reports = analysis.get('agent_reports', {})
        
        # Format agent reports section
        agent_section = ""
        if agent_reports:
            agent_section = "\\n\\n" + REPORT_SEPARATOR + "\\n"
            agent_section += "INDIVIDUAL AGENT REPORTS\\n"
            agent_section += REPORT_SEPARATOR + "\\n\\n"
            
            for idx, (agent_name, report) in enumerate(agent_reports.items(), 1):
                agent_section += f"[Agent {idx}] {agent_name}\\n"
                agent_section += "-" * 80 + "\\n"
                agent_section += f"{report}\\n\\n"
                if idx < len(agent_reports):
                    agent_section += REPORT_SEPARATOR + "\\n\\n"
        
        # Create comprehensive report
        return f"""
{REPORT_SEPARATOR}
COMPREHENSIVE STOCK ANALYSIS REPORT
{REPORT_SEPARATOR}

Symbol: {symbol}
Generated: {timestamp}
Analysis Type: {analysis.get('analysis_type', 'TRADING_AGENTS')}
Powered by: TradingAgents Multi-Agent Framework + GLM-4-32b-0414-128k (Z.AI)

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

{reasons}{agent_section}

{REPORT_SEPARATOR}
DISCLAIMER
{REPORT_SEPARATOR}

This analysis is generated by AI and should not be considered as financial advice.
Always do your own research and consult with a qualified financial advisor before
making investment decisions. Past performance does not guarantee future results.

Generated by Trading Agent Bot using:
- GLM-4-32b-0414-128k (Z.AI) for analysis
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
                f"{EMOJI_ERROR} An unexpected error occurred. Please try again later."
            )
    
    async def handle_callback_query(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle inline keyboard button presses.
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        user_id = update.effective_user.id
        
        logger.info(f"User {user_id} pressed button: {callback_data}")
        
        if callback_data == 'analyze_quick':
            await self._prompt_symbol(query)
        elif callback_data == 'help':
            help_text = self._get_help_text()
            keyboard = self._create_help_keyboard()
            await query.message.edit_text(help_text, parse_mode='HTML', reply_markup=keyboard)
        elif callback_data == 'about':
            await self._show_about(query)
        elif callback_data == 'analyze_another':
            await self._prompt_symbol(query)
        elif callback_data.startswith('view_details:'):
            symbol = callback_data.split(':')[1]
            await self._show_detailed_info(query, symbol)
        elif callback_data.startswith('download:'):
            symbol = callback_data.split(':')[1]
            await query.answer(f"📁 Report for {symbol} is attached to the message above")
        elif callback_data.startswith('compare_agents:'):
            symbol = callback_data.split(':')[1]
            await self._show_agent_comparison(query, symbol, user_id)
        elif callback_data.startswith('save:'):
            symbol = callback_data.split(':')[1]
            await self._save_analysis(query, symbol, user_id)
        elif callback_data.startswith('back_to_analysis:'):
            symbol = callback_data.split(':')[1]
            await self.handle_back_to_analysis(query, symbol, user_id)
        elif callback_data == 'delete':
            await self._delete_message(query)
        elif callback_data == 'menu':
            await self._show_menu(query)
        elif callback_data == 'settings':
            await self._show_settings(query)
        elif callback_data == 'commands':
            await self._show_commands(query)
    
    async def _prompt_symbol(self, query) -> None:
        """Prompt user to enter stock symbol.
        
        Args:
            query: Callback query object
        """
        await query.message.edit_text(
            f"📊 <b>Enter stock symbol to analyze:</b>\n\n"
            f"Example: <code>AAPL</code>, <code>TSLA</code>, <code>MSFT</code>\n\n"
            f"Type the symbol now or use /analyze &lt;symbol&gt;",
            parse_mode='HTML'
        )
    
    async def _show_about(self, query) -> None:
        """Show bot information.
        
        Args:
            query: Callback query object
        """
        about_text = (
            f"ℹ️ <b>About Trading Agent Bot</b>\n\n"
            f"Version: <code>1.0.0</code>\n"
            f"Powered by: <b>TradingAgents</b> + <b>GLM-4</b>\n\n"
            f"<b>Features:</b>\n"
            f"• AI-powered stock analysis\n"
            f"• Multi-agent consensus system\n"
            f"• Real-time market data\n"
            f"• Comprehensive reports\n\n"
            f"<i>Built with ❤️ for traders</i>"
        )
        keyboard = self._create_welcome_keyboard()
        await query.message.edit_text(about_text, parse_mode='HTML', reply_markup=keyboard)
    
    async def _show_detailed_info(self, query, symbol: str) -> None:
        """Show detailed information about a symbol.
        
        Args:
            query: Callback query object
            symbol: Stock ticker symbol
        """
        info_text = (
            f"📊 <b>Detailed Information for {symbol}</b>\n\n"
            f"To get the full analysis, use:\n"
            f"<code>/analyze {symbol}</code>\n\n"
            f"This will provide:\n"
            f"• Current price and price changes\n"
            f"• BUY/SELL/HOLD recommendation\n"
            f"• Confidence level and risk assessment\n"
            f"• Price targets\n"
            f"• Comprehensive AI analysis from multiple agents"
        )
        keyboard = self._create_welcome_keyboard()
        await query.message.edit_text(info_text, parse_mode='HTML', reply_markup=keyboard)
    
    async def _save_analysis(self, query, symbol: str, user_id: int) -> None:
        """Save analysis to user history.
        
        Args:
            query: Callback query object
            symbol: Stock ticker symbol
            user_id: User's Telegram ID
        """
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {'saved_analyses': [], 'last_symbol': None}
        
        self.user_sessions[user_id]['saved_analyses'].append({
            'symbol': symbol,
            'timestamp': query.message.date.isoformat()
        })
        self.user_sessions[user_id]['last_symbol'] = symbol
        
        await query.answer(f"💾 Analysis for {symbol} saved!")
        logger.info(f"User {user_id} saved analysis for {symbol}")
    
    async def _delete_message(self, query) -> None:
        """Delete the current message.
        
        Args:
            query: Callback query object
        """
        await query.message.delete()
    
    async def _show_menu(self, query) -> None:
        """Show main menu.
        
        Args:
            query: Callback query object
        """
        welcome_msg = self._get_welcome_message()
        keyboard = self._create_welcome_keyboard()
        await query.message.edit_text(welcome_msg, parse_mode='HTML', reply_markup=keyboard)
    
    async def _show_settings(self, query) -> None:
        """Show settings information.
        
        Args:
            query: Callback query object
        """
        settings_text = (
            f"⚙️ <b>Settings</b>\n\n"
            f"Current bot settings:\n"
            f"• Default Timeframe: <code>{Config.DEFAULT_TIMEFRAME}</code>\n"
            f"• Log Level: <code>{Config.LOG_LEVEL}</code>\n"
            f"• Max Recommendations: <code>{Config.MAX_RECOMMENDATIONS}</code>\n\n"
            f"<i>Advanced settings can be configured in .env file</i>"
        )
        keyboard = self._create_welcome_keyboard()
        await query.message.edit_text(settings_text, parse_mode='HTML', reply_markup=keyboard)
    
    async def _show_commands(self, query) -> None:
        """Show available commands.
        
        Args:
            query: Callback query object
        """
        commands_text = (
            f"📈 <b>Available Commands</b>\n\n"
            f"<code>/start</code> - Start the bot\n"
            f"<code>/analyze &lt;symbol&gt;</code> - Analyze a stock\n"
            f"<code>/help</code> - Show help information\n\n"
            f"<b>Example:</b>\n"
            f"<code>/analyze AAPL</code>\n"
            f"<code>/analyze TSLA</code>\n"
            f"<code>/analyze MSFT</code>"
        )
        keyboard = self._create_welcome_keyboard()
        await query.message.edit_text(commands_text, parse_mode='HTML', reply_markup=keyboard)
    
    async def _show_agent_comparison(self, query, symbol: str, user_id: int) -> None:
        """Show detailed comparison of individual agent analyses.
        
        Args:
            query: Callback query object
            symbol: Stock ticker symbol
            user_id: User's Telegram ID
        """
        # Get saved analysis
        if user_id not in self.user_sessions or 'last_analysis' not in self.user_sessions[user_id]:
            await query.answer("❌ No analysis found. Please run /analyze first.")
            return
        
        analysis = self.user_sessions[user_id]['last_analysis']
        agent_reports = analysis.get('agent_reports', {})
        
        if not agent_reports:
            await query.answer("❌ No individual agent reports available.")
            return
        
        # Format comparison with better separation
        comparison_text = f"🔍 <b>Multi-Agent Comparison for {symbol}</b>\n\n"
        comparison_text += "=" * 40 + "\n\n"
        
        for idx, (agent_name, report) in enumerate(agent_reports.items(), 1):
            comparison_text += f"<b>Agent {idx}: {agent_name}</b>\n"
            comparison_text += "-" * 40 + "\n"
            comparison_text += f"{report}\n\n"
            
            # Add separator between agents (except last one)
            if idx < len(agent_reports):
                comparison_text += "=" * 40 + "\n\n"
        
        comparison_text += f"\n<i>Use 📁 Download Report for full details</i>"
        
        # Create keyboard
        keyboard = [
            [
                InlineKeyboardButton("🔙 Back to Analysis", callback_data=f'back_to_analysis:{symbol}'),
            ],
        ]
        
        await query.message.edit_text(
            comparison_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logger.info(f"User {user_id} viewed agent comparison for {symbol}")
    
    @staticmethod
    def _create_welcome_keyboard():
        """Create inline keyboard for welcome message."""
        keyboard = [
            [
                InlineKeyboardButton("📊 Analyze Stock", callback_data='analyze_quick'),
                InlineKeyboardButton("❓ Help", callback_data='help'),
            ],
            [
                InlineKeyboardButton("ℹ️ About", callback_data='about'),
                InlineKeyboardButton("⚙️ Settings", callback_data='settings'),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def _create_help_keyboard():
        """Create inline keyboard for help message."""
        keyboard = [
            [
                InlineKeyboardButton("📊 Analyze Stock", callback_data='analyze_quick'),
            ],
            [
                InlineKeyboardButton("⬅️ Back to Menu", callback_data='menu'),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def _create_analysis_keyboard(symbol: str):
        """Create inline keyboard for analysis results."""
        keyboard = [
            [
                InlineKeyboardButton("🔍 Compare Agents", callback_data=f'compare_agents:{symbol}'),
                InlineKeyboardButton("📁 Download Report", callback_data=f'download:{symbol}'),
            ],
            [
                InlineKeyboardButton("💾 Save Analysis", callback_data=f'save:{symbol}'),
                InlineKeyboardButton("🔄 Analyze Another", callback_data='analyze_another'),
            ],
            [
                InlineKeyboardButton("❌ Close", callback_data='delete'),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def handle_back_to_analysis(self, query, symbol: str, user_id: int) -> None:
        """Handle back to analysis button.
        
        Args:
            query: Callback query object
            symbol: Stock ticker symbol
            user_id: User's Telegram ID
        """
        # Get saved analysis
        if user_id not in self.user_sessions or 'last_analysis' not in self.user_sessions[user_id]:
            await query.answer("❌ No analysis found.")
            return
        
        analysis = self.user_sessions[user_id]['last_analysis']
        
        # Show analysis summary with keyboard
        summary = self._format_analysis_summary(analysis)
        keyboard = self._create_analysis_keyboard(symbol)
        
        await query.message.edit_text(summary, parse_mode='HTML', reply_markup=keyboard)



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
        
        # Add callback query handler for inline keyboards
        application.add_handler(CallbackQueryHandler(bot.handle_callback_query))
        
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
