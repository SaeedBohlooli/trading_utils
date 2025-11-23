import os.path
import pandas as pd
import logging
import math
import time
import datetime
from ib_insync import *
import sys
import traceback
from trading_utils import *
sys.path.insert(0, f'../')

logger = logging.getLogger(__name__)

def disconnect_ib(ib):
    try:
        logger.info("We need to diconnect first ...")
        ib.disconnect()  # 🔹 Important: ensure full teardown
        time.sleep(1)

    except Exception as e:
        logger.error(f"disconnect_ib: ⚠️ Exception: {e}")
        time.sleep(1)


def on_disconnect():
    try:
        logger.warning("⚠️ IB disconnected! Reconnecting...")
        create_ib_connection()
    except Exception as e:
        logger.error(f"disconnect_ib: ⚠️ Exception: {e}")
        time.sleep(1)
    return


def create_ib_connection(ip, port, client_id):
    connected = False
    ib = None
    while not connected:
        try:
            ib = IB()
            disconnect_ib(ib)
            # ib.disconnectedEvent += on_disconnect
            ib.connect(ip, port, clientId=client_id, timeout=0)
            # ib.commissionReportEvent += ib_posttrade.on_commission_report
            # ib.updatePortfolioEvent += ib_posttrade.on_portfolio_update

            connected = True
            logger.info(f"IB connected.")
        except Exception as e:
            # TODO needs better exception handling
            logger.error(f"@@@@ error: {e}")
            logger.error(f"--------------")
            logger.error(traceback.format_exc())
            logger.info("Sleeping for 60 secs and retrying again ...")
            time.sleep(60)
    return ib