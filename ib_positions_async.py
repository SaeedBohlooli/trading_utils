import asyncio
import sys
from ib_async import *
import logging
sys.path.insert(0, f'../')
logger = logging.getLogger(__name__)
from trading_utils import *
from trading_utils import ib_posttrade
from trading_utils import date_utils
from trading_utils import ib_orders_async

def has_open_option_positions(ib, symbol, expiry): #TODO need to moved ...
    # Get all current positions
    positions = ib.positions()

    for pos in positions:
        contract = pos.contract
        position = pos.position

        if position == 0:
            continue  # already flat

        # Ensure the contract has an exchange # and not contract.exchange
        # I commented it ...
        if isinstance(contract, Option) :
            # TODO for now we dont send any order if we have open order
            # TODO we can send bu monitoring and close does not support it ...
            # but in case only we have one open option which is not executed, we will not be able to send ...

            if contract.lastTradeDateOrContractMonth == expiry:
                logger.warning(f"@@@ check_for_open_option_positions, There is at least one open option ...expiry: {expiry}, contract: {contract}")
                return True
    return False


def get_open_positions(ib: IB):
    """
    Synchronous version for fetching open positions in ib_async.
    Returns a list of Position objects.
    """

    positions = ib.positions()   # <-- sync call
    return positions

def get_position_by_symbol(ib: IB, symbol: str):
    for p in ib.positions():
        if p.contract.symbol == symbol:
            return p
    return None

def has_position(ib, symbol):
    p = get_position_by_symbol(ib, symbol)
    return p is not None and p.position != 0

def get_position_qty(ib, symbol):
    p = get_position_by_symbol(ib, symbol)
    return p.position if p else 0

def convert_positions_to_dict(ib):
    out = []

    for p in ib.positions():
        if p.position == 0:
            continue

        c = p.contract
        is_option = isinstance(c, Option)
        contract_type = ib_orders_async.CONTRACT_TYPE_MAP.get(type(c), "UNKNOWN")


        d = {
            # --------------------
            # Common fields
            # --------------------
            "symbol": c.symbol,
            "contract_id": c.conId,
            "sec_type": c.secType,
            "qty": p.position,
            "avg_cost": p.avgCost,
            "account": p.account,

            "side": (
                "long" if p.position > 0 else
                "short" if p.position < 0 else
                "flat"
            ),
            "abs_qty": abs(p.position),
            "contract_type": contract_type,
            "last_update": date_utils.time_now_yyyy_mm_dd_hh_mm_ss(),
            "close_requested": False,
            "close_request_id": None,
            "tags": [],
            "metadata": {},

            # --------------------
            # Option fields (FLAT, SAME LEVEL)
            # --------------------
            "strike": c.strike if is_option else None,
            "expiry": c.lastTradeDateOrContractMonth if is_option else None,
            "right": c.right if is_option else None,
            "multiplier": (
                int(c.multiplier) if is_option and c.multiplier
                else 100 if is_option
                else None
            ),
            "local_symbol": c.localSymbol if is_option else None,
            "trading_class": c.tradingClass if is_option else None,
            "exchange": c.exchange if is_option else None,
            "currency": c.currency if is_option else None,
        }

        out.append(d)

    return out

# TODO change to close_position_by_symbiol
# TODO Thisis very dangerous. bcs for SPX options, will close all positions ...
# TODO need to check type of contract ...
async def close_position_async(ib, symbol, position_side=None, qty_to_close=None, order_ref= None):
    """
    Close your existing position for the given symbol.
    - If long - > send SELL
    - If short - > send BUY
    """

    # --- Step 1: get open positions
    positions = ib.positions()

    for pos in positions:
        logger.info(f"Close_position_async, Checking position: {pos}  {pos.contract} ")

        if pos.contract.symbol != symbol:
            continue

        position_qty = pos.position
        if position_qty == 0:
            logger.info(f"@@ close_position_async, No open position to close for {symbol}")
            return None

        # Determine closing side
        action = "SELL" if position_qty > 0 else "BUY"

        if qty_to_close is not None:
            qty_to_close = min(abs(position_qty), qty_to_close) # we are not closing more than what we have
        else:
            qty_to_close = abs(position_qty)



        logger.info(f"close_position_async, Closing {symbol}: {action} qty_to_close: {qty_to_close}, position_qty={position_qty}, order_ref: {order_ref}")

        # Create a market order
        order = Order(
            action=action,
            orderType="MKT",
            totalQuantity=qty_to_close
        )
        order.tif = 'GTC'  # Good Till Cancelled
        if order_ref is not None:
            order.orderRef = order_ref
        if getattr(pos, "account", None):
            order.account = pos.account

        pos.contract.exchange = "SMART"  # Ensure exchange is set
        # Place order
        trade = ib.placeOrder(pos.contract, order)
        # trade = ib.placeOrder(contract, order)
        trade.fillEvent += ib_posttrade.on_fill
        logger.info(f"close_position_async, Order sent ....order_ref: {order_ref}")
        logger.info(f"close_position_async, trade: {trade}")

        return True

    logger.warning(f"@@@ close_position_async, No position found for symbol={symbol}, order_ref: {order_ref}")
    return False

def close_position_by_con_id(ib, symbol=None, side=None, con_id=None, qty_to_close=None, order_ref= None, exchange= None):
    # TODO check side to make sure we are closing correctly ...
    # THIS IS VERY IMPORTANT TO AVOID MISTAKES
    """
    Close your existing position for the given symbol.
    - If long - > send SELL
    - If short - > send BUY
    """
    logger.info(f"[close_position_by_con_id] Closing position for symbol: {symbol}, con_id: {con_id}, side: {side}, qty_to_close: {qty_to_close}")
    if con_id is None:
        return False
    # --- Step 1: get open positions
    positions = ib.positions()

    for pos in positions:
        if pos.contract.conId != con_id:
            continue

        position_qty = pos.position
        if position_qty == 0:
            logger.info(f"[close_position_by_con_id] No open position to close for con_id: {con_id}")
            return False

        # Determine closing side
        action = "SELL" if position_qty > 0 else "BUY"

        if qty_to_close is not None:
            qty_to_close = min(abs(position_qty), qty_to_close)
        else:
            qty_to_close = abs(position_qty)


        logger.info(f"[close_position_by_con_id] Closing {symbol}: {action} qty_to_close: {qty_to_close} (position_qty={position_qty}) , order_ref: {order_ref}")

        # Create a market order
        order = Order(
            action=action,
            orderType="MKT",
            totalQuantity=qty_to_close
        )
        order.tif = 'GTC'  # Good Till Cancelled
        if order_ref is not None:
            order.orderRef = order_ref
        if getattr(pos, "account", None):
            order.account = pos.account

        if exchange is None or exchange == "":
            pos.contract.exchange = "SMART"  # Ensure exchange is set
        else:
            pos.contract.exchange = "CME" # for Futures ...

        # Place order
        trade = ib.placeOrder(pos.contract, order)
        trade.fillEvent += ib_posttrade.on_fill
        logger.info(f"[close_position_by_con_id] Order sent ....")
        logger.info(f"[close_position_by_con_id] trade: {trade}")

        return True

    logger.info(f"[close_position_by_con_id]@@@@ No position found for con_id= {con_id} , order_ref: {order_ref}")
    return False

async def close_all_open_position_async(ib, order_ref=None): # TODO use above method ...


    # --- Step 1: get open positions
    positions = ib.positions()

    for pos in positions:

        position_qty = pos.position
        if position_qty == 0:
            logger.debug(f"close_all_open_position_async, No open position to close")
            continue
        # Determine closing side
        action = "SELL" if position_qty > 0 else "BUY"

        qty_to_close = abs(position_qty)

        # Create a market order
        order = Order(
            action=action,
            orderType="MKT",
            totalQuantity=qty_to_close
        )
        order.tif = 'GTC'  # Good Till Cancelled
        if order_ref is not None:
            order_ref = order_ref.replace("#symbol#", pos.contract.symbol)
            order.orderRef = order_ref
        if getattr(pos, "account", None):
            order.account = pos.account

        pos.contract.exchange = "SMART"  # Ensure exchange is set
        # Place order
        trade = ib.placeOrder(pos.contract, order)
        # trade = ib.placeOrder(contract, order)
        trade.fillEvent += ib_posttrade.on_fill
        logger.info(f"close_position_async, Order sent ....")
        logger.info(f"close_position_async, trade: {trade}")

        await asyncio.sleep(0.5) # wait a bit before sending next order


    return True

# TODO change to close_option_position_by_symbol
# TODO need to check type of contract ...
# TODO This is very dangerous. bcs for SPX options, will close all positions ... the strike, expiry, rght does not matther ...
def close_option_position(ib, symbol=None, qty_to_close= None, order_ref=None):

    positions = ib.positions()

    qty_to_close = int(qty_to_close)

    for pos in positions:
        contract = pos.contract

        position_qty = pos.position
        if position_qty == 0:
            logger.info(f"close_position_async, No open position to close for {symbol}")
            return None

        if contract.secType != 'OPT':
            continue

        if symbol is not None and symbol != contract.symbol:
            logger.info(f"We are not closing this symbol: {symbol}, contract.symbol: {contract.symbol}")
            continue

        if qty_to_close is not None:
            qty_to_close = min(abs(position_qty), qty_to_close)  # we are not closing more than what we have
        else:
            qty_to_close = abs(position_qty)

        # --- Step 2: Determine opposite action ---
        action = "SELL" if position_qty > 0 else "BUY"

        # Create a market order
        order = Order(
            action=action,
            orderType="MKT",
            totalQuantity=qty_to_close
        )
        order.tif = 'GTC'  # Good Till Cancelled
        if order_ref is not None:
            order.orderRef = order_ref
        if getattr(pos, "account", None):
            order.account = pos.account

        pos.contract.exchange = "SMART"  # Ensure exchange is set

        # Place order
        trade = ib.placeOrder(pos.contract, order)
        trade.fillEvent += ib_posttrade.on_fill
        logger.info(f"close_option_positions, Order sent ....order_ref: {order_ref}")
        logger.info(f"close_option_positions, trade: {trade}")

        return True
