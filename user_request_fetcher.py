import logging
import requests

logger = logging.getLogger(__name__)



def fetch_user_request(app_config, application_state):
    try:
        host = app_config.get("api_service", {}).get("host")
        port = app_config.get("api_service", {}).get("port")
        if not host or not port:
            logger.warning(f"[fetch_user_request], @@ Flask IP/port not configured properly. host:{host}, port:{port} ")
            return {}

        url = f"http://{host}:{port}/api/get-all-requests"
        logger.info(f"[fetch_user_request] Pulling data from Flask at {url} ")
        resp = requests.get(url)
        body = resp.json()
        user_requests = body.get('requests', [])
        logger.info(f"[fetch_user_request] Pulling data from Flask, {url}, resp.status_code: {resp.status_code}, type: {type(body)}, \n body: {body} ")

        application_state.setdefault('user_requests', []).extend(user_requests)

        return user_requests
    except Exception as e:
        logger.warning(f"@@ Unexpected error in fetch_user_request: {e}")
        return {}
