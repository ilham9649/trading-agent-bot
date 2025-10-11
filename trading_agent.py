import openai
import finnhub
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import json

class TradingAgent:
    """Trading agent that provides financial recommendations using OpenAI and Finnhub"""
    
    def __init__(self, openai_api_key: str, finnhub_api_key: str):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.finnhub_client = finnhub.Client(api_key=finnhub_api_key)
        self.logger = logging.getLogger(__name__)
    
    def get_stock_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Fetch stock data using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            return data
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_company_news(self, symbol: str, days: int = 7) -> List[Dict]:
        """Get recent company news from Finnhub"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            news = self.finnhub_client.company_news(
                symbol, 
                _from=start_date.strftime('%Y-%m-%d'),
                to=end_date.strftime('%Y-%m-%d')
            )
            return news[:10]  # Limit to 10 most recent news
        except Exception as e:
            self.logger.error(f"Error fetching news for {symbol}: {e}")
            return []
    
    def get_company_profile(self, symbol: str) -> Dict:
        """Get company profile from Finnhub"""
        try:
            profile = self.finnhub_client.company_profile2(symbol=symbol)
            return profile
        except Exception as e:
            self.logger.error(f"Error fetching profile for {symbol}: {e}")
            return {}
    
    def analyze_stock(self, symbol: str) -> Dict:
        """Analyze a stock and provide recommendation"""
        try:
            # Get stock data
            stock_data = self.get_stock_data(symbol)
            if stock_data.empty:
                return {"error": f"Could not fetch data for {symbol}"}
            
            # Get company information
            profile = self.get_company_profile(symbol)
            news = self.get_company_news(symbol)
            
            # Calculate basic technical indicators
            current_price = stock_data['Close'].iloc[-1]
            price_change = stock_data['Close'].pct_change().iloc[-1] * 100
            volume = stock_data['Volume'].iloc[-1]
            avg_volume = stock_data['Volume'].mean()
            
            # Calculate moving averages
            ma_20 = stock_data['Close'].rolling(window=20).mean().iloc[-1]
            ma_50 = stock_data['Close'].rolling(window=50).mean().iloc[-1]
            
            # Prepare data for AI analysis
            analysis_data = {
                "symbol": symbol,
                "current_price": round(current_price, 2),
                "price_change_pct": round(price_change, 2),
                "volume": int(volume),
                "avg_volume": int(avg_volume),
                "ma_20": round(ma_20, 2),
                "ma_50": round(ma_50, 2),
                "company_name": profile.get('name', 'Unknown'),
                "sector": profile.get('finnhubIndustry', 'Unknown'),
                "market_cap": profile.get('marketCapitalization', 0),
                "recent_news_count": len(news)
            }
            
            # Generate AI recommendation
            recommendation = self._generate_recommendation(analysis_data, news)
            
            return {
                "symbol": symbol,
                "analysis": analysis_data,
                "recommendation": recommendation,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return {"error": f"Analysis failed for {symbol}: {str(e)}"}
    
    def _generate_recommendation(self, data: Dict, news: List[Dict]) -> Dict:
        """Generate AI-powered recommendation using OpenAI"""
        try:
            # Prepare news summary
            news_summary = ""
            if news:
                news_summary = "Recent news:\n"
                for article in news[:3]:  # Top 3 news
                    news_summary += f"- {article.get('headline', 'No headline')}\n"
            
            # Create prompt for OpenAI
            prompt = f"""
            Analyze the following stock data and provide a trading recommendation:
            
            Stock: {data['symbol']} ({data['company_name']})
            Current Price: ${data['current_price']}
            Price Change: {data['price_change_pct']}%
            Volume: {data['volume']:,} (Avg: {data['avg_volume']:,})
            MA20: ${data['ma_20']}
            MA50: ${data['ma_50']}
            Sector: {data['sector']}
            Market Cap: ${data['market_cap']:,}
            
            {news_summary}
            
            Please provide:
            1. Overall recommendation (BUY/SELL/HOLD)
            2. Confidence level (1-10)
            3. Key reasons for the recommendation
            4. Price target (if applicable)
            5. Risk assessment (LOW/MEDIUM/HIGH)
            
            Format your response as JSON with these exact keys: recommendation, confidence, reasons, price_target, risk_level
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional financial analyst. Provide clear, data-driven trading recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    recommendation = json.loads(json_str)
                else:
                    # Fallback if no JSON found
                    recommendation = {
                        "recommendation": "HOLD",
                        "confidence": 5,
                        "reasons": content,
                        "price_target": data['current_price'],
                        "risk_level": "MEDIUM"
                    }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                recommendation = {
                    "recommendation": "HOLD",
                    "confidence": 5,
                    "reasons": content,
                    "price_target": data['current_price'],
                    "risk_level": "MEDIUM"
                }
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Error generating recommendation: {e}")
            return {
                "recommendation": "HOLD",
                "confidence": 1,
                "reasons": f"Analysis error: {str(e)}",
                "price_target": data['current_price'],
                "risk_level": "HIGH"
            }
    
    def get_market_overview(self) -> Dict:
        """Get general market overview"""
        try:
            # Get major indices
            indices = ['^GSPC', '^DJI', '^IXIC', '^VIX']
            market_data = {}
            
            for index in indices:
                data = self.get_stock_data(index, "5d")
                if not data.empty:
                    current = data['Close'].iloc[-1]
                    change = data['Close'].pct_change().iloc[-1] * 100
                    market_data[index] = {
                        'price': round(current, 2),
                        'change_pct': round(change, 2)
                    }
            
            return {
                "market_data": market_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market overview: {e}")
            return {"error": f"Market overview failed: {str(e)}"}