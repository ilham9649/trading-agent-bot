import asyncio
import logging
import sys
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

# Add TradingAgents to path
trading_agents_path = os.path.join(os.path.dirname(__file__), 'TradingAgents')
if trading_agents_path not in sys.path:
    sys.path.insert(0, trading_agents_path)

# Import TradingAgents
try:
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    from tradingagents.default_config import DEFAULT_CONFIG
    TRADING_AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: TradingAgents not available: {e}")
    TRADING_AGENTS_AVAILABLE = False

class EnhancedTradingAgent:
    """Enhanced trading agent using the actual TradingAgents library"""
    
    def __init__(self, openai_api_key: str, finnhub_api_key: str):
        self.openai_api_key = openai_api_key
        self.finnhub_api_key = finnhub_api_key
        self.logger = logging.getLogger(__name__)
        
        # Configure TradingAgents
        self.config = DEFAULT_CONFIG.copy()
        self.config["deep_think_llm"] = "gpt-4o-mini"  # Use cheaper model for cost efficiency
        self.config["quick_think_llm"] = "gpt-4o-mini"
        self.config["max_debate_rounds"] = 2  # Reduce debate rounds for faster response
        
        # Configure data vendors
        self.config["data_vendors"] = {
            "core_stock_apis": "yfinance",
            "technical_indicators": "yfinance", 
            "fundamental_data": "yfinance",  # Use yfinance instead of Alpha Vantage
            "news_data": "yfinance",
        }
        
        # Initialize TradingAgents
        self.trading_agents = None
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize the TradingAgents graph"""
        if not TRADING_AGENTS_AVAILABLE:
            self.logger.warning("TradingAgents not available, using fallback analysis")
            self.trading_agents = None
            return
            
        try:
            # Set environment variables for TradingAgents
            os.environ['OPENAI_API_KEY'] = self.openai_api_key
            
            self.trading_agents = TradingAgentsGraph(
                debug=False, 
                config=self.config
            )
            self.logger.info("TradingAgents initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize TradingAgents: {e}")
            self.trading_agents = None
    
    async def analyze_stock_enhanced(self, symbol: str) -> Dict:
        """Analyze a stock using the full TradingAgents framework"""
        if not self.trading_agents:
            return {"error": "TradingAgents not properly initialized"}
        
        try:
            # Get current date
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            self.logger.info(f"Starting enhanced analysis for {symbol} on {current_date}")
            
            # Run the full TradingAgents analysis
            # This will take much longer as it runs multiple agents
            result, decision = await asyncio.to_thread(
                self.trading_agents.propagate, 
                symbol, 
                current_date
            )
            
            # Format the result for Telegram
            formatted_result = self._format_trading_agents_result(symbol, result, decision)
            
            return formatted_result
            
        except Exception as e:
            self.logger.error(f"Error in enhanced analysis for {symbol}: {e}")
            return {"error": f"Enhanced analysis failed: {str(e)}"}
    
    def _format_trading_agents_result(self, symbol: str, result: Dict, decision: Dict) -> Dict:
        """Format TradingAgents result for Telegram display"""
        try:
            # Extract key information from the result
            analysis_data = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "decision": decision,
                "analysis_summary": result.get("analysis_summary", "No summary available"),
                "agents_insights": result.get("agents_insights", {}),
                "risk_assessment": result.get("risk_assessment", {}),
                "recommendation": self._extract_recommendation(decision),
                "confidence": self._extract_confidence(decision),
                "reasons": self._extract_reasons(decision),
                "price_target": self._extract_price_target(decision),
                "risk_level": self._extract_risk_level(decision)
            }
            
            return analysis_data
            
        except Exception as e:
            self.logger.error(f"Error formatting result: {e}")
            return {
                "symbol": symbol,
                "error": f"Error formatting result: {str(e)}",
                "raw_decision": str(decision),
                "raw_result": str(result)
            }
    
    def _extract_recommendation(self, decision: Dict) -> str:
        """Extract recommendation from decision"""
        if isinstance(decision, dict):
            if "action" in decision:
                return decision["action"]
            elif "recommendation" in decision:
                return decision["recommendation"]
            elif "decision" in decision:
                return decision["decision"]
        return "HOLD"
    
    def _extract_confidence(self, decision: Dict) -> int:
        """Extract confidence level from decision"""
        if isinstance(decision, dict):
            if "confidence" in decision:
                return int(decision["confidence"])
            elif "confidence_level" in decision:
                return int(decision["confidence_level"])
        return 5
    
    def _extract_reasons(self, decision: Dict) -> str:
        """Extract reasons from decision"""
        if isinstance(decision, dict):
            if "reasons" in decision:
                return decision["reasons"]
            elif "analysis" in decision:
                return decision["analysis"]
            elif "reasoning" in decision:
                return decision["reasoning"]
        return "Analysis completed by TradingAgents framework"
    
    def _extract_price_target(self, decision: Dict) -> float:
        """Extract price target from decision"""
        if isinstance(decision, dict):
            if "price_target" in decision:
                return float(decision["price_target"])
            elif "target_price" in decision:
                return float(decision["target_price"])
        return 0.0
    
    def _extract_risk_level(self, decision: Dict) -> str:
        """Extract risk level from decision"""
        if isinstance(decision, dict):
            if "risk_level" in decision:
                return decision["risk_level"]
            elif "risk" in decision:
                return decision["risk"]
        return "MEDIUM"
    
    async def get_quick_analysis(self, symbol: str) -> Dict:
        """Get a quick analysis using simplified approach for faster response"""
        try:
            import yfinance as yf
            
            # Get basic stock data
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1y")
            
            if hist.empty:
                return {"error": f"No data found for {symbol}"}
            
            current_price = hist['Close'].iloc[-1]
            price_change = hist['Close'].pct_change().iloc[-1] * 100
            
            # Basic technical indicators
            ma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            ma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            
            # Simple recommendation logic
            if ma_20 > ma_50 and price_change > 0:
                recommendation = "BUY"
                confidence = 7
            elif ma_20 < ma_50 and price_change < 0:
                recommendation = "SELL"
                confidence = 6
            else:
                recommendation = "HOLD"
                confidence = 5
            
            return {
                "symbol": symbol,
                "current_price": round(current_price, 2),
                "price_change_pct": round(price_change, 2),
                "ma_20": round(ma_20, 2),
                "ma_50": round(ma_50, 2),
                "company_name": info.get('longName', symbol),
                "sector": info.get('sector', 'Unknown'),
                "market_cap": info.get('marketCap', 0),
                "recommendation": recommendation,
                "confidence": confidence,
                "reasons": f"Quick analysis based on moving averages and price momentum",
                "price_target": round(current_price * (1 + price_change/100), 2),
                "risk_level": "MEDIUM",
                "analysis_type": "QUICK",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in quick analysis: {e}")
            return {"error": f"Quick analysis failed: {str(e)}"}