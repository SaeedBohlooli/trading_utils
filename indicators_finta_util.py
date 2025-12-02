import pandas as pd
import logging
from finta import TA

logger = logging.getLogger(__name__)


# ============================================================
# FUNCTION MAP — Using FINTA (fully aligned with your config)
# https://github.com/peerchemist/finta/blob/master/finta/finta.py
# ============================================================

FUNCTION_MAP = {

    # -------------------------------
    # SMA
    # -------------------------------
    "sma": lambda df, inputs, **params: TA.SMA(
        df,
        column=inputs[0],
        period=params["length"]  # from config
    ),

    # -------------------------------
    # EMA
    # -------------------------------
    "ema": lambda df, inputs, **params: TA.EMA(
        df,
        column=inputs[0],
        period=params["length"]
    ),

    # -------------------------------
    # ATR
    # -------------------------------
    "atr": lambda df, inputs, **params: TA.ATR(
        df,
        period=params["length"]  # config: length: 14
    ),

    # -------------------------------
    # PSAR (SAR in finta)
    # -------------------------------
    "psar": lambda df, inputs, **params: TA.SAR(
        df,
        af=params["af"],
        amax=params["amax"]
    ),

    # -------------------------------
    # MACD (finta returns columns MACD, SIGNAL, HISTOGRAM)
    # -------------------------------
    "macd": lambda df, inputs, **params: TA.MACD(
        df,
        column=inputs[0],
        period_slow=params["slow"],
        period_fast=params["fast"],
        signal=params["signal"]
    ),
}


# ============================================================
# COMPUTE INDICATOR
# ============================================================

def compute_indicator(df, ind_cfg):
    func_name = ind_cfg["function"]
    func = FUNCTION_MAP[func_name]

    inputs = ind_cfg.get("input", [])
    params = ind_cfg.get("params", {})

    return func(df, inputs, **params)


# ============================================================
# ADD INDICATOR TO DF
# ============================================================

def compute_and_add_indicator(df, indicator_config):
    """
    Computes an indicator and attaches outputs to the DataFrame using
    names defined in configuration.
    """

    # Compute indicator
    result = compute_indicator(df, indicator_config)

    # Normalize Series → DataFrame
    if isinstance(result, pd.Series):
        result = result.to_frame()

    logger.info(
        f"compute_and_add_indicator: {indicator_config['function']} to columns: {list(result.columns)}"
    )
    logger.info(f"Last 5 rows:\n{result.tail().to_markdown()}"
    )

    # Output mappings from config
    for ta_col, out_col in indicator_config["outputs"].items():

        # Safety check
        if ta_col not in result.columns:
            logger.error(
                f"@@@@ Missing TA column '{ta_col}' in result.columns: {list(result.columns)} for indicator {indicator_config}"
            )
            continue

        # Assign to DF
        df[out_col] = result[ta_col].rename(None)  # remove source name

    return df
