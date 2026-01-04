"""
High-Impact News Filter
Blocks trading around major economic news events
"""

import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import time


class NewsFilter:
    """Filter trades around high-impact news events"""

    def __init__(self, buffer_minutes_before=15, buffer_minutes_after=30):
        """
        Args:
            buffer_minutes_before: Minutes before news to stop trading
            buffer_minutes_after: Minutes after news to stop trading
        """
        self.buffer_before = buffer_minutes_before
        self.buffer_after = buffer_minutes_after
        self.news_events = []  # List of (datetime, event_name)

    def load_hardcoded_news(self, year=2025):
        """
        Load known recurring high-impact news times
        These are approximate - actual dates may vary
        """
        news = []

        # NFP (First Friday of each month at 13:30 UTC)
        for month in range(1, 13):
            # Find first Friday
            first_day = datetime(year, month, 1)
            days_until_friday = (4 - first_day.weekday()) % 7
            if days_until_friday == 0 and first_day.weekday() != 4:
                days_until_friday = 7
            nfp_date = first_day + timedelta(days=days_until_friday)
            news.append((nfp_date.replace(hour=13, minute=30), "NFP"))

        # CPI (Usually around 13th of month at 13:30 UTC - approximate)
        for month in range(1, 13):
            cpi_date = datetime(year, month, 13, 13, 30)
            news.append((cpi_date, "CPI"))

        # FOMC (8 times per year - approximate dates)
        # Typically: Jan, Mar, May, Jun, Jul, Sep, Nov, Dec
        fomc_months = [1, 3, 5, 6, 7, 9, 11, 12]
        for month in fomc_months:
            # Usually mid-month, 19:00 UTC
            fomc_date = datetime(year, month, 15, 19, 0)
            news.append((fomc_date, "FOMC"))

        self.news_events.extend(news)
        return len(news)

    def scrape_forexfactory(self, start_date, end_date):
        """
        Scrape Forex Factory calendar for high-impact news
        WARNING: This may be blocked or rate-limited

        Args:
            start_date: datetime object
            end_date: datetime object
        """
        # Note: This is a simplified example
        # Real implementation would need to handle pagination, rate limits, etc.

        print("Note: Forex Factory scraping not implemented for backtest")
        print("Using hardcoded news events instead")
        return 0

    def is_news_time(self, timestamp):
        """
        Check if timestamp is within news blackout period

        Args:
            timestamp: pandas Timestamp or datetime

        Returns:
            (is_blackout, event_name or None)
        """
        if isinstance(timestamp, pd.Timestamp):
            timestamp = timestamp.to_pydatetime()

        # Check if it's FOMC day or NFP day - block entire day
        current_date = timestamp.date()
        for news_time, event_name in self.news_events:
            if 'FOMC' in event_name and news_time.date() == current_date:
                return True, f"FOMC_DAY_{event_name}"
            if 'NFP' in event_name or 'Non-Farm Employment Change' in event_name:
                if news_time.date() == current_date:
                    return True, f"NFP_DAY_{event_name}"

        # Regular news buffer check
        for news_time, event_name in self.news_events:
            # Check if within buffer zone
            time_diff = (timestamp - news_time).total_seconds() / 60  # minutes

            # Before news: -buffer_before to 0
            # After news: 0 to +buffer_after
            if -self.buffer_before <= time_diff <= self.buffer_after:
                return True, event_name

        return False, None

    def get_next_news(self, current_time):
        """Get next upcoming news event"""
        if isinstance(current_time, pd.Timestamp):
            current_time = current_time.to_pydatetime()

        upcoming = [(t, name) for t, name in self.news_events if t > current_time]
        if upcoming:
            upcoming.sort(key=lambda x: x[0])
            return upcoming[0]
        return None, None

    def get_news_in_range(self, start_date, end_date):
        """Get all news events in date range"""
        if isinstance(start_date, pd.Timestamp):
            start_date = start_date.to_pydatetime()
        if isinstance(end_date, pd.Timestamp):
            end_date = end_date.to_pydatetime()

        events = [(t, name) for t, name in self.news_events
                  if start_date <= t <= end_date]
        events.sort(key=lambda x: x[0])
        return events

    def load_custom_news(self, news_list):
        """
        Load custom news events

        Args:
            news_list: List of tuples (datetime, event_name)
        """
        self.news_events.extend(news_list)

    def clear_news(self):
        """Clear all loaded news events"""
        self.news_events = []


# Specific high-impact news for November 2025
# Source: Forex Factory Calendar (provided by user)
# TIMES IN UTC (Budapest time + 1 hour converted to UTC)
# Only HIGH IMPACT (red/3-star) events included
KNOWN_NEWS_2025_2026 = [
    # November 2025 - High Impact Events Only
    (datetime(2025, 11, 1, 17, 0), "ISM Manufacturing PMI"),  # Budapest 4:00pm → UTC 5:00pm
    (datetime(2025, 11, 5, 15, 15), "ADP Non-Farm Employment Change"),  # Budapest 2:15pm → UTC 3:15pm
    (datetime(2025, 11, 5, 17, 0), "ISM Services PMI"),  # Budapest 4:00pm → UTC 5:00pm
    (datetime(2025, 11, 6, 14, 0), "BOE Monetary Policy Report"),  # Budapest 1:00pm → UTC 2:00pm - MAJOR
    (datetime(2025, 11, 6, 14, 0), "Monetary Policy Summary"),  # Budapest 1:00pm → UTC 2:00pm - MAJOR
    (datetime(2025, 11, 6, 14, 0), "MPC Official Bank Rate Votes"),  # Budapest 1:00pm → UTC 2:00pm - MAJOR
    (datetime(2025, 11, 6, 14, 0), "Official Bank Rate"),  # Budapest 1:00pm → UTC 2:00pm - MAJOR
    (datetime(2025, 11, 6, 14, 30), "BOE Gov Bailey Speaks"),  # Budapest 1:30pm → UTC 2:30pm - MAJOR
    (datetime(2025, 11, 11, 9, 0), "Claimant Count Change"),  # Budapest 8:00am → UTC 9:00am
    (datetime(2025, 11, 13, 9, 0), "GDP m/m"),  # Budapest 8:00am → UTC 9:00am
    (datetime(2025, 11, 18, 10, 10), "Unemployment Claims"),  # Budapest 9:10am → UTC 10:10am
    (datetime(2025, 11, 19, 9, 0), "CPI y/y"),  # Budapest 8:00am → UTC 9:00am - MAJOR
    (datetime(2025, 11, 19, 21, 0), "FOMC Meeting Minutes"),  # Budapest 8:00pm → UTC 9:00pm - MAJOR (FOMC DAY)
    (datetime(2025, 11, 20, 15, 30), "Average Hourly Earnings m/m"),  # Budapest 2:30pm → UTC 3:30pm - MAJOR
    (datetime(2025, 11, 20, 15, 30), "Non-Farm Employment Change"),  # Budapest 2:30pm → UTC 3:30pm - MAJOR (NFP)
    (datetime(2025, 11, 20, 15, 30), "Unemployment Claims"),  # Budapest 2:30pm → UTC 3:30pm
    (datetime(2025, 11, 20, 15, 30), "Unemployment Rate"),  # Budapest 2:30pm → UTC 3:30pm - MAJOR
    (datetime(2025, 11, 21, 9, 0), "Retail Sales m/m"),  # Budapest 8:00am → UTC 9:00am
]


if __name__ == "__main__":
    # Test the news filter
    news_filter = NewsFilter(buffer_minutes_before=15, buffer_minutes_after=30)

    # Load hardcoded events
    count = news_filter.load_hardcoded_news(2025)
    print(f"Loaded {count} hardcoded news events for 2025")

    # Load specific known events
    news_filter.load_custom_news(KNOWN_NEWS_2025_2026)
    print(f"Loaded {len(KNOWN_NEWS_2025_2026)} specific news events")

    # Test a specific time
    test_time = datetime(2025, 12, 6, 13, 20)  # 10 min before NFP
    is_blackout, event = news_filter.is_news_time(test_time)
    print(f"\nTest time: {test_time}")
    print(f"Is blackout: {is_blackout}")
    if event:
        print(f"Event: {event}")

    # Get news in date range
    start = datetime(2025, 12, 1)
    end = datetime(2025, 12, 31)
    events = news_filter.get_news_in_range(start, end)
    print(f"\nNews events in December 2025:")
    for event_time, event_name in events:
        print(f"  {event_time}: {event_name}")
