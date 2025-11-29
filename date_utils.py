import datetime

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
