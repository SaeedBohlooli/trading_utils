import logging
import pandas as pd
from ib_insync import util
import sys
import time
sys.path.insert(0, f'../')

from trading_utils import *
from trading_utils import df_utils

logger = logging.getLogger(__name__)

def get_historical_data (ib, contract, historical_days, time_frame):

    bars = ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr=historical_days,
            barSizeSetting=time_frame,
            whatToShow='TRADES',  # for BTC  'AGGTRADES',
            useRTH=False,
            formatDate=1)

    # Create a Pandas dataframe from the historical data
    df = util.df(bars)
    logger.info(f"get_historical_data, len(df): {len(df)}")

    if time_frame != '1 day':
        if df["date"].dt.tz is not None:
            df["date"] = df["date"].dt.tz_convert(None)
            df = df_utils.convert_column_timezone(df, 'date', 'date', from_zone='UTC', to_zone='America/New_York')

    return df

def get_historical_data_from_start_date(ib, contract, start_date, historical_days, time_frame, max_retries=3, retry_delay=5):
    for attempt in range(1, max_retries + 1):
        try:
            bars = ib.reqHistoricalData(
                contract,
                endDateTime=start_date,
                durationStr=historical_days,
                barSizeSetting=time_frame,
                whatToShow='TRADES',  # for BTC  'AGGTRADES',
                useRTH=False,
                formatDate=1)

            # Create a Pandas dataframe from the historical data
            df = util.df(bars)
            logger.info(f"get_historical_data_from_start_date, start_date: {start_date}, len(df): {len(df)}")

            if time_frame != '1 day':
                 # df["date"]=df["date"].dt.tz_convert(None)
                if df["date"].dt.tz is not None:
                    df["date"] = df["date"].dt.tz_convert(None)
                    df = df_utils.convert_column_timezone(df, 'date', 'date', from_zone='UTC', to_zone='America/New_York')

            logger.info(f"get_historical_data_from_start_date, {contract.symbol}, df['date'].min(): {df['date'].min()}, df['date'].max(): {df['date'].max()}")
            return df
        except Exception as e:
            # TODO add
            logger.error(e)
            logger.warning("we going try again")
            time.sleep(retry_delay)
    # if we are here, means that we could not get data
    return pd.DataFrame()
