import sys
from ib_async import *
import logging
import time
import math
import pandas as pd
import pprint
sys.path.insert(0, f'../')

from trading_utils import ib_utils
from trading_utils import date_utils
from trading_utils import ib_pricing
from trading_utils import ib_posttrade

logger = logging.getLogger(__name__)


def send_order(ib, legs, total_quantity, root_symbol, order_ref):
    # Combo Contract
    butterfly = Contract(
        symbol=root_symbol,
        secType='BAG',
        currency='USD',
        exchange='SMART',
        comboLegs=legs
    )
    order = MarketOrder('BUY', totalQuantity=total_quantity)

    order.orderRef = order_ref


    trade = ib.placeOrder(butterfly, order)

    logger.info(f"Order sent ....")
    logger.info(trade)
    return trade

