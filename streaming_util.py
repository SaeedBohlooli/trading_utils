import numpy as np
import math
def df_to_stream_payload(
    parent_df,
    child_df,
    key_col="symbol"):

#     """
#     [
#   {
#     "symbol": "SPX",
#     "bid": 12.3,
#     "ask": 12.5,
#     "records": [{...}, {...}]
#   },
#   {
#     "symbol": "NDX",
#     "bid": 8.1,
#     "ask": 8.4,
#     "records": [{...}]
#   }
# ]
#     :param parent_df:
#     :param child_df:
#     :param key_col:
#     :param child_key:
#     :return:
#     """
#
#     # ---- clean both dfs ----
#
#         # ---- clean both dfs ----
        def clean(df):
            return (
                df.replace({np.nan: None})
                .applymap(lambda x: x.item() if hasattr(x, "item") else x)
            )

        parent_df = clean(parent_df)
        child_df = clean(child_df)

        # ---- group child records by key ----
        child_map = (
            child_df
            .groupby(key_col)
            .apply(lambda g: g.drop(columns=[key_col]).to_dict("records"))
            .to_dict()
        )

        # ---- build final payload ----
        payload = []
        for row in parent_df.to_dict("records"):
            key = row[key_col]
            row["records"] = child_map.get(key, [])
            payload.append(row)

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