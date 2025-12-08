import time
from datetime import datetime, timedelta
import os
import sys
import logging
import argparse

sys.path.insert(0, f'../')
from trading_utils import email_utils
from trading_utils import config_utils

logger = logging.getLogger(__name__)


def check_health_status_from_file(health_status_file_path):
    if not os.path.exists(health_status_file_path):
        print(f"⚠️ Health log not found — application might be down. :{health_status_file_path}")
        return False

    try:
        with open(health_status_file_path, "r", encoding="utf-8") as f:
            line = f.readline().strip()
    except Exception as e:
        print(f"⚠️ Error reading health file: {e}")
        return False

    if not line:
        print("⚠️ Health file is empty — no status found.")
        return False

    # Expected line format: "2025-10-28 22:15:03 - APPLICATION IS HEALTHY"
    try:
        timestamp_str, _ = line.split(" - ", 1)
        last_healthy_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        print(f"⚠️ Invalid format in health file: {line}")
        return False

    now = datetime.now()
    diff = now - last_healthy_time

    if diff > timedelta(minutes=2):
        print(f"🚨 {datetime.now()} - Application might be hanged! Last healthy update was {diff.seconds // 60} minutes ago.")
        return False
    else:
        print(f"✅ {datetime.now()} - Application is healthy (last update {diff.seconds // 60} minutes ago).")
        return True

    return False

def write_health_status(portfolio_id):
    health_status_dir = f'../../portfolios/logs/{portfolio_id}'
    os.makedirs(health_status_dir, exist_ok=True)
    health_status_file_path = f'{health_status_dir}/health_status.log'

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"{now} - APPLICATION IS HEALTHY\n"

    with open(health_status_file_path, "w", encoding="utf-8") as f:
        f.write(message)

    logger.info(f"Health status written: {message.strip()}")

    return

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--portfolio-id', help="active portfolio", default='p250')
    args = parser.parse_args()
    portfolio_id = args.portfolio_id

    if portfolio_id == 'p000':
        print('you need to pass portfolio like  --portfolio-id=p100')
        exit()

    app_config = config_utils.load_app_config(portfolio_id)
    print(f"app_config: app_config")
    health_status_dir = f'../../portfolios/logs/{portfolio_id}'
    health_status_file_path = f'{health_status_dir}/health_status.log'

    last_email_time =  time.time()
    while True:
        now = datetime.now()
        current_hh_mm_ny = int(now.strftime("%H%M"))
        is_healthy = check_health_status_from_file(health_status_file_path)
        if not is_healthy:
            if app_config.get('health_check',{}).get('send_email', False):
                if not eval(app_config.get('health_check', {}).get('email_hours', '1 == 2')):
                    print(f"We are not sending email, email_hours: {app_config.get('health_check', {}).get('email_hours', False)}")
                else:
                    now_time = time.time()
                    minutes_from_last_email =  round( (now_time - last_email_time) / 60 , 2)
                    print(f"minutes_from_last_email: {minutes_from_last_email}")

                    if minutes_from_last_email >  int(app_config.get('health_check',{}).get('email_interval_minutes', 10)):
                        last_email_time = time.time()

                        print(f"Sending email ...last_email_time: {last_email_time}, now_time: {now_time}, minutes_from_last_email: {minutes_from_last_email}")
                        email_recipients = app_config.get('health_check',{}).get('email_recipients')
                        # subject = app_config.get('health_check',{}).get('email_subject', f'{portfolio_id} is not healthy' )
                        subject = f"{portfolio_id} is not healthy"
                        body = f"Hello, <br><br>Application in {portfolio_id} is not healthy.  <br> Check it out ..."

                        email_utils.send_email(email_recipients, subject, body=body)

        print(f'sleeping {portfolio_id} ....')
        time.sleep(1 * 60)
