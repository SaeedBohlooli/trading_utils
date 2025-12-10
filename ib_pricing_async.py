import logging
import asyncio
from trading_utils import *
from ib_async import *
import pandas as pd
logger = logging.getLogger(__name__)
import time
from trading_utils import date_utils
from trading_utils import global_state

async def get_current_price_SPX(ib, symbol='SPX', max_retries=3, retry_delay=0.5): # TODO need to be removed ...
    #
    if global_state.ib_config.get('fall_back', False):
        return generate_fake_spx_price()

    for attempt in range(1, max_retries + 1):
        # spx = Index(conId=416904, symbol='SPX', exchange='CBOE', currency='USD')
        spx = Index(symbol='SPX', exchange='CBOE', currency='USD')
        # spx = Contract()
        # spx.conId = 416904
        # spx.secType = "IND"
        # spx.symbol = "SPX"
        # spx.exchange = "CBOE"
        # spx.currency = "USD"

        details = await ib.qualifyContractsAsync(spx)
        logger.info(f"get_current_price_SPX, symbol: {symbol}, details: {details}")
        # logger.info(details[0].contract.conId)

        ticker = ib.reqMktData(spx, '', False, False)
        await asyncio.sleep(1)
        logger.info(f"get_current_price_SPX, symbol: {symbol}, last: {ticker.last},  bid:, {ticker.bid},  ask:{ticker.ask}")

        price = ticker.last
        if price is not None and not (pd.isna(price) or math.isnan(price)):
            if attempt > 1:
                logger.warning(f"@@ get_current_price_SPX, succefull try after attempt: {attempt}, symbol: {symbol}")
            return price
        else:
            logger.warning(
                f"@@@ get_current_price_SPX, {symbol}, price is nan, try again ... attempt: {attempt}")
            await asyncio.sleep(retry_delay)

    return price


async def qualify_contracts_v_1(ib, contracts):
    logger.info(f"qualify_contracts_v_1")
    # if global_state.ib_config.get('fall_back', '1 == 2'):
    #     return contracts

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


    # if global_state.ib_config.get('fall_back', '1 == 2'):
    #     data_list = []
    #     for contract in contracts:
    #         data = {
    #             "symbol": contract.symbol,
    #             "expiry": contract.lastTradeDateOrContractMonth,
    #             "strike": contract.strike,
    #             "right": contract.right,
    #             "bid": generate_fake_price(10),
    #             "ask": generate_fake_price(10),
    #             "last": generate_fake_price(10),
    #         }
    #
    #         data_list.append(data)
    #
    #     df = pd.DataFrame(data_list)
    #
    #     logger.info(f"get_quote_for_contracts(): \n{df.to_markdown()}")
    #
    #     return df

    logger.info(f"get_quote_for_contracts, calling ib.reqTickers started  ... ")
    start_time = time.time()
    tickers = await ib.reqTickersAsync(*contracts)
    end_time = time.time()
    run_spend_time = round(end_time - start_time, 2)

    logger.info(f"get_quote_for_contracts, calling ib.reqTickers finished, run_spend_time: {run_spend_time}  ...")
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


    # if global_state.ib_config.get('fall_back', '1 == 2'):
    #     data_list = []
    #     for contract in contracts:
    #         data = {
    #             "symbol": contract.symbol,
    #             "expiry": contract.lastTradeDateOrContractMonth,
    #             "strike": contract.strike,
    #             "right": contract.right,
    #             "bid": generate_fake_price(10),
    #             "ask": generate_fake_price(10),
    #             "last": generate_fake_price(10),
    #         }
    #
    #         data_list.append(data)
    #
    #     df = pd.DataFrame(data_list)
    #
    #     logger.info(f"get_quote_for_contracts(): \n{df.to_markdown()}")
    #
    #     return df

    logger.info(f"get_quote_for_contracts, calling ib.reqTickers started  ... ")
    start_time = time.time()
    tickers = await ib.reqTickersAsync(*contracts)
    end_time = time.time()
    run_spend_time = round(end_time - start_time, 2)

    logger.info(f"get_quote_for_contracts, calling ib.reqTickers finished, run_spend_time: {run_spend_time}  ...")
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



async def subscribe_symbol_once(ib, symbol, secType="STK", exchange="SMART", currency="USD"):
    """
    General purpose subscription for any stock/index/future/crypto.
    Example: TSLA, AMD, SPX, NDX, MSFT, AAPL, NVDA
    """

    if secType == "IND":
        contract = Index(symbol=symbol, exchange=exchange, currency=currency)
    elif secType == "STK":
        contract = Stock(symbol, exchange, currency)
    elif secType == "FUT":
        # You can refine this later
        contract = Future(symbol=symbol, exchange=exchange, currency=currency)
    else:
        raise Exception(f"Unsupported secType: {secType}")

    details = await ib.qualifyContractsAsync(contract)

    logger.info(f"[SUBSCRIBE], qualified contract: {symbol} details: {details}")

    qualified = details[0]  # this is already a Contract (Index/Stock/etc.)
    con_id = qualified.conId

    logger.info(f"[SUBSCRIBE] {symbol} qualified with conId={con_id}")

    ticker = ib.reqMktData(contract, "", False, False)
    ticker.updateEvent += on_ticker_update

    # store mappings
    global_state.symbol_to_conid[symbol] = con_id
    global_state.conid_to_symbol[con_id] = symbol

    return ticker

def get_latest_price(symbol, fallback=True):
    """
    Returns best available price (last > bid > ask) for any subscribed symbol.
    """
    con_id = global_state.symbol_to_conid.get(symbol)

    if con_id is None:
        logger.warning(f"@@ get_latest_price: Symbol {symbol} not subscribed")
        return None

    q = global_state.quote_cache.get(con_id)
    if q is None:
        logger.warning(f"@@ get_latest_price: No quote yet for {symbol}")
        return None

    last = q.get("last")
    bid  = q.get("bid")
    ask  = q.get("ask")

    # Best price logic
    if valid(last): return last
    if valid(bid): return bid
    if valid(ask): return ask

    return None


def valid(x):
    return x is not None and not pd.isna(x)



def on_ticker_update(ticker):
    logger.debug(f"[ib_pricing_async] on_ticker_update: ticker: {ticker.contract.conId}, last: {ticker.last}, bid: {ticker.bid}, ask: {ticker.ask}")
    c = ticker.contract
    if c is None:
        logger.warning(f"@@@@ on_ticker_update: Encountered None contract — skipping ticker: {ticker}")
        return
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


async def subscribe_to_contracts(ib, contracts):
    """
    Subscribe once to continuous market data for all given contracts.
    This is the FAST method: updates come automatically via callbacks.
    """
    for c in contracts:
        # request streaming market data
        if c is None:
            logger.error(f"@@@@@@ subscribe_to_contracts: Encountered None contract — skipping contract: {c}")
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
        logger.info(f"[ib_pricing_async] SUBSCRIBED: {symbol} (conId={con_id})")

    logger.info(f"[ib_pricing_async] Subscribed to {len(contracts)} contracts.")
    return


async def unsubscribe_contract(ib, contract):
    if contract is None:
        logger.warning("@@@ [ERROR] unsubscribe_contract: contract is None — skipping")
        return

    # IBKR-side unsubscribe
    try:
        ib.cancelMktData(contract)
    except Exception as e:
        logger.warning(f"[WARN] cancelMktData failed: {e}")

    # Remove from cache
    quote_cache.pop(contract.conId, None)

    logger.warning(f"[ib_pricing_async] UNSUBSCRIBED: {contract.localSymbol} (conId={contract.conId})")
    #
    #  I dont think we need to log cache removal here, as it's done above

    # # Remove from local cache
    # removed = quote_cache.pop(contract.conId, None)
    # if removed:
    #     logger.info(
    #         f"[CACHE REMOVED] {contract.localSymbol} | conId={contract.conId}"
    #     )
    # else:
    #     logger.warning(
    #         f"[CACHE MISS] Tried removing conId={contract.conId} but it was not found in quote_cache"
    #     )


def find_and_print_invalid_quotes(df):
    if df is None or len(df) == 0:
        return df

    invalid_mask = (
        (df["bid"].isna()) | (df["bid"] == -1) |
        (df["ask"].isna()) | (df["ask"] == -1)
    )

    invalid_rows = df.loc[invalid_mask]

    if not invalid_rows.empty:
        logger.warning(f"@@@ find_and_print_invalid_quotes, Invalid rows (bid or ask is NaN or -1): \n{invalid_rows.to_markdown()}")

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

    logger.warning("@@@@ fix_bid_ask_with_fallback, invalid rows (before fixing)")
    invalid_rows = df.loc[bid_invalid | ask_invalid]
    logger.warning(f"\n{invalid_rows.to_markdown()}")

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

    logger.info("@@@  INVALID ROWS (AFTER FIXING) ===")
    invalid_after = df.loc[
        df["bid"].isna() | (df["bid"] == -1) | df["ask"].isna() | (df["ask"] == -1)
    ]
    logger.info(f"\n{invalid_after.to_markdown()}")

    return df



