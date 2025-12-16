import asyncio
import sys
from ib_async import *
import logging
sys.path.insert(0, f'../')
logger = logging.getLogger(__name__)
from trading_utils import *
from trading_utils import ib_posttrade

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
        logger.info(f"convert_positions_to_dict: Processing position: {p}")
        sym = p.contract.symbol
        d = {
            "symbol": sym,
            "contract_id": p.contract.conId,
            "qty": p.position,
            "avg_cost": p.avgCost,
            # "market_price": p.marketPrice,
            # "market_value": p.marketValue,
            # "unrealized_pnl": p.unrealizedPNL,
            # "realized_pnl": p.realizedPNL,
            "account": p.account,

            # Derived fields
            "direction": (
                "long" if p.position > 0 else
                "short" if p.position < 0 else
                "flat"
            ),

            "abs_qty": abs(p.position),

            # Useful for engine routing/logic
            "last_update": date_utils.time_now_yyyy_mm_dd_hh_mm_ss(),
            "close_requested": False,
            "close_request_id": None,

            # Future usage
            "tags": [],        # e.g., ["hedge", "gamma_scalp", "manual"]
            "metadata": {},    # free-form space for storing strategy info
        }
        out.append(d)
    return out


# TODO change to close_position_by_symbiol
# TODO Thisis very dangerous. bcs for SPX options, will close all positions ...
# TODO need to check type of contract ...
async def close_position_async(ib, symbol, position_side=None, qty_to_close=None, order_ref= None):
    """
    Close your existing position for the given symbol.
    - If long → send SELL
    - If short → send BUY
    """

    # --- Step 1: get open positions
    positions = ib.positions()

    for pos in positions:
        logger.info(f"@@@ need to check symbol tyope.  FIXMEEEEEEEEEE .... close_position_async, Checking position: {pos}  {pos.contract} ")
        # for XPX it will not go based on the expiry or stike. ...

        if pos.contract.symbol != symbol:
            continue

        position_qty = pos.position
        if position_qty == 0:
            logger.info(f"close_position_async, No open position to close for {symbol}")
            return None

        # Determine closing side
        action = "SELL" if position_qty > 0 else "BUY"

        if qty_to_close is not None:
            qty_to_close = min(abs(position_qty), qty_to_close)
        else:
            qty_to_close = abs(position_qty)



        logger.info(f"close_position_async, Closing {symbol}: {action} qty_to_close: {qty_to_close} (position_qty={position_qty})")

        # Create a market order
        order = Order(
            action=action,
            orderType="MKT",
            totalQuantity=qty_to_close
        )
        order.tif = 'GTC'  # Good Till Cancelled
        if order_ref is not None:
            order.orderRef = order_ref

        pos.contract.exchange = "SMART"  # Ensure exchange is set
        # Place order
        trade = ib.placeOrder(pos.contract, order)
        # trade = ib.placeOrder(contract, order)
        trade.fillEvent += ib_posttrade.on_fill
        logger.info(f"close_position_async, Order sent ....")
        logger.info(f"close_position_async, trade: {trade}")

        return True

    logger.info(f"close_position_async, No position found for symbol={symbol}")
    return False

def close_position_by_con_id(ib, symbol=None, side=None, con_id=None, qty_to_close=None, order_ref= None):
    # TODO check side to make sure we are closing correctly ...
    # THIS IS VERY IMPORTANT TO AVOID MISTAKES
    """
    Close your existing position for the given symbol.
    - If long → send SELL
    - If short → send BUY
    """
    if con_id is None:
        return
    # --- Step 1: get open positions
    positions = ib.positions()

    for pos in positions:
        if pos.contract.conId != con_id:
            continue

        position_qty = pos.position
        if position_qty == 0:
            logger.info(f"close_position_by_con_id, No open position to close for con_id: {con_id}")
            return None

        # Determine closing side
        action = "SELL" if position_qty > 0 else "BUY"

        if qty_to_close is not None:
            qty_to_close = min(abs(position_qty), qty_to_close)
        else:
            qty_to_close = abs(position_qty)


        logger.info(f"close_position_by_con_id, Closing {symbol}: {action} qty_to_close: {qty_to_close} (position_qty={position_qty})")

        # Create a market order
        order = Order(
            action=action,
            orderType="MKT",
            totalQuantity=qty_to_close
        )
        order.tif = 'GTC'  # Good Till Cancelled
        if order_ref is not None:
            order.orderRef = order_ref

        pos.contract.exchange = "SMART"  # Ensure exchange is set

        # Place order
        trade = ib.placeOrder(pos.contract, order)
        trade.fillEvent += ib_posttrade.on_fill
        logger.info(f"close_position_by_con_id, Order sent ....")
        logger.info(f"close_position_by_con_id, trade: {trade}")

        return True

    logger.info(f"close_position_by_con_id, No position found for con_id={con_id}")
    return None


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

        pos.contract.exchange = "SMART"  # Ensure exchange is set
        # Place order
        trade = ib.placeOrder(pos.contract, order)
        # trade = ib.placeOrder(contract, order)
        trade.fillEvent += ib_posttrade.on_fill
        logger.info(f"close_position_async, Order sent ....")
        logger.info(f"close_position_async, trade: {trade}")

        asyncio.wait(0.5) # wait a bit before sending next order


    return True