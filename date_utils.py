import pytz
import datetime
import pandas as pd
import logging

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

    # If Saturday → skip to Monday
    if next_day.weekday() == 5:
        next_day += datetime.timedelta(days=2)
    if next_day.weekday() == 6:  # if Sunday → skip to Monday
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
            logger.warning("DataFrame is empty. Cannot compute time difference.")
            return None

        last_time = df.iloc[-1][column_name]

        # If conversion failed or is NaT
        if pd.isna(last_time):
            logger.warning("Last timestamp is invalid (NaT).")
            return None
        now = datetime.datetime.now(pytz.timezone("America/New_York"))
        logger.info(f"seconds_passed_since_last_record, Current time (NY): {now}, Last record time: {last_time}")
        seconds_passed = (now - last_time).total_seconds()
        return seconds_passed

    except Exception as e:
        logger.error(f"TODO Error in minutes_since_last_record: {e}", exc_info=True)
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