import os.path

import pandas as pd
import logging


df_file_map = {
    "ib_on_fill_fill_df": f"85-ib_on_fill_fill_df.csv",
    "ib_on_fill_trade_df": f"86-ib_on_fill_trade_df.csv",
    "ib_portfolio_df": f"87-ib_portfolio_df.csv",
    "ib_commission_df": f"88-ib_commission_df.csv",
    "ib_commission_fill_df": f"89-ib_commission_fill_df.csv",
    "ib_commission_trade_df": f"90-ib_commission_trade_df.csv",
    "ib_execution_df": f"91-ib_execution_df.csv",
}

import datetime
from ib_insync import *

logger = logging.getLogger(__name__)
import sys
sys.path.insert(0, f'../')

from trading_utils import global_state
from trading_utils import df_utils
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



def save_ib_dfs(portfolio_dir, ib):

    generate_ib_execution_df(ib) # save in the global_state

    for df_name, file_name in df_file_map.items():

        df = getattr(global_state, df_name, None)
        if df is not None:
            file_path = f"{portfolio_dir}/{file_name}"
            df_utils.save_df_to_csv_a_tabular(df, file_path=file_path, mode='a')


    if False:
        flatten_on_fill_fill_df_file_path = f"{portfolio_dir}/85-ib_on_fill_fill_df.csv"
        df_utils.save_df_to_csv_a_tabular(global_state.ib_on_fill_fill_df, file_path=flatten_on_fill_fill_df_file_path, mode='a')
        flatten_on_fill_trade_df_file_path = f"{portfolio_dir}/86-ib_on_fill_trade_df.csv"
        df_utils.save_df_to_csv_a_tabular(global_state.ib_on_fill_trade_df, file_path=flatten_on_fill_trade_df_file_path, mode='a')
        ib_portfolio_df_file_path = f"{portfolio_dir}/87-ib_portfolio_df.csv"
        df_utils.save_df_to_csv_a_tabular(global_state.ib_portfolio_df, file_path=ib_portfolio_df_file_path, mode='a')
        ib_commission_df_file_path = f"{portfolio_dir}/88-ib_commission_df.csv"
        df_utils.save_df_to_csv_a_tabular(global_state.ib_commission_df, file_path=ib_commission_df_file_path, mode='a')
        ib_commission_fill_df_file_path = f"{portfolio_dir}/89-ib_commission_fill_df.csv"
        df_utils.save_df_to_csv_a_tabular(global_state.ib_commission_fill_df, file_path=ib_commission_fill_df_file_path, mode='a')
        ib_commission_trade_df_file_path = f"{portfolio_dir}/90-ib_commission_trade_df.csv"
        df_utils.save_df_to_csv_a_tabular(global_state.ib_commission_trade_df, file_path=ib_commission_trade_df_file_path, mode='a')
        ib_execution_df_file_path = f"{portfolio_dir}/91-ib_execution_df.csv"
        df_utils.save_df_to_csv_a_tabular(global_state.ib_execution_df, file_path=ib_execution_df_file_path,mode='a')

    return
def generate_ib_execution_df(ib):
    # IB has only for 24 hrours ... so we need to save it ofter ...

    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=3)

    exec_filter = ExecutionFilter(
        time=yesterday.strftime('%Y%m%d %H:%M:%S')  # format: YYYYMMDD HH:MM:SS
    )
    execs = ib.reqExecutions(exec_filter)
    i = 0

    for trade in execs:
        i = i + 1
        if i < 2:
            logger.info(f"generate_ib_execution_df(), trade: {trade}")

        flatten_dic = flatten(trade)
        logger.debug(f"generate_ib_execution_df, flatten :{flatten_dic}")
        global_state.ib_execution_df = pd.concat([global_state.ib_execution_df, pd.DataFrame([flatten_dic])], ignore_index=True)
    return global_state.ib_execution_df


def test_me():
    logger.info("I am in test_me")
    logger.info(f"global_state: {global_state.application_state}")

    print("I am in test log")
    global_state.application_state = "SET IN THE UTILS ..."


def load_ib_df(portfolio_dir, df_name='ib_on_fill_fill_df'):
    df_file_name = df_file_map.get(df_name, None)
    if df_file_name is None:
        return  pd.DataFrame()
    file_path = f"{portfolio_dir}/{df_file_name}"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        return df
    return pd.DataFrame()
