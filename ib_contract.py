from ib_async import IB, Contract, Stock, Option
import logging
from trading_utils import global_state

logger = logging.getLogger(__name__)


async def get_cached_contract(ib: IB, symbol: str) -> Contract:
    """
    Return a fully-qualified IB contract for `symbol`, using global_state.contract_cache.
    - First call for a symbol: creates + qualifies + caches the contract.
    - Next calls: return from cache (no IB round-trip, much faster).
    """

    cache = global_state.contract_cache

    # 1) If already cached → return it immediately
    if symbol in cache:
        logger.info(f"[CONTRACT_CACHE] Returning cached contract for symbol={symbol}")
        return cache[symbol]

    logger.info(f"[CONTRACT_CACHE] Qualifying new contract for symbol={symbol}")

    contract = Stock(symbol, "SMART", "USD")

    # Qualify once (async)
    qualified = await ib.qualifyContractsAsync(contract)
    if not qualified:
        raise RuntimeError(f" @@@ Could not qualify contract for symbol={symbol}")

    qualified_contract = qualified[0]

    # 3) Update reverse mappings & cache
    global_state.contract_cache[symbol] = qualified_contract

    if qualified_contract.conId:
        global_state.symbol_to_conid[symbol] = qualified_contract.conId
        global_state.conid_to_symbol[qualified_contract.conId] = symbol

    logger.info(
        f"[CONTRACT_CACHE] Cached contract for {symbol}, conId={qualified_contract.conId}"
    )

    return qualified_contract



def create_option_contract(symbol=None, expiry=None,strike=None, right=None, trading_class=None, exchange=None):
    contract = Option(
        symbol=symbol,
        lastTradeDateOrContractMonth=expiry,
        strike=strike,
        right=right,
        exchange=exchange,
        tradingClass=trading_class
    )
    return contract
