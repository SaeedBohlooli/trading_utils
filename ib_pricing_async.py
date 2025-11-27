import logging
import asyncio
from trading_utils import *
from trading_utils import global_state
from ib_async import *
import pandas as pd
logger = logging.getLogger(__name__)
import time
async def get_current_price_SPX(ib, symbol='SPX', max_retries=3, retry_delay=0.5):
    #
    # if global_state.ib_config.get('fall_back', False):
    #     return generate_fake_spx_price()

    for attempt in range(1, max_retries + 1):
        # spx = Index(conId=416904, symbol='SPX', exchange='CBOE', currency='USD')
        spx = Index(symbol='SPX', exchange='CBOE', currency='USD')
        # spx = Contract()
        # spx.conId = 416904
        # spx.secType = "IND"
        # spx.symbol = "SPX"
        # spx.exchange = "CBOE"
        # spx.currency = "USD"

        details = await ib.qualifyContractsAsync(spx)
        logger.info(f"get_current_price_SPX, symbol: {symbol}, details: {details}")
        # logger.info(details[0].contract.conId)

        ticker = ib.reqMktData(spx, '', False, False)
        await asyncio.sleep(1)
        logger.info(f"get_current_price_SPX, symbol: {symbol}, last: {ticker.last},  bid:, {ticker.bid},  ask:{ticker.ask}")

        price = ticker.last
        if price is not None and not (pd.isna(price) or math.isnan(price)):
            if attempt > 1:
                logger.warning(f"@@ succefull try after attempt: {attempt}, symbol: {symbol}")
            return price
        else:
            logger.warning(
                f"@@@ get_current_price_for_contract,{symbol}, price is nan, try again ... attempt: {attempt}")
            await asyncio.sleep(retry_delay)
        return price


async def qualify_contracts_v_1(ib, contracts):
    logger.info(f"qualify_contracts_v_1")
    # if global_state.ib_config.get('fall_back', '1 == 2'):
    #     return contracts

    # The asterisk (*) is crucial because it "unpacks" the list, sending each individual contract within the list as a separate argument to the qualifyContractsAsync method. This will resolve the AttributeError because the method will then correctly receive contract objects with an includeExpired attribute, rather than an unprocessable list.

    qualified_contracts = await ib.qualifyContractsAsync(*contracts)
    logger.info(f"qualify_contracts, qualified: {qualified_contracts}")
    return qualified_contracts


async def qualify_contracts(ib, contracts):

    logger.info(f"qualify_contracts, contracts: {contracts}")

    # Schedule each qualification in parallel
    tasks = [ib.qualify_contracts(c) for c in contracts]

    # Run all IBKR requests concurrently
    results = await asyncio.gather(*tasks, return_exceptions=False)

    qualified = []
    for res in results:
        if res:
            # res is a list: [ContractDetails.contract]
            qualified.append(res[0])
        else:
            logger.warning("Failed to qualify a contract")

    return qualified



async def get_quote_for_contracts(ib, contracts):


    # if global_state.ib_config.get('fall_back', '1 == 2'):
    #     data_list = []
    #     for contract in contracts:
    #         data = {
    #             "symbol": contract.symbol,
    #             "expiry": contract.lastTradeDateOrContractMonth,
    #             "strike": contract.strike,
    #             "right": contract.right,
    #             "bid": generate_fake_price(10),
    #             "ask": generate_fake_price(10),
    #             "last": generate_fake_price(10),
    #         }
    #
    #         data_list.append(data)
    #
    #     df = pd.DataFrame(data_list)
    #
    #     logger.info(f"get_quote_for_contracts(): \n{df.to_markdown()}")
    #
    #     return df

    logger.info(f"get_quote_for_contracts, calling ib.reqTickers started  ... ")
    start_time = time.time()
    tickers = await ib.reqTickersAsync(*contracts)
    end_time = time.time()
    run_spend_time = round(end_time - start_time, 2)

    logger.info(f"get_quote_for_contracts, calling ib.reqTickers finished, run_spend_time: {run_spend_time}  ...")
    # Build DataFrame
    data_list = []
    for t in tickers:
        logger.info(f"get_quote_for_contracts: t.contract: {t.contract}")
        # t.contract: Option(conId=807843628, symbol='SPX', lastTradeDateOrContractMonth='20251128', strike=6845.0, right='C', multiplier='100', exchange='CBOE', currency='USD', localSymbol='SPXW  251128C06845000', tradingClass='SPXW')
        data = {
            "symbol": t.contract.symbol,
            "local_symbol": t.contract.localSymbol,
            "expiry": t.contract.lastTradeDateOrContractMonth,
            "strike": t.contract.strike,
            "con_id": t.contract.conId,
            "right": t.contract.right,
            "bid": t.bid,
            "ask": t.ask,
            "last": t.last,
        }

        data_list.append(data)

    df = pd.DataFrame(data_list)

    logger.info(f"get_quote_for_contracts(): \n{df.to_markdown()}")

    return df
