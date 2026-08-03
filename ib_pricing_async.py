import logging
logger = logging.getLogger(__name__)
import asyncio
from trading_utils import *
from ib_async import *
import pandas as pd
import time
from trading_utils import date_utils
from trading_utils import global_state
from trading_utils import ib_contract
import numpy as np
import math
import datetime


# async def XXX_get_current_price_SPX(ib, symbol='SPX', max_retries=3, retry_delay=0.5): # TODO need to be removed ...
#     #
#
#     for attempt in range(1, max_retries + 1):
#         # spx = Index(conId=416904, symbol='SPX', exchange='CBOE', currency='USD')
#         spx = Index(symbol='SPX', exchange='CBOE', currency='USD')
#         # spx = Contract()
#         # spx.conId = 416904
#         # spx.secType = "IND"
#         # spx.symbol = "SPX"
#         # spx.exchange = "CBOE"
#         # spx.currency = "USD"
#
#         details = await ib.qualifyContractsAsync(spx)
#         logger.info(f"get_current_price_SPX, symbol: {symbol}, details: {details}")
#         # logger.info(details[0].contract.conId)
#
#         ticker = ib.reqMktData(spx, '', False, False)
#         await asyncio.sleep(1)
#         logger.info(f"get_current_price_SPX, symbol: {symbol}, last: {ticker.last},  bid:, {ticker.bid},  ask:{ticker.ask}")
#
#         price = ticker.last
#         if price is not None and not (pd.isna(price) or math.isnan(price)):
#             if attempt > 1:
#                 logger.warning(f"@@ get_current_price_SPX, succefull try after attempt: {attempt}, symbol: {symbol}")
#             return price
#         else:
#             logger.warning(f"@@@ get_current_price_SPX, {symbol}, price is nan, try again ... attempt: {attempt}")
#             await asyncio.sleep(retry_delay)
#
#     return price


async def qualify_contracts_v_1(ib, contracts):
    logger.info(f"qualify_contracts_v_1")

    # The asterisk (*) is crucial because it "unpacks" the list, sending each individual contract within the list as a separate argument to the qualifyContractsAsync method. This will resolve the AttributeError because the method will then correctly receive contract objects with an includeExpired attribute, rather than an unprocessable list.

    qualified_contracts = await ib.qualifyContractsAsync(*contracts)
    if None in qualified_contracts:

        logger.error(f"@@@@ qualify_contracts, encountered None in qualified_contracts")
        logger.info(f"qualify_contracts, qualified_contracts: {len(qualified_contracts)} , contracts: {len(contracts)}")
        logger.info("@@@@ qualify_contracts, qualified:\n" + "\n".join(map(str, qualified_contracts)))
        logger.info("@@@@ qualify_contracts, contracts:\n" + "\n".join(map(str, contracts)))

    return qualified_contracts


async def qualify_contracts(ib, contracts):

    logger.info(f"qualify_contracts, contracts: {contracts}")

    # Schedule each qualification in parallel
    tasks = [ib.qualify_contracts(c) for c in contracts]

    # Run all IBKR requests concurrently
    results = await asyncio.gather(*tasks, return_exceptions=False)

    qualified = []
    for res in results:
        if res:
            # res is a list: [ContractDetails.contract]
            qualified.append(res[0])
        else:
            logger.warning("Failed to qualify a contract")

    return qualified



async def get_quote_for_contracts(ib, contracts):



    logger.info(f"get_quote_for_contracts, calling ib.reqTickers started  ... ")
    start_time = time.time()
    tickers = await ib.reqTickersAsync(*contracts)
    end_time = time.time()
    run_time_spent = round(end_time - start_time, 2)

    logger.info(f"get_quote_for_contracts, calling ib.reqTickers finished, run_time_spent: {run_time_spent}  ...")
    # Build DataFrame
    data_list = []
    for t in tickers:
        logger.info(f"get_quote_for_contracts: t.contract: {t.contract}")
        # t.contract: Option(conId=807843628, symbol='SPX', lastTradeDateOrContractMonth='20251128', strike=6845.0, right='C', multiplier='100', exchange='CBOE', currency='USD', localSymbol='SPXW  251128C06845000', tradingClass='SPXW')
        data = {
            "symbol": t.contract.symbol,
            "local_symbol": t.contract.localSymbol,
            "expiry": t.contract.lastTradeDateOrContractMonth,
            "strike": t.contract.strike,
            "con_id": t.contract.conId,
            "right": t.contract.right,
            "bid": t.bid,
            "ask": t.ask,
            "last": t.last,
        }

        data_list.append(data)

    df = pd.DataFrame(data_list)

    logger.info(f"get_quote_for_contracts(): \n{df.to_markdown()}")

    return df


# This one is subscribing ....
async def get_quote_for_contracts_ver_2(ib, contracts):

    logger.info(f"get_quote_for_contracts, calling ib.reqTickers started  ... ")
    start_time = time.time()
    tickers = await ib.reqTickersAsync(*contracts)
    end_time = time.time()
    run_time_spent = round(end_time - start_time, 2)

    logger.info(f"get_quote_for_contracts, calling ib.reqTickers finished, run_time_spent: {run_time_spent}  ...")
    # Build DataFrame
    data_list = []
    for t in tickers:
        logger.info(f"get_quote_for_contracts: t.contract: {t.contract}")
        # t.contract: Option(conId=807843628, symbol='SPX', lastTradeDateOrContractMonth='20251128', strike=6845.0, right='C', multiplier='100', exchange='CBOE', currency='USD', localSymbol='SPXW  251128C06845000', tradingClass='SPXW')
        data = {
            "symbol": t.contract.symbol,
            "local_symbol": t.contract.localSymbol,
            "expiry": t.contract.lastTradeDateOrContractMonth,
            "strike": t.contract.strike,
            "con_id": t.contract.conId,
            "right": t.contract.right,
            "bid": t.bid,
            "ask": t.ask,
            "last": t.last,
        }

        data_list.append(data)

    df = pd.DataFrame(data_list)

    logger.info(f"get_quote_for_contracts(): \n{df.to_markdown()}")

    return df



async def subscribe_symbol_for_market_price(ib, symbol, secType= None, exchange= None, currency=None, contract_month=None):
    """
    General purpose subscription for any stock/index/future/crypto.
    Example: TSLA, AMD, SPX, NDX, MSFT, AAPL, NVDA
    """
    if secType is None:
        # try to infer from registry
        reg = global_state.symbol_registry.get(symbol)
        if reg is not None:
            secType = reg.get("secType")
            exchange = reg.get("exchange", exchange)
            currency = reg.get("currency", currency)
        elif contract_month is not None:
            secType = "FUT"
            exchange = "CME"
            currency = "USD"
        else:
            # it is STK by default
            secType = "STK"
            exchange = "SMART"
            currency = "USD"

    if secType == "IND":
        contract = Index(symbol=symbol, exchange=exchange, currency=currency)
    elif secType == "STK":
        contract = Stock(symbol, exchange, currency)
    elif secType == "FUT":
        # You can refine this later
        contract = Future(symbol=symbol, exchange=exchange, currency=currency, lastTradeDateOrContractMonth=contract_month)
    else:
        raise Exception(f"Unsupported secType: {secType}")

    details = await ib.qualifyContractsAsync(contract)

    logger.info(f"[subscribe_symbol_for_market_price] qualified contract: {symbol} details: {details}")

    qualified = details[0]  # this is already a Contract (Index/Stock/etc.)
    if qualified is None:
        logger.warning(f"[subscribe_symbol_for_market_price] @@@@@ : qualified contract is None for symbol: {symbol}")
        return None

    con_id = qualified.conId

    logger.info(f"[subscribe_symbol_for_market_price] {symbol} qualified with conId= {con_id}")

    ticker = ib.reqMktData(contract, "", False, False)
    ticker.updateEvent += on_ticker_update

    # store mappings
    global_state.symbol_to_conid[symbol] = con_id
    global_state.conid_to_symbol[con_id] = symbol
    global_state.conid_to_symbol_subscribed_for_quotes[con_id] = symbol

    return ticker

async def get_or_subscribe_symbol_price(ib,
                                        symbol,
                                        contract_month=None,
                                        wait_for_price=False,
                                        timeout_sec=10.0,
                                        poll_interval=0.5,):
    """
    Returns best available price (last > bid > ask) for any subscribed symbol.
    """
    con_id = None
    attempt = 0
    while con_id is None: # wait until you get con_id
        attempt += 1
        con_id = global_state.symbol_to_conid.get(symbol)

        if con_id is None:
            logger.info(f"[get_or_subscribe_symbol_price] symbol {symbol} not subscribed yet, subscribing now ... attempt: {attempt}")
            await subscribe_symbol_for_market_price(ib, symbol, contract_month=contract_month)
            # return None
        if attempt > 3:
            logger.error(f"[get_or_subscribe_symbol_price] @@ Failed to get conId for symbol: {symbol} after {attempt} attempts.")
            await asyncio.sleep(poll_interval)


    q = global_state.quote_cache.get(con_id)
    if q is None:
        await subscribe_symbol_for_market_price(ib, symbol, contract_month=contract_month)


    start = time.time()
    warned = False

    while True:
        q = global_state.quote_cache.get(con_id)

        logger.debug(f"[get_or_subscribe_symbol_price] @ get_latest_price: symbol: {symbol}, con_id: {con_id}, global_state.quote_cache: {global_state.quote_cache}")
        logger.debug(f"[get_or_subscribe_symbol_price] @ get_latest_price: symbol: q: {q}")

        if q:
            last = q.get("last")
            bid = q.get("bid")
            ask = q.get("ask")

            # Best price logic
            if valid(last): return last
            if valid(bid): return bid
            if valid(ask): return ask
        # -----------------------------
        # No price yet
        # -----------------------------
        if not wait_for_price:
            logger.warning(f"[get_or_subscribe_symbol_price] @ No quote yet for {symbol}")
            return None

        if time.time() - start > timeout_sec:
            logger.warning(f"[get_or_subscribe_symbol_price] @ Timeout waiting for price for {symbol} after {timeout_sec}s"
            )
            return None

        if not warned:
            logger.info(f"[get_or_subscribe_symbol_price] @ Waiting for first price for {symbol}")
            warned = True
        logger.info(f"[get_or_subscribe_symbol_price] @ No valid price yet for {symbol} ... we still waiting ...")
        await asyncio.sleep(poll_interval)

def valid(x):
    return x is not None and not pd.isna(x)



def on_ticker_update(ticker):
    logger.debug(f"[ib_pricing_async] on_ticker_update: ticker: {ticker.contract.conId}, last: {ticker.last}, bid: {ticker.bid}, ask: {ticker.ask}")
    c = ticker.contract
    if c is None:
        logger.warning(f"@@@@ on_ticker_update: Encountered None contract — skipping ticker: {ticker}")
        return

    if ticker.contract.conId in [822548126]: # debug holder ...
        logger.debug(f"[ib_pricing_async] on_ticker_update: ticker: {ticker.contract.conId}, last: {ticker.last}, bid: {ticker.bid}, ask: {ticker.ask}")

    global_state.quote_cache[c.conId] = {
        "symbol": c.symbol,
        "local_symbol": c.localSymbol,
        "expiry": c.lastTradeDateOrContractMonth,
        "strike": c.strike,
        "right": c.right,
        "con_id": c.conId,
        "bid": ticker.bid,
        "ask": ticker.ask,
        "last": ticker.last,
        "timestamp": date_utils.time_now_yyyy_mm_dd_hh_mm_ss(),
    }


async def subscribe_contracts_to_market_data(ib, contracts):
    """
    Subscribe once to continuous market data for all given contracts.
    This is the FAST method: updates come automatically via callbacks.
    """
    # for c in contracts:
    #     logger.info(f"@@ subscribe_contracts_to_market_data: {c}")

    for c in contracts:
        # request streaming market data
        logger.info(f"[subscribe_contracts_to_market_data] Contract to subscribe: {c}")
        if c is None:
            logger.error(f"[subscribe_contracts_to_market_data] @@@@@@ subscribe_to_contracts: Encountered None contract — skipping contract: {c}")
            continue

        if c.conId in global_state.conid_to_symbol_subscribed_for_quotes.keys():
            logger.debug(f"[subscribe_contracts_to_market_data] @ subscribe_to_contracts: Already subscribed to conId={c.conId}, skipping...")
            continue
        ticker = ib.reqMktData(
            c,
            genericTickList="",
            snapshot=False,
            regulatorySnapshot=False
        )

        # attach callback
        ticker.updateEvent += on_ticker_update

        symbol = c.localSymbol
        con_id = c.conId

        global_state.symbol_to_conid[symbol] = con_id
        global_state.conid_to_symbol[con_id] = symbol
        global_state.conid_to_symbol_subscribed_for_quotes[con_id] = symbol

        logger.info(f"[subscribe_contracts_to_market_data] SUBSCRIBED: {symbol} (conId={con_id})")

    logger.info(f"[subscribe_contracts_to_market_data] Subscribed to {len(contracts)} contracts.")
    return

async def get_or_subscribe_option_price(ib, symbol=None, expiry=None,strike=None, right=None):
    contract = await ib_contract.get_option_contract_cached(ib, symbol, expiry, strike, right)
    if contract is None:
        logger.warning(f"[get_or_subscribe_option_price] @@@ contract is None for symbol: {symbol}, expiry: {expiry}, strike: {strike}, right: {right}")
        return np.nan, np.nan, np.nan
    await subscribe_contracts_to_market_data(ib, [contract])

    option_contrat = await ib_contract.get_option_contract_cached(ib, symbol, expiry, strike, right)
    bid, ask, last = get_bid_ask_last_for_c_id(option_contrat.conId)
    return bid, ask, last




def get_bid_ask_last_for_c_id(con_id):
    quotes = global_state.quote_cache
    q = quotes.get(con_id)
    if q is None:
        return None, None, None
    bid = q.get("bid")
    ask = q.get("ask")
    last = q.get("last")
    return bid, ask, last

def get_all_quotes_as_df():
    quotes = global_state.quote_cache
    if quotes == {}:
        return pd.DataFrame()  # empty
    df = pd.DataFrame(list(quotes.values()))  #  {con_id: {}}
    return df

def get_all_quotes_as_dic():
    quotes = global_state.quote_cache
    return quotes


async def unsubscribe_contracts_from_market_data(ib, contracts):
    """
    Unsubscribe from continuous market data for given contracts.
    This MUST be symmetric to reqMktData.
    """
    for c in contracts:
        if c is None:
            logger.error("[unsubscribe_contracts_from_market_data] @@@@@@ Encountered None contract — skipping")
            continue

        con_id = c.conId
        symbol = global_state.conid_to_symbol.get(con_id)

        if con_id not in global_state.conid_to_symbol_subscribed_for_quotes:
            logger.warning(f"[unsubscribe_contracts_from_market_data] @ Not subscribed to conId={con_id}, skipping...")
            continue

        try:
            logger.info(f"[unsubscribe_contracts_from_market_data] UNSUBSCRIBING: {symbol} (conId={con_id})")

            # IMPORTANT: this is the real unsubscribe
            ib.cancelMktData(c)


            # remove from global_state.quote_cache
            global_state.quote_cache.pop(con_id, None)
            global_state.conid_to_symbol_subscribed_for_quotes.pop(con_id, None)  # This keeps which conid are subscribed ...


        except Exception as e:
            logger.exception(
                f"[unsubscribe_contracts_from_market_data] @@@@@@ Failed to unsubscribe conId={con_id}, symbol={symbol}: {e}"
            )

    logger.info(f"[unsubscribe_contracts_from_market_data] Unsubscribe completed.")
    return


def find_and_print_invalid_quotes(df):
    if df is None or len(df) == 0:
        return df

    invalid_mask = (
        (df["bid"].isna()) | (df["bid"] == -1) |
        (df["ask"].isna()) | (df["ask"] == -1)
    )

    invalid_rows = df.loc[invalid_mask]

    if not invalid_rows.empty:
        logger.warning(f"[find_and_print_invalid_quotes] @ Invalid rows (bid or ask is NaN or -1): \n{invalid_rows.to_markdown()}")

    return invalid_rows

def fix_bid_ask_df(df):
    if df is None or len(df) == 0:
        return df

    # Last is valid only if NOT -1 and NOT NaN
    last_valid = (df["last"] != -1) & (~df["last"].isna())

    # Masks for which rows will change
    mask_bid = (df["bid"] == -1) & last_valid
    mask_ask = (df["ask"] == -1) & last_valid

    # Combined mask for printing
    mask_any = mask_bid | mask_ask

    # Print rows BEFORE replacement
    if mask_any.any():
        logger.warning(f"@@@ fix_bid_ask_df, Rows to be replaced:\n{df.loc[mask_any].to_markdown()}")

    # Apply replacements
    df["bid"] = np.where(mask_bid, df["last"], df["bid"])
    df["ask"] = np.where(mask_ask, df["last"], df["ask"])

    return df



def fix_bid_ask_with_fallback(df):
    """
    IF bid == -1 or NaN:
        IF last is valid (not -1, not NaN):
            bid = last
        ELSE IF ask is valid (not -1, not NaN):
            bid = ask
    IF ask == -1 or NaN:
        IF last is valid:
            ask = last
        ELSE IF bid is valid:
            ask = bid

    :param df:
    :return:
    """
    if df is None or len(df) == 0:
        return df

    # convenience aliases
    bid = df["bid"]
    ask = df["ask"]
    last = df["last"]

    # Validity masks
    bid_invalid = bid.isna() | (bid == -1)
    ask_invalid = ask.isna() | (ask == -1)
    last_valid = (~last.isna()) & (last != -1)

    ask_valid = (~ask.isna()) & (ask != -1)
    bid_valid = (~bid.isna()) & (bid != -1)


    invalid_rows = df.loc[bid_invalid | ask_invalid]
    if len(invalid_rows) > 0:
        logger.warning(f"@@ fix_bid_ask_with_fallback, invalid rows (before fixing) \n{invalid_rows.to_markdown()}")

    # -------------------------
    # FIX BID
    # -------------------------

    # 1) Replace bid with last if bid invalid and last valid
    df["bid"] = np.where(bid_invalid & last_valid, last, bid)

    # 2) Replace bid with ask if still invalid and ask valid
    bid = df["bid"]   # refresh after step 1
    bid_invalid_after_1 = bid.isna() | (bid == -1)
    df["bid"] = np.where(bid_invalid_after_1 & ask_valid, ask, bid)

    # -------------------------
    # FIX ASK
    # -------------------------

    # 3) Replace ask with last if ask invalid and last valid
    df["ask"] = np.where(ask_invalid & last_valid, last, ask)

    # 4) Replace ask with bid if still invalid and bid valid
    ask = df["ask"]   # refresh after step 3
    ask_invalid_after_1 = ask.isna() | (ask == -1)
    df["ask"] = np.where(ask_invalid_after_1 & bid_valid, df["bid"], ask)

    invalid_after = df.loc[
        df["bid"].isna() | (df["bid"] == -1) | df["ask"].isna() | (df["ask"] == -1)
    ]
    if len(invalid_after) == 0:
        logger.info("All invalid rows have been fixed.")
    else:
        logger.info("@@@ invalid rows (after fixing) ===")
        logger.info(f"\n{invalid_after.to_markdown()}")

    return df



async def get_active_subscriptions(ib):
    """
    Returns a list of active ticker subscriptions (symbols + conIds)
    from the ib_async engine.
    """
    # ib.tickers() is safe to call anytime — it shows all active reqMktData streams
    tickers = ib.tickers()

    active = []
    for t in tickers:
        contract = t.contract
        symbol = getattr(contract, "localSymbol", None)
        con_id  = getattr(contract, "conId", None)

        active.append({
            "symbol": symbol,
            "conId": con_id
        })

    return active


async def check_are_they_shortable(ib, contracts):
    """
    Given a list of conIds, fetch the current borrow fees for each.
    Returns a DataFrame with conId and fee_per_annum columns.
    """
    logger.info(f"check_are_they_shortable:  {len(contracts)} ")

    fees_data = []
    for c in contracts:
        # logger.info(f"Fetching fee for conId {c} ...")
        try:
            ticker = ib.reqMktData(
                c,
                genericTickList="236",
                snapshot=False, # This required.
                regulatorySnapshot=False
            )

            # wait until populated
            for _ in range(40):  # ~2 seconds max
                if ticker.shortableShares is not None and not math.isnan(ticker.shortableShares):
                    break
                await asyncio.sleep(0.05)

            shortable = ticker.shortableShares
            shortableShares = ticker.shortableShares  # placeholder for actual fee field

            # IMPORTANT: cancel to avoid streaming forever
            ib.cancelMktData(c)
            await asyncio.sleep(1)  # wait for data to arrive

            fees_data.append({
                # "conId": c,
                "symbol": c.symbol,
                "shortableShares": shortableShares,
                "shortable": shortable,

            })
            logger.info(f"Fetched  shortable: {shortable} shortableShares: {shortableShares}, {c.symbol}")

        except Exception as e:
            logger.error(f"@@@ Error check_are_they_shortable fee for conId {c}: {e}")

    # df = pd.DataFrame(fees_data)
    return fees_data



def find_bid_ask(df, symbol, strike, expiry=None, right=None):
    if df is None or df.empty:
        return {}
    mask = (
        (df["symbol"] == symbol) &
        (df["strike"] == strike)
    )

    if expiry is not None:
        mask &= (df["expiry"] == expiry)

    if right is not None:
        mask &= (df["right"] == right)

    row = df.loc[mask]

    if row.empty:
        return {}
    # TODO in case more than one row. we need to handle it ...

    r = row.iloc[0]

    return {'bid': r["bid"], 'ask': r["ask"], 'timestamp': r["timestamp"]}

def round_based_on_symbol(symbol, price):
    if symbol == 'MNQ':
        return round(price / 5) * 5  # returns 10,15,20 ...
        # return (price // 5) * 5 This returns the floor ..
    else:
        return price

def cleanup_stale_quotes(max_age_seconds=120):
    """
    Removes entries from global_state.quote_cache whose timestamp is older
    than max_age_seconds (default: 120 seconds = 2 minutes).

    Timestamp format expected: "%Y-%m-%d %H:%M:%S"  (set by date_utils.time_now_yyyy_mm_dd_hh_mm_ss)

    Call this periodically (e.g. once per engine cycle) to prevent the cache
    from growing indefinitely with stale option/contract quotes.

    Returns the number of entries removed.
    """

    now = datetime.datetime.now()
    stale_con_ids = []

    for con_id, entry in list(global_state.quote_cache.items()):
        ts_str = entry.get('timestamp')
        if ts_str is None:
            # no timestamp — treat as stale
            stale_con_ids.append(con_id)
            continue
        try:
            ts = datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            age_seconds = (now - ts).total_seconds()
            if age_seconds > max_age_seconds:
                stale_con_ids.append(con_id)
        except Exception as e:
            logger.warning(f"[cleanup_stale_quotes] Could not parse timestamp '{ts_str}' for conId={con_id}: {e}")
            stale_con_ids.append(con_id)

    for con_id in stale_con_ids:
        entry = global_state.quote_cache.pop(con_id, None)
        symbol = entry.get('symbol', '?') if entry else '?'
        logger.info(f"[cleanup_stale_quotes] Removed stale quote: conId={con_id} symbol={symbol} age>{max_age_seconds}s")

    if stale_con_ids:
        logger.info(f"[cleanup_stale_quotes] Removed {len(stale_con_ids)} stale entries. "
                    f"Cache size now: {len(global_state.quote_cache)}")
    else:
        logger.debug(f"[cleanup_stale_quotes] No stale entries. Cache size: {len(global_state.quote_cache)}")

    return len(stale_con_ids)

async def filter_valid_symbols(ib, symbols):
    """
    Given a list of symbols, attempts to qualify each one with IB.
    Returns only the symbols that IB successfully qualifies (valid symbols).
    Invalid or unknown symbols are logged and excluded.

    Args:
        ib: IB connection instance
        symbols: list of symbol strings (e.g. ['AAPL', 'TSLA', 'INVALIDXYZ'])
        contract_month: optional contract month for futures (e.g. '202509')

    Returns:
        list[str]: valid symbols only
    """
    valid = []
    for symbol in symbols:
        secType = None
        exchange = None
        currency = None

        # TODO need t be fixed for FUT and INDX
        reg = global_state.symbol_registry.get(symbol)
        secType = "STK"
        exchange = "SMART"
        currency = "USD"
        contract_month = ''

        # if reg is not None:
        #     secType = reg.get("secType")
        #     exchange = reg.get("exchange")
        #     currency = reg.get("currency")
        # elif contract_month is not None:
        #     secType = "FUT"
        #     exchange = "CME"
        #     currency = "USD"
        # else:
        #     secType = "STK"
        #     exchange = "SMART"
        #     currency = "USD"

        try:
            if secType == "IND":
                contract = Index(symbol=symbol, exchange=exchange, currency=currency)
            elif secType == "STK":
                contract = Stock(symbol, exchange, currency)
            elif secType == "FUT":
                contract = Future(symbol=symbol, exchange=exchange, currency=currency,
                                  lastTradeDateOrContractMonth=contract_month)
            else:
                logger.warning(f"[filter_valid_symbols] Unsupported secType '{secType}' for {symbol}, skipping.")
                continue

            details = await ib.qualifyContractsAsync(contract)
            if details and details[0] is not None and details[0].conId != 0:
                logger.info(f"[filter_valid_symbols] '{symbol}' is valid (conId={details[0].conId})")
                valid.append(symbol)
            else:
                logger.warning(f"[filter_valid_symbols] '{symbol}' is INVALID — no conId returned, skipping.")
        except Exception as e:
            logger.warning(f"[filter_valid_symbols] '{symbol}' raised exception during qualification: {e}, skipping.")

    logger.info(f"[filter_valid_symbols] {len(valid)}/{len(symbols)} symbols valid: {valid}")
    return valid