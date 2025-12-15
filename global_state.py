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


symbol_to_conid = {}        # Maps “SPX” → 416904
conid_to_symbol = {}        # Reverse lookup
quote_cache = {}

# Optional: define a helper for safe updates
def update_quote(con_id, data):
    quote_cache[con_id] = data

# ----------------------------------------------------
# GLOBAL contract cache for historical / live requests
# ----------------------------------------------------
contract_cache = {}     # symbol -> fully qualified contract object


option_contract_cache = {}  # symbol+expiry+strike+right -> fully qualified contract object"
