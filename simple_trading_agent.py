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
    from tradingagents.agents.utils.memory import FinancialSituationMemory
    from openai import OpenAI
    
    # Monkey patch to fix Z.AI embeddings issue (Z.AI doesn't support embeddings)
    original_init = FinancialSituationMemory.__init__
    
    def patched_init(self, name, config):
        """Patched init that uses OpenAI for embeddings, regardless of backend_url"""
        import chromadb
        from chromadb.config import Settings
        
        if config["backend_url"] == "http://localhost:11434/v1":
            self.embedding = "nomic-embed-text"
            self.client = OpenAI(base_url=config["backend_url"])
        else:
            # Always use OpenAI API for embeddings (Z.AI doesn't support embeddings)
            self.embedding = "text-embedding-3-small"
            # Use separate OpenAI key for embeddings
            openai_embeddings_key = os.environ.get('OPENAI_EMBEDDINGS_KEY')
            self.client = OpenAI(
                api_key=openai_embeddings_key,
                base_url="https://api.openai.com/v1"
            )
        
        self.chroma_client = chromadb.Client(Settings(allow_reset=True))
        self.situation_collection = self.chroma_client.create_collection(name=name)
    
    # Apply the monkey patch
    FinancialSituationMemory.__init__ = patched_init
    
    TRADING_AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: TradingAgents not available: {e}")
    TRADING_AGENTS_AVAILABLE = False

class SimpleTradingAgent:
    """Simple trading agent that uses TradingAgents library directly"""
    
    def __init__(self, glm_api_key: str, finnhub_api_key: str, openai_api_key: str = None):
        self.glm_api_key = glm_api_key
        self.finnhub_api_key = finnhub_api_key
        self.openai_api_key = openai_api_key or glm_api_key  # Fallback to GLM if not provided
        self.logger = logging.getLogger(__name__)
        
        # Configure TradingAgents to use GLM-4.6
        self.config = DEFAULT_CONFIG.copy()
        self.config["llm_provider"] = "openai"  # GLM is OpenAI-compatible
        self.config["backend_url"] = "https://api.z.ai/api/paas/v4/"
        self.config["deep_think_llm"] = "glm-4.6"  # Use GLM-4.6 for deep thinking
        self.config["quick_think_llm"] = "glm-4.6"  # Use GLM-4.6 for quick thinking
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
            # Set OPENAI_API_KEY to GLM key because TradingAgents uses this env variable
            # The monkey patch will use a separate OpenAI client for embeddings
            os.environ['OPENAI_API_KEY'] = self.glm_api_key
            # Store OpenAI key separately for embeddings
            os.environ['OPENAI_EMBEDDINGS_KEY'] = self.openai_api_key
            
            self.trading_agents = TradingAgentsGraph(
                debug=False, 
                config=self.config
            )
            self.logger.info("TradingAgents initialized successfully with GLM-4.6 (chat) + OpenAI (embeddings)")
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
            
            # Log raw result and decision for debugging
            self.logger.info(f"TradingAgents result type: {type(result)}, decision type: {type(decision)}")
            self.logger.info(f"TradingAgents result keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")
            self.logger.info(f"TradingAgents decision: {decision}")
            
            # Format the result for display
            formatted_result = self._format_trading_agents_result(symbol, result, decision)
            
            return formatted_result
            
        except Exception as e:
            self.logger.error(f"Error in TradingAgents analysis for {symbol}: {e}")
            return {"error": f"TradingAgents analysis failed: {str(e)}"}
    
    def _format_trading_agents_result(self, symbol: str, result: Dict, decision: str) -> Dict:
        """Format TradingAgents result for Telegram display"""
        try:
            # Decision is a string like "BUY", "SELL", or "HOLD"
            recommendation = str(decision).strip().upper() if decision else 'HOLD'
            
            # Extract comprehensive analysis from final_state (result)
            analysis_text = ""
            
            if isinstance(result, dict):
                # Get the full trade decision text
                final_decision = result.get('final_trade_decision', '')
                investment_plan = result.get('investment_plan', '')
                trader_plan = result.get('trader_investment_plan', '')
                
                # Combine all analysis sections
                analysis_sections = []
                
                if result.get('market_report'):
                    analysis_sections.append(f"Market Analysis: {result['market_report']}")
                
                if result.get('fundamentals_report'):
                    analysis_sections.append(f"Fundamental Analysis: {result['fundamentals_report']}")
                
                if result.get('news_report'):
                    analysis_sections.append(f"News Analysis: {result['news_report']}")
                
                if result.get('sentiment_report'):
                    analysis_sections.append(f"Sentiment Analysis: {result['sentiment_report']}")
                
                # Add investment debate conclusions
                if result.get('investment_debate_state', {}).get('judge_decision'):
                    analysis_sections.append(f"Investment Debate: {result['investment_debate_state']['judge_decision']}")
                
                # Add trader's plan
                if trader_plan:
                    analysis_sections.append(f"Trading Plan: {trader_plan}")
                
                # Add final investment plan
                if investment_plan:
                    analysis_sections.append(f"Investment Plan: {investment_plan}")
                
                # Add final decision
                if final_decision:
                    analysis_sections.append(f"Final Decision: {final_decision}")
                
                analysis_text = "\n\n".join(analysis_sections)
            
            # Get stock price from yfinance (TradingAgents doesn't return it in final state)
            import yfinance as yf
            current_price = 0
            price_change = 0
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                    if len(hist) > 1:
                        price_change = float((hist['Close'].iloc[-1] / hist['Close'].iloc[-2] - 1) * 100)
            except Exception as e:
                self.logger.error(f"Error fetching price for {symbol}: {e}")
            
            # Calculate price target based on recommendation
            price_target = 0
            if current_price > 0:
                if recommendation == 'BUY':
                    price_target = current_price * 1.1  # 10% above
                elif recommendation == 'SELL':
                    price_target = current_price * 0.9  # 10% below
                else:
                    price_target = current_price * 1.05  # 5% above
            
            # Determine confidence and risk based on analysis depth
            confidence = 8 if analysis_text else 5  # Higher confidence if we have full analysis
            risk_level = "MEDIUM"  # Default, could be extracted from risk debate if available
            
            if isinstance(result, dict) and result.get('risk_debate_state', {}).get('judge_decision'):
                risk_decision = result['risk_debate_state']['judge_decision']
                if 'high' in risk_decision.lower() or 'aggressive' in risk_decision.lower():
                    risk_level = "HIGH"
                elif 'low' in risk_decision.lower() or 'conservative' in risk_decision.lower():
                    risk_level = "LOW"
            
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "analysis_type": "TRADING_AGENTS",
                "current_price": current_price,
                "price_change": price_change,
                "recommendation": recommendation,
                "confidence": confidence,
                "reasons": analysis_text if analysis_text else "Full TradingAgents analysis completed",
                "price_target": price_target,
                "risk_level": risk_level
            }
            
        except Exception as e:
            self.logger.error(f"Error formatting TradingAgents result: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                "symbol": symbol,
                "error": f"Error formatting result: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "analysis_type": "TRADING_AGENTS"
            }