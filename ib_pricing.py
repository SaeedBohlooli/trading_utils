import os.path
import pandas as pd
import logging
import math
import time
import datetime
from ib_insync import *
import sys

sys.path.insert(0, f'../')
from trading_utils import global_state
from trading_utils import df_utils

logger = logging.getLogger(__name__)

#
# General IB helpers (connection, symbols, formatting)	ib_utils.py	✅ Keep as-is, good
# Order placement, monitoring, trade status	ib_orders.py or ib_order_utils.py	Easier to recall & grep
# Price handling, ticker streaming, market data	ib_pricing.py	More concise than ib_pricing_utils
# Post-trade operations (fills, commissions, PnL updates)	ib_posttrade.py or ib_fills.py	Clearer than “after_order”
# Portfolio state, open positions, PnL calc	ib_portfolio.py	Keeps logic grouped
# Risk, limits, margin checks	ib_risk.py	Optional future separation

def test_me():
    logger.info("I am in test_me")
    logger.info(f"global_state: {global_state.application_state}")

    print("I am in test log")
    global_state.application_state = "SET IN THE UTILS ..."


def round_based_on_symbol(symbol, price):
    if symbol == 'MNQ':
        return round(price * 4) / 4
    else:
        return price


def get_current_price_for_contract(ib, contract, max_retries=3, retry_delay=0.5):
    # request market data to get the current price
    for attempt in range(1, max_retries + 1):

        ticker = ib.reqTickers(contract)[0]
        price = ticker.marketPrice()
        if price is not None and not (pd.isna(price) or math.isnan(price)):
            return price
        else:
            logger.warning(f"@@@ get_current_price,{contract}, price is nan, try again ... attempt: {attempt}")
            time.sleep(retry_delay)
        return price



def get_current_price_from_ib(ib, symbol, max_retries=3, retry_delay=0.5):

    underlying = Stock(symbol, 'SMART', 'USD')
    for attempt in range(1, max_retries + 1):

        ib.qualifyContracts(underlying)
        ticker = ib.reqMktData(underlying)
        ib.sleep(0.2)
        price = ticker.last or ticker.close
        if price is not None and not (pd.isna(price) or math.isnan(price)):
            if attempt > 1:
                logger.warning(f"@@ succefull try after attempt: {attempt}, symbol: {symbol}")
            return price
        else:
            logger.warning(f"@@@ get_current_price_from_ib, {symbol}, price is nan, try again ... attempt: {attempt}")
            time.sleep(retry_delay)
    return price


def get_current_price(ib, contract): #TODO add rety ...
    # request market data to get the current price
    ticker = ib.reqTickers(contract)[0]
    current_price = ticker.marketPrice()
    return current_price