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

# Backtest
START_DATE = "2024-01-01"
END_DATE = "2024-12-31"
INITIAL_BALANCE = 10000