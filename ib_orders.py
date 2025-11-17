import sys
from ib_insync import *
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

def send_market_order_w_sl_tp(ib, side, contract, stop_loss_price, take_profit_price, quantity, order_ref, candle_date=''):

    tp_price = ib_pricing.round_based_on_symbol(contract.symbol, take_profit_price)
    sl_price = ib_pricing.round_based_on_symbol(contract.symbol, stop_loss_price)

    parent_order_id = ib.client.getReqId()
    side = 'BUY' if side.lower() in ['buy', 'long'] else 'SELL' # unify ..
    revers = 'SELL' if side == 'BUY' else 'BUY'

    logger.warning(f"side: {side}, revers: {revers}, tp_price: {tp_price}, sl_price:{sl_price}, contract: {contract} ")

    parent = MarketOrder(side, quantity, orderId=parent_order_id)
    parent.outsideRth = True
    parent.transmit = False
    parent.tif = 'GTC'
    parent.outsideRth = True
    parent.orderRef = f'{order_ref}'
    logger.warning(f"parent: {parent}")

    # Take profit (limit sell)
    tp_order_id = ib.client.getReqId()
    tp = LimitOrder(revers, quantity, tp_price, parentId=parent_order_id, orderId=tp_order_id)
    tp.outsideRth = True
    tp.transmit = False
    tp.tif = 'GTC'
    tp.outsideRth = True
    tp_order_ref = f'{order_ref}-TP'
    tp.orderRef = tp_order_ref
    logger.warning(f"tp: {tp}")

    # Stop loss (stop sell)
    sl_order_id = ib.client.getReqId()
    sl = StopOrder(revers, 1, sl_price, parentId=parent_order_id, orderId=sl_order_id)
    sl.transmit = True  # Last child sets transmit=True
    sl.outsideRth = True
    sl.tif = 'GTC'
    sl.outsideRth = True
    sl_order_ref = f'{order_ref}-SL'
    sl.orderRef = sl_order_ref
    logger.warning(f"sl: {sl}")

    # Place all 3
    parent_trade = ib.placeOrder(contract, parent)
    parent_trade.fillEvent += ib_posttrade.on_fill
    logger.warning(f"parent_trade: {parent_trade}")

    tp_trade = ib.placeOrder(contract, tp)
    tp_trade.fillEvent += ib_posttrade.on_fill
    logger.warning(f"tp_trade: {tp_trade}")

    sl_trade = ib.placeOrder(contract, sl)
    sl_trade.fillEvent += ib_posttrade.on_fill
    logger.warning(f"sl_trade: {sl_trade}")


    logger.info("@@ before sleep")
    ib.sleep(1)
    logger.info("@@ after ib sleep")
    time.sleep(1)
    logger.info("@@ after time.sleep sleep")

    data = {
        'available_quantity': quantity,
        'date': f'{str(date_utils.time_now())}',
        'candle_date': str(candle_date),
        'open_trade_side': side,
        'open_trade_order_id': parent_order_id,
        'open_trade_open_price': 1,
        'open_trade_order_ref' : order_ref,
        'open_trade_stop_loss_price': sl_price,
        'open_trade_stop_loss_order_id': sl_order_id,
        'open_trade_stop_loss_order_ref': sl_order_ref,
        'open_trade_take_profit_price': tp_price,
        'open_trade_take_profit_order_id' : tp_order_id,
        'open_trade_take_profit_order_re' : tp_order_ref,
        'market_order_sent': True,
        'market_order_executed': False,

    }

    logger.info("order sent.. we sleep 1 sec to order get executed ..") # removing sleep will cause issue
    time.sleep(1)
    return data




def get_all_open_orders(ib):
    open_orders = ib.reqAllOpenOrders()
    return open_orders

def cancel_open_option_orders(ib, symbol):

    open_orders = ib.reqAllOpenOrders()
    # Cancel all open orders
    for order in open_orders:
        logger.info('----')
        logger.warning(f"Canceling open order, order_id: {order.order.orderId}, order: {order}")
        contract = order.contract

        if not isinstance(contract, Option):
            logger.warning(f"it is NOT an option!!!")
        else:
            logger.warning(f"it is an option!!!")
            if order.contract.symbol == symbol:
                trade = ib.cancelOrder(order.order)
                trade.fillEvent += ib_utils.on_fill
                logger.warning(f"open order canceled, trade: {trade}")
                while not trade.isDone():
                    logger.warning(f"sleep until is done, trade.isDone(): {trade.isDone()}")
                    ib.sleep(0.5)
            else:
                logger.warning(f"in cancel_all_open_orders, not canceling order.contract.symbol: {order.contract.symbol}")
    return

def cancel_open_order(ib, order_id):
    logger.warning(f"Canceling open order order_id: {order_id}")
    open_orders = ib.reqAllOpenOrders()
    found = False
    for order in open_orders:
        if order.order.orderId == order_id:
            logger.warning(f"Canceling open order, order: {order}")
            trade = ib.cancelOrder(order.order)
            trade.fillEvent += ib_utils.on_fill
            logger.warning(f"trade: {trade}")
            ib.sleep(1)
            found = True
    if not found:
        logger.warning(f"@@@ Couldn't fine the order to cancel, order_id: {order_id}")
    return