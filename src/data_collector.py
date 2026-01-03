"""
MT5 Data Collector
Downloads historical 1-minute OHLC data for specified forex pairs
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *


def connect_mt5():
    """Connect to MetaTrader 5"""
    if not mt5.initialize():
        print(f"❌ MT5 initialization failed, error code = {mt5.last_error()}")
        return False
    
    print(f"✅ MT5 connected successfully")
    print(f"   Version: {mt5.version()}")
    print(f"   Terminal info: {mt5.terminal_info()}")
    
    # Login if credentials provided (optional)
    if MT5_LOGIN and MT5_PASSWORD and MT5_SERVER:
        authorized = mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER)
        if not authorized:
            print(f"⚠️  Login failed, error code = {mt5.last_error()}")
            print("   Continuing without login (limited data may be available)")
        else:
            print(f"✅ Logged in as {MT5_LOGIN}")
    
    return True


def download_data(symbol, timeframe, start_date, end_date):
    """
    Download historical data for a symbol
    
    Args:
        symbol: Forex pair (e.g., "EURUSD")
        timeframe: Timeframe string (e.g., "M1")
        start_date: Start date string "YYYY-MM-DD"
        end_date: End date string "YYYY-MM-DD"
    
    Returns:
        pandas.DataFrame with OHLC data
    """
    
    # Timeframe mapping
    timeframe_dict = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }
    
    tf = timeframe_dict.get(timeframe, mt5.TIMEFRAME_M1)
    
    # Convert dates to datetime
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    print(f"\n📊 Downloading {symbol} {timeframe}...")
    print(f"   Period: {start_date} to {end_date}")
    
    # Download data
    rates = mt5.copy_rates_range(symbol, tf, start, end)
    
    if rates is None or len(rates) == 0:
        print(f"❌ No data retrieved, error code = {mt5.last_error()}")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    print(f"✅ Downloaded {len(df):,} candles")
    print(f"   First candle: {df['time'].iloc[0]}")
    print(f"   Last candle: {df['time'].iloc[-1]}")
    
    return df


def save_data(df, symbol, timeframe):
    """Save data to CSV in data/raw folder"""
    
    # Create directory if not exists
    os.makedirs("data/raw", exist_ok=True)
    
    filename = f"data/raw/{symbol}_{timeframe}_{START_DATE}_{END_DATE}.csv"
    df.to_csv(filename, index=False)
    
    print(f"💾 Saved to: {filename}")
    print(f"   File size: {os.path.getsize(filename) / 1024 / 1024:.2f} MB")


def main():
    """Main execution function"""
    
    print("=" * 60)
    print("MT5 DATA COLLECTOR")
    print("=" * 60)
    
    # Connect to MT5
    if not connect_mt5():
        print("\n❌ Failed to connect to MT5. Please ensure:")
        print("   1. MetaTrader 5 is installed")
        print("   2. MT5 terminal is running")
        print("   3. You have an active demo/live account")
        return
    
    # Download data for each pair
    print(f"\n📋 Pairs to download: {', '.join(PAIRS)}")
    print(f"⏰ Timeframe: {TIMEFRAME}")
    
    successful = []
    failed = []
    
    for pair in PAIRS:
        try:
            df = download_data(pair, TIMEFRAME, START_DATE, END_DATE)
            
            if df is not None:
                save_data(df, pair, TIMEFRAME)
                successful.append(pair)
            else:
                failed.append(pair)
                
        except Exception as e:
            print(f"❌ Error downloading {pair}: {str(e)}")
            failed.append(pair)
    
    # Summary
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {len(successful)} - {', '.join(successful)}")
    if failed:
        print(f"❌ Failed: {len(failed)} - {', '.join(failed)}")
    
    # Shutdown MT5
    mt5.shutdown()
    print("\n✅ MT5 connection closed")
    print("=" * 60)


if __name__ == "__main__":
    main()