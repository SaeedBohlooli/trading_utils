import subprocess
import socket
import time
import psutil
import logging
from datetime import datetime

# -----------------------------------
# CONFIG
# -----------------------------------
GATEWAY_PORT = 4002                 # <-- Change if needed
PROCESS_NAME = "ibgateway.exe"      # Process to monitor
IBC_START_SCRIPT = r"C:\Jts\IBController\start-gateway.bat"  # <-- your start script

CHECK_INTERVAL = 30  # seconds

# Logging
logging.basicConfig(
    filename="watchdog_ibgateway.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

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
        return False

def is_process_running(name):
    """Check if IB Gateway exe is running."""
    for proc in psutil.process_iter(['name']):
        if name.lower() in proc.info['name'].lower():
            return True
    return False

def start_gateway():
    """Start IB Gateway using IBC."""
    logging.warning("Starting IB Gateway through IBC...")
    subprocess.Popen(IBC_START_SCRIPT, shell=True)

def kill_gateway():
    """Kill IB Gateway cleanly."""
    logging.warning("Killing IB Gateway process...")
    for proc in psutil.process_iter(['name']):
        if PROCESS_NAME.lower() in proc.info['name'].lower():
            proc.kill()

# -----------------------------------
# MAIN WATCHDOG LOOP
# -----------------------------------

logging.info("Starting IB Gateway watchdog...")

while True:
    alive = is_process_running(PROCESS_NAME)
    port_ok = is_port_open(GATEWAY_PORT)

    if not alive:
        logging.error("Gateway process not running! Restarting...")
        start_gateway()

    elif alive and not port_ok:
        logging.error("Gateway running but API port is DOWN! Restarting...")
        kill_gateway()
        time.sleep(3)
        start_gateway()

    else:
        logging.info("IB Gateway OK")

    time.sleep(CHECK_INTERVAL)
