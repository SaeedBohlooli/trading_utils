import logging

logger = logging.getLogger(__name__)
from trading_utils import email_utils

def notify_user(app_config, application_state, msg=None, subject=None):
    logger.info(f"notify_user called with msg: {msg}, subject: {subject}")
    notify = True
    try:
        for c in app_config.get('notification',{}).get('conditions', []):
            if not eval(c):
                notify = False
                break

        if notify:
            email_recipients = app_config.get('notification',{}).get('recipients')
            email_utils.send_email(to_emails=email_recipients, subject=subject, body=msg)

    except Exception as e:
        logger.exception("Error evaluating notification condition: %s", e)
        notify = False

