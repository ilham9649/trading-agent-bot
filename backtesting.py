"""Backtesting Framework for Trading Agent Bot.

This module provides comprehensive backtesting capabilities to evaluate
the performance of the TradingAgents strategy on historical data.

Features:
- Portfolio simulation with cash and position management
- Transaction cost modeling
- Multiple performance metrics (returns, Sharpe ratio, max drawdown, etc.)
- Trade history tracking
- Detailed performance reports
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

import yfinance as yf
import pandas as pd
import numpy as np

from trading_agent import TradingAgent, TradingAgentError
from constants import RECOMMENDATION_BUY, RECOMMENDATION_SELL, RECOMMENDATION_HOLD

logger = logging.getLogger(__name__)


class PositionSide(Enum):
    """Position side enum."""
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


@dataclass
class Trade:
    """Represents a single trade."""
    date: str
    symbol: str
    action: str  # BUY, SELL, HOLD
    price: float
    shares: float
    value: float
    commission: float
    cash_before: float
    cash_after: float
    portfolio_value: float
    confidence: int
    reason: str = ""


@dataclass
class Position:
    """Represents a stock position."""
    symbol: str
    shares: float
    avg_price: float
    current_price: float = 0.0
    
    @property
    def value(self) -> float:
        """Current value of position."""
        return self.shares * self.current_price
    
    @property
    def cost_basis(self) -> float:
        """Total cost basis."""
        return self.shares * self.avg_price
    
    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss."""
        return self.value - self.cost_basis
    
    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized profit/loss percentage."""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    commission_pct: float = 0.001  # 0.1% per trade
    position_size_pct: float = 1.0  # Use 100% of capital per position
    allow_short: bool = False
    rebalance_frequency: str = "daily"  # daily, weekly, monthly
    min_confidence: int = 5  # Minimum confidence to take a trade


@dataclass
class BacktestResult:
    """Results from a backtest run."""
    config: BacktestConfig
    trades: List[Trade] = field(default_factory=list)
    daily_portfolio_values: List[Tuple[str, float]] = field(default_factory=list)
    final_portfolio_value: float = 0.0
    total_return: float = 0.0
    total_return_pct: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    total_commission: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "config": {
                "symbol": self.config.symbol,
                "start_date": self.config.start_date,
                "end_date": self.config.end_date,
                "initial_capital": self.config.initial_capital,
                "commission_pct": self.config.commission_pct,
                "position_size_pct": self.config.position_size_pct,
            },
            "performance": {
                "final_portfolio_value": self.final_portfolio_value,
                "total_return": self.total_return,
                "total_return_pct": self.total_return_pct,
                "sharpe_ratio": self.sharpe_ratio,
                "max_drawdown": self.max_drawdown,
                "win_rate": self.win_rate,
            },
            "trades": {
                "total": self.total_trades,
                "winning": self.winning_trades,
                "losing": self.losing_trades,
                "avg_win": self.avg_win,
                "avg_loss": self.avg_loss,
                "total_commission": self.total_commission,
            }
        }


class BacktestEngine:
    """Main backtesting engine.
    
    This class simulates trading based on TradingAgent signals over
    historical data and calculates performance metrics.
    
    Attributes:
        config: Backtesting configuration
        trading_agent: TradingAgent instance for generating signals
        cash: Current cash balance
        positions: Dictionary of current positions
        trades: List of all trades executed
        portfolio_values: Daily portfolio value history
    """
    
    def __init__(
        self,
        config: BacktestConfig,
        trading_agent: TradingAgent
    ):
        """Initialize backtesting engine.
        
        Args:
            config: Backtesting configuration
            trading_agent: TradingAgent instance
        """
        self.config = config
        self.trading_agent = trading_agent
        
        # Portfolio state
        self.cash = config.initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.portfolio_values: List[Tuple[str, float]] = []
        
        # Price data cache
        self.price_data: Optional[pd.DataFrame] = None
        
    def load_price_data(self) -> pd.DataFrame:
        """Load historical price data.
        
        Returns:
            DataFrame with historical OHLCV data
        """
        logger.info(
            f"Loading price data for {self.config.symbol} "
            f"from {self.config.start_date} to {self.config.end_date}"
        )
        
        ticker = yf.Ticker(self.config.symbol)
        df = ticker.history(
            start=self.config.start_date,
            end=self.config.end_date,
            interval="1d"
        )
        
        if df.empty:
            raise ValueError(f"No data available for {self.config.symbol}")
        
        self.price_data = df
        logger.info(f"Loaded {len(df)} days of price data")
        
        return df
    
    def get_portfolio_value(self, current_date: str) -> float:
        """Calculate total portfolio value.
        
        Args:
            current_date: Current date for price lookup
            
        Returns:
            Total portfolio value (cash + positions)
        """
        positions_value = 0.0
        
        for position in self.positions.values():
            # Update position with current price
            if current_date in self.price_data.index:
                position.current_price = self.price_data.loc[current_date, 'Close']
                positions_value += position.value
        
        return self.cash + positions_value
    
    def execute_trade(
        self,
        date: str,
        action: str,
        price: float,
        confidence: int,
        reason: str = ""
    ) -> Optional[Trade]:
        """Execute a trade.
        
        Args:
            date: Trade date
            action: BUY, SELL, or HOLD
            price: Execution price
            confidence: Confidence level (0-10)
            reason: Reason for trade
            
        Returns:
            Trade object if executed, None if skipped
        """
        symbol = self.config.symbol
        
        # Skip if confidence is too low
        if confidence < self.config.min_confidence:
            logger.debug(f"{date}: Confidence {confidence} below minimum, skipping trade")
            return None
        
        # Calculate position size
        position_size = self.config.position_size_pct
        
        if action == RECOMMENDATION_BUY:
            # Calculate shares to buy
            max_investment = self.cash * position_size
            shares = max_investment / price
            trade_value = shares * price
            commission = trade_value * self.config.commission_pct
            total_cost = trade_value + commission
            
            # Check if we have enough cash
            if total_cost > self.cash:
                logger.warning(f"{date}: Insufficient cash for BUY (need ${total_cost:.2f}, have ${self.cash:.2f})")
                return None
            
            # Execute buy
            cash_before = self.cash
            self.cash -= total_cost
            
            # Update or create position
            if symbol in self.positions:
                pos = self.positions[symbol]
                total_shares = pos.shares + shares
                total_cost_basis = (pos.shares * pos.avg_price) + trade_value
                pos.avg_price = total_cost_basis / total_shares
                pos.shares = total_shares
            else:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    shares=shares,
                    avg_price=price,
                    current_price=price
                )
            
            trade = Trade(
                date=date,
                symbol=symbol,
                action=action,
                price=price,
                shares=shares,
                value=trade_value,
                commission=commission,
                cash_before=cash_before,
                cash_after=self.cash,
                portfolio_value=self.get_portfolio_value(date),
                confidence=confidence,
                reason=reason
            )
            
            logger.info(
                f"{date}: BUY {shares:.2f} shares of {symbol} @ ${price:.2f} "
                f"(value: ${trade_value:.2f}, commission: ${commission:.2f})"
            )
            
            self.trades.append(trade)
            return trade
            
        elif action == RECOMMENDATION_SELL:
            # Check if we have a position to sell
            if symbol not in self.positions:
                logger.debug(f"{date}: No position to sell")
                return None
            
            position = self.positions[symbol]
            shares = position.shares
            trade_value = shares * price
            commission = trade_value * self.config.commission_pct
            proceeds = trade_value - commission
            
            # Execute sell
            cash_before = self.cash
            self.cash += proceeds
            
            # Calculate realized P&L
            realized_pnl = trade_value - (shares * position.avg_price)
            
            # Remove position
            del self.positions[symbol]
            
            trade = Trade(
                date=date,
                symbol=symbol,
                action=action,
                price=price,
                shares=shares,
                value=trade_value,
                commission=commission,
                cash_before=cash_before,
                cash_after=self.cash,
                portfolio_value=self.get_portfolio_value(date),
                confidence=confidence,
                reason=reason
            )
            
            logger.info(
                f"{date}: SELL {shares:.2f} shares of {symbol} @ ${price:.2f} "
                f"(value: ${trade_value:.2f}, commission: ${commission:.2f}, P&L: ${realized_pnl:.2f})"
            )
            
            self.trades.append(trade)
            return trade
        
        return None
    
    async def run(self) -> BacktestResult:
        """Run the backtest.
        
        Returns:
            BacktestResult with performance metrics
        """
        logger.info("Starting backtest...")
        logger.info("="*80)
        logger.info("IMPORTANT: Historical Date Handling")
        logger.info("- TradingAgents will analyze each historical date as if it's 'today'")
        logger.info("- News data will be fetched for that specific date (via Alpha Vantage)")
        logger.info("- However, LLM knowledge cutoff may affect analysis quality")
        logger.info("- Check logs to verify dates being used")
        logger.info("="*80)
        
        # Load price data
        price_data = self.load_price_data()
        
        # Iterate through each trading day
        total_days = len(price_data)
        for i, (date, row) in enumerate(price_data.iterrows()):
            date_str = date.strftime("%Y-%m-%d")
            current_price = row['Close']
            
            logger.info(f"\n{'='*80}")
            logger.info(f"Processing Day {i+1}/{total_days}: {date_str}")
            logger.info(f"Price: ${current_price:.2f}")
            logger.info(f"Analyzing as if today is: {date_str}")
            logger.info(f"{'='*80}")
            
            try:
                # IMPORTANT: The TradingAgent will use this date for analysis
                # News, fundamentals, and all data should be relative to this date
                logger.info(f"Calling TradingAgent with date: {date_str}")
                
                # Get trading signal from agent
                # CRITICAL: Pass the historical date for proper backtesting
                analysis = await self.trading_agent.analyze_stock(
                    self.config.symbol, 
                    trade_date=date_str
                )
                
                if "error" in analysis:
                    logger.error(f"{date_str}: Analysis error: {analysis['error']}")
                    continue
                
                recommendation = analysis.get('recommendation', RECOMMENDATION_HOLD)
                confidence = analysis.get('confidence', 5)
                reasons = analysis.get('reasons', '')
                
                logger.info(
                    f"{date_str}: Signal: {recommendation} "
                    f"(confidence: {confidence}/10)"
                )
                
                # Execute trade based on signal
                self.execute_trade(
                    date=date_str,
                    action=recommendation,
                    price=current_price,
                    confidence=confidence,
                    reason=reasons[:200]  # Truncate for storage
                )
                
            except TradingAgentError as e:
                logger.error(f"{date_str}: Trading agent error: {e}")
                continue
            except Exception as e:
                logger.error(f"{date_str}: Unexpected error: {e}", exc_info=True)
                continue
            
            # Record portfolio value
            portfolio_value = self.get_portfolio_value(date_str)
            self.portfolio_values.append((date_str, portfolio_value))
            
            logger.info(f"{date_str}: Portfolio value: ${portfolio_value:,.2f}")
        
        # Calculate final metrics
        result = self._calculate_metrics()
        
        logger.info("Backtest completed!")
        logger.info(f"Final portfolio value: ${result.final_portfolio_value:,.2f}")
        logger.info(f"Total return: ${result.total_return:,.2f} ({result.total_return_pct:.2f}%)")
        logger.info(f"Sharpe ratio: {result.sharpe_ratio:.2f}")
        logger.info(f"Max drawdown: {result.max_drawdown:.2f}%")
        logger.info(f"Win rate: {result.win_rate:.2f}%")
        
        return result
    
    def _calculate_metrics(self) -> BacktestResult:
        """Calculate performance metrics.
        
        Returns:
            BacktestResult with all metrics
        """
        result = BacktestResult(config=self.config)
        
        # Basic metrics
        result.trades = self.trades
        result.daily_portfolio_values = self.portfolio_values
        result.total_trades = len(self.trades)
        
        # Final portfolio value
        if self.portfolio_values:
            result.final_portfolio_value = self.portfolio_values[-1][1]
        else:
            result.final_portfolio_value = self.config.initial_capital
        
        # Returns
        result.total_return = result.final_portfolio_value - self.config.initial_capital
        result.total_return_pct = (result.total_return / self.config.initial_capital) * 100
        
        # Commission
        result.total_commission = sum(trade.commission for trade in self.trades)
        
        # Win/loss analysis
        buy_sell_pairs = []
        buy_trades = [t for t in self.trades if t.action == RECOMMENDATION_BUY]
        sell_trades = [t for t in self.trades if t.action == RECOMMENDATION_SELL]
        
        for i in range(min(len(buy_trades), len(sell_trades))):
            buy = buy_trades[i]
            sell = sell_trades[i]
            pnl = (sell.price - buy.price) * buy.shares - buy.commission - sell.commission
            pnl_pct = ((sell.price / buy.price) - 1) * 100
            buy_sell_pairs.append((pnl, pnl_pct))
        
        if buy_sell_pairs:
            winning_pairs = [p for p in buy_sell_pairs if p[0] > 0]
            losing_pairs = [p for p in buy_sell_pairs if p[0] < 0]
            
            result.winning_trades = len(winning_pairs)
            result.losing_trades = len(losing_pairs)
            result.win_rate = (result.winning_trades / len(buy_sell_pairs)) * 100
            
            if winning_pairs:
                result.avg_win = sum(p[0] for p in winning_pairs) / len(winning_pairs)
            if losing_pairs:
                result.avg_loss = sum(p[0] for p in losing_pairs) / len(losing_pairs)
        
        # Calculate Sharpe ratio and max drawdown
        if len(self.portfolio_values) > 1:
            values = [v[1] for v in self.portfolio_values]
            returns = pd.Series(values).pct_change().dropna()
            
            if len(returns) > 0 and returns.std() > 0:
                # Annualized Sharpe ratio (assuming 252 trading days)
                result.sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
            
            # Max drawdown
            cumulative = pd.Series(values)
            running_max = cumulative.cummax()
            drawdown = (cumulative - running_max) / running_max * 100
            result.max_drawdown = drawdown.min()
        
        return result


def save_backtest_result(result: BacktestResult, output_dir: str = "./backtest_results") -> str:
    """Save backtest result to file.
    
    Args:
        result: BacktestResult to save
        output_dir: Directory to save results
        
    Returns:
        Path to saved file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backtest_{result.config.symbol}_{timestamp}.json"
    filepath = output_path / filename
    
    with open(filepath, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    
    logger.info(f"Backtest result saved to {filepath}")
    return str(filepath)
