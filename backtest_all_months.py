"""
Backtest October, November, December 2025 separately
Each with their own news events
"""
import pandas as pd
import sys
sys.path.insert(0, 'src')
from strategy import TrendFollowingStrategy
from backtester import Backtester
from config import *

months = [
    ('September', 'data/raw/EURUSD_M15_2025-09-01_2025-09-30.csv'),
    ('October', 'data/raw/EURUSD_M15_2025-10-01_2025-10-31.csv'),
    ('November', 'data/raw/EURUSD_M15_2025-11-01_2025-11-30.csv'),
    ('December', 'data/raw/EURUSD_M15_2025-12-05_2026-01-04.csv'),
]

print("\n" + "="*80)
print("BACKTEST: SEPTEMBER, OCTOBER, NOVEMBER, DECEMBER 2025")
print("="*80)

total_trades = 0
total_pnl = 0
month_results = []

for month_name, file_path in months:
    print(f"\n{'='*80}")
    print(f"{month_name.upper()} 2025")
    print(f"{'='*80}")

    # Load data
    df = pd.read_csv(file_path)
    df['time'] = pd.to_datetime(df['time'])

    # Create strategy with month-specific news
    strategy = TrendFollowingStrategy(
        individual_tp_pips=INDIVIDUAL_TP_PIPS,
        risk_per_trade=RISK_PER_TRADE,
        max_stop_loss_percent=MAX_STOP_LOSS_PERCENT,
        trading_hours=TRADING_HOURS,
        analysis_hours=ANALYSIS_HOURS,
        swing_lookback=SWING_LOOKBACK,
        enable_news_filter=False,  # Disable auto-loading, we'll load manually
        news_buffer_before=NEWS_BEFORE_MINUTES,
        news_buffer_after=NEWS_AFTER_MINUTES
    )

    # Manually load month-specific news
    if ENABLE_NEWS_FILTER:
        from news_filter import NewsFilter
        from news_events_by_month import get_news_for_month

        strategy.news_filter = NewsFilter(NEWS_BEFORE_MINUTES, NEWS_AFTER_MINUTES)

        # Get month number from month name
        month_map = {'September': 9, 'October': 10, 'November': 11, 'December': 12}
        month_num = month_map.get(month_name)

        if month_num:
            month_news = get_news_for_month(2025, month_num)
            strategy.news_filter.load_custom_news(month_news)
            print(f"Loaded {len(month_news)} news events for {month_name}")

        strategy.enable_news_filter = True
    else:
        strategy.news_filter = None

    backtester = Backtester(INITIAL_BALANCE, "EURUSD")

    # Run backtest
    for i in range(0, len(df)):
        candle = df.iloc[i]

        if strategy.check_daily_reset(candle['time']):
            if backtester.open_positions:
                backtester.close_all_positions(candle['time'], candle['close'], 'DAILY_RESET')
            strategy.reset_daily_state()

        if strategy.should_close_all_positions(candle['time']):
            if backtester.open_positions:
                backtester.close_all_positions(candle['time'], candle['close'], 'END_OF_DAY')

        if strategy.enable_news_filter and strategy.news_filter:
            is_news, event = strategy.news_filter.is_news_time(candle['time'])
            if is_news and backtester.open_positions:
                backtester.close_all_positions(candle['time'], candle['close'], f'NEWS_{event}')

        strategy.update_swing_levels(df, i)
        strategy.check_bias_change(df, i)

        # Check if mitigation was tested
        strategy.check_mitigation_test(candle)

        # Increment entry candle count if ready to trade
        if strategy.ready_to_trade:
            strategy.entry_candle_count += 1

        backtester.update_positions(candle, strategy.bias, strategy.mitigation_high, strategy.mitigation_low)

        if strategy.is_trading_hours(candle['time'], df, i) and strategy.should_enter(candle):
            if MAX_OPEN_POSITIONS is None or len(backtester.open_positions) < MAX_OPEN_POSITIONS:
                if strategy.mitigation_high is not None and strategy.mitigation_low is not None:
                    entry_price = strategy.get_entry_price(candle)
                    lot_size = strategy.calculate_position_size(backtester.balance, entry_price, "EURUSD")

                    if lot_size > 0:
                        # Get TP based on which entry candle (1st, 2nd, or 3rd)
                        tp_pips = strategy.get_tp_pips_for_entry_candle()

                        backtester.open_position(
                            entry_time=candle['time'],
                            entry_price=entry_price,
                            direction=strategy.bias,
                            lot_size=lot_size,
                            sl_price=strategy.get_sl_price(),
                            tp_pips=tp_pips,
                            spread_pips=SPREAD_PIPS
                        )

    # Results
    month_pnl = backtester.balance - INITIAL_BALANCE
    month_return = (month_pnl / INITIAL_BALANCE) * 100
    wins = len([p for p in backtester.closed_positions if p.pnl > 0])
    losses = len([p for p in backtester.closed_positions if p.pnl < 0])
    win_rate = (wins / len(backtester.closed_positions) * 100) if backtester.closed_positions else 0

    print(f"\nResults:")
    print(f"  Trades: {len(backtester.closed_positions)}")
    print(f"  Wins: {wins}, Losses: {losses}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  P&L: ${month_pnl:+,.2f}")
    print(f"  Return: {month_return:+.2f}%")

    total_trades += len(backtester.closed_positions)
    total_pnl += month_pnl

    month_results.append({
        'month': month_name,
        'trades': len(backtester.closed_positions),
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'pnl': month_pnl,
        'return': month_return
    })

# Summary
print(f"\n{'='*80}")
print("OVERALL SUMMARY")
print(f"{'='*80}")

for result in month_results:
    print(f"\n{result['month']:10s} | {result['trades']:3d} trades | WR: {result['win_rate']:5.1f}% | Return: {result['return']:+6.2f}%")

total_return = (total_pnl / INITIAL_BALANCE) * 100
print(f"\n{'='*80}")
print(f"TOTAL: {total_trades} trades | P&L: ${total_pnl:+,.2f} | Return: {total_return:+.2f}%")
print(f"{'='*80}\n")
