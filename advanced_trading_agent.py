import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import yfinance as yf
import pandas as pd
import numpy as np
import openai
import finnhub
import requests
from ta import add_all_ta_features
from ta.utils import dropna

class AdvancedTradingAgent:
    """Advanced trading agent with comprehensive analysis but without complex dependencies"""
    
    def __init__(self, openai_api_key: str, finnhub_api_key: str):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.finnhub_client = finnhub.Client(api_key=finnhub_api_key)
        self.logger = logging.getLogger(__name__)
    
    async def analyze_stock_advanced(self, symbol: str) -> Dict:
        """Perform advanced stock analysis with multiple indicators and AI reasoning"""
        try:
            self.logger.info(f"Starting advanced analysis for {symbol}")
            
            # Get comprehensive stock data
            stock_data = await self._get_comprehensive_data(symbol)
            if "error" in stock_data:
                return stock_data
            
            # Perform technical analysis with error handling
            try:
                technical_analysis = await self._perform_technical_analysis(symbol, stock_data)
            except Exception as e:
                self.logger.warning(f"Technical analysis failed for {symbol}: {e}")
                technical_analysis = {"error": f"Technical analysis failed: {str(e)}"}
            
            # Get fundamental analysis with error handling
            try:
                fundamental_analysis = await self._perform_fundamental_analysis(symbol, stock_data)
            except Exception as e:
                self.logger.warning(f"Fundamental analysis failed for {symbol}: {e}")
                fundamental_analysis = {"error": f"Fundamental analysis failed: {str(e)}"}
            
            # Get sentiment analysis with error handling
            try:
                sentiment_analysis = await self._perform_sentiment_analysis(symbol)
            except Exception as e:
                self.logger.warning(f"Sentiment analysis failed for {symbol}: {e}")
                sentiment_analysis = {"error": f"Sentiment analysis failed: {str(e)}"}
            
            # Generate AI-powered recommendation
            try:
                recommendation = await self._generate_advanced_recommendation(
                    symbol, stock_data, technical_analysis, fundamental_analysis, sentiment_analysis
                )
            except Exception as e:
                self.logger.warning(f"AI recommendation failed for {symbol}: {e}")
                recommendation = {
                    "recommendation": "HOLD",
                    "confidence": 3,
                    "reasons": f"Analysis incomplete due to errors: {str(e)}",
                    "price_target": stock_data.get("price_data", {}).get("current_price", 0),
                    "risk_level": "HIGH",
                    "time_horizon": "MEDIUM"
                }
            
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "analysis_type": "ADVANCED",
                "stock_data": stock_data,
                "technical_analysis": technical_analysis,
                "fundamental_analysis": fundamental_analysis,
                "sentiment_analysis": sentiment_analysis,
                "recommendation": recommendation
            }
            
        except Exception as e:
            self.logger.error(f"Error in advanced analysis for {symbol}: {e}")
            return {"error": f"Advanced analysis failed: {str(e)}"}
    
    async def _get_comprehensive_data(self, symbol: str) -> Dict:
        """Get comprehensive stock data from multiple sources"""
        try:
            # Get data from yfinance
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2y")
            info = ticker.info
            
            if hist.empty:
                return {"error": f"No data found for {symbol}"}
            
            # Get additional data from Finnhub
            profile = self.finnhub_client.company_profile2(symbol=symbol)
            news = self.finnhub_client.company_news(symbol, _from=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'), to=datetime.now().strftime('%Y-%m-%d'))
            
            # Calculate price changes safely
            current_price = float(hist['Close'].iloc[-1])
            price_change_1d = float(hist['Close'].pct_change().iloc[-1] * 100) if not hist['Close'].pct_change().iloc[-1] is None else 0
            price_change_5d = float(hist['Close'].pct_change(5).iloc[-1] * 100) if not hist['Close'].pct_change(5).iloc[-1] is None else 0
            price_change_1m = float(hist['Close'].pct_change(20).iloc[-1] * 100) if not hist['Close'].pct_change(20).iloc[-1] is None else 0
            price_change_3m = float(hist['Close'].pct_change(60).iloc[-1] * 100) if not hist['Close'].pct_change(60).iloc[-1] is None else 0
            price_change_1y = float(hist['Close'].pct_change(252).iloc[-1] * 100) if not hist['Close'].pct_change(252).iloc[-1] is None else 0
            
            self.logger.info(f"Price data for {symbol}: current=${current_price:.2f}, change={price_change_1d:.2f}%")
            
            return {
                "price_data": {
                    "current_price": current_price,
                    "open": float(hist['Open'].iloc[-1]),
                    "high": float(hist['High'].iloc[-1]),
                    "low": float(hist['Low'].iloc[-1]),
                    "volume": int(hist['Volume'].iloc[-1]),
                    "price_change": price_change_1d,
                    "price_change_5d": price_change_5d,
                    "price_change_1m": price_change_1m,
                    "price_change_3m": price_change_3m,
                    "price_change_1y": price_change_1y
                },
                "company_info": {
                    "name": info.get('longName', profile.get('name', symbol)),
                    "sector": info.get('sector', profile.get('finnhubIndustry', 'Unknown')),
                    "industry": info.get('industry', 'Unknown'),
                    "market_cap": info.get('marketCap', profile.get('marketCapitalization', 0)),
                    "pe_ratio": info.get('trailingPE', 0),
                    "forward_pe": info.get('forwardPE', 0),
                    "peg_ratio": info.get('pegRatio', 0),
                    "price_to_book": info.get('priceToBook', 0),
                    "dividend_yield": info.get('dividendYield', 0),
                    "beta": info.get('beta', 1.0)
                },
                "news_count": len(news) if news else 0,
                "recent_news": news[:5] if news else []
            }
            
        except Exception as e:
            self.logger.error(f"Error getting comprehensive data: {e}")
            return {"error": f"Data retrieval failed: {str(e)}"}
    
    async def _perform_technical_analysis(self, symbol: str, stock_data: Dict) -> Dict:
        """Perform comprehensive technical analysis"""
        try:
            # Get historical data for technical indicators
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            
            if hist.empty:
                return {"error": "No historical data for technical analysis"}
            
            # Add technical indicators using ta library
            try:
                df = add_all_ta_features(hist, open="Open", high="High", low="Low", close="Close", volume="Volume")
                df = dropna(df)
            except Exception as e:
                self.logger.warning(f"Error adding technical indicators: {e}, using basic calculations")
                # Fallback to basic technical indicators
                df = hist.copy()
                df['trend_sma_20'] = df['Close'].rolling(window=20).mean()
                df['trend_sma_50'] = df['Close'].rolling(window=50).mean()
                df['trend_sma_200'] = df['Close'].rolling(window=200).mean()
                df['trend_ema_12'] = df['Close'].ewm(span=12).mean()
                df['trend_ema_26'] = df['Close'].ewm(span=26).mean()
                df['momentum_rsi'] = 50  # Default neutral RSI
                df['momentum_stoch'] = 50
                df['momentum_wr'] = -50
                df['volatility_bbh'] = df['Close'] + (df['Close'].rolling(window=20).std() * 2)
                df['volatility_bbl'] = df['Close'] - (df['Close'].rolling(window=20).std() * 2)
                df['volatility_bbm'] = df['Close'].rolling(window=20).mean()
                df['volatility_atr'] = df['High'] - df['Low']
                df['volume_obv'] = df['Volume'].cumsum()
                df['volume_ad'] = df['Volume'].cumsum()
                df['volume_mfi'] = 50
            
            current_price = stock_data["price_data"]["current_price"]
            
            # Calculate key technical indicators with safe access
            def safe_get_value(df, column, default=0):
                try:
                    if column in df.columns and not df[column].isna().iloc[-1]:
                        return float(df[column].iloc[-1])
                    return default
                except (KeyError, IndexError, ValueError):
                    return default
            
            technical_indicators = {
                "moving_averages": {
                    "sma_20": safe_get_value(df, 'trend_sma_20', current_price),
                    "sma_50": safe_get_value(df, 'trend_sma_50', current_price),
                    "sma_200": safe_get_value(df, 'trend_sma_200', current_price),
                    "ema_12": safe_get_value(df, 'trend_ema_12', current_price),
                    "ema_26": safe_get_value(df, 'trend_ema_26', current_price)
                },
                "momentum": {
                    "rsi": safe_get_value(df, 'momentum_rsi', 50),
                    "stoch": safe_get_value(df, 'momentum_stoch', 50),
                    "williams_r": safe_get_value(df, 'momentum_wr', -50)
                },
                "volatility": {
                    "bb_upper": safe_get_value(df, 'volatility_bbh', current_price * 1.1),
                    "bb_lower": safe_get_value(df, 'volatility_bbl', current_price * 0.9),
                    "bb_middle": safe_get_value(df, 'volatility_bbm', current_price),
                    "atr": safe_get_value(df, 'volatility_atr', current_price * 0.02)
                },
                "volume": {
                    "obv": safe_get_value(df, 'volume_obv', 0),
                    "ad": safe_get_value(df, 'volume_ad', 0),
                    "mfi": safe_get_value(df, 'volume_mfi', 50)
                }
            }
            
            # Generate technical signals
            signals = self._generate_technical_signals(technical_indicators, current_price)
            
            return {
                "indicators": technical_indicators,
                "signals": signals,
                "analysis": self._analyze_technical_patterns(technical_indicators, current_price)
            }
            
        except Exception as e:
            self.logger.error(f"Error in technical analysis: {e}")
            return {"error": f"Technical analysis failed: {str(e)}"}
    
    def _generate_technical_signals(self, indicators: Dict, current_price: float) -> Dict:
        """Generate technical trading signals"""
        signals = {
            "trend": "NEUTRAL",
            "momentum": "NEUTRAL", 
            "volatility": "NORMAL",
            "volume": "NORMAL",
            "overall": "NEUTRAL"
        }
        
        # Trend analysis
        sma_20 = indicators["moving_averages"]["sma_20"]
        sma_50 = indicators["moving_averages"]["sma_50"]
        sma_200 = indicators["moving_averages"]["sma_200"]
        
        if current_price > sma_20 > sma_50 > sma_200:
            signals["trend"] = "STRONG_BULLISH"
        elif current_price > sma_20 > sma_50:
            signals["trend"] = "BULLISH"
        elif current_price < sma_20 < sma_50 < sma_200:
            signals["trend"] = "STRONG_BEARISH"
        elif current_price < sma_20 < sma_50:
            signals["trend"] = "BEARISH"
        
        # Momentum analysis
        rsi = indicators["momentum"]["rsi"]
        if rsi > 70:
            signals["momentum"] = "OVERBOUGHT"
        elif rsi < 30:
            signals["momentum"] = "OVERSOLD"
        elif rsi > 50:
            signals["momentum"] = "BULLISH"
        else:
            signals["momentum"] = "BEARISH"
        
        # Volatility analysis
        bb_upper = indicators["volatility"]["bb_upper"]
        bb_lower = indicators["volatility"]["bb_lower"]
        if current_price > bb_upper:
            signals["volatility"] = "HIGH"
        elif current_price < bb_lower:
            signals["volatility"] = "LOW"
        
        # Overall signal
        bullish_count = sum([
            signals["trend"] in ["BULLISH", "STRONG_BULLISH"],
            signals["momentum"] in ["BULLISH", "OVERSOLD"],
            signals["volatility"] == "LOW"
        ])
        
        bearish_count = sum([
            signals["trend"] in ["BEARISH", "STRONG_BEARISH"],
            signals["momentum"] in ["BEARISH", "OVERBOUGHT"],
            signals["volatility"] == "HIGH"
        ])
        
        if bullish_count > bearish_count:
            signals["overall"] = "BULLISH"
        elif bearish_count > bullish_count:
            signals["overall"] = "BEARISH"
        
        return signals
    
    def _analyze_technical_patterns(self, indicators: Dict, current_price: float) -> str:
        """Analyze technical patterns and provide insights"""
        analysis = []
        
        # Moving average analysis
        sma_20 = indicators["moving_averages"]["sma_20"]
        sma_50 = indicators["moving_averages"]["sma_50"]
        
        if current_price > sma_20 > sma_50:
            analysis.append("Price is above both 20-day and 50-day moving averages, indicating bullish momentum")
        elif current_price < sma_20 < sma_50:
            analysis.append("Price is below both 20-day and 50-day moving averages, indicating bearish momentum")
        else:
            analysis.append("Mixed signals from moving averages")
        
        # RSI analysis
        rsi = indicators["momentum"]["rsi"]
        if rsi > 70:
            analysis.append(f"RSI at {rsi:.1f} suggests overbought conditions")
        elif rsi < 30:
            analysis.append(f"RSI at {rsi:.1f} suggests oversold conditions")
        else:
            analysis.append(f"RSI at {rsi:.1f} indicates neutral momentum")
        
        # Bollinger Bands analysis
        bb_upper = indicators["volatility"]["bb_upper"]
        bb_lower = indicators["volatility"]["bb_lower"]
        if current_price > bb_upper:
            analysis.append("Price is above upper Bollinger Band, may indicate overbought")
        elif current_price < bb_lower:
            analysis.append("Price is below lower Bollinger Band, may indicate oversold")
        else:
            analysis.append("Price is within normal Bollinger Band range")
        
        return " | ".join(analysis)
    
    async def _perform_fundamental_analysis(self, symbol: str, stock_data: Dict) -> Dict:
        """Perform fundamental analysis"""
        try:
            company_info = stock_data["company_info"]
            
            # Calculate fundamental metrics
            pe_ratio = company_info.get("pe_ratio", 0)
            forward_pe = company_info.get("forward_pe", 0)
            peg_ratio = company_info.get("peg_ratio", 0)
            price_to_book = company_info.get("price_to_book", 0)
            dividend_yield = company_info.get("dividend_yield", 0)
            beta = company_info.get("beta", 1.0)
            
            # Fundamental scoring
            fundamental_score = 0
            analysis_points = []
            
            # P/E Ratio analysis
            if 0 < pe_ratio < 15:
                fundamental_score += 2
                analysis_points.append(f"P/E ratio of {pe_ratio:.1f} suggests undervalued")
            elif 15 <= pe_ratio <= 25:
                fundamental_score += 1
                analysis_points.append(f"P/E ratio of {pe_ratio:.1f} is reasonable")
            elif pe_ratio > 25:
                analysis_points.append(f"P/E ratio of {pe_ratio:.1f} suggests overvalued")
            
            # PEG Ratio analysis
            if 0 < peg_ratio < 1:
                fundamental_score += 2
                analysis_points.append(f"PEG ratio of {peg_ratio:.1f} indicates good growth value")
            elif 1 <= peg_ratio <= 2:
                fundamental_score += 1
                analysis_points.append(f"PEG ratio of {peg_ratio:.1f} is acceptable")
            
            # Price-to-Book analysis
            if 0 < price_to_book < 1:
                fundamental_score += 2
                analysis_points.append(f"P/B ratio of {price_to_book:.1f} suggests undervalued")
            elif 1 <= price_to_book <= 3:
                fundamental_score += 1
                analysis_points.append(f"P/B ratio of {price_to_book:.1f} is reasonable")
            
            # Beta analysis
            if beta < 0.8:
                analysis_points.append(f"Low beta of {beta:.1f} indicates lower volatility")
            elif beta > 1.2:
                analysis_points.append(f"High beta of {beta:.1f} indicates higher volatility")
            
            # Dividend analysis
            if dividend_yield > 0.03:
                fundamental_score += 1
                analysis_points.append(f"Good dividend yield of {dividend_yield:.1%}")
            
            return {
                "metrics": {
                    "pe_ratio": pe_ratio,
                    "forward_pe": forward_pe,
                    "peg_ratio": peg_ratio,
                    "price_to_book": price_to_book,
                    "dividend_yield": dividend_yield,
                    "beta": beta
                },
                "score": fundamental_score,
                "analysis": " | ".join(analysis_points) if analysis_points else "Limited fundamental data available"
            }
            
        except Exception as e:
            self.logger.error(f"Error in fundamental analysis: {e}")
            return {"error": f"Fundamental analysis failed: {str(e)}"}
    
    async def _perform_sentiment_analysis(self, symbol: str) -> Dict:
        """Perform sentiment analysis based on news and market data"""
        try:
            # Get recent news
            news = self.finnhub_client.company_news(
                symbol, 
                _from=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                to=datetime.now().strftime('%Y-%m-%d')
            )
            
            if not news:
                return {
                    "sentiment_score": 0,
                    "news_count": 0,
                    "analysis": "No recent news available for sentiment analysis"
                }
            
            # Simple sentiment analysis based on news headlines
            positive_keywords = ['growth', 'profit', 'revenue', 'increase', 'positive', 'strong', 'beat', 'exceed', 'upgrade', 'bullish']
            negative_keywords = ['loss', 'decline', 'decrease', 'negative', 'weak', 'miss', 'downgrade', 'bearish', 'concern', 'risk']
            
            sentiment_score = 0
            news_analysis = []
            
            for article in news[:10]:  # Analyze top 10 news
                headline = article.get('headline', '').lower()
                summary = article.get('summary', '').lower()
                text = headline + ' ' + summary
                
                positive_count = sum(1 for word in positive_keywords if word in text)
                negative_count = sum(1 for word in negative_keywords if word in text)
                
                if positive_count > negative_count:
                    sentiment_score += 1
                elif negative_count > positive_count:
                    sentiment_score -= 1
            
            # Normalize sentiment score
            max_possible_score = min(len(news), 10)
            normalized_score = sentiment_score / max_possible_score if max_possible_score > 0 else 0
            
            if normalized_score > 0.2:
                sentiment = "POSITIVE"
            elif normalized_score < -0.2:
                sentiment = "NEGATIVE"
            else:
                sentiment = "NEUTRAL"
            
            return {
                "sentiment_score": normalized_score,
                "sentiment": sentiment,
                "news_count": len(news),
                "analysis": f"Sentiment analysis based on {len(news)} recent news articles"
            }
            
        except Exception as e:
            self.logger.error(f"Error in sentiment analysis: {e}")
            return {"error": f"Sentiment analysis failed: {str(e)}"}
    
    async def _generate_advanced_recommendation(self, symbol: str, stock_data: Dict, 
                                              technical: Dict, fundamental: Dict, sentiment: Dict) -> Dict:
        """Generate AI-powered recommendation based on all analysis"""
        try:
            # Prepare comprehensive data for AI analysis
            analysis_data = {
                "symbol": symbol,
                "current_price": stock_data["price_data"]["current_price"],
                "price_change_1d": stock_data["price_data"]["price_change"],
                "price_change_1m": stock_data["price_data"]["price_change_1m"],
                "price_change_1y": stock_data["price_data"]["price_change_1y"],
                "volume": stock_data["price_data"]["volume"],
                "market_cap": stock_data["company_info"]["market_cap"],
                "pe_ratio": fundamental.get("metrics", {}).get("pe_ratio", 0),
                "beta": stock_data["company_info"]["beta"],
                "technical_signals": technical.get("signals", {}),
                "fundamental_score": fundamental.get("score", 0),
                "sentiment_score": sentiment.get("sentiment_score", 0),
                "news_count": sentiment.get("news_count", 0)
            }
            
            # Create comprehensive prompt for AI
            prompt = f"""
            Analyze the following comprehensive stock data and provide a detailed trading recommendation:
            
            Stock: {symbol}
            Current Price: ${analysis_data['current_price']:.2f}
            Price Changes: 1D: {analysis_data['price_change_1d']:+.2f}%, 1M: {analysis_data['price_change_1m']:+.2f}%, 1Y: {analysis_data['price_change_1y']:+.2f}%
            Volume: {analysis_data['volume']:,}
            Market Cap: ${analysis_data['market_cap']:,}
            P/E Ratio: {analysis_data['pe_ratio']:.1f}
            Beta: {analysis_data['beta']:.2f}
            
            Technical Analysis:
            - Trend: {analysis_data['technical_signals'].get('trend', 'Unknown')}
            - Momentum: {analysis_data['technical_signals'].get('momentum', 'Unknown')}
            - Volatility: {analysis_data['technical_signals'].get('volatility', 'Unknown')}
            - Overall Signal: {analysis_data['technical_signals'].get('overall', 'Unknown')}
            
            Fundamental Analysis:
            - Score: {analysis_data['fundamental_score']}/5
            - Analysis: {fundamental.get('analysis', 'No analysis available')}
            
            Sentiment Analysis:
            - Score: {analysis_data['sentiment_score']:.2f}
            - News Count: {analysis_data['news_count']}
            - Analysis: {sentiment.get('analysis', 'No analysis available')}
            
            Please provide:
            1. Overall recommendation (BUY/SELL/HOLD)
            2. Confidence level (1-10)
            3. Key reasons for the recommendation (3-5 bullet points)
            4. Price target (realistic range)
            5. Risk assessment (LOW/MEDIUM/HIGH)
            6. Time horizon (SHORT/MEDIUM/LONG term)
            
            Format your response as JSON with these exact keys: recommendation, confidence, reasons, price_target, risk_level, time_horizon
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional financial analyst with expertise in technical analysis, fundamental analysis, and market sentiment. Provide clear, data-driven trading recommendations based on comprehensive analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            
            try:
                # Extract JSON from response
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
                        "price_target": analysis_data['current_price'],
                        "risk_level": "MEDIUM",
                        "time_horizon": "MEDIUM"
                    }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                current_price = analysis_data['current_price']
                recommendation = {
                    "recommendation": "HOLD",
                    "confidence": 5,
                    "reasons": content,
                    "price_target": current_price * 1.05 if current_price > 0 else 0,  # 5% above current price
                    "risk_level": "MEDIUM",
                    "time_horizon": "MEDIUM"
                }
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Error generating advanced recommendation: {e}")
            current_price = stock_data.get("price_data", {}).get("current_price", 0)
            return {
                "recommendation": "HOLD",
                "confidence": 1,
                "reasons": f"Analysis error: {str(e)}",
                "price_target": current_price * 1.05 if current_price > 0 else 0,
                "risk_level": "HIGH",
                "time_horizon": "MEDIUM"
            }