"""TradingAgent - Integration with TradingAgents Framework.

This module provides an interface to the TradingAgents multi-agent
trading framework, configured to use GLM-4-32b-0414-128k for analysis and OpenAI for embeddings.

The module handles:
- TradingAgents configuration and initialization
- Stock analysis orchestration
- Result formatting for Telegram display
- Error handling and logging

Note: This implementation uses a custom memory patch to support separate
API keys for GLM (analysis) and OpenAI (embeddings).
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path

from constants import (
    PRICE_TARGET_BUY_MULTIPLIER,
    PRICE_TARGET_SELL_MULTIPLIER,
    PRICE_TARGET_HOLD_MULTIPLIER,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    RISK_HIGH_KEYWORDS,
    RISK_LOW_KEYWORDS,
    RISK_LEVEL_HIGH,
    RISK_LEVEL_MEDIUM,
    RISK_LEVEL_LOW,
    RECOMMENDATION_BUY,
    RECOMMENDATION_SELL,
    RECOMMENDATION_HOLD,
    TRADINGAGENTS_MAX_DEBATE_ROUNDS,
    TRADINGAGENTS_DATA_VENDOR,
    GLM_MODEL_VERSION,
    GLM_API_BASE_URL,
    OPENAI_EMBEDDING_MODEL,
    OPENAI_API_BASE_URL,
    DEFAULT_HISTORY_PERIOD,
)

# Add TradingAgents to Python path
trading_agents_path = Path(__file__).parent / 'TradingAgents'
if str(trading_agents_path) not in sys.path:
    sys.path.insert(0, str(trading_agents_path))

# Import TradingAgents with error handling
try:
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.agents.utils.memory import FinancialSituationMemory
    from openai import OpenAI
    
    # Patch FinancialSituationMemory to use separate API keys
    # This is necessary because Z.AI doesn't support embeddings
    _original_memory_init = FinancialSituationMemory.__init__
    
    def _patched_memory_init(self, name: str, config: Dict[str, Any]) -> None:
        """Patched init that uses OpenAI for embeddings regardless of backend_url.
        
        Args:
            name: Name for the memory collection
            config: Configuration dictionary with backend_url
        """
        import chromadb
        from chromadb.config import Settings
        
        if config.get("backend_url") == "http://localhost:11434/v1":
            # Local Ollama setup
            self.embedding = "nomic-embed-text"
            self.client = OpenAI(base_url=config["backend_url"])
        else:
            # Always use OpenAI for embeddings when using cloud APIs
            self.embedding = OPENAI_EMBEDDING_MODEL
            openai_key = os.environ.get('OPENAI_EMBEDDINGS_KEY')
            self.client = OpenAI(
                api_key=openai_key,
                base_url=OPENAI_API_BASE_URL
            )
        
        self.chroma_client = chromadb.Client(Settings(allow_reset=True))
        self.situation_collection = self.chroma_client.create_collection(name=name)
    
    # Apply the patch
    FinancialSituationMemory.__init__ = _patched_memory_init
    
    TRADING_AGENTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"TradingAgents library not available: {e}")
    TRADING_AGENTS_AVAILABLE = False


logger = logging.getLogger(__name__)


class TradingAgentError(Exception):
    """Raised when there's an error in trading agent operations."""
    pass


class TradingAgent:
    """Interface to TradingAgents framework.
    
    This class provides a streamlined way to analyze stocks using the
    TradingAgents multi-agent framework with GLM-4-32b-0414-128k for analysis.
    
    Attributes:
        glm_api_key: API key for Z.AI (GLM)
        finnhub_api_key: API key for Finnhub
        openai_api_key: API key for OpenAI (embeddings only)
        alpha_vantage_api_key: API key for Alpha Vantage (news data)
        config: TradingAgents configuration dictionary
        trading_agents: Instance of TradingAgentsGraph
    """
    
    def __init__(
        self,
        glm_api_key: str,
        finnhub_api_key: str,
        openai_api_key: Optional[str] = None,
        alpha_vantage_api_key: Optional[str] = None
    ) -> None:
        """Initialize TradingAgent.
        
        Args:
            glm_api_key: Z.AI API key for GLM-4-32b-0414-128k
            finnhub_api_key: Finnhub API key for market data
            openai_api_key: OpenAI API key for embeddings (optional, defaults to GLM key)
            alpha_vantage_api_key: Alpha Vantage API key for news data (optional)
        """
        self.glm_api_key = glm_api_key
        self.finnhub_api_key = finnhub_api_key
        self.openai_api_key = openai_api_key or glm_api_key
        self.alpha_vantage_api_key = alpha_vantage_api_key
        
        # Configure TradingAgents to use GLM-4-32b-0414-128k
        self.config = self._create_config()
        
        # Initialize TradingAgents
        self.trading_agents: Optional[TradingAgentsGraph] = None
        self._initialize_agents()
    
    def _create_config(self) -> Dict[str, Any]:
        """Create TradingAgents configuration.
        
        Returns:
            Dictionary with TradingAgents configuration
        """
        config = DEFAULT_CONFIG.copy()
        
        # Configure LLM provider (GLM is OpenAI-compatible)
        config["llm_provider"] = "openai"
        config["backend_url"] = GLM_API_BASE_URL
        config["deep_think_llm"] = GLM_MODEL_VERSION
        config["quick_think_llm"] = GLM_MODEL_VERSION
        config["max_debate_rounds"] = TRADINGAGENTS_MAX_DEBATE_ROUNDS
        
        # Configure data vendors
        # Use yfinance for stock data, Alpha Vantage for news
        config["data_vendors"] = {
            "core_stock_apis": TRADINGAGENTS_DATA_VENDOR,
            "technical_indicators": TRADINGAGENTS_DATA_VENDOR,
            "fundamental_data": TRADINGAGENTS_DATA_VENDOR,
            "news_data": "alpha_vantage",  # Alpha Vantage for news data
        }
        
        return config
    
    def _initialize_agents(self) -> None:
        """Initialize the TradingAgents graph.
        
        Raises:
            TradingAgentError: If initialization fails
        """
        if not TRADING_AGENTS_AVAILABLE:
            logger.warning("TradingAgents library not available")
            self.trading_agents = None
            return
        
        try:
            # Set environment variables for TradingAgents
            # Main API key is GLM, separate key for embeddings
            os.environ['OPENAI_API_KEY'] = self.glm_api_key
            os.environ['OPENAI_EMBEDDINGS_KEY'] = self.openai_api_key
            
            # Set Alpha Vantage API key if provided
            if self.alpha_vantage_api_key:
                os.environ['ALPHA_VANTAGE_API_KEY'] = self.alpha_vantage_api_key
                logger.info("Alpha Vantage API key configured for news data")
            else:
                logger.warning(
                    "Alpha Vantage API key not provided - news data may be limited. "
                    "Get a free key at https://www.alphavantage.co/support/#api-key"
                )
            
            self.trading_agents = TradingAgentsGraph(
                debug=False,
                config=self.config
            )
            
            logger.info(
                "TradingAgents initialized successfully "
                f"(Analysis: GLM-4-32b-0414-128k, Embeddings: OpenAI)"
            )
        except Exception as e:
            logger.error(f"Failed to initialize TradingAgents: {e}", exc_info=True)
            raise TradingAgentError(f"Initialization failed: {e}")
    
    async def analyze_stock(self, symbol: str, trade_date: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a stock using TradingAgents framework.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            trade_date: Optional date for historical analysis (YYYY-MM-DD format)
                       If None, uses current date. For backtesting, pass historical date.
            
        Returns:
            Dictionary containing analysis results with keys:
                - symbol: Stock ticker
                - timestamp: Analysis timestamp
                - analysis_type: Type of analysis performed
                - current_price: Current stock price
                - price_change: Price change percentage
                - recommendation: BUY/SELL/HOLD
                - confidence: Confidence score (0-10)
                - reasons: Detailed analysis text
                - price_target: Target price
                - risk_level: Risk assessment
                
        Raises:
            TradingAgentError: If analysis fails
        """
        if not self.trading_agents:
            raise TradingAgentError("TradingAgents not properly initialized")
        
        try:
            # Use provided date for backtesting, otherwise use current date
            current_date = trade_date if trade_date else datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"Analyzing {symbol} for date: {current_date}")
            if trade_date:
                logger.info(f"BACKTEST MODE: Using historical date {current_date}")
                logger.info(f"News and data will be fetched for this date")
            
            logger.info(f"Starting analysis for {symbol} on {current_date}")
            
            # Run TradingAgents analysis in thread pool
            result, decision = await asyncio.to_thread(
                self.trading_agents.propagate,
                symbol,
                current_date
            )
            
            logger.info(f"Analysis completed for {symbol}: {decision}")
            logger.debug(f"Result type: {type(result)}, Decision: {decision}")
            
            # Format and return results
            return self._format_analysis_result(symbol, result, decision)
            
        except Exception as e:
            logger.error(
                f"Analysis failed for {symbol}: {e}",
                exc_info=True
            )
            raise TradingAgentError(f"Analysis failed: {e}")
    
    def _format_analysis_result(
        self,
        symbol: str,
        result: Dict[str, Any],
        decision: str
    ) -> Dict[str, Any]:
        """Format TradingAgents result for Telegram display.
        
        Args:
            symbol: Stock ticker symbol
            result: Raw result from TradingAgents
            decision: Trading decision (BUY/SELL/HOLD)
            
        Returns:
            Formatted analysis dictionary
        """
        try:
            # Normalize recommendation
            recommendation = self._normalize_recommendation(decision)
            
            # Extract comprehensive analysis
            analysis_text = self._extract_analysis_text(result)
            
            # Get current price data
            current_price, price_change = self._fetch_price_data(symbol)
            
            # Calculate price target
            price_target = self._calculate_price_target(
                current_price,
                recommendation
            )
            
            # Determine confidence and risk
            confidence = CONFIDENCE_HIGH if analysis_text else CONFIDENCE_MEDIUM
            risk_level = self._determine_risk_level(result)
            
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "analysis_type": "TRADING_AGENTS",
                "current_price": current_price,
                "price_change": price_change,
                "recommendation": recommendation,
                "confidence": confidence,
                "reasons": analysis_text or "Analysis completed successfully",
                "price_target": price_target,
                "risk_level": risk_level
            }
            
        except Exception as e:
            logger.error(f"Error formatting result: {e}", exc_info=True)
            return {
                "symbol": symbol,
                "error": f"Formatting error: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "analysis_type": "TRADING_AGENTS"
            }
    
    @staticmethod
    def _normalize_recommendation(decision: Optional[str]) -> str:
        """Normalize trading decision to standard format.
        
        Args:
            decision: Raw decision string from TradingAgents
            
        Returns:
            Normalized recommendation (BUY/SELL/HOLD)
        """
        if not decision:
            return RECOMMENDATION_HOLD
        
        decision_upper = str(decision).strip().upper()
        
        if decision_upper in (RECOMMENDATION_BUY, RECOMMENDATION_SELL, RECOMMENDATION_HOLD):
            return decision_upper
        
        return RECOMMENDATION_HOLD
    
    @staticmethod
    def _extract_analysis_text(result: Dict[str, Any]) -> str:
        """Extract comprehensive analysis text from result.
        
        Args:
            result: Raw result dictionary from TradingAgents
            
        Returns:
            Formatted analysis text
        """
        if not isinstance(result, dict):
            return ""
        
        sections = []
        
        # Extract key reports
        report_keys = [
            ('market_report', 'Market Analysis'),
            ('fundamentals_report', 'Fundamental Analysis'),
            ('news_report', 'News Analysis'),
            ('sentiment_report', 'Sentiment Analysis'),
        ]
        
        # Error phrases to filter out
        error_phrases = [
            'i apologize for the confusion',
            'future date',
            'invalid inputs',
            'let me know how you\'d like to proceed',
            'cannot provide news for the future',
            'it seems there was an issue',
        ]
        
        for key, title in report_keys:
            report_text = result.get(key, '')
            if report_text:
                # Filter out error messages
                report_lower = report_text.lower()
                is_error = any(phrase in report_lower for phrase in error_phrases)
                
                if not is_error and len(report_text.strip()) > 50:
                    sections.append(f"{title}: {report_text}")
                elif is_error:
                    logger.warning(f"{title} contained error message, skipping")
        
        # Add investment debate conclusions
        debate_decision = result.get('investment_debate_state', {}).get('judge_decision')
        if debate_decision:
            sections.append(f"Investment Debate: {debate_decision}")
        
        # Add trader's plan
        trader_plan = result.get('trader_investment_plan')
        if trader_plan:
            sections.append(f"Trading Plan: {trader_plan}")
        
        # Add investment plan
        investment_plan = result.get('investment_plan')
        if investment_plan:
            sections.append(f"Investment Plan: {investment_plan}")
        
        # Add final decision
        final_decision = result.get('final_trade_decision')
        if final_decision:
            sections.append(f"Final Decision: {final_decision}")
        
        # If no valid sections, provide a default message
        if not sections:
            sections.append("Analysis completed. Recommendation based on multi-agent consensus and risk assessment.")
        
        return "\\n\\n".join(sections)
    
    @staticmethod
    def _fetch_price_data(symbol: str) -> Tuple[float, float]:
        """Fetch current price and price change for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Tuple of (current_price, price_change_percent)
        """
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=DEFAULT_HISTORY_PERIOD)
            
            if hist.empty:
                logger.warning(f"No price data available for {symbol}")
                return 0.0, 0.0
            
            current_price = float(hist['Close'].iloc[-1])
            
            if len(hist) > 1:
                prev_price = float(hist['Close'].iloc[-2])
                price_change = ((current_price / prev_price) - 1) * 100
            else:
                price_change = 0.0
            
            return current_price, price_change
            
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return 0.0, 0.0
    
    @staticmethod
    def _calculate_price_target(
        current_price: float,
        recommendation: str
    ) -> float:
        """Calculate price target based on recommendation.
        
        Args:
            current_price: Current stock price
            recommendation: Trading recommendation
            
        Returns:
            Target price
        """
        if current_price <= 0:
            return 0.0
        
        multipliers = {
            RECOMMENDATION_BUY: PRICE_TARGET_BUY_MULTIPLIER,
            RECOMMENDATION_SELL: PRICE_TARGET_SELL_MULTIPLIER,
            RECOMMENDATION_HOLD: PRICE_TARGET_HOLD_MULTIPLIER,
        }
        
        multiplier = multipliers.get(recommendation, PRICE_TARGET_HOLD_MULTIPLIER)
        return current_price * multiplier
    
    @staticmethod
    def _determine_risk_level(result: Dict[str, Any]) -> str:
        """Determine risk level from analysis result.
        
        Args:
            result: Result dictionary from TradingAgents
            
        Returns:
            Risk level string (HIGH/MEDIUM/LOW)
        """
        if not isinstance(result, dict):
            return RISK_LEVEL_MEDIUM
        
        risk_decision = result.get('risk_debate_state', {}).get('judge_decision', '')
        
        if not risk_decision:
            return RISK_LEVEL_MEDIUM
        
        risk_lower = risk_decision.lower()
        
        if any(keyword in risk_lower for keyword in RISK_HIGH_KEYWORDS):
            return RISK_LEVEL_HIGH
        elif any(keyword in risk_lower for keyword in RISK_LOW_KEYWORDS):
            return RISK_LEVEL_LOW
        
        return RISK_LEVEL_MEDIUM
