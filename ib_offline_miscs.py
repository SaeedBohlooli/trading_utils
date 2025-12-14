import pandas as pd
import os.path
import sys

sys.path.insert(0, f'../')
from trading_utils import df_utils
from trading_utils import ib_posttrade
from trading_utils import *

def polish_executions_df(df):

    df["signed_qty"] = df.apply(
        lambda x: x["execution_shares"] if x["execution_side"] == "BOT" else -x["execution_shares"], axis=1)

    # ensure proper datetime
    df["execution_time"] = pd.to_datetime(df["execution_time"])
    df = df.sort_values("execution_time")
    df["cum_position"] = df.groupby("contract_localSymbol")["signed_qty"].cumsum()

    df = df [['contract_symbol', 'contract_strike',  'contract_right', 'execution_shares', 'signed_qty', 'cum_position', 'execution_side',
              'execution_avgPrice', 'execution_price', 'execution_orderRef', 'execution_time', 'contract_localSymbol', 'execution_execId', 'commissionReport_realizedPNL']]

    return df


def extract_trades_with_prices(df):
    trades = []
    for contract_localSymbol, group in df.groupby("contract_localSymbol"):
        group = group.sort_values("execution_time").reset_index(drop=True)
        if 'NVDA' in contract_localSymbol:
            print(f"group, {contract_localSymbol}, group: \n{group.to_markdown()} ")
        print(f"group, {contract_localSymbol}, group: \n{group.to_markdown()} ")

        pos = 0
        open_price = 0
        close_price = 0
        total_cost = 0
        realized_pnl = 0
        open_time = None
        close_time = None
        commission = 0.0
        execution_orderRef = ""
        num_of_orders = 0
        close_price_avg = 0
        total_sell = 0
        sell_qty = 0
        total_buy = 0
        buy_qty = 0
        direction = None

        for _, row in group.iterrows():
            qty = row["signed_qty"]
            price = row["execution_avgPrice"]
            contract_symbol = row["contract_symbol"]
            realized_pnl += row.get("realizedPNL", 0) or 0
            commission += row.get("commission", 0) or 0
            execution_orderRef += " # " + row["execution_orderRef"]
            num_of_orders += 1

            # Detect initial trade direction (buy-first or sell-first)
            if direction is None:
                direction = "long" if qty > 0 else "short"
                open_time = row["execution_time"]

            if direction == "long":
            # -- BUY (open or add)
                if qty > 0:

                    pos += qty
                    total_cost += qty * price
                    if pos == 0:
                        open_price = 0
                    else:
                        open_price = total_cost / pos  # weighted average

                # -- SELL (reduce or close)
                elif qty < 0:
                    sell_qty += abs(qty)
                    close_time = row["execution_time"]
                    close_price = price # this takes latest ..
                    total_sell += price * abs(qty)
                    close_price_avg = total_sell / sell_qty if sell_qty else close_price_avg
                    pos -= abs(qty)
                    total_cost = open_price * pos  # remaining cost
            elif direction == "short":
                if qty < 0:  # opening/add
                    pos += qty  # pos becomes negative
                    total_sell += abs(qty) * price
                    open_price = total_sell / abs(pos)
                elif qty > 0:  # buying to cover
                    buy_qty += qty
                    total_buy += qty * price
                    close_time = row["execution_time"]
                    close_price = price
                    close_price_avg = total_buy / buy_qty if buy_qty else close_price_avg
                    pos += qty  # reduces negative position
        trades.append({
            "contract_localSymbol": contract_localSymbol,
            'num_of_orders': num_of_orders,
            "contract_symbol": contract_symbol,
            "contracts": pos,
            "open_price": round(open_price, 2),
            "close_price": round(close_price, 2),
            "close_price_avg": round(close_price_avg, 2),
            "realized_pnl": round(realized_pnl, 2),
            "commission": round(commission, 2),
            "open_time": open_time,
            "close_time": close_time,
            "execution_orderRef": execution_orderRef,
        })

    trades_df = pd.DataFrame(trades).sort_values("open_time")
    trades_df["open_date"] = trades_df["open_time"].dt.strftime("%Y-%m-%d")

    return trades_df

def do_x(df):
    df['roi'] = round(df['close_price'] / df['open_price'] -1 , 2)
    df["roi"] = df["roi"].fillna(0)

    df = df[['contract_localSymbol', 'num_of_orders', 'contract_symbol', 'open_date', 'open_price', 'close_price_avg', 'roi' , 'realized_pnl', 'commission']]
    return df

def do_y(df):
    summary_df = (
        df.groupby("open_date", as_index=False)
        .agg({
            "realized_pnl": "sum",
            "commission": "sum",
            "roi": "mean"
        })
        .rename(columns={"roi": "avg_roi"}))
    summary_df["net_pnl"] = summary_df["realized_pnl"] - summary_df["commission"]

    return summary_df

def orchestrate(portfolio_id='p250'):
    ib_dir = f'../../portfolios/ib/{portfolio_id}'
    ib_pnl_dir = f'../../portfolios/ib-pnl/{portfolio_id}'



    executions_df = ib_posttrade.load_ib_df(ib_dir, 'ib_on_fill_fill_df')
    executions_df = polish_executions_df(executions_df)

    print('--------------------------')
    print(f"executions_df:\n{df_utils.capture_df_starting_hour_x_on_last_day(executions_df, 'execution_time', '00:00').to_markdown()}")

    commission_df = ib_posttrade.load_ib_df(ib_dir, 'ib_commission_df')
    merged_df = pd.merge(executions_df, commission_df, left_on="execution_execId", right_on="execId", how="left")

    print('--------------------------')
    print(f"merged_df:\n{df_utils.capture_df_starting_hour_x_on_last_day(merged_df, 'execution_time', '00:00').to_markdown()}")

    # TODO debug ,,,
    #merged_df = df_utils.capture_df_starting_hour_x_on_last_day(merged_df, 'execution_time', '00:00')
    trades_w_prices_df = extract_trades_with_prices(merged_df)
    
    
    df_utils.save_df_to_csv_a_tabular(trades_w_prices_df, file_path=ib_pnl_dir)

    print('--------------------------')
    print(f"trades_w_prices_df \n{trades_w_prices_df[0:].to_markdown()}")

    trades_w_roi_df = do_x(trades_w_prices_df)
    print('--------------------------')
    print(f"trades_w_roi_df \n{trades_w_roi_df[0:].to_markdown()}")

    trades_w_pnl_df = do_y(trades_w_roi_df)
    print('--------------------------')
    print(f"trades_w_roi_df \n{trades_w_pnl_df[0:].to_markdown()}")


    # summarize_trades_df = summarize_trades(merged_df)
    #
    # print('--------------------------')
    # print(f"summarize_trades_df:\n{df_utils.capture_df_starting_hour_x_on_last_day(summarize_trades_df, 'open_time', '00:00').to_markdown()}")


if __name__ == "__main__":

    portfolio_id = 'p250'
    orchestrate(portfolio_id)
