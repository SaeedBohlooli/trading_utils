import logging
from datetime import datetime
from itertools import count

import pytz

from ib_async import IB, Stock

logger = logging.getLogger(__name__)


async def calculate_market_session(ib: IB) -> dict:
    """
    Calculates today's US equity market session using AAPL.
    Called ONCE per trading day.
    """
    contract = Stock("AAPL", "SMART", "USD")
    await ib.qualifyContractsAsync(contract)
    details = await ib.reqContractDetailsAsync(contract)

    logger.debug(f"[MarketSession] details: {details}")
    # 2025-12-14 11:14:11,368 - trading_utils.market_session - INFO - [MarketSession] details:
    # [ContractDetails(contract=Contract(secType='STK', conId=265598, symbol='AAPL', exchange='SMART', primaryExchange='ISLAND', currency='USD', localSymbol='AAPL', tradingClass='NMS'), marketName='NMS', minTick=0.01, orderTypes='ACTIVETIM,AD,ADDONT,ADJUST,ALERT,ALGO,ALLOC,AON,AVGCOST,BASKET,BENCHPX,CASHQTY,COND,CONDORDER,DARKONLY,DARKPOLL,DAY,DEACT,DEACTDIS,DEACTEOD,DIS,DUR,GAT,GTC,GTD,GTT,HID,IBKRATS,ICE,IMB,IOC,LIT,LMT,LOC,MIDPX,MIT,MKT,MOC,MTL,NGCOMB,NODARK,NONALGO,OCA,OPG,OPGREROUT,PEGBENCH,PEGMID,POSTATS,POSTONLY,PREOPGRTH,PRICECHK,REL,REL2MID,RELPCTOFS,RPI,RTH,SCALE,SCALEODD,SCALERST,SIZECHK,SMARTSTG,SNAPMID,SNAPMKT,SNAPREL,STP,STPLMT,SWEEP,TRAIL,TRAILLIT,TRAILLMT,TRAILMIT,WHATIF', validExchanges='SMART,AMEX,NYSE,CBOE,PHLX,ISE,CHX,ARCA,ISLAND,DRCTEDGE,BEX,BATS,EDGEA,BYX,IEX,EDGX,FOXRIVER,PEARL,NYSENAT,LTSE,MEMX,IBEOS,OVERNIGHT,TPLUS0,PSX,T24X', priceMagnifier=1, underConId=0, longName='APPLE INC', contractMonth='', industry='Technology', category='Computers', subcategory='Computers', timeZoneId='US/Eastern', tradingHours='20251214:CLOSED;20251215:0400-20251215:2000;20251216:0400-20251216:2000;20251217:0400-20251217:2000;20251218:0400-20251218:2000;20251219:0400-20251219:2000', liquidHours='20251214:CLOSED;20251215:0930-20251215:1600;20251216:0930-20251216:1600;20251217:0930-20251217:1600;20251218:0930-20251218:1600;20251219:0930-20251219:1600', evRule='', evMultiplier=0, mdSizeMultiplier=1, aggGroup=1, underSymbol='', underSecType='', marketRuleIds='26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26', secIdList=[TagValue(tag='ISIN', value='US0378331005')], realExpirationDate='', lastTradeTime='', stockType='COMMON', minSize=0.0001, sizeIncrement=0.0001, suggestedSizeIncrement=100.0, cusip='', ratings='', descAppend='', bondType='', couponType='', callable=False, putable=False, coupon=0, convertible=False, maturity='', issueDate='', nextOptionDate='', nextOptionType='', nextOptionPartial=False, notes='')]

    details = details[0]
    logger.info(f"[MarketSession] Trading hours: {details.tradingHours}, Timezone: {details.timeZoneId}, details: {details}")

    # 2025-12-14 11:12:15,196 - trading_utils.market_session - INFO - [MarketSession] Trading hours:
    # 20251214:CLOSED;20251215:0400-20251215:2000;20251216:0400-20251216:2000;20251217:0400-20251217:2000;20251218:0400-20251218:2000;20251219:0400-20251219:2000,
    # Timezone: US/Eastern,
    # details: ContractDetails(contract=Contract(secType='STK', conId=265598, symbol='AAPL', exchange='SMART', primaryExchange='ISLAND', currency='USD', localSymbol='AAPL', tradingClass='NMS'), marketName='NMS', minTick=0.01, orderTypes='ACTIVETIM,AD,ADDONT,ADJUST,ALERT,ALGO,ALLOC,AON,AVGCOST,BASKET,BENCHPX,CASHQTY,COND,CONDORDER,DARKONLY,DARKPOLL,DAY,DEACT,DEACTDIS,DEACTEOD,DIS,DUR,GAT,GTC,GTD,GTT,HID,IBKRATS,ICE,IMB,IOC,LIT,LMT,LOC,MIDPX,MIT,MKT,MOC,MTL,NGCOMB,NODARK,NONALGO,OCA,OPG,OPGREROUT,PEGBENCH,PEGMID,POSTATS,POSTONLY,PREOPGRTH,PRICECHK,REL,REL2MID,RELPCTOFS,RPI,RTH,SCALE,SCALEODD,SCALERST,SIZECHK,SMARTSTG,SNAPMID,SNAPMKT,SNAPREL,STP,STPLMT,SWEEP,TRAIL,TRAILLIT,TRAILLMT,TRAILMIT,WHATIF', validExchanges='SMART,AMEX,NYSE,CBOE,PHLX,ISE,CHX,ARCA,ISLAND,DRCTEDGE,BEX,BATS,EDGEA,BYX,IEX,EDGX,FOXRIVER,PEARL,NYSENAT,LTSE,MEMX,IBEOS,OVERNIGHT,TPLUS0,PSX,T24X', priceMagnifier=1, underConId=0, longName='APPLE INC', contractMonth='', industry='Technology', category='Computers', subcategory='Computers', timeZoneId='US/Eastern', tradingHours='20251214:CLOSED;20251215:0400-20251215:2000;20251216:0400-20251216:2000;20251217:0400-20251217:2000;20251218:0400-20251218:2000;20251219:0400-20251219:2000', liquidHours='20251214:CLOSED;20251215:0930-20251215:1600;20251216:0930-20251216:1600;20251217:0930-20251217:1600;20251218:0930-20251218:1600;20251219:0930-20251219:1600', evRule='', evMultiplier=0, mdSizeMultiplier=1, aggGroup=1, underSymbol='', underSecType='', marketRuleIds='26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26', secIdList=[TagValue(tag='ISIN', value='US0378331005')], realExpirationDate='', lastTradeTime='', stockType='COMMON', minSize=0.0001, sizeIncrement=0.0001, suggestedSizeIncrement=100.0, cusip='', ratings='', descAppend='', bondType='', couponType='', callable=False, putable=False, coupon=0, convertible=False, maturity='', issueDate='', nextOptionDate='', nextOptionType='', nextOptionPartial=False, notes='')

    tz = pytz.timezone(details.timeZoneId)

    now = datetime.now(tz)
    today = now.strftime("%Y%m%d")

    for segment in details.tradingHours.split(";"):
        logger.info(f"[MarketSession] Processing segment: {segment}")
        count_clone = segment.count(":")  # 20251214:CLOSED
        if count_clone == 1:
            date, hours = segment.split(":")

            if date != today:
                continue

            if hours == "CLOSED":
                logger.info("[MarketSession] Market CLOSED today")
                return {
                    "date": now.date().isoformat(),
                    "is_open": False,
                    "start": None,
                    "end": None,
                }
        else: # 20251215:0400-20251215:2000

            start_str, end_str = segment.split("-")
            d, start = start_str.split(":")
            d, end   = end_str.split(":")
            start_dt = tz.localize(datetime.strptime(d + start, "%Y%m%d%H%M"))
            end_dt   = tz.localize(datetime.strptime(d + end,   "%Y%m%d%H%M"))

            return {
                "date": now.date().isoformat(),
                "is_open": start_dt <= now <= end_dt,
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
            }

    logger.warning(f"@@@@ [MarketSession] Market session failed {details}")
    return {
        "date": now.date().isoformat(),
        "is_open": False,
        "start": None,
        "end": None,
    }


async def calculate_market_session_orig(ib: IB) -> dict:
    """
    Calculates today's US equity market session using AAPL.
    Called ONCE per trading day.
    """
    contract = Stock("AAPL", "SMART", "USD")
    await ib.qualifyContractsAsync(contract)
    details = await ib.reqContractDetailsAsync(contract)

    logger.debug(f"[MarketSession] details: {details}")
    # 2025-12-14 11:14:11,368 - trading_utils.market_session - INFO - [MarketSession] details:
    # [ContractDetails(contract=Contract(secType='STK', conId=265598, symbol='AAPL', exchange='SMART', primaryExchange='ISLAND', currency='USD', localSymbol='AAPL', tradingClass='NMS'), marketName='NMS', minTick=0.01, orderTypes='ACTIVETIM,AD,ADDONT,ADJUST,ALERT,ALGO,ALLOC,AON,AVGCOST,BASKET,BENCHPX,CASHQTY,COND,CONDORDER,DARKONLY,DARKPOLL,DAY,DEACT,DEACTDIS,DEACTEOD,DIS,DUR,GAT,GTC,GTD,GTT,HID,IBKRATS,ICE,IMB,IOC,LIT,LMT,LOC,MIDPX,MIT,MKT,MOC,MTL,NGCOMB,NODARK,NONALGO,OCA,OPG,OPGREROUT,PEGBENCH,PEGMID,POSTATS,POSTONLY,PREOPGRTH,PRICECHK,REL,REL2MID,RELPCTOFS,RPI,RTH,SCALE,SCALEODD,SCALERST,SIZECHK,SMARTSTG,SNAPMID,SNAPMKT,SNAPREL,STP,STPLMT,SWEEP,TRAIL,TRAILLIT,TRAILLMT,TRAILMIT,WHATIF', validExchanges='SMART,AMEX,NYSE,CBOE,PHLX,ISE,CHX,ARCA,ISLAND,DRCTEDGE,BEX,BATS,EDGEA,BYX,IEX,EDGX,FOXRIVER,PEARL,NYSENAT,LTSE,MEMX,IBEOS,OVERNIGHT,TPLUS0,PSX,T24X', priceMagnifier=1, underConId=0, longName='APPLE INC', contractMonth='', industry='Technology', category='Computers', subcategory='Computers', timeZoneId='US/Eastern', tradingHours='20251214:CLOSED;20251215:0400-20251215:2000;20251216:0400-20251216:2000;20251217:0400-20251217:2000;20251218:0400-20251218:2000;20251219:0400-20251219:2000', liquidHours='20251214:CLOSED;20251215:0930-20251215:1600;20251216:0930-20251216:1600;20251217:0930-20251217:1600;20251218:0930-20251218:1600;20251219:0930-20251219:1600', evRule='', evMultiplier=0, mdSizeMultiplier=1, aggGroup=1, underSymbol='', underSecType='', marketRuleIds='26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26', secIdList=[TagValue(tag='ISIN', value='US0378331005')], realExpirationDate='', lastTradeTime='', stockType='COMMON', minSize=0.0001, sizeIncrement=0.0001, suggestedSizeIncrement=100.0, cusip='', ratings='', descAppend='', bondType='', couponType='', callable=False, putable=False, coupon=0, convertible=False, maturity='', issueDate='', nextOptionDate='', nextOptionType='', nextOptionPartial=False, notes='')]

    details = details[0]
    logger.info(f"[MarketSession] Trading hours: {details.tradingHours}, Timezone: {details.timeZoneId}, details: {details}")

    # 2025-12-14 11:12:15,196 - trading_utils.market_session - INFO - [MarketSession] Trading hours:
    # 20251214:CLOSED;20251215:0400-20251215:2000;20251216:0400-20251216:2000;20251217:0400-20251217:2000;20251218:0400-20251218:2000;20251219:0400-20251219:2000,
    # Timezone: US/Eastern,
    # details: ContractDetails(contract=Contract(secType='STK', conId=265598, symbol='AAPL', exchange='SMART', primaryExchange='ISLAND', currency='USD', localSymbol='AAPL', tradingClass='NMS'), marketName='NMS', minTick=0.01, orderTypes='ACTIVETIM,AD,ADDONT,ADJUST,ALERT,ALGO,ALLOC,AON,AVGCOST,BASKET,BENCHPX,CASHQTY,COND,CONDORDER,DARKONLY,DARKPOLL,DAY,DEACT,DEACTDIS,DEACTEOD,DIS,DUR,GAT,GTC,GTD,GTT,HID,IBKRATS,ICE,IMB,IOC,LIT,LMT,LOC,MIDPX,MIT,MKT,MOC,MTL,NGCOMB,NODARK,NONALGO,OCA,OPG,OPGREROUT,PEGBENCH,PEGMID,POSTATS,POSTONLY,PREOPGRTH,PRICECHK,REL,REL2MID,RELPCTOFS,RPI,RTH,SCALE,SCALEODD,SCALERST,SIZECHK,SMARTSTG,SNAPMID,SNAPMKT,SNAPREL,STP,STPLMT,SWEEP,TRAIL,TRAILLIT,TRAILLMT,TRAILMIT,WHATIF', validExchanges='SMART,AMEX,NYSE,CBOE,PHLX,ISE,CHX,ARCA,ISLAND,DRCTEDGE,BEX,BATS,EDGEA,BYX,IEX,EDGX,FOXRIVER,PEARL,NYSENAT,LTSE,MEMX,IBEOS,OVERNIGHT,TPLUS0,PSX,T24X', priceMagnifier=1, underConId=0, longName='APPLE INC', contractMonth='', industry='Technology', category='Computers', subcategory='Computers', timeZoneId='US/Eastern', tradingHours='20251214:CLOSED;20251215:0400-20251215:2000;20251216:0400-20251216:2000;20251217:0400-20251217:2000;20251218:0400-20251218:2000;20251219:0400-20251219:2000', liquidHours='20251214:CLOSED;20251215:0930-20251215:1600;20251216:0930-20251216:1600;20251217:0930-20251217:1600;20251218:0930-20251218:1600;20251219:0930-20251219:1600', evRule='', evMultiplier=0, mdSizeMultiplier=1, aggGroup=1, underSymbol='', underSecType='', marketRuleIds='26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26', secIdList=[TagValue(tag='ISIN', value='US0378331005')], realExpirationDate='', lastTradeTime='', stockType='COMMON', minSize=0.0001, sizeIncrement=0.0001, suggestedSizeIncrement=100.0, cusip='', ratings='', descAppend='', bondType='', couponType='', callable=False, putable=False, coupon=0, convertible=False, maturity='', issueDate='', nextOptionDate='', nextOptionType='', nextOptionPartial=False, notes='')

    tz = pytz.timezone(details.timeZoneId)

    now = datetime.now(tz)
    today = now.strftime("%Y%m%d")

    for segment in details.tradingHours.split(";"):
        logger.info(f"[MarketSession] Processing segment: {segment}")
        date, hours = segment.split(":")

        if date != today:
            continue

        if hours == "CLOSED":
            logger.info("[MarketSession] Market CLOSED today")
            return {
                "date": now.date().isoformat(),
                "is_open": False,
                "start": None,
                "end": None,
            }

        start, end = hours.split("-")

        start_dt = tz.localize(datetime.strptime(date + start, "%Y%m%d%H%M"))
        end_dt   = tz.localize(datetime.strptime(date + end,   "%Y%m%d%H%M"))

        return {
            "date": now.date().isoformat(),
            "is_open": start_dt <= now <= end_dt,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
        }

    logger.warning(f"@@@@ [MarketSession] Market session failed {details}")
    return {
        "date": now.date().isoformat(),
        "is_open": False,
        "start": None,
        "end": None,
    }
