import pytz
import datetime
import pandas as pd
import logging
import pandas_market_calendars as mcal
from typing import List

logger = logging.getLogger(__name__)

def time_now():
    now_date_time = datetime.datetime.now()
    return now_date_time.strftime("%Y-%m-%d %H:%M:%S")

def get_current_hhmm_ny():
    now = datetime.datetime.now() # TODO put local NY time
    current_hhmm_ny = int(now.strftime("%H%M"))
    return current_hhmm_ny

def time_now_yyyy_mm_dd_hh_mm():
    now_date_time = datetime.datetime.now()
    return now_date_time.strftime("%Y-%m-%d %H:%M")

def time_now_yyyy_mm_dd_hh_mm_ss():
    now_date_time = datetime.datetime.now()
    return now_date_time.strftime("%Y-%m-%d %H:%M:%S")

def get_yyyymmdd():
    now_date_time = datetime.datetime.now()
    return now_date_time.strftime("%Y%m%d")

def get_yyyy_mm_dd():
    now_date_time = datetime.datetime.now()
    return now_date_time.strftime("%Y-%m-%d")


def time_now_yyyy_mm_dd_hh_mm_ss_as_id():
    now_date_time = datetime.datetime.now()
    return now_date_time.strftime("%Y%m%d-%H%M%S")

def format_yyyymmdd(date_obj):
    """
    Convert a datetime.date (or datetime.datetime) to yyyymmdd string.
    """
    return date_obj.strftime("%Y%m%d")

def next_business_day(start_date=None, offset=1):
    """
    Return the next business day after start_date.
    Skips weekends only (Saturday/Sunday).
    """
    if start_date is None:
        start_date = datetime.date.today()

    next_day = start_date + datetime.timedelta(days=offset)

    # If Saturday - > skip to Monday
    if next_day.weekday() == 5:
        next_day += datetime.timedelta(days=2)
    if next_day.weekday() == 6:  # if Sunday - > skip to Monday
        next_day += datetime.timedelta(days=1)

    return next_day


def get_hhm_mm_of_last_record(df=None):
    if df is None or len(df) == 0:
        return "N/A"
    return df['date'].iloc[-1].strftime('%H:%M')


def get_last_record_hhmm(df=None):
    if len(df) == 0 or df is None:
        return -1

    last_record_hh_mm = int(df['date'].iloc[-1].strftime('%H%M'))
    return int(last_record_hh_mm)

def get_hhmm_int(date_obj):
    if date_obj is None:  # TOOD check it is idate
        return -1

    hhmm = int(date_obj.strftime('%H%M'))
    return hhmm


def seconds_passed_since_last_record(df, column_name='date'):
    try:
        # Check empty DataFrame
        if df.empty:
            logger.warning("[seconds_passed_since_last_record] DataFrame is empty. Cannot compute time difference.")
            return None

        last_time = df.iloc[-1][column_name]

        # If conversion failed or is NaT
        if pd.isna(last_time):
            logger.warning("[seconds_passed_since_last_record] Last timestamp is invalid (NaT).")
            return None
        now = datetime.datetime.now(pytz.timezone("America/New_York"))
        logger.info(f"[seconds_passed_since_last_record] seconds_passed_since_last_record, Current time (NY): {now}, Last record time: {last_time}")
        seconds_passed = (now - last_time).total_seconds()
        return seconds_passed

    except Exception as e:
        logger.error(f"[seconds_passed_since_last_record] Error in minutes_since_last_record: {e}", exc_info=True)
        return None

def next_fridays(n=10):
    today = datetime.date.today()
    result = []

    # Find the upcoming Friday (weekday(): Monday=0, Sunday=6)
    days_until_friday = (4 - today.weekday()) % 7
    next_friday = today + datetime.timedelta(days=days_until_friday)

    for _ in range(n):
        result.append(next_friday.strftime("%Y%m%d"))
        next_friday += datetime.timedelta(days=7)

    return result


def next_option_expirations(n=10, market: str = "NYSE") -> List[str]:
    """
    Return the next N option expiration dates in yyyymmdd format.
    Options normally expire on Fridays.
    If a Friday is a market holiday, the expiration moves to Thursday (the previous trading day).

    Args:
        n:      Number of expirations to return.
        market: Market calendar to use for holiday checking (default: NYSE).

    Returns:
        List of yyyymmdd strings, e.g. ['20260619', '20260626', ...]
    """
    cal = mcal.get_calendar(market)
    today = datetime.date.today()

    # Build a generous schedule window (n weeks * 7 days + buffer)
    end_date = today + datetime.timedelta(days=n * 7 + 14)
    schedule = cal.schedule(start_date=today, end_date=end_date)
    trading_days_set = set(schedule.index.normalize().date)

    result = []

    # Find next Friday
    days_until_friday = (4 - today.weekday()) % 7
    candidate_friday = today + datetime.timedelta(days=days_until_friday)

    while len(result) < n:
        if candidate_friday in trading_days_set:
            # Friday is a trading day — normal expiration
            result.append(candidate_friday.strftime("%Y%m%d"))
        else:
            # Friday is a holiday — fall back to Thursday
            thursday = candidate_friday - datetime.timedelta(days=1)
            if thursday in trading_days_set:
                logger.info(
                    f"[next_option_expirations] Friday {candidate_friday} is a holiday, "
                    f"using Thursday {thursday} instead."
                )
                result.append(thursday.strftime("%Y%m%d"))
            else:
                logger.warning(
                    f"[next_option_expirations] Both Friday {candidate_friday} and "
                    f"Thursday {thursday} are non-trading days, skipping."
                )

        candidate_friday += datetime.timedelta(days=7)

    return result

def next_business_days(n=10, market: str = "NYSE") -> List[str]:
    """
    Return the next N business days starting from today, in yyyymmdd format.
    Skips weekends AND market holidays (NYSE by default).
    """
    cal = mcal.get_calendar(market)
    today = datetime.date.today()

    # Build a generous schedule window
    end_date = today + datetime.timedelta(days=n * 2 + 14)
    schedule = cal.schedule(start_date=today, end_date=end_date)
    trading_days_set = set(schedule.index.normalize().date)

    result = []
    day = today

    while len(result) < n:
        if day in trading_days_set:
            result.append(day.strftime("%Y%m%d"))
        day += datetime.timedelta(days=1)

    return result
def business_days_ago(ts: str, days: int) -> pd.Timestamp:
    return pd.Timestamp(ts) - pd.offsets.BDay(days)


import pandas as pd
import pandas_market_calendars as mcal

def trading_days_ago_at_time(
    ts: str | pd.Timestamp,
    days_back: int,
    market: str = "NYSE",
    hour: int = 9,
    minute: int = 30,
    tz: str = "America/New_York",
) -> pd.Timestamp:
    ts = pd.Timestamp(ts)
    # Ensure timezone
    ts = ts.tz_localize(tz) if ts.tzinfo is None else ts.tz_convert(tz)

    cal = mcal.get_calendar(market)

    # Build a schedule window big enough to cover days_back trading days
    # (use a generous lookback buffer to account for weekends/holidays)
    start = (ts - pd.Timedelta(days=30)).date()
    end = ts.date()

    sched = cal.schedule(start_date=start, end_date=end)
    # print(f"trading_days_ago_at_time: schedule from {start} to {end} has {len(sched)} trading days \n{sched.to_markdown()}.")

    if sched.empty:
        raise RuntimeError(f"No trading schedule found for {market} in range {start}..{end}")

    trading_days = sched.index  # DatetimeIndex of trading dates (midnight-like)
    # Find the last trading day <= ts.date()
    valid_days = trading_days[trading_days <= pd.Timestamp(end)]
    if len(valid_days) == 0:
        raise RuntimeError("No trading day on or before the given timestamp date.")

    anchor_day = valid_days[-1]
    target_day = valid_days[-(days_back + 1)]  # 0 back = same day

    # Set to desired wall-clock time (09:30) in tz
    target_ts = pd.Timestamp(
        year=target_day.year,
        month=target_day.month,
        day=target_day.day,
        hour=hour,
        minute=minute,
        tz=tz,
    )
    return target_ts

import pandas as pd
import pandas_market_calendars as mcal

def trading_days_ahead_at_time(
    ts: str | pd.Timestamp,
    days_ahead: int,
    market: str = "NYSE",
    hour: int = 9,
    minute: int = 30,
    tz: str = "America/New_York",
) -> pd.Timestamp:
    ts = pd.Timestamp(ts)
    ts = ts.tz_localize(tz) if ts.tzinfo is None else ts.tz_convert(tz)

    cal = mcal.get_calendar(market)

    # Look forward enough to cover holidays/weekends
    start = ts.date()
    end = (ts + pd.Timedelta(days=30)).date()

    sched = cal.schedule(start_date=start, end_date=end)

    if sched.empty:
        raise RuntimeError(f"No trading schedule found for {market} in range {start}..{end}")

    trading_days = sched.index

    # Trading days on or after ts.date()
    valid_days = trading_days[trading_days >= pd.Timestamp(start)]

    if len(valid_days) <= days_ahead:
        raise RuntimeError("Not enough future trading days in schedule window")

    target_day = valid_days[days_ahead]

    return pd.Timestamp(
        year=target_day.year,
        month=target_day.month,
        day=target_day.day,
        hour=hour,
        minute=minute,
        tz=tz,
    )


import pandas as pd
import pandas_market_calendars as mcal
from typing import List

def trading_dates_between(
    ts: str | pd.Timestamp,
    days_back: int,
    days_ahead: int = 0,
) -> List[pd.Timestamp]:
    """
    Return NYSE trading dates:
    [ts - days_back, ..., ts, ..., ts + days_ahead]
    """

    anchor = pd.Timestamp(ts).normalize()   # tz-naive, date-only

    cal = mcal.get_calendar("NYSE")

    # Build a window that safely covers holidays/weekends
    start = anchor - pd.Timedelta(days=days_back * 3 + 10)
    end = anchor + pd.Timedelta(days=days_ahead * 3 + 10)

    schedule = cal.schedule(
        start_date=start.date(),
        end_date=end.date()
    )

    if schedule.empty:
        return []

    trading_days = schedule.index.normalize()  # tz-naive dates

    # Find anchor index (or nearest previous trading day)
    anchor_idx = trading_days.get_indexer(
        [anchor],
        method="ffill"
    )[0]

    if anchor_idx == -1:
        raise RuntimeError("Anchor date is before first trading day in range")

    start_idx = max(anchor_idx - days_back, 0)
    end_idx = anchor_idx + days_ahead + 1

    return list(trading_days[start_idx:end_idx])


if __name__== "__main__":
    # Example
    entry_ts = "2025-12-19 13:05:05"
    print(trading_days_ago_at_time(entry_ts, days_back=2, market="NYSE", hour=9, minute=30))

    entry_ts = "2026-01-05"
    print(trading_days_ahead_at_time(entry_ts, days_ahead=1, market="NYSE", hour=9, minute=30))

    entry_ts = "2026-01-05"
    start = trading_days_ago_at_time(entry_ts, days_back=2, market="NYSE", hour=9, minute=30)
    print(type(start))



    dates = nyse_trading_dates_between(
        ts="2026-01-05",
        days_back=2,
        days_ahead=0,
    )

    for d in dates:
        print(d.date())