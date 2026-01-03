# MT5 Configuration
MT5_LOGIN = None  # Demo hesap numarası (opsiyonel)
MT5_PASSWORD = None  # Password (opsiyonel)
MT5_SERVER = None  # Server adı (opsiyonel)

# Strategy Parameters
PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
TIMEFRAME = "M1"  # 1 minute
TRADING_HOURS = (13, 20)  # Hungary time

# Risk Management
RISK_PER_TRADE = 0.0001  # 0.01% per trade
EMERGENCY_SL_PERCENT = 0.02  # 2%
INDIVIDUAL_TP_PIPS = 15  # TP for each position

# News Filter
NEWS_BEFORE_MINUTES = 15
NEWS_AFTER_MINUTES = 30

# Backtest (SON 30 GÜN - MT5 veri limiti için)
from datetime import datetime, timedelta

end_dt = datetime.now()
start_dt = end_dt - timedelta(days=30)

START_DATE = start_dt.strftime("%Y-%m-%d")
END_DATE = end_dt.strftime("%Y-%m-%d")
INITIAL_BALANCE = 10000

print(f"📅 Backtest period: {START_DATE} to {END_DATE}")

# Advanced Strategy Parameters
MIN_MITIGATION_DISTANCE_PIPS = 5  # Mitigation update için min mesafe
INDIVIDUAL_TP_PIPS = 30  # 15'ten 30'a çıkardık