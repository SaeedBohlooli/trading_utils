import sys
from ib_async import *
import logging
import asyncio
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
    logger.info(f"TODO {order}")

    order.orderRef = order_ref


    trade = ib.placeOrder(butterfly, order)
    trade.fillEvent += ib_posttrade.on_fill

    logger.info(f"Order sent ....")
    logger.info(f"trade: {trade}")

    return trade



def generate_order_ref(portfolio_id, event=None, symbol=None, side=None, unique_run_number=None, right= None, alias=None):
    # event: OPEN, CLOSE
    ev = 'OP' if event == 'OPEN' else 'CL'

    order_ref = f"{portfolio_id}--{symbol}--{ev}"

    if side:
        order_ref += f"--{side}"

    if right:
        order_ref += f"--{right}"

    if alias:
        order_ref += f"--{alias}"

    if unique_run_number:
        order_ref += f"--{unique_run_number}"

    return order_ref


async def place_order(ib: IB, symbol: str, quantity: int, action: str = "BUY", order_ref= None) :
    """
    Place a MARKET order for a given stock symbol.

    :param ib: Connected IB instance
    :param symbol: e.g. "TSLA"
    :param quantity: number of shares
    :param action: "BUY" or "SELL"
    """
    action = 'BUY' if action.lower() in ["buy", "long"] else 'SELL'
    logger.info(f"place_order, Preparing to place {action} order for {quantity} shares of {symbol}")
    # 1) Define the contract
    contract = Stock(symbol, "SMART", "USD")

    # 2) Qualify the contract
    [qualified_contract] = await ib.qualifyContractsAsync(contract)

    logger.info(f"place_order, Qualified contract: {qualified_contract}")

    # 3) Create a Market Order
    order = MarketOrder(action, quantity)
    order.tif = 'GTC'  # Good Till Cancelled
    if order_ref:
        order.orderRef = order_ref

    # 4) Place the order
    trade = ib.placeOrder(qualified_contract, order)
    trade.fillEvent += ib_posttrade.on_fill
    logger.info(f"Order sent ....order_ref: {order_ref}")
    # await trade.completion()  # Wait until the order is completed - need to be verified.
    logger.info(f"Order sent after await ....")

    logger.warning(f"trade: {trade}")

    logger.info(f"Submitted {action} {quantity} {symbol}, orderId={trade.order.orderId}, order_ref: {order_ref}")

    # OPTIONAL: wait until it is filled or cancelled
    while trade.orderStatus.status in ("PendingSubmit", "Submitted"):  # TODO need to be checked for other statuses
        await asyncio.sleep(0.5)
        logger.info( f"@@@ Waiting for status update ... order_ref: {order_ref}"
            f"Order status: {trade.orderStatus.status}, "
            f"filled={trade.orderStatus.filled}, "
            f"remaining={trade.orderStatus.remaining}"
        )

    logger.info(f"Final status: {trade.orderStatus.status}, order_ref: {order_ref}")
    return trade
