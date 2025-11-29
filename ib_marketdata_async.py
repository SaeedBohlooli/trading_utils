import asyncio
import pandas as pd
from ib_async import *
import logging
logger = logging.getLogger(__name__)

BAR_SIZE_MAP = {
    "1D": "1 day",
    "1H": "1 hour",
    "5m": "5 mins",
    "1m": "1 min",
}

DEFAULT_DURATION_MAP = {
    "1D": "60 D",     # 60 days of daily bars
    "1H": "15 D",     # 15 days of hourly bars
    "5m": "5 D",      # 5 days of 5-min bars
    "1m": "5 D",      # 2 days of 1-min bars
}


async def get_stock_historical_data(
    ib: IB,
    symbol: str,
    time_frame: str,
    end_date: str | None = None,     # <--- kept
    duration: str | None = None,     # <--- optional
    max_retries: int = 5,
    retry_delay: float = 2.0,
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
    if duration is None:
        duration = DEFAULT_DURATION_MAP[time_frame]


    # Prepare contract
    contract = Stock(symbol, "SMART", "USD")
    logger.info(f"Fetching historical data for {symbol}, timeframe: {time_frame}, duration: {duration}, end_date: {end_date}, contract: {contract}")
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
                whatToShow="TRADES",  # or 'MIDPOINT', 'ASK', 'BID', 'ADJUSTED_LAST'
                useRTH=True, # Use Regular Trading Hours
                keepUpToDate=False,
            )
            break  # success

        except Exception as e:
            logger.error(f"@@@@ Historical request failed (attempt {attempt}/{max_retries}): {e}")

            if attempt == max_retries:
                logger.error("[ERROR] Max retries reached. Reraising.")
                raise

            await asyncio.sleep(retry_delay)
            retry_delay *= 1.5  # exponential backoff

    # Convert results → DataFrame
    logger.info(f"Fetched {len(bars)} bars for {symbol}")
    df = util.df(bars)

    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    logger.info(f"get_stock_historical_data, {symbol}, df['date'].min(): {df['date'].min()}, df['date'].max(): {df['date'].max()}")
    logger.info(f"get_stock_historical_data, df:\n {df[-3:].to_markdown()}")

    # df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert("America/New_York")

    # df["date"] = (
    #     pd.to_datetime(df["date"], utc=True)
    #     .dt.tz_convert("America/New_York")
    #     .dt.tz_localize(None)
    # )

    return df
