# MT5 Configuration
MT5_LOGIN = None  # Demo account number (optional)
MT5_PASSWORD = None  # Password (optional)
MT5_SERVER = None  # Server name (optional)

# Strategy Parameters
PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
TIMEFRAME = "M15"  # 15 minute
TRADING_HOURS = (12, 19)  # UTC 12:00-19:00
ANALYSIS_HOURS = (11, 12)  # UTC 11:00-12:00

# Risk Management
RISK_PER_TRADE = 0.002  # 0.2% per trade
INDIVIDUAL_TP_PIPS = 25  # NOTE: Not used - Dynamic TP based on ATR (20-25 pip range)
MAX_STOP_LOSS_PERCENT = 0.035  # Maximum 3.5% SL
MAX_OPEN_POSITIONS = None  # No limit on concurrent positions

# Dynamic TP Settings (ATR-based to avoid overfitting)
# - High volatility (ATR > avg*1.1): 25 pip TP
# - Low volatility: 20 pip TP
# - Adapts to market conditions each month automatically

# Spread & Slippage (realistic costs)
SPREAD_PIPS = 1.5  # Average spread in pips (EURUSD typical: 1-2 pips)

# News Filter
ENABLE_NEWS_FILTER = True  # Enable/disable news filter
NEWS_BEFORE_MINUTES = 30  # Stop trading X minutes before news
NEWS_AFTER_MINUTES = 30  # Resume trading X minutes after news

# Backtest (Last 30 days - MT5 data limit)
from datetime import datetime, timedelta

end_dt = datetime.now()
start_dt = end_dt - timedelta(days=30)

START_DATE = start_dt.strftime("%Y-%m-%d")
END_DATE = end_dt.strftime("%Y-%m-%d")
INITIAL_BALANCE = 10000

print(f"Backtest period: {START_DATE} to {END_DATE}")

# Advanced Strategy Parameters
SWING_LOOKBACK = 2  # Left/Right candles for swing high/low detection
