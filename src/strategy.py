"""
Price Action Trend Following Strategy - SWING-BASED VERSION

Key Concepts:
- Daily Reset: 12:00-13:00 analysis period, fresh start every day
- Swing High/Low: Left 2 Right 2 candle pattern for reference levels
- Reference levels require BREAK (not equal/touch)
- Mitigation: Last counter-trend candle BEFORE a new swing high/low
- LONG bias: RED candle before new HIGH becomes mitigation
- SHORT bias: GREEN candle before new LOW becomes mitigation
- Bias changes when price CLOSES outside mitigation candle
- Entry: ALL candles when bias is active (color independent)
- Exit: TP hit, bias change, or end of day
- News Filter: No trading 30min before/after high-impact news
- Scalp: 5 pip TP, 0.01% risk per trade
"""

import pandas as pd
from news_filter import NewsFilter


class TrendFollowingStrategy:
    """
    Swing-based trend following strategy with daily reset
    """

    def __init__(self, individual_tp_pips=5, risk_per_trade=0.0001,
                 max_stop_loss_percent=0.035, trading_hours=(13, 20),
                 analysis_hours=(12, 13), swing_lookback=2,
                 enable_news_filter=True, news_buffer_before=15,
                 news_buffer_after=30):
        """
        Args:
            individual_tp_pips: TP in pips for each individual position (scalp)
            risk_per_trade: Risk per trade as fraction of balance (0.002 = 0.2%)
            max_stop_loss_percent: Maximum SL as fraction of balance (0.035 = 3.5%)
            trading_hours: Tuple of (start_hour, end_hour) - entries until 19:55, close at 20:00
            analysis_hours: Tuple of (start_hour, end_hour) for daily analysis
            swing_lookback: Number of candles on each side for swing detection (default: 2)
            enable_news_filter: Enable/disable news filter
            news_buffer_before: Minutes before news to stop trading
            news_buffer_after: Minutes after news to stop trading
        """
        self.individual_tp_pips = individual_tp_pips
        self.risk_per_trade = risk_per_trade
        self.max_stop_loss_percent = max_stop_loss_percent
        self.trading_hours = trading_hours
        self.analysis_hours = analysis_hours
        self.swing_lookback = swing_lookback
        self.enable_news_filter = enable_news_filter

        # Initialize news filter
        if self.enable_news_filter:
            self.news_filter = NewsFilter(news_buffer_before, news_buffer_after)
            # Load specific news for each month from news_events_by_month.py (optional)
            try:
                import sys
                import os
                parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                from news_events_by_month import get_all_news_2025
                all_news = get_all_news_2025()
                self.news_filter.load_custom_news(all_news)
            except ImportError:
                # news_events_by_month.py not found, will use default news filter
                pass
        else:
            self.news_filter = None

        # State variables
        self.bias = 'LONG'  # Start with LONG, will adjust during analysis
        self.mitigation_high = None
        self.mitigation_low = None
        self.mitigation_candle_idx = None

        # Reference high/low (swing-based)
        self.reference_high = None
        self.reference_low = None
        self.reference_high_idx = None
        self.reference_low_idx = None

        # Pending swing highs/lows (not yet confirmed)
        self.pending_swing_highs = []  # [(price, index), ...]
        self.pending_swing_lows = []   # [(price, index), ...]

        # Track mitigation test for entry
        self.mitigation_tested = False  # Has price entered mitigation zone after bias change?
        self.ready_to_trade = False  # Mitigation tested + new high/low confirmed
        self.entry_candle_count = 0  # Count candles since ready_to_trade
        self.last_bias_change_idx = None  # Track when bias last changed

        # Last analysis day tracking
        self.last_analysis_day = None


    def is_bullish_candle(self, row):
        """Check if candle is bullish (green)"""
        return row['close'] > row['open']


    def is_bearish_candle(self, row):
        """Check if candle is bearish (red)"""
        return row['close'] < row['open']


    def is_swing_high(self, df, idx):
        """
        Check if candle at idx is a swing high (left 2 right 2)
        Returns True if the HIGH at idx is greater than all surrounding candles
        """
        if idx < self.swing_lookback or idx >= len(df) - self.swing_lookback:
            return False

        center_high = df.iloc[idx]['high']

        # Check left candles
        for i in range(idx - self.swing_lookback, idx):
            if df.iloc[i]['high'] >= center_high:
                return False

        # Check right candles
        for i in range(idx + 1, idx + self.swing_lookback + 1):
            if df.iloc[i]['high'] >= center_high:
                return False

        return True


    def is_swing_low(self, df, idx):
        """
        Check if candle at idx is a swing low (left 2 right 2)
        Returns True if the LOW at idx is lower than all surrounding candles
        """
        if idx < self.swing_lookback or idx >= len(df) - self.swing_lookback:
            return False

        center_low = df.iloc[idx]['low']

        # Check left candles
        for i in range(idx - self.swing_lookback, idx):
            if df.iloc[i]['low'] <= center_low:
                return False

        # Check right candles
        for i in range(idx + 1, idx + self.swing_lookback + 1):
            if df.iloc[i]['low'] <= center_low:
                return False

        return True


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


    def reset_daily_state(self):
        """Reset state for new trading day"""
        self.bias = 'LONG'
        self.mitigation_high = None
        self.mitigation_low = None
        self.mitigation_candle_idx = None
        self.reference_high = None
        self.reference_low = None
        self.reference_high_idx = None
        self.reference_low_idx = None
        self.pending_swing_highs = []
        self.pending_swing_lows = []
        self.mitigation_tested = False
        self.ready_to_trade = False
        self.entry_candle_count = 0
        self.last_bias_change_idx = None


    def is_analysis_period(self, timestamp):
        """Check if current time is in analysis period (12:00-13:00)"""
        hour = timestamp.hour
        return self.analysis_hours[0] <= hour < self.analysis_hours[1]


    def calculate_adx(self, df, current_idx, period=14):
        """
        Calculate ADX (Average Directional Index)
        ADX < 25 = weak trend / ranging market
        ADX > 25 = strong trend
        """
        if current_idx < period + 1:
            return 50  # Default to "trending" if not enough data

        # Get recent candles
        start_idx = max(0, current_idx - period - 1)
        candles = df.iloc[start_idx:current_idx + 1]

        # Calculate True Range (TR)
        high = candles['high'].values
        low = candles['low'].values
        close = candles['close'].values

        tr = []
        for i in range(1, len(candles)):
            h_l = high[i] - low[i]
            h_pc = abs(high[i] - close[i-1])
            l_pc = abs(low[i] - close[i-1])
            tr.append(max(h_l, h_pc, l_pc))

        # Calculate +DM and -DM
        plus_dm = []
        minus_dm = []
        for i in range(1, len(candles)):
            up_move = high[i] - high[i-1]
            down_move = low[i-1] - low[i]

            if up_move > down_move and up_move > 0:
                plus_dm.append(up_move)
            else:
                plus_dm.append(0)

            if down_move > up_move and down_move > 0:
                minus_dm.append(down_move)
            else:
                minus_dm.append(0)

        # Smooth TR, +DM, -DM with EMA
        if len(tr) < period:
            return 50  # Not enough data

        # Simple average for first period
        atr = sum(tr[-period:]) / period
        plus_di_smoothed = sum(plus_dm[-period:]) / period
        minus_di_smoothed = sum(minus_dm[-period:]) / period

        # Calculate +DI and -DI
        if atr == 0:
            return 0  # No movement = ranging

        plus_di = 100 * (plus_di_smoothed / atr)
        minus_di = 100 * (minus_di_smoothed / atr)

        # Calculate DX
        di_sum = plus_di + minus_di
        if di_sum == 0:
            return 0

        dx = 100 * abs(plus_di - minus_di) / di_sum

        # ADX is smoothed DX (simplified: using DX directly for now)
        return dx

    def is_choppy_market(self, current_time, df=None, current_idx=None):
        """
        Check if market is choppy using ADX
        ADX < 30 = weak trend / ranging market (choppy)
        """
        if df is None or current_idx is None:
            return False

        adx = self.calculate_adx(df, current_idx, period=14)

        # ADX below 30 = choppy/ranging market (increased from 25)
        return adx < 30

    def calculate_atr(self, df, current_idx, period=14):
        """Calculate Average True Range (ATR) for volatility"""
        if current_idx < period:
            return 0.0003  # Default ATR value

        # Get recent candles
        start_idx = max(0, current_idx - period)
        candles = df.iloc[start_idx:current_idx + 1]

        high = candles['high'].values
        low = candles['low'].values
        close = candles['close'].values

        # Calculate True Range
        tr = []
        for i in range(1, len(candles)):
            h_l = high[i] - low[i]
            h_pc = abs(high[i] - close[i-1])
            l_pc = abs(low[i] - close[i-1])
            tr.append(max(h_l, h_pc, l_pc))

        # ATR is average of TR
        if len(tr) >= period:
            return sum(tr[-period:]) / period
        else:
            return sum(tr) / len(tr) if tr else 0.0003

    def get_dynamic_tp_atr(self, df, current_idx):
        """
        Get dynamic TP based on ATR (volatility)
        Conservative range: 20-25 pips
        Low volatility: 20 pips
        High volatility: 25 pips
        """
        atr = self.calculate_atr(df, current_idx, period=14)

        # Calculate average ATR from last 50 candles
        start_idx = max(0, current_idx - 50)
        avg_atr = 0.0003  # Default

        if current_idx >= 50:
            atr_values = []
            for i in range(start_idx, current_idx):
                atr_values.append(self.calculate_atr(df, i, period=14))
            avg_atr = sum(atr_values) / len(atr_values)

        # Dynamic TP based on current ATR vs average
        if atr > avg_atr * 1.1:  # High volatility
            return 25
        else:  # Normal/Low volatility
            return 20

    def get_dynamic_tp_hybrid(self, df, current_idx):
        """
        Hybrid: ADX (trend strength) + ATR (volatility)
        Conservative range: 20-25 pips
        Uses both indicators for fine-tuning
        """
        adx = self.calculate_adx(df, current_idx, period=14)
        atr = self.calculate_atr(df, current_idx, period=14)

        # Calculate average ATR
        start_idx = max(0, current_idx - 50)
        avg_atr = 0.0003
        if current_idx >= 50:
            atr_values = []
            for i in range(start_idx, current_idx):
                atr_values.append(self.calculate_atr(df, i, period=14))
            avg_atr = sum(atr_values) / len(atr_values)

        # Start with base TP
        base_tp = 22  # Middle ground

        # ADX adjustment (-2 to +2)
        if adx >= 35:
            base_tp += 2  # Strong trend
        elif adx < 28:
            base_tp -= 2  # Weak trend

        # ATR adjustment (-1 to +1)
        if atr > avg_atr * 1.15:  # High volatility
            base_tp += 1
        elif atr < avg_atr * 0.85:  # Low volatility
            base_tp -= 1

        # Clamp between 20-25
        return max(20, min(25, base_tp))

    def get_dynamic_tp(self, df, current_idx):
        """
        Get dynamic TP based on ADX (trend strength)
        Conservative range: 20-25 pips
        ADX 25-32: 20 pips (moderate trend)
        ADX 32+:   25 pips (strong trend)
        """
        adx = self.calculate_adx(df, current_idx, period=14)

        if adx >= 32:
            return 25  # Strong trend
        else:  # 25-32
            return 20  # Moderate trend


    def is_high_volatility_recent(self, df, current_idx, lookback=4):
        """
        Check if there was high volatility in recent candles
        High volatility = any candle in last 4 candles with 2x+ average range
        """
        if current_idx < lookback + 14:
            return False

        # Calculate average ATR from last 20 candles
        atr_sum = 0
        for i in range(current_idx - 20, current_idx):
            candle = df.iloc[i]
            candle_range = candle['high'] - candle['low']
            atr_sum += candle_range
        avg_range = atr_sum / 20

        # Check last 4 candles for volatility spike (2x threshold)
        for i in range(current_idx - lookback, current_idx):
            candle = df.iloc[i]
            candle_range = candle['high'] - candle['low']
            if candle_range > avg_range * 2:
                return True  # Extreme volatility detected in recent candles

        return False

    def is_trading_hours(self, timestamp, df=None, current_idx=None):
        """
        Check if current time is within trading hours (13:00-19:55)
        AND not during news blackout period
        AND not during choppy market conditions (ADX filter)
        AND not after recent high volatility (ATR filter)
        """
        hour = timestamp.hour
        minute = timestamp.minute

        # After 19:55, no new entries
        if hour == 19 and minute >= 55:
            return False

        # Check basic trading hours
        if not (self.trading_hours[0] <= hour < self.trading_hours[1]):
            return False

        # Check news filter
        if self.enable_news_filter and self.news_filter:
            is_news, event = self.news_filter.is_news_time(timestamp)
            if is_news:
                return False  # Block trading during news

        # Check choppy market filter (ADX-based, threshold 25)
        if df is not None and current_idx is not None:
            if self.is_choppy_market(timestamp, df, current_idx):
                return False  # Block trading during choppy conditions

        # Check recent high volatility filter (ATR-based)
        if df is not None and current_idx is not None:
            if self.is_high_volatility_recent(df, current_idx, lookback=4):
                return False  # Block trading after volatility spike

        return True


    def should_close_all_positions(self, timestamp):
        """Check if it's time to close all positions (20:00)"""
        return timestamp.hour >= self.trading_hours[1]


    def check_daily_reset(self, timestamp):
        """
        Check if we need to reset for a new day
        Returns True if reset happened
        """
        current_day = timestamp.date()

        # If it's a new day and we're in analysis period
        if self.last_analysis_day != current_day and self.is_analysis_period(timestamp):
            self.reset_daily_state()
            self.last_analysis_day = current_day
            return True

        return False


    def update_swing_levels(self, df, current_idx):
        """
        Update swing high/low tracking
        Check for new swings and confirm pending ones

        ONLY during analysis period (12:00-13:00) and trading hours (13:00-20:00)
        """
        candle = df.iloc[current_idx]

        # Only update during analysis or trading hours
        hour = candle['time'].hour
        if not (self.analysis_hours[0] <= hour < self.trading_hours[1]):
            return

        # If we don't have initial references yet, initialize them with first swing
        if self.reference_high is None and self.pending_swing_highs:
            highest_swing = max(self.pending_swing_highs, key=lambda x: x[0])
            self.reference_high = highest_swing[0]
            self.reference_high_idx = highest_swing[1]

        if self.reference_low is None and self.pending_swing_lows:
            lowest_swing = min(self.pending_swing_lows, key=lambda x: x[0])
            self.reference_low = lowest_swing[0]
            self.reference_low_idx = lowest_swing[1]

        # Detect new swing high (need to wait 2 candles to confirm)
        if current_idx >= self.swing_lookback + 2:
            swing_idx = current_idx - self.swing_lookback
            if self.is_swing_high(df, swing_idx):
                swing_price = df.iloc[swing_idx]['high']
                # Add to pending if not already there
                if not any(idx == swing_idx for _, idx in self.pending_swing_highs):
                    self.pending_swing_highs.append((swing_price, swing_idx))

        # Detect new swing low (need to wait 2 candles to confirm)
        if current_idx >= self.swing_lookback + 2:
            swing_idx = current_idx - self.swing_lookback
            if self.is_swing_low(df, swing_idx):
                swing_price = df.iloc[swing_idx]['low']
                # Add to pending if not already there
                if not any(idx == swing_idx for _, idx in self.pending_swing_lows):
                    self.pending_swing_lows.append((swing_price, swing_idx))

        # Check if pending swing highs are confirmed (price broke reference low)
        if self.reference_low is not None and self.pending_swing_highs:
            # BREAK required: low must be LESS than reference_low (not equal)
            if candle['low'] < self.reference_low:
                # Find the highest pending swing high
                highest_swing = max(self.pending_swing_highs, key=lambda x: x[0])
                new_high = highest_swing[0]
                new_high_idx = highest_swing[1]

                # Always update reference level to track market structure
                old_ref_high = self.reference_high
                self.reference_high = new_high
                self.reference_high_idx = new_high_idx
                self.pending_swing_highs = []  # Clear all pending

                # LONG bias: Always update mitigation on any new swing high
                if self.bias == 'LONG':
                    self.update_mitigation_for_new_high(df, self.reference_high_idx)

        # Check if pending swing lows are confirmed (price broke reference high)
        if self.reference_high is not None and self.pending_swing_lows:
            # BREAK required: high must be GREATER than reference_high (not equal)
            if candle['high'] > self.reference_high:
                # Find the lowest pending swing low
                lowest_swing = min(self.pending_swing_lows, key=lambda x: x[0])
                new_low = lowest_swing[0]
                new_low_idx = lowest_swing[1]

                # Always update reference level to track market structure
                old_ref_low = self.reference_low
                self.reference_low = new_low
                self.reference_low_idx = new_low_idx
                self.pending_swing_lows = []  # Clear all pending

                # SHORT bias: Always update mitigation on any new swing low
                if self.bias == 'SHORT':
                    self.update_mitigation_for_new_low(df, self.reference_low_idx)


    def update_mitigation_for_new_high(self, df, high_idx):
        """Update mitigation when new reference high is confirmed"""
        # Find last RED candle before this high
        last_red, last_red_idx = self.find_last_counter_candle_before_index(df, high_idx + 1, 'red')

        if last_red is not None:
            # Update mitigation (no minimum distance check)
            self.mitigation_high = last_red['high']
            self.mitigation_low = last_red['low']
            self.mitigation_candle_idx = last_red_idx


    def update_mitigation_for_new_low(self, df, low_idx):
        """Update mitigation when new reference low is confirmed"""
        # Find last GREEN candle before this low
        last_green, last_green_idx = self.find_last_counter_candle_before_index(df, low_idx + 1, 'green')

        if last_green is not None:
            # Update mitigation (no minimum distance check)
            self.mitigation_high = last_green['high']
            self.mitigation_low = last_green['low']
            self.mitigation_candle_idx = last_green_idx


    def check_bias_change(self, df, current_idx):
        """
        Check if bias should change based on mitigation break

        LONG bias changes if price CLOSES below mitigation LOW
        SHORT bias changes if price CLOSES above mitigation HIGH

        ONLY during analysis period (12:00-13:00) and trading hours (13:00-20:00)

        Returns: True if bias changed, False otherwise
        """
        candle = df.iloc[current_idx]

        if self.mitigation_high is None or self.mitigation_low is None:
            return False

        # Only allow bias change during analysis or trading hours
        hour = candle['time'].hour
        if not (self.analysis_hours[0] <= hour < self.trading_hours[1]):
            return False

        changed = False

        if self.bias == 'LONG':
            # LONG bias changes if price CLOSES below mitigation LOW (BREAK, not equal)
            if candle['close'] < self.mitigation_low:
                # Bias changes to SHORT
                self.bias = 'SHORT'

                # New mitigation = last green candle BEFORE the breaking candle (not including it)
                last_green, last_green_idx = self.find_last_counter_candle_before_index(df, current_idx, 'green')

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
            # SHORT bias changes if price CLOSES above mitigation HIGH (BREAK, not equal)
            if candle['close'] > self.mitigation_high:
                # Bias changes to LONG
                self.bias = 'LONG'

                # New mitigation = last red candle BEFORE the breaking candle (not including it)
                last_red, last_red_idx = self.find_last_counter_candle_before_index(df, current_idx, 'red')

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

                # Reset ready_to_trade on bias change and mark bias change
                self.ready_to_trade = False
                self.mitigation_tested = False
                self.entry_candle_count = 0
                self.last_bias_change_idx = current_idx

        return changed

    def check_mitigation_test(self, candle):
        """
        Check if price has entered mitigation zone after bias change
        Mitigation zone is set when bias changes
        """
        if self.mitigation_high is None or self.mitigation_low is None:
            return

        # Only track mitigation test if we haven't tested yet
        if self.mitigation_tested:
            return

        # Check if price is inside mitigation zone
        if self.bias == 'LONG':
            # For LONG, check if price touched or entered mitigation
            if candle['low'] <= self.mitigation_high:
                self.mitigation_tested = True
        elif self.bias == 'SHORT':
            # For SHORT, check if price touched or entered mitigation
            if candle['high'] >= self.mitigation_low:
                self.mitigation_tested = True

    def should_enter(self, candle):
        """
        Check if we should enter a trade on this candle
        Entry: When bias is active and mitigation is set
        """
        if self.bias in ['LONG', 'SHORT'] and self.mitigation_high is not None and self.mitigation_low is not None:
            return True
        return False

    def get_tp_pips_for_entry_candle(self):
        """
        Get TP in pips based on which entry candle this is
        Candle 1: 25 pips
        Candle 2: 20 pips
        Candle 3: 15 pips
        """
        if self.entry_candle_count == 0:
            return 25
        elif self.entry_candle_count == 1:
            return 20
        elif self.entry_candle_count == 2:
            return 15
        else:
            return 15  # Fallback


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
        Risk = balance * risk_per_trade (0.2% = 0.002)
        SL = mitigation boundary (max 3.5% of balance)
        """
        sl_price = self.get_sl_price()

        if sl_price is None:
            return 0

        # Calculate SL distance in price
        sl_distance = abs(entry_price - sl_price)

        if sl_distance == 0:
            return 0

        # Risk amount in dollars (0.2% of balance)
        risk_amount = balance * self.risk_per_trade

        # Gold (XAU) specific calculation
        if 'XAU' in symbol or 'GOLD' in symbol.upper():
            # For gold: 1 lot = 100 oz, $1 move = $100 per lot
            # SL distance is in dollars (e.g., if gold moves $10, that's $10)
            # Dollar value per lot for $1 move = 100
            dollar_value_per_lot = 100

            # Lot size = risk / (sl_distance * dollar_value_per_lot)
            lot_size = risk_amount / (sl_distance * dollar_value_per_lot)
            lot_size = round(lot_size, 2)

            # Check max SL
            max_sl_amount = balance * self.max_stop_loss_percent
            potential_loss = lot_size * sl_distance * dollar_value_per_lot

            if potential_loss > max_sl_amount:
                lot_size = max_sl_amount / (sl_distance * dollar_value_per_lot)
                lot_size = round(lot_size, 2)

        # Forex pairs (EURUSD, GBPUSD, etc.)
        else:
            # Pip size
            if 'JPY' in symbol:
                pip_size = 0.01
            else:
                pip_size = 0.0001

            pip_value_per_lot = 10  # Standard lot

            # SL distance in pips
            sl_pips = sl_distance / pip_size

            # Lot size based on risk
            lot_size = risk_amount / (sl_pips * pip_value_per_lot)
            lot_size = round(lot_size, 2)

            # Check if SL would exceed max allowed (3.5% of balance)
            max_sl_amount = balance * self.max_stop_loss_percent
            potential_loss = lot_size * sl_pips * pip_value_per_lot

            if potential_loss > max_sl_amount:
                # Reduce lot size to meet max SL requirement
                lot_size = max_sl_amount / (sl_pips * pip_value_per_lot)
                lot_size = round(lot_size, 2)

        # Minimum lot size
        if lot_size < 0.01:
            lot_size = 0.01

        return lot_size


def generate_signals(df, strategy):
    """Generate trading signals with daily reset"""
    signals = []

    print(f"Starting signal generation...")

    # Process each candle
    for i in range(0, len(df)):
        candle = df.iloc[i]

        # Check for daily reset
        if strategy.check_daily_reset(candle['time']):
            signals.append({
                'index': i,
                'time': candle['time'],
                'type': 'DAILY_RESET',
                'price': candle['close']
            })

        # Update swing levels
        strategy.update_swing_levels(df, i)

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

        # Check entry (only during trading hours, not analysis period)
        if strategy.is_trading_hours(candle['time']) and strategy.should_enter(candle):
            if strategy.mitigation_high is not None and strategy.mitigation_low is not None:
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
