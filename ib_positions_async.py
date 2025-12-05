import sys
from ib_async import *
import logging
sys.path.insert(0, f'../')
logger = logging.getLogger(__name__)
from trading_utils import date_utils

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
        logger.debug(f"convert_positions_to_dict: Processing position: {p}")
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