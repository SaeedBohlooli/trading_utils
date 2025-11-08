import datetime

def time_now():
    now_date_time = datetime.datetime.now()
    return  now_date_time.strftime("%Y-%m-%d %H:%M:%S")