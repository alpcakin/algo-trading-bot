import MetaTrader5 as mt5
from datetime import datetime, timedelta

mt5.initialize()

symbol = "EURUSD"
print(f"Testing {symbol}...")

# Symbol bilgisi
symbol_info = mt5.symbol_info(symbol)
if symbol_info is None:
    print(f"Symbol {symbol} not found")
else:
    print(f"✅ Symbol found: {symbol_info.name}")
    print(f"   Visible: {symbol_info.visible}")
    print(f"   Description: {symbol_info.description}")

# Son 1 gün için test et
end = datetime.now()
start = end - timedelta(days=1)

print(f"\nTrying to get data:")
print(f"  From: {start}")
print(f"  To: {end}")

rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, start, end)

if rates is None:
    print(f"❌ Error: {mt5.last_error()}")
else:
    print(f"✅ Got {len(rates)} candles")
    if len(rates) > 0:
        print(f"   First: {datetime.fromtimestamp(rates[0][0])}")
        print(f"   Last: {datetime.fromtimestamp(rates[-1][0])}")

mt5.shutdown()