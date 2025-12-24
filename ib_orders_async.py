import sys
from ib_async import *
import logging
import asyncio
import time
import math
import pandas as pd
import pprint
from trading_utils import date_utils
import logging
from trading_utils import global_state

sys.path.insert(0, f'../')

from trading_utils import ib_utils
from trading_utils import date_utils
from trading_utils import ib_pricing
from trading_utils import ib_posttrade

logger = logging.getLogger(__name__)

CONTRACT_TYPE_MAP = {
    Stock: "STOCK",
    Option: "OPTION",
    Future: "FUTURE",
    Forex: "FOREX",
    Index: "INDEX",
    Bag: "BAG",
    CFD: "CFD",
    Crypto: "CRYPTO",
    Bond: "BOND",
    Commodity: "COMMODITY",
    MutualFund: "FUND",
    Warrant: "WARRANT",
}

# TODO in 102 change to place_multi_leg_option_order
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


async def place_single_leg_option_order(ib, symbol=None, expiry=0, strike=0, right=None, side=None, total_quantity=0, order_ref=None, exchange=None, currency=None, trading_class=None):
    # Combo Contract

    logger.info(f"Placing single leg option order for {symbol} {expiry} {strike} {right} {side} qty={total_quantity} {exchange} {currency} {trading_class} order_ref={order_ref}")

    if exchange is None:
        reg = global_state.symbol_registry.get(symbol)
        if reg is not None:
            exchange = reg.get("exchange", exchange)
            currency = reg.get("currency", currency)
            trading_class = reg.get("trading_class")
        else:
            logger.warning(f"Symbol {symbol} not found in symbol_registry, using default exchange SMART and currency USD")
            exchange = 'SMART'
            currency = 'USD'
            trading_class = symbol

    if trading_class is None:
        trading_class = symbol

    contract = Option(
        symbol=symbol,
        lastTradeDateOrContractMonth=expiry,
        strike=float(strike),
        right=right,
        exchange=exchange,
        currency=currency,
        tradingClass=trading_class)

    action = 'BUY' if side.lower() in ['buy', 'long'] else 'SELL'

    # 2) Qualify contract (fills in conId etc.)
    qualified = await ib.qualifyContractsAsync(contract)
    if not qualified:
        logger.error(f"Could not qualify contract (check symbol/expiry/strike/exchange). {symbol} {expiry} {strike} {right} {exchange} {currency} {trading_class}")
        return

    contract = qualified[0]
    print("Qualified:", contract)

    order = MarketOrder(action, totalQuantity=total_quantity)
    logger.info(f"TODO {order}")
    if order_ref:
        order.orderRef = order_ref


    trade = ib.placeOrder(contract, order)
    trade.fillEvent += ib_posttrade.on_fill

    logger.info(f"Order sent ....")
    logger.info(f"trade: {trade}")

    return trade

async def submit_prequalified_option_order(ib, q_contract, side, total_quantity=0, order_ref=None):
    # Combo Contract


    action = 'BUY' if side.lower() in ['buy', 'long'] else 'SELL'


    print("Qualified:", q_contract)

    order = MarketOrder(action, totalQuantity=total_quantity)
    logger.info(f"TODO {order}")
    if order_ref:
        order.orderRef = order_ref


    trade = ib.placeOrder(q_contract, order)
    trade.fillEvent += ib_posttrade.on_fill

    logger.info(f"Order sent ....")
    logger.info(f"trade: {trade}")

    return trade


def generate_order_ref(portfolio_id, event=None, symbol=None, side=None, unique_run_number=None, right= None, alias=None):
    # event: OPEN, CLOSE
    ev = 'OP' if event == 'OPEN' else 'CL'

    symbol = symbol if symbol else 'ALL'  # e.g. for portfolio-wide orders

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

# in 106 change to place_stock_order
async def place_order(ib: IB, symbol: str, quantity: int, action: str = "BUY", order_ref= None, algo_strategy=None, adaptive_priority=None, wait_untill_filled: bool=False ) :
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

    if algo_strategy:
        order.algoStrategy = algo_strategy
        if adaptive_priority:
            order.algoParams = [TagValue("adaptivePriority", str(adaptive_priority))]
        logger.info(f"place_order, Using algo strategy: {algo_strategy}, adaptive_priority: {adaptive_priority}")

    # 4) Place the order
    trade = ib.placeOrder(qualified_contract, order)
    trade.fillEvent += ib_posttrade.on_fill
    logger.info(f"Order sent ....order_ref: {order_ref}")
    # await trade.completion()  # Wait until the order is completed - need to be verified.
    logger.info(f"Order sent after await ....")

    logger.warning(f"trade: {trade}")

    logger.info(f"Submitted {action} {quantity} {symbol}, orderId={trade.order.orderId}, order_ref: {order_ref}")

    # OPTIONAL: wait until it is filled or cancelled
    if wait_untill_filled:
        while trade.orderStatus.status in ("PendingSubmit", "Submitted"):  # TODO need to be checked for other statuses
            await asyncio.sleep(0.5)
            logger.info( f"@@@ Waiting for status update ... order_ref: {order_ref}"
                f"Order status: {trade.orderStatus.status}, "
                f"filled={trade.orderStatus.filled}, "
                f"remaining={trade.orderStatus.remaining}"
            )

    logger.info(f"Final status: {trade.orderStatus.status}, order_ref: {order_ref}")
    return trade



async def get_open_orders(ib: IB):
    # Ensures IB sends all open orders
    await ib.reqOpenOrders()

    # This returns Trade objects
    open_trades = ib.trades()

    # Filter only open / working orders

    return open_trades




async def convert_open_orders_to_dict(ib: IB):
    out = []

    # Force IB to send all open orders
    await ib.reqOpenOrdersAsync()

    for t in ib.trades():
        status = t.orderStatus.status

        # # Keep only active orders
        if status  in ("Cancelled", 'Filled'):
            logger.info(f"convert_open_orders_to_dict: Skipping orderId={t.order.orderId} with status={status}")
            continue

        o = t.order
        c = t.contract

        c_type = CONTRACT_TYPE_MAP.get(type(c), "UNKNOWN")

        if o.totalQuantity == 0:
            continue

        logger.info(f"convert_open_orders_to_dict: Processing orderId={o.orderId}")
        logger.info(f"convert_open_orders_to_dict:   status={status}, action={o.action}, qty={o.totalQuantity}, filled={t.orderStatus.filled}, remaining={t.orderStatus.remaining}, limit_price={o.lmtPrice}, aux_price={o.auxPrice}")

        d = {
            # --------------------
            # Identity
            # --------------------
            "order_id": o.orderId,
            "perm_id": o.permId,
            "order_ref": o.orderRef,
            "client_id": o.clientId,
            "account": o.account,

            # --------------------
            # Contract
            # --------------------
            "symbol": c.symbol,
            "local_symbol": getattr(c, "localSymbol", None),
            "contract_id": c.conId,
            "sec_type": c.secType,
            "exchange": c.exchange,
            "contract_type": c_type,

            # --------------------
            # Order details
            # --------------------
            "action": o.action,                     # BUY / SELL
            "order_type": o.orderType,              # LMT / MKT / STP
            "qty": o.totalQuantity,
            "filled_qty": t.orderStatus.filled,
            "remaining_qty": t.orderStatus.remaining,
            "limit_price": o.lmtPrice,
            "aux_price": o.auxPrice,
            "tif": o.tif,

            # --------------------
            # Status
            # --------------------
            "status": status,                       # Submitted / PreSubmitted
            "why_held": t.orderStatus.whyHeld,

            # --------------------
            # Derived fields
            # --------------------
            "side": "buy" if o.action == "BUY" else "sell",

            "is_working": status in ("Submitted", "PreSubmitted"),
            "is_filled": t.orderStatus.remaining == 0,
            "remaining": t.orderStatus.remaining,

            # --------------------
            # Engine / routing
            # --------------------
            "last_update": date_utils.time_now_yyyy_mm_dd_hh_mm_ss(),
            # "cancel_requested": False,
            # "cancel_request_id": None,

            # --------------------
            # Future usage
            # --------------------
            "tags": [],        # ["entry", "exit", "hedge"]
            "metadata": {},    # strategy_id, portfolio_id, model_price, etc.
        }

        out.append(d)

    return out


# trading_utils/ib_orders_async.py

async def cancel_open_order(ib: IB, order_id: int) -> bool:
    """
    Cancel a single open order by orderId.
    Returns True if cancel request was sent.
    """
    for t in ib.trades():
        if t.order.orderId == order_id:
            logger.info(f"[CANCEL] Sending cancel for orderId={order_id}")
            ib.cancelOrder(t.order)
            return True

    logger.warning(f"[CANCEL] orderId={order_id} not found")
    return False


async def cancel_all_open_orders(ib: IB) -> int:
    """
    Cancel all active open orders.
    Returns number of cancel requests sent.
    """
    count = 0

    for t in ib.trades():
        status = t.orderStatus.status
        if status in ("PreSubmitted", "Submitted"):
            ib.cancelOrder(t.order)

            count += 1

    logger.info(f"[CANCEL] Cancel requested for {count} orders")
    # return count
    return True


async def cancel_open_orders_by_symbol(ib: IB, symbol: str) -> int:
    """
    Cancel all open orders for a given symbol.
    """
    count = 0

    for t in ib.trades():
        c = t.contract
        if (
            c.symbol == symbol
            and t.orderStatus.status in ("PreSubmitted", "Submitted")
        ):
            ib.cancelOrder(t.order)
            count += 1

    logger.info(f"[CANCEL] {count} orders canceled for symbol={symbol}")
    return count


async def cancel_open_orders_by_order_ref(
    ib: IB,
    order_ref: str,
) -> int:
    """
    Cancel all open orders matching orderRef.
    """
    count = 0

    for t in ib.trades():
        o = t.order
        if (
            o.orderRef == order_ref
            and t.orderStatus.status in ("PreSubmitted", "Submitted")
        ):
            ib.cancelOrder(o)
            count += 1

    logger.info(
        f"[CANCEL] {count} orders canceled for orderRef={order_ref}"
    )
    return count
