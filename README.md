 # Algorithmic Trading Bot

  A price action-based trend-following strategy for forex markets using MetaTrader 5.

  ## Features
  - **Price Action Trading**: Trend detection using swing highs/lows
  - **Dynamic Risk Management**: ATR-based take profit levels
  - **News Filter**: Avoid trading during high-impact news events
  - **Backtesting**: Historical performance analysis with realistic costs
  - **Multi-Pair Support**: EURUSD, GBPUSD, USDJPY

  ## Strategy Overview
  - **Timeframe**: M15 (15 minutes)
  - **Entry Logic**: Trend-aligned breakouts
  - **Exit Logic**: Dynamic TP based on ATR (20-25 pips)
  - **Risk**: 0.2% per trade, max 3.5% stop loss
  - **Trading Hours**: 12:00-19:00 UTC

  ## Installation

  ### Prerequisites
  - MetaTrader 5 installed and running
  - Python 3.8+

  ### Setup
  ```bash
  # Clone the repository
  git clone https://github.com/yourusername/algo-trading-bot.git
  cd algo-trading-bot

  # Install dependencies
  pip install -r requirements.txt

  # Configure MT5 credentials (optional)
  # Edit config.py with your MT5 login details

  Usage

  Run Backtest

  python backtest_all_months.py

  Collect Data from MT5

  python src/download_m15_data.py

  Project Structure

  ├── src/
  │   ├── backtester.py      # Backtesting engine
  │   ├── strategy.py         # Trading strategy logic
  │   ├── news_filter.py      # News event filtering
  │   └── data_collector.py   # MT5 data collection
  ├── config.py               # Configuration settings
  ├── backtest_all_months.py  # Main backtest script
  └── requirements.txt        # Python dependencies

  Configuration

  Key parameters in config.py:
  - PAIRS: Trading pairs
  - TIMEFRAME: Chart timeframe
  - RISK_PER_TRADE: Risk percentage per trade
  - ENABLE_NEWS_FILTER: Toggle news filtering

  Development Journey & Performance

  Initial Strategy (M1 Scalping)

  The strategy was initially developed on 1-minute charts with 2 pip TP:
  - December 2025: ~80% monthly return
  - Performance: Excellent results in initial testing

  Reality Check: Spread Impact

  After implementing realistic spread costs (1.5 pips):
  - Scalping strategy collapsed: 2-pip TP couldnt overcome spread costs
  - Lesson learned: Transaction costs are critical for scalping strategies

  Adaptation to M15 Timeframe

  Strategy was re-engineered for 15-minute charts with 20-25 pip TP:
  - December 2025: Strong returns
  - September-November 2025: Underperformed expectations
  - Issues: Strategy didnt maintain consistency across different market conditions

  Key Takeaways

  - Initial backtest results can be misleading without realistic costs
  - Scalping requires ultra-low spreads to be viable
  - Market conditions vary significantly month-to-month
  - Strategy optimization is an ongoing process

  Disclaimer

  This is an educational project documenting a learning journey in algorithmic trading.

  - Trading involves substantial risk of loss
  - Past performance does not guarantee future results
  - The strategy showed inconsistent results across different periods
  - Transaction costs (spread, slippage) significantly impact profitability
  - Always test thoroughly with realistic costs before live trading
  - Never risk more than you can afford to lose

  This code is shared for educational purposes only. Use at your own risk.

  License

  MIT License
  ```