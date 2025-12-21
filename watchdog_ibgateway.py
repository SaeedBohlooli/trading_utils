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
                "process": {"active": True},
                "port": {"active": True},
                "api": {"active": True},
                "heartbeat": {"active": True},
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
        return DEFAULT_CONFIG

    try:
        with open(CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f) or {}
        return deep_merge(DEFAULT_CONFIG, data)
    except Exception:
        return DEFAULT_CONFIG


# -----------------------------------
# INITIAL CONFIG (STATIC PARTS)
# -----------------------------------

config = load_config()

IB_PORT = config["ib_app"]["port"]
PROCESS_NAME = config["ib_app"]["process_name"]
START_SCRIPT = config["ib_app"]["start_script"]

IB_API_CLIENT_ID = config["ib_api"]["client_id"]
IB_API_TIMEOUT = config["ib_api"]["timeout"]

# -----------------------------------
# LOGGING SETUP (STATIC)
# -----------------------------------

LOG_BASE_DIR = config["logging"]["base_dir"]
LOG_FILE_NAME = config["logging"]["file_name"]
LOG_MAX_BYTES = config["logging"]["max_bytes"]
LOG_BACKUP_COUNT = config["logging"]["backup_count"]
LOG_LEVEL = getattr(logging, config["logging"]["level"].upper(), logging.INFO)

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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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
    logger.warning("IB application started")


def kill_ib_app():
    logger.warning("Killing IB application")
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
        ts = datetime.fromisoformat(open(path, "r").read().strip())
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def is_heartbeat_healthy_from_cfg(hb_cfg: dict) -> bool:
    """
    Heartbeat check can also be disabled via watchdog.heartbeat.enabled
    in addition to health.components.heartbeat.active
    """
    if not hb_cfg.get("enabled", True):
        return True

    base_dir = os.path.join(BASE_DIR, hb_cfg["base_dir"])
    os.makedirs(base_dir, exist_ok=True)

    app_file = os.path.join(base_dir, hb_cfg["app_file"])
    ib_file = os.path.join(base_dir, hb_cfg["ib_file"])
    max_lag = hb_cfg.get("max_lag_seconds", 300)

    app_ts = read_heartbeat_ts(app_file)
    ib_ts = read_heartbeat_ts(ib_file)

    if not app_ts or not ib_ts:
        return False

    return (app_ts - ib_ts).total_seconds() <= max_lag


# -----------------------------------
# HEALTH RULE ENGINE (active flags)
# -----------------------------------

def _is_component_active(components_cfg: dict, name: str) -> bool:
    """
    supports:
      components:
        process: {active: true}
    """
    item = components_cfg.get(name, {})
    if isinstance(item, dict):
        return bool(item.get("active", False))
    # backward compatibility if someone sets process: true/false
    return bool(item)


def evaluate_health(results: dict, health_cfg: dict) -> tuple[bool, str]:
    components_cfg = health_cfg.get("components", {})
    rules = health_cfg.get("failure_rules", [])

    # Only consider active components
    active_results = {
        k: v for k, v in results.items()
        if _is_component_active(components_cfg, k)
    }

    # OR of AND rules: a rule triggers failure if ALL comps in it are active AND failed
    for rule in rules:
        # if rule references a component that's inactive, we treat rule as not applicable
        if any(not _is_component_active(components_cfg, comp) for comp in rule):
            continue

        if all(not active_results.get(comp, True) for comp in rule):
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
# MAIN WATCHDOG LOOP (HOT RELOAD)
# -----------------------------------

async def run_watchdog():
    logger.info("Starting IB watchdog (config hot-reload enabled)")
    failures = 0

    while True:
        try:
            # 🔄 Reload config every loop
            config = load_config()

            wd_cfg = config.get("watchdog", {})
            CHECK_INTERVAL = wd_cfg.get("check_interval", 60)
            MIN_FAILURE_NEEDED_TO_RESTART = wd_cfg.get("min_failures_to_restart", 2)

            heartbeat_cfg = wd_cfg.get("heartbeat", {})
            health_cfg = wd_cfg.get("health", {})
            components_cfg = health_cfg.get("components", {})

            # Run checks ONLY if active; otherwise set to True (neutral)
            process_ok = is_process_running(PROCESS_NAME) if _is_component_active(components_cfg, "process") else True
            port_ok = is_port_open(IB_PORT) if _is_component_active(components_cfg, "port") else True
            api_ok = await is_ib_api_healthy() if _is_component_active(components_cfg, "api") else True
            heartbeat_ok = is_heartbeat_healthy_from_cfg(heartbeat_cfg) if _is_component_active(components_cfg, "heartbeat") else True

            results = {
                "process": process_ok,
                "port": port_ok,
                "api": api_ok,
                "heartbeat": heartbeat_ok,
            }

            health_ok, health_msg = evaluate_health(results, health_cfg)

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
            await asyncio.sleep(30)


# -----------------------------------
# ENTRY POINT
# -----------------------------------

if __name__ == "__main__":
    asyncio.run(run_watchdog())
