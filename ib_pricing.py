import os.path
import pandas as pd
import logging
import math
import time
import datetime
from ib_insync import *
import sys
import random
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


def round_based_on_symbol(symbol, price):
    if symbol == 'MNQ':
        return round(price / 5) * 5  # returns 10,15,20 ...
        # return (price // 5) * 5 This returns the floor ..
    else:
        return price

def round_to_increment(value: float, increment: int = 5) -> int:
    """
    Round a value to the nearest multiple of 'increment'.
    Example: round_to_increment(123, 5) -> 125
             round_to_increment(122, 5) -> 120
    """
    return round(value / increment) * increment

def get_current_price_for_contract(ib, contract, max_retries=3, retry_delay=0.5):
    # request market data to get the current price
    for attempt in range(1, max_retries + 1):

        ticker = ib.reqTickers(contract)[0]
        price = ticker.marketPrice()
        if price is not None and not (pd.isna(price) or math.isnan(price)):
            if attempt > 1:
                logger.warning(f"@@ succefull try after attempt: {attempt}, contract: {contract}")
            return price
        else:
            logger.warning(f"@@@ get_current_price_for_contract,{contract}, price is nan, try again ... attempt: {attempt}")
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


def get_current_price_SPX(ib, symbol='SPX'):  # Remy app
    spx = Index(symbol='SPX', exchange='CBOE', currency='USD')
    ib.qualifyContracts(spx)

    # Request market data
    ticker = ib.reqMktData(spx, '', False, False)

    ib.sleep(1)
    logger.info(f"get_current_price_SPX, symbol: {symbol}, last: {ticker.last},  bid:, {ticker.bid},  ask:{ticker.ask}")
    last_price = ticker.last

    return last_price

def get_quote_for_contracts(ib, contracts):


    if global_state.ib_config.get('fall_back', '1 == 2'):
        data_list = []
        for contract in contracts:
            data = {
                "symbol": contract.symbol,
                "expiry": contract.lastTradeDateOrContractMonth,
                "strike": contract.strike,
                "right": contract.right,
                "bid": generate_fake_price(10),
                "ask": generate_fake_price(10),
                "last": generate_fake_price(10),
            }

            data_list.append(data)

        df = pd.DataFrame(data_list)

        logger.info(f"get_quote_for_contracts(): \n{df.to_markdown()}")

        return df

    logger.info(f"get_quote_for_contracts, calling ib.reqTickers started  ... ")
    tickers = ib.reqTickers(*contracts)
    logger.info(f"get_quote_for_contracts, calling ib.reqTickers finished  ...")
    # Build DataFrame
    data_list = []
    for t in tickers:
        data = {
            "symbol": t.contract.symbol,
            "expiry": t.contract.lastTradeDateOrContractMonth,
            "strike": t.contract.strike,
            "right": t.contract.right,
            "bid": t.bid,
            "ask": t.ask,
            "last": t.last,
        }

        data_list.append(data)

    df = pd.DataFrame(data_list)

    logger.info(f"get_quote_for_contracts(): \n{df.to_markdown()}")

    return df


def create_equity_contract(symbol, contract_month=''):
    if symbol == 'MNQ':
        contract = Future('MNQ', contract_month, 'CME')
    elif symbol == 'BTC':
        contract_btc = Contract()
        contract_btc.symbol = "BTC"
        contract_btc.secType = "CRYPTO"
        contract_btc.currency = "USD"
        contract_btc.exchange = "PAXOS"
        contract = contract_btc
    else:
        contract = Stock(symbol, 'SMART', 'USD')
    return contract


# def create_future_contract(symbol, contract_month=None):
#     if symbol == 'MNQ':
#         contract = Future('MNQ', contract_month, 'CME')
#     elif symbol == 'BTC':
#         contract_btc = Contract()
#         contract_btc.symbol = "BTC"
#         contract_btc.secType = "CRYPTO"
#         contract_btc.currency = "USD"
#         contract_btc.exchange = "PAXOS"
#         contract = contract_btc
#     else:
#         contract = Stock(symbol, 'SMART', 'USD')
#     return contract



def qualify_contracts(ib, contracts):
    logger.info(f"TBD")
    if global_state.ib_config.get('fall_back', '1 == 2'):
        return contracts

    qualified_contracts = ib.qualifyContracts(*contracts)
    logger.info(f"qualify_contracts, qualified: {qualified_contracts}")
    return qualified_contracts


import time
import logging
from ib_insync import *

logger = logging.getLogger(__name__)

def qualify_contracts_with_retry(ib, contracts, max_retries=5, sleep_sec=0.5):
    """
    Qualify a LIST of IB contracts with retry logic.

    Params:
        ib: IB instance
        contracts: list of unqualified IB contracts
        max_retries: number of retries
        sleep_sec: sleep between retries

    Returns:
        (qualified, failed)
        qualified → list of successfully qualified contracts
        failed → list of contracts that could not be qualified
    """

    # Make a mutable copy
    pending = contracts.copy()
    qualified = []
    failed = []

    for attempt in range(1, max_retries + 1):
        if not pending:
            break  # nothing left to qualify

        logger.info(f"[BulkQualify] Attempt {attempt}/{max_retries}, pending={len(pending)}")

        try:
            # IB can qualify only using *args
            result = ib.qualifyContracts(*pending)
        except Exception as e:
            logger.warning(f"[BulkQualify] Error on attempt {attempt}: {e}")
            time.sleep(sleep_sec)
            continue

        # result is a list in the SAME ORDER as 'pending', but failed ones become "" placeholder
        still_pending = []

        for original_contract, qualified_contract in zip(pending, result):
            if qualified_contract and getattr(qualified_contract, "conId", 0) != 0:
                qualified.append(qualified_contract)
            else:
                still_pending.append(original_contract)

        pending = still_pending
        time.sleep(sleep_sec)

    # Anything still pending after retries = failed
    failed.extend(pending)

    logger.info(f"[BulkQualify] Done. Qualified={len(qualified)}, Failed={len(failed)}")

    return qualified, failed
