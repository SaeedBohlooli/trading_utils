import logging
from ib_async.contract import Index
import asyncio
from trading_utils import *

logger = logging.getLogger(__name__)

async def get_current_price_SPX(ib):

    if global_state.ib_config.get('fall_back', False):
        return generate_fake_spx_price()

    c = Index("SPX", exchange="CBOE")
    await ib.qualifyContractsAsync(c)

    ticker = ib.reqMktData(c)
    await asyncio.sleep(0.5)

    print("Bid:", ticker.bid)
    print("Ask:", ticker.ask)
    print("Last:", ticker.last)
    return ticker.last