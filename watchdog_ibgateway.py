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
from datetime import datetime, timezone
from ib_async import IB

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
        "check_interval": 60,
        "min_failures_to_restart": 2,
        "heartbeat": {
            "enabled": True,
            "base_dir": "logs/heartbeat",
            "app_file": "app_heartbeat.log",
            "ib_file": "ib_heartbeat.log",
            "max_lag_seconds": 300,
        },
        "health": {
            "components": {
                "process": True,
                "port": True,
                "api": True,
                "heartbeat": True,
            },
            "failure_rules": [
                ["port", "api"],
                ["heartbeat"],
            ],
        },
    },
    "ib_api": {
        "client_id": 990,
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
# LOAD CONFIG
# -----------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "..", "configs", "watchdog_config.yaml")


def deep_merge(defaults: dict, overrides: dict) -> dict:
    result = defaults.copy()
    for k, v in overrides.items():
        if isinstance(v, dict) and k in result:
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        print(f"No config file found at {CONFIG_PATH}")
        return DEFAULT_CONFIG

    try:
        with open(CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f) or {}
        return deep_merge(DEFAULT_CONFIG, data)
    except Exception as e:
        print(f"Failed to load config, using defaults: {e}")
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

# ---- HEARTBEAT CONFIG ----

HB_CFG = config["watchdog"]["heartbeat"]
HEARTBEAT_ENABLED = HB_CFG.get("enabled", True)
HEARTBEAT_BASE_DIR = os.path.join(BASE_DIR, HB_CFG["base_dir"])
APP_HEARTBEAT_FILE = os.path.join(HEARTBEAT_BASE_DIR, HB_CFG["app_file"])
IB_HEARTBEAT_FILE = os.path.join(HEARTBEAT_BASE_DIR, HB_CFG["ib_file"])
HEARTBEAT_MAX_LAG_SECONDS = HB_CFG.get("max_lag_seconds", 300)

os.makedirs(HEARTBEAT_BASE_DIR, exist_ok=True)

HEALTH_CFG = config["watchdog"]["health"]

# -----------------------------------
# LOGGING SETUP
# -----------------------------------

log_dir = os.path.join(BASE_DIR, LOG_BASE_DIR)
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, LOG_FILE_NAME)

handler = logging.handlers.RotatingFileHandler(
    filename=log_file,
    maxBytes=LOG_MAX_BYTES,
    backupCount=LOG_BACKUP_COUNT,
)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

handler.setFormatter(formatter)

logging.basicConfig(
    level=LOG_LEVEL,
    handlers=[handler, logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# -----------------------------------
# UTILITIES
# -----------------------------------

def is_process_running(name: str) -> bool:
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and name.lower() in proc.info["name"].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False


def is_port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def start_ib_app():
    logger.warning("Starting IB application")
    subprocess.Popen(START_SCRIPT, shell=True)


def kill_ib_app():
    logger.warning("Killing IB application process")
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and PROCESS_NAME.lower() in proc.info["name"].lower():
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


# -----------------------------------
# HEARTBEAT
# -----------------------------------

def read_heartbeat_ts(path: str):
    if not os.path.exists(path):
        return None
    try:
        ts = datetime.fromisoformat(open(path).read().strip())
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def is_heartbeat_healthy() -> bool:
    if not HEARTBEAT_ENABLED:
        return True

    app_ts = read_heartbeat_ts(APP_HEARTBEAT_FILE)
    ib_ts = read_heartbeat_ts(IB_HEARTBEAT_FILE)

    if not app_ts or not ib_ts:
        return False

    lag = (app_ts - ib_ts).total_seconds()
    return lag <= HEARTBEAT_MAX_LAG_SECONDS


# -----------------------------------
# HEALTH RULE ENGINE (CONFIG-DRIVEN)
# -----------------------------------

def evaluate_health(results: dict, health_cfg: dict) -> tuple[bool, str]:
    enabled = health_cfg.get("components", {})
    rules = health_cfg.get("failure_rules", [])

    active = {
        k: v for k, v in results.items()
        if enabled.get(k, False)
    }

    for rule in rules:
        if all(not active.get(comp, True) for comp in rule):
            return False, f"failure rule triggered: {rule}"

    return True, "health OK"


# -----------------------------------
# IB API HEALTH CHECK
# -----------------------------------

async def is_ib_api_healthy() -> bool:
    ib = IB()
    client_id = IB_API_CLIENT_ID + (int(time.time()) % 1000)

    try:
        await asyncio.wait_for(
            ib.connectAsync("127.0.0.1", IB_PORT, clientId=client_id, readonly=True),
            timeout=IB_API_TIMEOUT,
        )
        await asyncio.wait_for(
            ib.reqCurrentTimeAsync(),
            timeout=IB_API_TIMEOUT,
        )
        return True
    except Exception:
        return False
    finally:
        try:
            if ib.isConnected():
                ib.disconnect()
        except Exception:
            pass


# -----------------------------------
# MAIN WATCHDOG LOOP
# -----------------------------------

async def run_watchdog():
    logger.info("Starting IB watchdog")
    failures = 0

    while True:
        try:
            process_ok = is_process_running(PROCESS_NAME)
            port_ok = is_port_open(IB_PORT)
            api_ok = await is_ib_api_healthy()
            heartbeat_ok = is_heartbeat_healthy()

            results = {
                "process": process_ok,
                "port": port_ok,
                "api": api_ok,
                "heartbeat": heartbeat_ok,
            }

            health_ok, health_msg = evaluate_health(results, HEALTH_CFG)

            logger.info(f"Health={results} | {health_msg}")

            if not health_ok:
                failures += 1
                logger.error(f"Failure detected count={failures}")
            else:
                failures = 0

            if failures >= MIN_FAILURE_NEEDED_TO_RESTART:
                logger.warning("Restarting IB application")
                kill_ib_app()
                await asyncio.sleep(5)
                start_ib_app()
                await asyncio.sleep(10)
                failures = 0

            await asyncio.sleep(CHECK_INTERVAL)

        except Exception:
            logger.error(traceback.format_exc())
            await asyncio.sleep(CHECK_INTERVAL)


# -----------------------------------
# ENTRY POINT
# -----------------------------------

if __name__ == "__main__":
    asyncio.run(run_watchdog())
