import traceback
import subprocess
import socket
import time
import psutil
import logging
import logging.handlers
import os
import asyncio
import yaml
from ib_insync import IB

# -----------------------------------
# DEFAULT CONFIG
# -----------------------------------

DEFAULT_CONFIG = {
    "ib_app": {
        "type": "gateway",
        "port": 4002,
        "process_name": "java",
        "start_script": r"C:\IBC\startgateway.bat",
    },
    "watchdog": {
        "check_interval": 30,
        "min_failures_to_restart": 2,
    },
    "ib_api": {
        "client_id": 99,
        "timeout": 3,
    },
    "logging": {
        "base_dir": "logs",
        "file_name": "watchdog-ib.log",
        "max_bytes": 5 * 1024 * 1024,
        "backup_count": 200,
        "level": "INFO",
    },
}

# -----------------------------------
# CONFIG LOADING
# -----------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "watchdog_config.yaml")


def deep_merge(defaults: dict, overrides: dict) -> dict:
    result = defaults.copy()
    for k, v in overrides.items():
        if isinstance(v, dict) and k in result:
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return DEFAULT_CONFIG

    try:
        with open(CONFIG_PATH, "r") as f:
            yaml_config = yaml.safe_load(f) or {}
        return deep_merge(DEFAULT_CONFIG, yaml_config)
    except Exception as e:
        print(f"Failed to load YAML config, using defaults: {e}")
        return DEFAULT_CONFIG


config = load_config()

# -----------------------------------
# EXTRACT CONFIG
# -----------------------------------

IB_PORT = config["ib_app"]["port"]
PROCESS_NAME = config["ib_app"]["process_name"]
START_SCRIPT = config["ib_app"]["start_script"]

CHECK_INTERVAL = config["watchdog"]["check_interval"]
MIN_FAILURE_NEEDED_TO_RESTART = config["watchdog"]["min_failures_to_restart"]

IB_API_CLIENT_ID = config["ib_api"]["client_id"]
IB_API_TIMEOUT = config["ib_api"]["timeout"]

LOG_BASE_DIR = config["logging"]["base_dir"]
LOG_FILE_NAME = config["logging"]["file_name"]
LOG_MAX_BYTES = config["logging"]["max_bytes"]
LOG_BACKUP_COUNT = config["logging"]["backup_count"]
LOG_LEVEL = getattr(logging, config["logging"]["level"].upper(), logging.INFO)

# -----------------------------------
# LOGGING SETUP
# -----------------------------------

log_dir = os.path.join(BASE_DIR, LOG_BASE_DIR)
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, LOG_FILE_NAME)

handler = logging.handlers.RotatingFileHandler(
    filename=log_file,
    maxBytes=LOG_MAX_BYTES,
    backupCount=LOG_BACKUP_COUNT
)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

handler.setFormatter(formatter)

logging.basicConfig(
    level=LOG_LEVEL,
    handlers=[handler, logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# -----------------------------------
# UTILITY FUNCTIONS
# -----------------------------------

def is_process_running(name: str) -> bool:
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and name.lower() in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    logger.error(f"IB process '{name}' is NOT running")
    return False


def is_port_open(port: int) -> bool:
    s = socket.socket()
    s.settimeout(1)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        logger.error(f"Port {port} is NOT open")
        return False


def start_ib_app():
    logger.warning("Starting IB application via script...")
    subprocess.Popen(START_SCRIPT, shell=True)


def kill_ib_app():
    logger.warning("Killing IB application process...")
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and PROCESS_NAME.lower() in proc.info['name'].lower():
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


# -----------------------------------
# IB API HEALTH CHECK
# -----------------------------------

async def is_ib_api_healthy(
    host="127.0.0.1",
    port=IB_PORT,
    client_id=IB_API_CLIENT_ID,
    timeout=IB_API_TIMEOUT
) -> bool:
    ib = IB()
    try:
        await asyncio.wait_for(
            ib.connectAsync(
                host=host,
                port=port,
                clientId=client_id,
                timeout=timeout,
                readonly=True
            ),
            timeout=timeout + 1
        )

        await asyncio.wait_for(ib.reqCurrentTime(), timeout=timeout)
        return True

    except Exception as e:
        logger.error(f"IB API health check failed: {e}")
        return False

    finally:
        try:
            ib.disconnect()
        except Exception:
            pass


# -----------------------------------
# MAIN WATCHDOG
# -----------------------------------

def run_watchdog():
    logger.info("Starting IB watchdog (Gateway / TWS compatible)")
    nu_of_failures = 0

    while True:
        try:
            logger.info("============================")

            process_alive = is_process_running(PROCESS_NAME)
            port_open = is_port_open(IB_PORT)
            ib_api_ok = asyncio.run(is_ib_api_healthy())

            logger.info(
                f"Health process_alive={process_alive}, "
                f"port_open={port_open}, ib_api_ok={ib_api_ok}"
            )

            if not process_alive and not port_open and not ib_api_ok:
                nu_of_failures += 1
                logger.error(
                    f"IB APP DOWN + Port DOWN + API DOWN "
                    f"(failure {nu_of_failures})"
                )
            else:
                nu_of_failures = 0
                logger.info("No restart condition met")

            if nu_of_failures >= MIN_FAILURE_NEEDED_TO_RESTART:
                logger.warning("Restarting IB application (confirmed hard failure)")
                kill_ib_app()
                time.sleep(5)
                start_ib_app()
                nu_of_failures = 0

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())


# -----------------------------------
# ENTRY POINT
# -----------------------------------

if __name__ == "__main__":
    run_watchdog()

