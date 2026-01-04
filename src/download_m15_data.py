"""
Download M15 (15-minute) data from MT5
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import os

# Initialize MT5
if not mt5.initialize():
    print("MT5 initialization failed")
    mt5.shutdown()
    exit()

print("MT5 initialized successfully")

# Parameters
symbol = "EURUSD"
timeframe = mt5.TIMEFRAME_M15  # 15-minute candles

# November 2025 data (Nov 1 - Nov 30, 2025)
start_date = datetime(2025, 11, 1)
end_date = datetime(2025, 11, 30, 23, 59, 59)

print(f"\nDownloading {symbol} M15 data...")
print(f"From: {start_date}")
print(f"To: {end_date}")

# Get data
rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)

if rates is None:
    print(f"Failed to get data: {mt5.last_error()}")
    mt5.shutdown()
    exit()

# Convert to DataFrame
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')

print(f"\nData downloaded: {len(df)} candles")
print(f"Time range: {df['time'].min()} to {df['time'].max()}")

# Save to CSV
output_dir = "data/raw"
os.makedirs(output_dir, exist_ok=True)

filename = f"{output_dir}/{symbol}_M15_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}.csv"
df.to_csv(filename, index=False)

print(f"\nSaved to: {filename}")

# Shutdown MT5
mt5.shutdown()
print("Done!")
