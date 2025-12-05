import logging
import requests

logger = logging.getLogger(__name__)



def fetch_user_input(app_config, application_state):
    try:
        host = app_config.get("flask", {}).get("host")
        port = app_config.get("flask", {}).get("port")
        if not host or not port:
            logger.warning("@@@ fetch_user_input, Flask IP/port not configured properly.")
            return {}

        url = f"http://{host}:{port}/api/get-all-requests"
        logger.info(f"fetch_user_input, Pulling data from Flask at {url} ")
        resp = requests.get(url)
        body = resp.json()
        user_requests = body.get('requests', [])
        logger.info(f"fetch_user_input, Pulling data from Flask, {url}, resp.status_code: {resp.status_code}, {type(body)}, body: {body} ")

        application_state.setdefault('user_requests', []).extend(user_requests)

        return user_requests
    except Exception as e:
        logger.warning(f"@@ Unexpected error in fetch_user_input: {e}")
        # logger.warning(f"@@@ {trace}")
        return {}


def remove_request(request_id, app_config, application_state):
    logger.info(f"remove_request called with request_id: {request_id}")
    logger.info(f"@@@@@@@@@@@@  TODO implement remove_request function ")


def remove_request(request_id, app_config, application_state):
    logger.info(f"remove_request called with request_id: {request_id}")
    logger.info(f"@@@@@@@@@@@@  TODO implement remove_request function ")

def mark_user_request_as_processed(app_config, application_state, user_request):
    logger.info(f"mark_user_request_as_processed called with request_id: {user_request}")
    logger.info(f"@@@@@@@@@@@@  TODO implement remove_request function ")