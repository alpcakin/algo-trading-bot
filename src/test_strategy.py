"""Test strategy on downloaded data"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy import TrendFollowingStrategy, generate_signals
from config import *

# Load data
print("Loading data...")
df = pd.read_csv(f"data/raw/EURUSD_M1_{START_DATE}_{END_DATE}.csv")
df['time'] = pd.to_datetime(df['time'])

print(f"Loaded {len(df):,} candles")
print(f"Period: {df['time'].iloc[0]} to {df['time'].iloc[-1]}")

# Create strategy
strategy = TrendFollowingStrategy(
    individual_tp_pips=INDIVIDUAL_TP_PIPS,
    risk_per_trade=RISK_PER_TRADE,
    emergency_sl_percent=EMERGENCY_SL_PERCENT,
    trading_hours=TRADING_HOURS
)

# Generate signals
print("\nGenerating signals...")
signals = generate_signals(df, strategy)

# Analyze signals
entry_signals = [s for s in signals if s['type'] == 'ENTRY']
bias_changes = [s for s in signals if s['type'] == 'BIAS_CHANGE']

print(f"\n{'='*60}")
print(f"SIGNAL SUMMARY")
print(f"{'='*60}")
print(f"Total entry signals: {len(entry_signals)}")
print(f"Total bias changes: {len(bias_changes)}")
print(f"\nFirst 10 entries:")
for i, sig in enumerate(entry_signals[:10]):
    print(f"{i+1}. {sig['time']} | {sig['direction']} @ {sig['entry_price']:.5f}")