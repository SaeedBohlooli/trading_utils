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
    global ib_commission_df
    global ib_commission_trade_df
    global ib_commission_fill_df

    flatten_dic = flatten(commission_report)
    ib_commission_df = pd.concat([ib_commission_df, pd.DataFrame([flatten_dic])], ignore_index=True)

    flatten_dic = flatten(trade)
    ib_commission_trade_df = pd.concat([ib_commission_trade_df, pd.DataFrame([flatten_dic])], ignore_index=True)

    flatten_dic = flatten(fill)
    ib_commission_fill_df = pd.concat([ib_commission_fill_df, pd.DataFrame([flatten_dic])], ignore_index=True)

    logger.debug(f"@ on_commission_report, report: {commission_report}")
    return

def on_portfolio_update(item):
    """Update or insert portfolio position."""
    global ib_portfolio_df
    flatten_dic = flatten(item)
    logger.info(f"on_portfolio_update(), flatten :{flatten_dic}")
    ib_portfolio_df = pd.concat([ib_portfolio_df, pd.DataFrame([flatten_dic])], ignore_index=True)

    return


def on_fill(trade, fill):
    global on_fill_fill_df
    global on_fill_trade_df

    logger.warning(f'in on_fill, trade: {trade}')
    logger.warning(f'in on_fill, fill: {fill}')
    logger.warning(f'in on_fill, fill.execution.order_id: {fill.execution.orderId}, fill.contract.symbol: {fill.contract.symbol}')

    flatten_dic = flatten(fill)
    logger.info(f":flatten :{flatten_dic}")
    on_fill_fill_df = pd.concat([on_fill_fill_df, pd.DataFrame([flatten_dic])], ignore_index=True)

    flatten_dic = flatten(trade)
    logger.info(f":flatten :{flatten_dic}")
    on_fill_trade_df = pd.concat([on_fill_trade_df, pd.DataFrame([flatten_dic])], ignore_index=True)

    return


def test_log():
    logger.info("I am in test_log")
    print("I am in test log")


