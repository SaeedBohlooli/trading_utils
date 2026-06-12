from ib_async import IB, Contract, Stock, Option, Future, Index
import logging
from trading_utils import global_state

logger = logging.getLogger(__name__)


async def get_cached_contract(ib: IB, symbol: str, contract_month=None) -> Contract:
    """
    Return a fully-qualified IB contract for `symbol`, using global_state.contract_cache.
    - First call for a symbol: creates + qualifies + caches the contract.
    - Next calls: return from cache (no IB round-trip, much faster).
    """

    cache = global_state.contract_cache

    # 1) If already cached - > return it immediately
    if symbol in cache:
        logger.info(f"[get_cached_contract] Returning cached contract for symbol={symbol}")
        return cache[symbol]

    logger.info(f"[get_cached_contract] Qualifying new contract for symbol={symbol}, contract_month: {contract_month}")

    if contract_month is not None:
        contract = Future(symbol, contract_month, 'CME')
    elif symbol == 'SPX':
        contract = Index(symbol=symbol, exchange="CBOE", currency="USD")
    else:
        contract = Stock(symbol, "SMART", "USD")

    # Qualify once (async)
    qualified = await ib.qualifyContractsAsync(contract)
    if not qualified:
        raise RuntimeError(f"[get_cached_contract] @@@ Could not qualify contract for symbol={symbol}")

    qualified_contract = qualified[0]

    # 3) Update reverse mappings & cache
    global_state.contract_cache[symbol] = qualified_contract

    if qualified_contract.conId:
        global_state.symbol_to_conid[symbol] = qualified_contract.conId
        global_state.conid_to_symbol[qualified_contract.conId] = symbol
        global_state.conid_to_contract_cache[qualified_contract.conId] = qualified_contract

    logger.info(f"[get_cached_contract] Cached contract for {symbol}, conId={qualified_contract.conId}"
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

async def get_option_contract_cached(ib, symbol=None, expiry=None,strike=None, right=None, trading_class=None, exchange=None):

    key = (symbol, expiry, int(strike), right.upper())
    cache = global_state.option_contract_cache

    # Cache hit
    res = cache.get(key)
    if res is not None:
        return cache[key]

    logger.info(f"[get_option_contract_cached] Cache miss for key: {key}, creating and qualifying new contract.")

    if trading_class is None:
        trading_class = "SPXW" if symbol == "SPX" else symbol
    if exchange is None:
        exchange = "CBOE" if symbol == "SPX" else "SMART"

    # Cache miss - > create new contract
    contract = Option(
        symbol=symbol,
        lastTradeDateOrContractMonth=expiry,
        strike=strike,
        right=right,
        exchange=exchange,
        tradingClass=trading_class,
    )
    # Qualify once (async)

    qualified = await ib.qualifyContractsAsync(contract)

    qc = qualified[0]
    if qc is None:
        logger.warning(f"[get_option_contract_cached] @@@ Could not qualify contract for symbol={symbol}, key: {key}")
    else:
        cache[key] = qc
        global_state.conid_to_contract_cache[qc.conId] = qc
    return qc

async def get_option_contract_by_conid(ib, con_id):

    if con_id in global_state.conid_to_contract_cache:
        return global_state.conid_to_contract_cache[con_id]

    contract = Contract(conId=con_id)
    qualified = await ib.reqContractDetailsAsync(contract)
    if not qualified:
        logger.error(f" @@@ [get_option_contract_by_conid], Could not qualify contract for conid={con_id}")
        return None
    qc = qualified[0]
    logger.info(f"[get_option_contract_by_conid] Qualified contract for conid= {con_id}, qc: {qc}" )
    qc = qc.contract   # the object is ContractDetails, we take contract field
    global_state.conid_to_contract_cache[con_id] = qc

    return qc

async def get_nearest_future_contract_month(ib, symbol="MNQ", exchange='CME'):
    logger.info(f"[get_nearest_future_contract_month] Finding first contract month for future symbol={symbol} on exchange={exchange} ...")

    contract = Future(symbol=symbol, exchange=exchange)
    details = await ib.reqContractDetailsAsync(contract)
    contract_months = []
    for d in details:
        c = d.contract
        contract_months.append(c.lastTradeDateOrContractMonth)
        # logger.info(f"[get_nearest_future_contract_month] localSymbol: {c.localSymbol}")
        # logger.info(f"[get_nearest_future_contract_month] contractMonth:{c.lastTradeDateOrContractMonth}  , type: {type(c.lastTradeDateOrContractMonth)}")

    contract_months = sorted(contract_months)
    logger.info(f"[get_nearest_future_contract_month] sorted, contract_months: {contract_months}")
    if len(contract_months) > 1:
        return contract_months[0][:6]
    else:
        return None