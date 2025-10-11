import asyncio
import logging
import sys
import os
from typing import Dict
from datetime import datetime

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

class SimpleTradingAgent:
    """Simple trading agent that uses TradingAgents library directly"""
    
    def __init__(self, openai_api_key: str, finnhub_api_key: str):
        self.openai_api_key = openai_api_key
        self.finnhub_api_key = finnhub_api_key
        self.logger = logging.getLogger(__name__)
        
        # Configure TradingAgents
        self.config = DEFAULT_CONFIG.copy()
        self.config["deep_think_llm"] = "gpt-4o-mini"  # Use cheaper model
        self.config["quick_think_llm"] = "gpt-4o-mini"
        self.config["max_debate_rounds"] = 1  # Reduce debate rounds for faster response
        
        # Configure data vendors to use yfinance
        self.config["data_vendors"] = {
            "core_stock_apis": "yfinance",
            "technical_indicators": "yfinance", 
            "fundamental_data": "yfinance",
            "news_data": "yfinance",
        }
        
        # Initialize TradingAgents
        self.trading_agents = None
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize the TradingAgents graph"""
        if not TRADING_AGENTS_AVAILABLE:
            self.logger.warning("TradingAgents not available")
            self.trading_agents = None
            return
            
        try:
            # Set environment variables
            os.environ['OPENAI_API_KEY'] = self.openai_api_key
            
            self.trading_agents = TradingAgentsGraph(
                debug=False, 
                config=self.config
            )
            self.logger.info("TradingAgents initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize TradingAgents: {e}")
            self.trading_agents = None
    
    async def analyze_stock(self, symbol: str) -> Dict:
        """Analyze a stock using TradingAgents library directly"""
        if not self.trading_agents:
            return {"error": "TradingAgents not properly initialized"}
        
        try:
            # Get current date
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            self.logger.info(f"Starting TradingAgents analysis for {symbol} on {current_date}")
            
            # Run TradingAgents analysis
            result, decision = await asyncio.to_thread(
                self.trading_agents.propagate, 
                symbol, 
                current_date
            )
            
            # Format the result for display
            formatted_result = self._format_trading_agents_result(symbol, result, decision)
            
            return formatted_result
            
        except Exception as e:
            self.logger.error(f"Error in TradingAgents analysis for {symbol}: {e}")
            return {"error": f"TradingAgents analysis failed: {str(e)}"}
    
    def _format_trading_agents_result(self, symbol: str, result: Dict, decision: Dict) -> Dict:
        """Format TradingAgents result for Telegram display"""
        try:
            # Extract basic information
            analysis_data = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "analysis_type": "TRADING_AGENTS",
                "raw_result": result,
                "raw_decision": decision
            }
            
            # Try to extract recommendation from decision
            if isinstance(decision, dict):
                recommendation = decision.get('recommendation', decision.get('action', decision.get('decision', 'HOLD')))
                confidence = decision.get('confidence', decision.get('confidence_level', 5))
                reasons = decision.get('reasons', decision.get('analysis', decision.get('reasoning', 'Analysis completed by TradingAgents')))
                price_target = decision.get('price_target', decision.get('target_price', 0))
                risk_level = decision.get('risk_level', decision.get('risk', 'MEDIUM'))
            else:
                # If decision is not a dict, use defaults
                recommendation = 'HOLD'
                confidence = 5
                reasons = str(decision) if decision else 'Analysis completed by TradingAgents'
                price_target = 0
                risk_level = 'MEDIUM'
            
            # Try to extract price information from result
            current_price = 0
            price_change = 0
            
            if isinstance(result, dict):
                # Look for price data in various possible locations
                price_data = result.get('price_data', {})
                if not price_data:
                    price_data = result.get('stock_data', {})
                if not price_data:
                    price_data = result.get('data', {})
                
                current_price = price_data.get('current_price', price_data.get('price', 0))
                price_change = price_data.get('price_change', price_data.get('change', 0))
                
                # If still no price data, try to get it from other fields
                if not current_price:
                    current_price = result.get('current_price', result.get('price', 0))
                if not price_change:
                    price_change = result.get('price_change', result.get('change', 0))
            
            # Ensure numeric values
            try:
                current_price = float(current_price) if current_price else 0
                price_change = float(price_change) if price_change else 0
                price_target = float(price_target) if price_target else 0
            except (ValueError, TypeError):
                current_price = 0
                price_change = 0
                price_target = 0
            
            # If no price target provided, calculate a reasonable one
            if price_target == 0 and current_price > 0:
                if recommendation.upper() == 'BUY':
                    price_target = current_price * 1.1  # 10% above current price
                elif recommendation.upper() == 'SELL':
                    price_target = current_price * 0.9  # 10% below current price
                else:
                    price_target = current_price * 1.05  # 5% above current price
            
            analysis_data.update({
                "current_price": current_price,
                "price_change": price_change,
                "recommendation": recommendation,
                "confidence": confidence,
                "reasons": reasons,
                "price_target": price_target,
                "risk_level": risk_level
            })
            
            return analysis_data
            
        except Exception as e:
            self.logger.error(f"Error formatting TradingAgents result: {e}")
            return {
                "symbol": symbol,
                "error": f"Error formatting result: {str(e)}",
                "raw_result": str(result),
                "raw_decision": str(decision)
            }