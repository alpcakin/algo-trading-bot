"""
Price Action Trend Following Strategy - CORRECTED VERSION

Key Concepts:
- Reference HIGH/LOW: Based on last 20 candles, resets on bias change
- Mitigation: Last counter-trend candle BEFORE a new high/low was made
- LONG bias: RED candle before new HIGH becomes mitigation
- SHORT bias: GREEN candle before new LOW becomes mitigation
- Bias changes when price CLOSES outside mitigation candle
"""

import pandas as pd
import numpy as np


class TrendFollowingStrategy:
    """
    Trend following strategy based on mitigation level breaks
    """
    
    def __init__(self, individual_tp_pips=30, risk_per_trade=0.0001, 
                 emergency_sl_percent=0.02, trading_hours=(13, 20),
                 min_mitigation_distance_pips=5, lookback_for_high_low=20):
        """
        Args:
            individual_tp_pips: TP in pips for each individual position
            risk_per_trade: Risk per trade as fraction of balance (0.0001 = 0.01%)
            emergency_sl_percent: Emergency SL as fraction of balance (0.02 = 2%)
            trading_hours: Tuple of (start_hour, end_hour) in local time
            min_mitigation_distance_pips: Minimum distance for mitigation update
            lookback_for_high_low: Number of candles to look back for reference high/low
        """
        self.individual_tp_pips = individual_tp_pips
        self.risk_per_trade = risk_per_trade
        self.emergency_sl_percent = emergency_sl_percent
        self.trading_hours = trading_hours
        self.min_mitigation_distance_pips = min_mitigation_distance_pips
        self.lookback_for_high_low = lookback_for_high_low
        
        # State variables
        self.bias = None  # 'LONG' or 'SHORT'
        self.mitigation_high = None
        self.mitigation_low = None
        self.mitigation_candle_idx = None
        
        # Reference high/low (last 20 candles, resets on bias change)
        self.reference_high = None
        self.reference_low = None
        self.reference_high_idx = None
        self.reference_low_idx = None
    
    
    def is_bullish_candle(self, row):
        """Check if candle is bullish (green)"""
        return row['close'] > row['open']
    
    
    def is_bearish_candle(self, row):
        """Check if candle is bearish (red)"""
        return row['close'] < row['open']
    
    
    def reset_reference_high_low(self, df, current_idx):
        """
        Reset reference high/low based on last N candles
        Called at initialization and on every bias change
        """
        start_idx = max(0, current_idx - self.lookback_for_high_low)
        lookback_candles = df.iloc[start_idx:current_idx+1]
        
        # Find highest high and lowest low
        max_high_idx = lookback_candles['high'].idxmax()
        min_low_idx = lookback_candles['low'].idxmin()
        
        self.reference_high = lookback_candles.loc[max_high_idx, 'high']
        self.reference_low = lookback_candles.loc[min_low_idx, 'low']
        self.reference_high_idx = max_high_idx
        self.reference_low_idx = min_low_idx
    
    
    def find_last_counter_candle_before_index(self, df, before_idx, candle_type):
        """
        Find the last counter-trend candle before a specific index
        
        Args:
            before_idx: Search before this index
            candle_type: 'red' or 'green'
        
        Returns:
            (candle_data, index) or (None, None)
        """
        search_start = max(0, before_idx - 100)  # Look back max 100 candles
        
        for i in range(before_idx - 1, search_start - 1, -1):
            candle = df.iloc[i]
            
            if candle_type == 'red' and self.is_bearish_candle(candle):
                return candle, i
            elif candle_type == 'green' and self.is_bullish_candle(candle):
                return candle, i
        
        return None, None
    
    
    def initialize_bias(self, df, start_idx=60):
        """
        Initialize bias by looking at recent candles
        """
        if len(df) < start_idx:
            start_idx = len(df) - 1
        
        # Reset reference high/low for initial period
        self.reset_reference_high_low(df, start_idx)
        
        # Look for mitigation candles in initial period
        initial_candles = df.iloc[:start_idx+1]
        
        last_red_making_high = None
        last_red_making_high_idx = None
        last_green_making_low = None
        last_green_making_low_idx = None
        
        current_high = initial_candles.iloc[0]['high']
        current_low = initial_candles.iloc[0]['low']
        
        for i in range(len(initial_candles)):
            candle = initial_candles.iloc[i]
            
            # Check if new high was made
            if candle['high'] > current_high:
                # Find last red candle before this high
                last_red, last_red_idx = self.find_last_counter_candle_before_index(df, i, 'red')
                if last_red is not None:
                    last_red_making_high = last_red
                    last_red_making_high_idx = last_red_idx
                current_high = candle['high']
            
            # Check if new low was made
            if candle['low'] < current_low:
                # Find last green candle before this low
                last_green, last_green_idx = self.find_last_counter_candle_before_index(df, i, 'green')
                if last_green is not None:
                    last_green_making_low = last_green
                    last_green_making_low_idx = last_green_idx
                current_low = candle['low']
        
        # Determine bias based on which is more recent
        if last_red_making_high_idx is not None and last_green_making_low_idx is not None:
            if last_red_making_high_idx > last_green_making_low_idx:
                self.bias = 'LONG'
                self.mitigation_high = last_red_making_high['high']
                self.mitigation_low = last_red_making_high['low']
                self.mitigation_candle_idx = last_red_making_high_idx
            else:
                self.bias = 'SHORT'
                self.mitigation_high = last_green_making_low['high']
                self.mitigation_low = last_green_making_low['low']
                self.mitigation_candle_idx = last_green_making_low_idx
        
        elif last_red_making_high_idx is not None:
            self.bias = 'LONG'
            self.mitigation_high = last_red_making_high['high']
            self.mitigation_low = last_red_making_high['low']
            self.mitigation_candle_idx = last_red_making_high_idx
        
        elif last_green_making_low_idx is not None:
            self.bias = 'SHORT'
            self.mitigation_high = last_green_making_low['high']
            self.mitigation_low = last_green_making_low['low']
            self.mitigation_candle_idx = last_green_making_low_idx
        
        else:
            # Default to LONG with last candle
            self.bias = 'LONG'
            last_candle = df.iloc[start_idx]
            self.mitigation_high = last_candle['high']
            self.mitigation_low = last_candle['low']
            self.mitigation_candle_idx = start_idx
    
    
    def update_mitigation(self, df, current_idx):
        """
        Update mitigation if new high/low is made
        
        For LONG bias:
        - If new HIGH is made (any candle color)
        - Find last RED candle before this high
        - That red candle becomes new mitigation
        
        For SHORT bias:
        - If new LOW is made (any candle color)
        - Find last GREEN candle before this low
        - That green candle becomes new mitigation
        """
        candle = df.iloc[current_idx]
        
        pip_size = 0.0001  # EURUSD/GBPUSD
        min_distance = self.min_mitigation_distance_pips * pip_size
        
        if self.bias == 'LONG':
            # Check if new HIGH was made
            if candle['high'] > self.reference_high:
                # New high made! Find last RED candle before this
                last_red, last_red_idx = self.find_last_counter_candle_before_index(df, current_idx + 1, 'red')
                
                if last_red is not None:
                    # Check if distance is significant
                    if self.mitigation_high is not None:
                        distance = last_red['high'] - self.mitigation_high
                        if distance < min_distance:
                            # Update reference but not mitigation
                            self.reference_high = candle['high']
                            self.reference_high_idx = current_idx
                            return
                    
                    # Update mitigation to this red candle
                    self.mitigation_high = last_red['high']
                    self.mitigation_low = last_red['low']
                    self.mitigation_candle_idx = last_red_idx
                
                # Update reference high
                self.reference_high = candle['high']
                self.reference_high_idx = current_idx
        
        elif self.bias == 'SHORT':
            # Check if new LOW was made
            if candle['low'] < self.reference_low:
                # New low made! Find last GREEN candle before this
                last_green, last_green_idx = self.find_last_counter_candle_before_index(df, current_idx + 1, 'green')
                
                if last_green is not None:
                    # Check if distance is significant
                    if self.mitigation_low is not None:
                        distance = self.mitigation_low - last_green['low']
                        if distance < min_distance:
                            # Update reference but not mitigation
                            self.reference_low = candle['low']
                            self.reference_low_idx = current_idx
                            return
                    
                    # Update mitigation to this green candle
                    self.mitigation_high = last_green['high']
                    self.mitigation_low = last_green['low']
                    self.mitigation_candle_idx = last_green_idx
                
                # Update reference low
                self.reference_low = candle['low']
                self.reference_low_idx = current_idx
    
    
    def check_bias_change(self, df, current_idx):
        """
        Check if bias should change based on mitigation break
        
        LONG bias changes if price CLOSES below mitigation LOW
        SHORT bias changes if price CLOSES above mitigation HIGH
        
        Returns: True if bias changed, False otherwise
        """
        candle = df.iloc[current_idx]
        
        if self.mitigation_high is None or self.mitigation_low is None:
            return False
        
        changed = False
        
        if self.bias == 'LONG':
            # LONG bias changes if price CLOSES below mitigation LOW
            if candle['close'] < self.mitigation_low:
                # Bias changes to SHORT
                self.bias = 'SHORT'
                
                # Reset reference high/low for last 20 candles
                self.reset_reference_high_low(df, current_idx)
                
                # New mitigation = last green candle before current
                last_green, last_green_idx = self.find_last_counter_candle_before_index(df, current_idx + 1, 'green')
                
                if last_green is not None:
                    self.mitigation_high = last_green['high']
                    self.mitigation_low = last_green['low']
                    self.mitigation_candle_idx = last_green_idx
                else:
                    # Fallback: use current candle
                    self.mitigation_high = candle['high']
                    self.mitigation_low = candle['low']
                    self.mitigation_candle_idx = current_idx
                
                changed = True
        
        elif self.bias == 'SHORT':
            # SHORT bias changes if price CLOSES above mitigation HIGH
            if candle['close'] > self.mitigation_high:
                # Bias changes to LONG
                self.bias = 'LONG'
                
                # Reset reference high/low for last 20 candles
                self.reset_reference_high_low(df, current_idx)
                
                # New mitigation = last red candle before current
                last_red, last_red_idx = self.find_last_counter_candle_before_index(df, current_idx + 1, 'red')
                
                if last_red is not None:
                    self.mitigation_high = last_red['high']
                    self.mitigation_low = last_red['low']
                    self.mitigation_candle_idx = last_red_idx
                else:
                    # Fallback: use current candle
                    self.mitigation_high = candle['high']
                    self.mitigation_low = candle['low']
                    self.mitigation_candle_idx = current_idx
                
                changed = True
        
        return changed
    
    
    def should_enter(self, candle):
        """
        Check if we should enter a trade on this candle
        Entry: Candle color matches bias direction
        """
        if self.bias == 'LONG':
            return self.is_bullish_candle(candle)
        elif self.bias == 'SHORT':
            return self.is_bearish_candle(candle)
        return False
    
    
    def is_trading_hours(self, timestamp):
        """Check if current time is within trading hours"""
        hour = timestamp.hour
        return self.trading_hours[0] <= hour < self.trading_hours[1]
    
    
    def get_entry_price(self, candle):
        """Get entry price (close of the candle)"""
        return candle['close']
    
    
    def get_sl_price(self):
        """Get stop loss price (mitigation boundary)"""
        if self.bias == 'LONG':
            return self.mitigation_low
        else:
            return self.mitigation_high
    
    
    def calculate_position_size(self, balance, entry_price, symbol):
        """
        Calculate position size based on risk
        Risk = balance * risk_per_trade
        SL = mitigation boundary
        """
        sl_price = self.get_sl_price()
        
        if sl_price is None:
            return 0
        
        # Calculate SL distance in price
        sl_distance = abs(entry_price - sl_price)
        
        if sl_distance == 0:
            return 0
        
        # Risk amount in dollars
        risk_amount = balance * self.risk_per_trade
        
        # Pip size
        if 'JPY' in symbol:
            pip_size = 0.01
        else:
            pip_size = 0.0001
        
        pip_value_per_lot = 10  # Standard lot
        
        # SL distance in pips
        sl_pips = sl_distance / pip_size
        
        # Lot size
        lot_size = risk_amount / (sl_pips * pip_value_per_lot)
        lot_size = round(lot_size, 2)
        
        # Minimum lot size
        if lot_size < 0.01:
            lot_size = 0.01
        
        return lot_size


def generate_signals(df, strategy):
    """Generate trading signals"""
    signals = []
    
    # Initialize bias
    strategy.initialize_bias(df, start_idx=60)
    
    print(f"Initial bias: {strategy.bias}")
    print(f"  Mitigation HIGH: {strategy.mitigation_high:.5f}")
    print(f"  Mitigation LOW: {strategy.mitigation_low:.5f}")
    print(f"  Reference HIGH: {strategy.reference_high:.5f}")
    print(f"  Reference LOW: {strategy.reference_low:.5f}")
    
    # Start from candle 60
    for i in range(60, len(df)):
        candle = df.iloc[i]
        
        # Update mitigation
        strategy.update_mitigation(df, i)
        
        # Check for bias change
        bias_changed = strategy.check_bias_change(df, i)
        
        if bias_changed:
            signals.append({
                'index': i,
                'time': candle['time'],
                'type': 'BIAS_CHANGE',
                'new_bias': strategy.bias,
                'mitigation_high': strategy.mitigation_high,
                'mitigation_low': strategy.mitigation_low,
                'price': candle['close']
            })
        
        # Check entry
        if strategy.is_trading_hours(candle['time']) and strategy.should_enter(candle):
            entry_price = strategy.get_entry_price(candle)
            
            signal = {
                'index': i,
                'time': candle['time'],
                'type': 'ENTRY',
                'direction': strategy.bias,
                'entry_price': entry_price,
                'mitigation_high': strategy.mitigation_high,
                'mitigation_low': strategy.mitigation_low,
                'sl': strategy.get_sl_price()
            }
            
            signals.append(signal)
    
    return signals