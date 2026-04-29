import asyncio
import pandas as pd
from ib_async import *
import logging
from trading_utils import ib_contract
from typing import Optional, Dict, Tuple, List

logger = logging.getLogger(__name__)

# Map user-friendly timeframes to IB's bar size settings
BAR_SIZE_MAP = {
    "1D": "1 day",
    "1d": "1 day",
    "1H": "1 hour",
    "1h": "1 hour",
    "5m": "5 mins",
    "1m": "1 min",
    "1min": "1 min",
    "1 day": "1 day",   # default ib syntax for bar size
    "1 hour": "1 hour", # default ib syntax for bar size
    "5 mins": "5 mins", # default ib syntax for bar size
    "1 min": "1 min", #
}

DEFAULT_DURATION_MAP = {
    "1 day": "60 D",     # 60 days of daily bars
    "1 hour": "15 D",     # 15 days of hourly bars
    "5 mins": "5 D",      # 5 days of 5-min bars
    "1 min": "5 D",      # 2 days of 1-min bars
}


async def get_stock_historical_data(
    ib: IB,
    symbol: str,
    time_frame: str,
    end_date: str | None = None,     # <--- kept
    duration: str | None = None,     # <--- optional
    max_retries: int = 5,
    retry_delay: float = 2.0,
    what_to_show: str = "TRADES",
    contract_month: str = None,  # used only for MNQ futures,
    use_RTH: bool = True, # True is faster no extra work by IB to trim bars to RTH
    print_last_few_rows = 0
):
    """
    Fetch historical data ending at `end_date` (optional)
    Duration goes backward from end_date.
    start_date removed.
    """

    if time_frame not in BAR_SIZE_MAP:
        raise ValueError(f"Invalid timeframe '{time_frame}'. Use: 1D, 1H, 5M, 1M")
    ib_timeframe = BAR_SIZE_MAP[time_frame]

    # user did not specify duration → use smart default
    if duration is None or duration =="":
        duration = DEFAULT_DURATION_MAP[ib_timeframe]

    use_cache = True
    if use_cache:
        contract = await ib_contract.get_cached_contract(ib, symbol, contract_month=contract_month)
    else:
        logger.info(f"[get_stock_historical_data] : Caching disabled.")
        if symbol == "MNQ":
            contract = Future('MNQ', contract_month, 'CME')
        elif symbol == "SPX":
            contract = Index(symbol=symbol, exchange="CBOE", currency="USD")
        else:
            contract = Stock(symbol, "SMART", "USD")

    # Prepare contract
    logger.info(f"[get_stock_historical_data] , Fetching historical data for {symbol}, timeframe: {time_frame}, duration: {duration}, end_date: {end_date}, contract: {contract}")
    # await ib.qualifyContractsAsync(contract)

    # Set IBKR endDateTime
    if end_date:   # should be in 'YYYYMMDD' format
        endDateTime = f"{end_date} 23:59:59"
    else:
        endDateTime = ""   # means "now"

    # ---------------------------------------------------------
    #                     RETRY LOGIC
    # ---------------------------------------------------------
    for attempt in range(1, max_retries + 1):
        try:
            bars = await ib.reqHistoricalDataAsync(
                contract=contract,
                endDateTime=endDateTime,   # <--- this is the cutoff
                durationStr=duration,         # <--- goes backwards from endDate
                barSizeSetting=ib_timeframe,
                whatToShow=what_to_show, # or 'MIDPOINT', 'ASK', 'BID', 'ADJUSTED_LAST'. TRADES is typical for stocks but is slowest. go for MIDPOINT for faster data if no need to bars and volume
                useRTH=use_RTH, # Use Regular Trading Hours # useRTH=True = IB trims bars, extra server work → slower.
                keepUpToDate=False,
            )
            break  # success

        except Exception as e:
            logger.error(f"[get_stock_historical_data] @@@@ Historical request failed (attempt {attempt}/{max_retries}): {e}")

            if attempt == max_retries:
                logger.error("[get_stock_historical_data] Max retries reached. Reraising.")
                raise

            await asyncio.sleep(retry_delay)
            retry_delay *= 1.5  # exponential backoff

    # Convert results → DataFrame
    logger.info(f"[get_stock_historical_data] Fetched {len(bars)} bars for {symbol}")
    df = util.df(bars)
    if df is None:
        logger.warning(f"[get_stock_historical_data] @@@@@@ get_stock_historical_data: df is None for symbol: {symbol}")
        return pd.DataFrame()
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    logger.info(f"[get_stock_historical_data] , {symbol}, {time_frame}, df['date'].min(): {df['date'].min()}, df['date'].max(): {df['date'].max()}")
    if print_last_few_rows > 0:
        logger.info(f"[get_stock_historical_data] , {symbol}, {time_frame}, df:\n {df[-3:].to_markdown()}")

    # df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert("America/New_York")

    # df["date"] = (
    #     pd.to_datetime(df["date"], utc=True)
    #     .dt.tz_convert("America/New_York")
    #     .dt.tz_localize(None)
    # )

    return df


async def get_option_historical_data(
    ib: IB,
    symbol: str,
    expiry: str,
    strike: float,
    right: str,
    *,
    end_date: str | None = None,  # <--- kept  "" means "now"
    duration: str = "2 D",       # e.g. "1 D", "2 D", "1 W", "1 M"
    time_frame: str = "5 mins", # "1 min", "5 mins", "1 hour", "1 day", ...
    whatToShow: str = "TRADES",     # "TRADES", "MIDPOINT", "BID", "ASK", ...
    useRTH: bool = True,
    formatDate: int = 1,            # 1 => string dates, 2 => unix time
    keepUpToDate: bool = False,
    exchange: str = "SMART",
    currency: str = "USD",
    multiplier: str = "100",
) -> List[BarData]:
    """
    Async fetch historical bars for a specific option contract.
    Returns list of BarData.
    """
    contract = await  ib_contract.get_option_contract_cached(ib, symbol=symbol, expiry=expiry, strike=strike, right=right)
    if contract is None:
        logger.error(f"@@@@@ get_option_historical_data: Could not get contract for {symbol} {expiry} {strike} {right}")
        return pd.DataFrame()

    if time_frame not in BAR_SIZE_MAP:
        raise ValueError(f"Invalid timeframe '{time_frame}'. Use: 1D, 1H, 5M, 1M")
    ib_timeframe = BAR_SIZE_MAP[time_frame]

    # user did not specify duration → use smart default
    if duration is None:
        duration = DEFAULT_DURATION_MAP[ib_timeframe]

    # Set IBKR endDateTime
    if end_date:   # should be in 'YYYYMMDD' format
        end_date = end_date.replace('-', '')  # remove dashes if any
        end_date = f"{end_date} 23:59:59"
    else:
        end_date = ""   # means "now"


    bars = await ib.reqHistoricalDataAsync(
        contract,
        endDateTime=end_date,
        durationStr=duration,
        barSizeSetting=ib_timeframe,
        whatToShow=whatToShow,
        useRTH=useRTH,
        formatDate=formatDate,
        keepUpToDate=keepUpToDate,
    )

    logger.info(f"Fetched {len(bars)} bars for {symbol} {expiry} {strike} {right}")
    df = util.df(bars)
    if df is None:
        logger.warning(f"@@@@@@ get_stock_historical_data: df is None for {symbol} {expiry} {strike} {right}")
        return pd.DataFrame()
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    logger.info(f"get_option_historical_data, {symbol}, df['date'].min(): {df['date'].min()}, df['date'].max(): {df['date'].max()}")
    logger.info(f"get_option_historical_data, df:\n {df[:3].to_markdown()}")
    logger.info(f"get_option_historical_data, df:\n {df[-3:].to_markdown()}")

    # df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert("America/New_York")

    # df["date"] = (
    #     pd.to_datetime(df["date"], utc=True)
    #     .dt.tz_convert("America/New_York")
    #     .dt.tz_localize(None)
    # )

    return df

