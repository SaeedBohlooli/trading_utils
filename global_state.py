import pandas as pd
user_input = 'not set yet'


ib_on_fill_fill_df = pd.DataFrame()
ib_on_fill_trade_df = pd.DataFrame()
ib_portfolio_df = pd.DataFrame()
ib_commission_df = pd.DataFrame()
ib_commission_trade_df = pd.DataFrame()
ib_commission_fill_df = pd.DataFrame()
ib_execution_df = pd.DataFrame()
ib_errors_df = pd.DataFrame()

ib_config = {}
# --------------
# Cache dictionaries
# --------------

quote_cache = {}
conid_to_symbol_subscribed_for_quotes = {}  # conid -> symbol for subscribed quotes

symbol_to_conid = {}        # Maps “SPX” → 416904
conid_to_symbol = {}        # Reverse lookup
contract_cache = {}     # symbol -> fully qualified contract object
option_contract_cache = {}  # symbol+expiry+strike+right -> fully qualified contract object"
conid_to_contract_cache = {} # conid -> fully qualified contract object
# Optional: define a helper for safe updates
def update_quote(con_id, data):
    quote_cache[con_id] = data

# ----------------------------------------------------
# GLOBAL contract cache for historical / live requests
# ----------------------------------------------------

symbol_registry = {
    "SPX": {
        "secType": "IND",
        "exchange": "CBOE",
        "currency": "USD",
        "trading_class": "SPXW",
    },
    "MNQ": {
        "secType": "FUT",
        "exchange": "CME",
        "currency": "USD",
    }
}


# This is used to stringify option cache keys for logging or serialization
# This is the error prone part since keys can be tuples
# 2025-12-23 14:22:11,459 - trading_core.data_saver_manager - ERROR - @@@ [DataSaverManager] Unexpected error keys must be str, int, float, bool or None, not tuple

def stringify_option_cache(cache: dict) -> dict:
    out = {}
    for k, v in cache.items():
        if isinstance(k, tuple):
            out["|".join(map(str, k))] = str(v)
        else:
            out[k] = str(v)
    return out


def extract_symbols_from_quote_cache() :
    symbols = []
    for conid in quote_cache.keys():
        symbol = conid_to_symbol.get(conid)
        if symbol:
            symbols.append(symbol)
    return symbols