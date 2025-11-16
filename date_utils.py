import datetime

def time_now():
    now_date_time = datetime.datetime.now()
    return  now_date_time.strftime("%Y-%m-%d %H:%M:%S")


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
        next_day += datetime.timedelta(days=offset + 2)

    return next_day