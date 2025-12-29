import pandas as pd
import logging
import pandas_ta as ta

logger = logging.getLogger(__name__)

#
# ============================================================
# FUNCTION MAP — Using PANDAS_TA (fully aligned with your config)
# DO NOT USE THIS FOR INDICATORS NOT SUPPORTED BY PANDAS_TA
#

FUNCTION_MAP = {
    "sma": lambda df, inputs, **params: ta.sma(df[inputs[0]], **params),
    "ema": lambda df, inputs, **params: ta.ema(df[inputs[0]], **params),

    "atr": lambda df, inputs, **params: ta.atr(
        df[inputs[0]], df[inputs[1]], df[inputs[2]], **params
    ),

    "psar": lambda df, inputs, **params: ta.psar(
        df[inputs[0]], df[inputs[1]], df["close"],
        af=params.get("acceleration_factor", 0.02),
        max_af=params.get("acceleration_limit", 0.2)
    ),

    "macd": lambda df, inputs, **params: ta.macd(
        df[inputs[0]],
        fast=params.get("fast", 12),
        slow=params.get("slow", 26),
        signal=params.get("signal", 9)
    ),

    # add more functions here...
}

def compute_indicator(df, ind_cfg):

    func_name = ind_cfg["function"]
    func = FUNCTION_MAP[func_name]

    inputs = ind_cfg.get("input", [])
    params = ind_cfg.get("params", {})

    return func(df, inputs, **params)


def compute_and_add_indicator(df, indicator_config):

    # Compute the indicator based on the configuration and add the results to the DataFrame.

    result = compute_indicator(df, indicator_config)

    if isinstance(result, pd.Series):
        # wrap into DF to normalize
        result = result.to_frame()
    logger.info(f"compute_and_add_indicators, func: {indicator_config['function']}, result columns: {result.columns}")
    logger.info(f"compute_and_add_indicators, result[-5:0]\n{result[-5:].to_markdown()}")

    for ta_col, out_col in indicator_config["outputs"].items():
        if ta_col not in result.columns:
            logger.error(f"@@@@ compute_and_add_indicators, Missing TA column {ta_col}, {indicator_config}")
            continue

        df[out_col] = result[ta_col].rename(None) # removes the generated column name

    return df