import numpy as np
import math
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def df_to_stream_payload(
        parent_df,
        child_df,
        key_col="symbol"):
    """
    [
      {
        "symbol": "SPX",
        "bid": 12.3,
        "ask": 12.5,
        "records": [{...}, {...}]
      },
      {
        "symbol": "NDX",
        "bid": 8.1,
        "ask": 8.4,
        "records": [{...}]
      }
    ]
    :param parent_df:
    :param child_df:
    :param key_col:
    :param child_key:
    :return:
    """

    logger.info(f"df_to_stream_payload START - key_col: {key_col}")
    logger.info(f"parent_df type: {type(parent_df)}, child_df type: {type(child_df)}")

    # ---- clean both dfs ----
    def clean(df):
        logger.info(f"clean() START - input type: {type(df)}, is None: {df is None}")

        # Guard: return early if None or empty
        if df is None:
            logger.info("clean() - df is None, returning None")
            return df

        if isinstance(df, pd.DataFrame) and df.empty:
            logger.info("clean() - df is empty DataFrame, returning empty")
            return df

        if not isinstance(df, pd.DataFrame):
            logger.warning(f"clean() - df is not DataFrame, it's {type(df)}, returning as-is")
            return df

        logger.info(f"clean() - df shape before clean: {df.shape}")

        result = (
            df.replace({np.nan: None})
            .map(lambda x: x.item() if hasattr(x, "item") else x)
        )

        logger.info(f"clean() - df shape after clean: {result.shape}")
        return result

    logger.info("Calling clean() on parent_df")
    parent_df = clean(parent_df)

    logger.info("Calling clean() on child_df")
    child_df = clean(child_df)

    # ---- group child records by key ----
    child_map = {}
    logger.info(
        f"Checking child_df - is DataFrame: {isinstance(child_df, pd.DataFrame)}, empty: {isinstance(child_df, pd.DataFrame) and child_df.empty}")

    if isinstance(child_df, pd.DataFrame) and not child_df.empty:
        logger.info(f"child_df columns: {list(child_df.columns)}")
        logger.info(f"key_col '{key_col}' in child_df.columns: {key_col in child_df.columns}")

        if key_col in child_df.columns:
            logger.info(f"Grouping child_df by '{key_col}'")
            try:
                child_map = (
                    child_df
                    .groupby(key_col)
                    .apply(lambda g: g.drop(columns=[key_col]).to_dict("records"))
                    .to_dict()
                )
                logger.info(f"child_map created with {len(child_map)} groups")
                logger.info(f"child_map keys: {list(child_map.keys())}")
            except Exception as e:
                logger.error(f"Error during groupby: {e}", exc_info=True)
                child_map = {}
        else:
            logger.warning(f"key_col '{key_col}' NOT found in child_df columns")
    else:
        logger.warning("child_df is None, not a DataFrame, or empty - skipping groupby")

    # ---- build final payload ----
    payload = []
    logger.info(
        f"Checking parent_df - is DataFrame: {isinstance(parent_df, pd.DataFrame)}, empty: {isinstance(parent_df, pd.DataFrame) and parent_df.empty}")

    if isinstance(parent_df, pd.DataFrame) and not parent_df.empty:
        logger.info(f"parent_df shape: {parent_df.shape}")
        logger.info(f"parent_df columns: {list(parent_df.columns)}")
        logger.info(f"Processing {len(parent_df)} rows from parent_df")

        for idx, row in enumerate(parent_df.to_dict("records")):
            key = row.get(key_col)
            logger.debug(f"Row {idx}: key='{key}'")

            row["records"] = child_map.get(key, [])
            logger.debug(f"Row {idx}: attached {len(row['records'])} child records")

            payload.append(row)
    else:
        logger.warning("parent_df is None, not a DataFrame, or empty - no rows to process")

    logger.info(f"df_to_stream_payload COMPLETE - payload has {len(payload)} records")
    return payload


def sanitize_for_json(obj, nan_value=None):
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v, nan_value) for k, v in obj.items()}

    if isinstance(obj, list):
        return [sanitize_for_json(v, nan_value) for v in obj]

    if isinstance(obj, float):
        return None if math.isnan(obj) or math.isinf(obj) else obj

    if isinstance(obj, np.floating):
        return None if np.isnan(obj) or np.isinf(obj) else float(obj)

    return obj


def convert_df_to_dic_for_stream(df):
    return df.to_dict(orient="records")
