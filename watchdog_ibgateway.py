import traceback
import subprocess
import socket
import time
import psutil
import logging
import logging.handlers
from datetime import datetime
import os
# -----------------------------------
# CONFIG
# -----------------------------------
GATEWAY_PORT = 4002                 # <-- Change if needed
PROCESS_NAME = "ibgateway.exe"      # Process to monitor
PROCESS_NAME = "chrome"      # Process to monitor # TEST to see is the PORT check is working?!!! - IT WORKED
PROCESS_NAME = "java"      # Process to monitor
# IBC_START_SCRIPT = r"C:\Jts\IBController\start-gateway.bat"  # <-- your start script
IBC_START_SCRIPT = r"C:\IBC\startgateway.bat"  # <-- your start script
MIN_FAILURE_NEEDED_TO_RESTART = 2

CHECK_INTERVAL = 30  # seconds


file = f'watchdog-ibgateway.log'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(BASE_DIR, "..", "..", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = f"{log_dir}/{file}"

handler = logging.handlers.RotatingFileHandler(
    filename=log_file,
    maxBytes=5 * 1024 * 1024,
    backupCount=200
)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[handler, logging.StreamHandler()]

)
logger = logging.getLogger(__name__)
# -----------------------------------
# UTILITY FUNCTIONS
# -----------------------------------

def is_port_open(port):
    """Check if IB API port is open."""
    s = socket.socket()
    s.settimeout(1)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except:
        logger.error(f"Port {port} is down. Restarting...")
        return False

def is_process_running(name):
    """Check if IB Gateway exe is running."""
    for proc in psutil.process_iter(['name']):
        # logger.info(f"Checking {name}... in { proc.info['name'].lower()}")
        if name.lower() in proc.info['name'].lower():

            return True
    logger.error(f"IB Gateway {name} is not running.")
    return False

def start_gateway():
    """Start IB Gateway using IBC."""
    logger.warning("Starting IB Gateway through IBC...")
    subprocess.Popen(IBC_START_SCRIPT, shell=True)

def kill_gateway():
    """Kill IB Gateway cleanly."""
    logger.warning("Killing IB Gateway process...")
    for proc in psutil.process_iter(['name']):
        if PROCESS_NAME.lower() in proc.info['name'].lower():
            proc.kill()

# -----------------------------------
# MAIN WATCHDOG LOOP
# -----------------------------------

import asyncio
import logging
from ib_insync import IB

logger = logging.getLogger(__name__)

async def check_ib_api_health(ib: IB, timeout: float = 3.0) -> bool:
    """
    True  -> IB API is healthy
    False -> IB API is unhealthy
    """

    try:
        # 1. Must be connected at socket level
        if not ib.isConnected():
            logger.error("IB socket not connected")
            return False

        # 2. Lightweight request that requires full session validity
        await asyncio.wait_for(ib.reqCurrentTime(), timeout=timeout)

        return True

    except asyncio.TimeoutError:
        logger.error("IB API health check timed out")
        return False

    except Exception as e:
        logger.error(f"IB API health check failed: {e}")
        return False


logger.info("Starting IB Gateway watchdog...")
nu_of_failures = 0
while True:

    try:
        logger.info("================= ")
        alive = is_process_running(PROCESS_NAME)
        port_ok = is_port_open(GATEWAY_PORT)
        connection_is_healthy = True
        if not alive:
            connection_is_healthy = False
            logger.error("Gateway process not running!...")
            nu_of_failures += 1

        elif alive and not port_ok:
            connection_is_healthy = False
            logger.error("Gateway running but API port is DOWN! ...")
            nu_of_failures += 1

        else:
            logger.info("IB Gateway OK")
            nu_of_failures = 0


        if nu_of_failures > MIN_FAILURE_NEEDED_TO_RESTART:
            logger.info("Killing the Gateway...")
            kill_gateway()
            time.sleep(5)
            logger.info("Restarting IB Gateway...")
            start_gateway()


        time.sleep(CHECK_INTERVAL)
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())