import pandas as pd
import logging

logger = logging.getLogger(__name__)
def flatten(obj, prefix=''):
    """
    Recursively flatten an object (like Fill, Execution, CommissionReport) into a dict.
    """
    result = {}
    for attr in dir(obj):
        if attr.startswith('_') or callable(getattr(obj, attr)):
            continue
        value = getattr(obj, attr)
        if hasattr(value, '__dict__'):
            # nested object → recurse
            result.update(flatten(value, prefix=f'{prefix}{attr}_'))
        else:
            result[f'{prefix}{attr}'] = value
    return result


def on_commission_report(trade, fill, commission_report):

    flatten_dic = flatten(commission_report)
    global_state.ib_commission_df = pd.concat([global_state.ib_commission_df, pd.DataFrame([flatten_dic])], ignore_index=True)

    flatten_dic = flatten(trade)
    global_state.ib_commission_trade_df = pd.concat([global_state.ib_commission_trade_df, pd.DataFrame([flatten_dic])], ignore_index=True)

    flatten_dic = flatten(fill)
    global_state.ib_commission_fill_df = pd.concat([global_state.ib_commission_fill_df, pd.DataFrame([flatten_dic])], ignore_index=True)

    logger.debug(f"@ on_commission_report, report: {commission_report}")
    return

def on_portfolio_update(item):
    """Update or insert portfolio position."""
    flatten_dic = flatten(item)
    logger.info(f"on_portfolio_update(), flatten :{flatten_dic}")
    global_state.ib_portfolio_df = pd.concat([global_state.ib_portfolio_df, pd.DataFrame([flatten_dic])], ignore_index=True)

    return


def on_fill(trade, fill):

    logger.warning(f'in on_fill, trade: {trade}')
    logger.warning(f'in on_fill, fill: {fill}')
    logger.warning(f'in on_fill, fill.execution.order_id: {fill.execution.orderId}, fill.contract.symbol: {fill.contract.symbol}')

    flatten_dic = flatten(fill)
    logger.info(f":flatten :{flatten_dic}")
    global_state.ib_on_fill_fill_df = pd.concat([global_state.ib_on_fill_fill_df, pd.DataFrame([flatten_dic])], ignore_index=True)

    flatten_dic = flatten(trade)
    logger.info(f":flatten :{flatten_dic}")
    global_state.ib_on_fill_trade_df = pd.concat([global_state.ib_on_fill_trade_df, pd.DataFrame([flatten_dic])], ignore_index=True)

    return
import sys
sys.path.insert(0, f'../')

from trading_utils import global_state
def test_me():
    logger.info("I am in test_me")
    logger.info(f"global_state: {global_state.application_state}")

    print("I am in test log")
    global_state.application_state = "SET IN THE UTILS ..."

