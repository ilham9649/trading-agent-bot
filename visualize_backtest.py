"""Backtest Visualization - Generate charts and reports.

This script creates visual reports from backtest results including:
- Portfolio value over time
- Trade markers
- Returns distribution
- Drawdown chart

Usage:
    python visualize_backtest.py backtest_results/backtest_AAPL_20241012_123456.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

try:
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    print("Warning: matplotlib and pandas required for visualization")
    print("Install with: pip install matplotlib pandas")


def load_backtest_result(filepath: str) -> Dict[str, Any]:
    """Load backtest result from JSON file.
    
    Args:
        filepath: Path to JSON result file
        
    Returns:
        Dictionary with backtest results
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def create_visualizations(result_file: str, output_dir: str = None):
    """Create visualization charts from backtest results.
    
    Args:
        result_file: Path to backtest result JSON
        output_dir: Output directory for charts (default: same as result file)
    """
    if not VISUALIZATION_AVAILABLE:
        print("Visualization libraries not available. Install matplotlib and pandas.")
        return
    
    # Load results
    result = load_backtest_result(result_file)
    
    # Setup output directory
    if output_dir is None:
        output_dir = Path(result_file).parent
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    symbol = result['config']['symbol']
    
    # Create figure with subplots
    fig = plt.figure(figsize=(15, 10))
    fig.suptitle(f'Backtest Results: {symbol}', fontsize=16, fontweight='bold')
    
    # 1. Portfolio Value Over Time
    ax1 = plt.subplot(2, 2, 1)
    
    # Note: daily_portfolio_values is stored as list of [date, value] pairs
    portfolio_data = result.get('daily_portfolio_values', [])
    if portfolio_data:
        dates = [item[0] for item in portfolio_data]
        values = [item[1] for item in portfolio_data]
        
        ax1.plot(dates, values, linewidth=2, color='#2E86AB')
        ax1.axhline(y=result['config']['initial_capital'], color='gray', linestyle='--', alpha=0.5, label='Initial Capital')
        ax1.set_title('Portfolio Value Over Time')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Portfolio Value ($)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Format x-axis
        if len(dates) > 20:
            # Show fewer labels for readability
            step = len(dates) // 10
            ax1.set_xticks(ax1.get_xticks()[::step])
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 2. Performance Metrics Bar Chart
    ax2 = plt.subplot(2, 2, 2)
    
    metrics = {
        'Total Return\n(%)': result['performance']['total_return_pct'],
        'Sharpe\nRatio': result['performance']['sharpe_ratio'],
        'Win Rate\n(%)': result['performance']['win_rate'],
        'Max Drawdown\n(%)': abs(result['performance']['max_drawdown'])
    }
    
    colors = ['#06A77D' if v > 0 else '#D64545' for v in metrics.values()]
    bars = ax2.bar(metrics.keys(), metrics.values(), color=colors, alpha=0.7)
    ax2.set_title('Key Performance Metrics')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom' if height > 0 else 'top')
    
    # 3. Trade Distribution
    ax3 = plt.subplot(2, 2, 3)
    
    trade_data = result['trades']
    if trade_data['total'] > 0:
        labels = ['Winning\nTrades', 'Losing\nTrades']
        sizes = [trade_data['winning'], trade_data['losing']]
        colors_pie = ['#06A77D', '#D64545']
        explode = (0.05, 0.05)
        
        if sum(sizes) > 0:
            ax3.pie(sizes, explode=explode, labels=labels, colors=colors_pie,
                   autopct='%1.1f%%', shadow=True, startangle=90)
            ax3.set_title('Trade Win/Loss Distribution')
    else:
        ax3.text(0.5, 0.5, 'No trades executed', ha='center', va='center',
                transform=ax3.transAxes, fontsize=12)
        ax3.set_title('Trade Win/Loss Distribution')
    
    # 4. Returns Distribution (if we have portfolio values)
    ax4 = plt.subplot(2, 2, 4)
    
    if portfolio_data and len(portfolio_data) > 1:
        values = [item[1] for item in portfolio_data]
        returns = pd.Series(values).pct_change().dropna() * 100  # Convert to percentage
        
        if len(returns) > 0:
            ax4.hist(returns, bins=30, color='#2E86AB', alpha=0.7, edgecolor='black')
            ax4.axvline(x=0, color='red', linestyle='--', linewidth=2, alpha=0.7)
            ax4.set_title('Daily Returns Distribution')
            ax4.set_xlabel('Return (%)')
            ax4.set_ylabel('Frequency')
            ax4.grid(True, alpha=0.3)
            
            # Add statistics
            mean_return = returns.mean()
            std_return = returns.std()
            ax4.text(0.02, 0.98, f'Mean: {mean_return:.2f}%\nStd: {std_return:.2f}%',
                    transform=ax4.transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # Save figure
    output_file = output_dir / f"{symbol}_backtest_visualization.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Visualization saved to: {output_file}")
    
    # Show plot
    plt.show()


def print_text_report(result_file: str):
    """Print a detailed text report.
    
    Args:
        result_file: Path to backtest result JSON
    """
    result = load_backtest_result(result_file)
    
    print("\n" + "="*80)
    print("DETAILED BACKTEST REPORT")
    print("="*80)
    
    # Configuration
    config = result['config']
    print(f"\n📋 Configuration:")
    print(f"  Symbol:           {config['symbol']}")
    print(f"  Period:           {config['start_date']} to {config['end_date']}")
    print(f"  Initial Capital:  ${config['initial_capital']:,.2f}")
    print(f"  Commission:       {config['commission_pct']*100:.3f}%")
    print(f"  Position Size:    {config['position_size_pct']*100:.1f}%")
    
    # Performance
    perf = result['performance']
    print(f"\n💰 Performance Summary:")
    print(f"  Final Portfolio Value:  ${perf['final_portfolio_value']:,.2f}")
    print(f"  Total Return:           ${perf['total_return']:,.2f}")
    print(f"  Total Return %:         {perf['total_return_pct']:+.2f}%")
    print(f"  Sharpe Ratio:           {perf['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown:           {perf['max_drawdown']:.2f}%")
    print(f"  Win Rate:               {perf['win_rate']:.2f}%")
    
    # Trade statistics
    trades = result['trades']
    print(f"\n📊 Trade Statistics:")
    print(f"  Total Trades:      {trades['total']}")
    print(f"  Winning Trades:    {trades['winning']}")
    print(f"  Losing Trades:     {trades['losing']}")
    if trades['avg_win'] > 0:
        print(f"  Average Win:       ${trades['avg_win']:,.2f}")
    if trades['avg_loss'] != 0:
        print(f"  Average Loss:      ${trades['avg_loss']:,.2f}")
    print(f"  Total Commission:  ${trades['total_commission']:,.2f}")
    
    # Analysis
    print(f"\n📈 Analysis:")
    
    if perf['total_return_pct'] > 0:
        print(f"  ✅ Strategy was PROFITABLE (+{perf['total_return_pct']:.2f}%)")
    else:
        print(f"  ❌ Strategy was UNPROFITABLE ({perf['total_return_pct']:.2f}%)")
    
    if perf['sharpe_ratio'] > 1:
        print(f"  ✅ Good risk-adjusted returns (Sharpe: {perf['sharpe_ratio']:.2f})")
    elif perf['sharpe_ratio'] > 0:
        print(f"  ⚠️  Moderate risk-adjusted returns (Sharpe: {perf['sharpe_ratio']:.2f})")
    else:
        print(f"  ❌ Poor risk-adjusted returns (Sharpe: {perf['sharpe_ratio']:.2f})")
    
    if perf['win_rate'] > 50:
        print(f"  ✅ Win rate above 50% ({perf['win_rate']:.1f}%)")
    else:
        print(f"  ⚠️  Win rate below 50% ({perf['win_rate']:.1f}%)")
    
    if abs(perf['max_drawdown']) < 10:
        print(f"  ✅ Low drawdown ({perf['max_drawdown']:.1f}%)")
    elif abs(perf['max_drawdown']) < 20:
        print(f"  ⚠️  Moderate drawdown ({perf['max_drawdown']:.1f}%)")
    else:
        print(f"  ❌ High drawdown ({perf['max_drawdown']:.1f}%)")
    
    print("\n" + "="*80 + "\n")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python visualize_backtest.py <result_file.json> [--no-plot]")
        print("\nExample:")
        print("  python visualize_backtest.py backtest_results/backtest_AAPL_20241012_123456.json")
        sys.exit(1)
    
    result_file = sys.argv[1]
    
    if not Path(result_file).exists():
        print(f"Error: File not found: {result_file}")
        sys.exit(1)
    
    # Print text report
    print_text_report(result_file)
    
    # Create visualizations unless --no-plot is specified
    if '--no-plot' not in sys.argv:
        if VISUALIZATION_AVAILABLE:
            create_visualizations(result_file)
        else:
            print("\nSkipping visualization (matplotlib not installed)")


if __name__ == '__main__':
    main()
