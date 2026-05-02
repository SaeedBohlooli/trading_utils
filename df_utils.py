import sys
import time
from tabulate import tabulate
import logging
import os.path
import pandas as pd
import numpy as np
import configparser
sys.path.insert(0, f'../')


from trading_utils import file_utils

logger = logging.getLogger(__name__)


def load_csv_file(file_path, expected_columns=[]):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        if expected_columns != []:
            if list(df.columns) != expected_columns:
                logger.warning("@@@@ The loaded CSV has different columns, so we are returning an emppty DF")
                df = pd.DataFrame()

    else:
        df = pd.DataFrame()

    return df

def cut_df_strating_hour_x_on_last_day(df, cutoff_time="13:00"):
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    # Find the last trading day in the DataFrame
    last_day = df['date'].dt.normalize().max()

    # Create masks
    cutoff_t = pd.to_datetime(cutoff_time).time()
    mask_time = df['date'].dt.time >= cutoff_t
    mask_day = df['date'].dt.normalize() == last_day

    # Keep all prior calendar days in full, and on the last day only rows from cutoff onward
    prior_days = df["date"].dt.normalize() < last_day
    cut_df = df[prior_days | (mask_day & mask_time)]
    return cut_df


def cut_df_until_hour_x_on_last_day(df, cutoff_time="13:00"):
    """
    Cut the DataFrame up to (and including) a specific time on the last day in df['date'].

    Parameters:
        df : pd.DataFrame
            Must contain a 'date' column of datetime type.
        cutoff_time : str
            Time in HH:MM (24-hour) format. Default is '13:00'.

    Returns:
        pd.DataFrame : sliced DataFrame up to cutoff_time of the last day.
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    # Find the last trading day in the DataFrame
    last_day = df['date'].dt.normalize().max()

    # Create masks
    mask_day = df['date'].dt.normalize() == last_day
    mask_time = df['date'].dt.time <= pd.to_datetime(cutoff_time).time()

    # Keep everything before that cutoff on the last day, and all prior days
    cut_df = df[(df['date'].dt.normalize() < last_day) | (mask_day & mask_time)]
    return cut_df


def capture_df_starting_hour_x_on_last_day(df, date_f='date', cutoff_time="13:00"):
    # print(f"in capture_df_starting_hour_x_on_last_day: \n{df[-1:].to_markdown()}")
    df = df.copy()
    df[date_f] = pd.to_datetime(df[date_f])

    # Find the last trading day in the DataFrame
    last_day = df[date_f].dt.normalize().max()

    # Create masks
    mask_time = df[date_f].dt.time >= pd.to_datetime(cutoff_time).time()
    mask_day = df[date_f].dt.normalize() == last_day

    # Keep everything aftere that cutoff on the last day, and all prior days
    cut_df = df[(mask_day & mask_time)]
    return cut_df

def drop_dupplicates_in_file(file_path, unique_columns=[], keep='last'):
    # Drop dupplicaes
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        if unique_columns == []:
            df = df.drop_duplicates(keep=f'{keep}')
        else: # has fields ...
            df = df.drop_duplicates(subset=unique_columns, keep=f'{keep}')
        df.to_csv(file_path, index=False, mode='w')
    return

def save_df_to_csv(df=None, file_path='', mode='w', check_columns: bool = True, tabular: bool= False, drop_dupplicates=True, unique_columns=[], keep='last'):
    if df is None :
        logger.warning("save_df_to_csv: df is None, nothing to save.")
        return

    if len(df) == 0 and mode == 'a':
        logger.warning(f"save_df_to_csv: Empty df, mode = {mode}, nothing to save.")
        return

    save_df_to_csv_w_mode(df, file_path, mode=mode, check_columns=check_columns)

    if drop_dupplicates:
        if unique_columns == [] and 'unique_id' in df.columns: # it is passeD_empty, but uunique_id is there we add it
            unique_columns = ['unique_id']
        drop_dupplicates_in_file(file_path, unique_columns=unique_columns, keep=keep)
    if tabular:
        write_file_in_tabulate(src_file_path=file_path)

    return


def save_df_to_csv_w_mode(df, file_path: str, mode: str= None, check_columns: bool = True):
    if df is None:
        logger.warning("save_df_to_csv_w_mode: df is None, nothing to save.")
        return
    if len(df) == 0 and mode == 'a':
        logger.warning("save_df_to_csv_w_mode: Empty df, nothing to save.")
        return

    if len(df) == 0 and mode == 'w':
        logger.warning(f"save_df_to_csv_w_mode: Empty df, saving empty df to a file. file_path: {file_path}")
        df.to_csv(file_path, mode=mode, index=False)
        return

    # -----------------------------------------
    # WRITE MODE
    # -----------------------------------------
    if mode == 'w':
        df.to_csv(file_path, mode='w', index=False, header=True)
        return

        # -----------------------------------------
        # APPEND MODE (schema-aware)
        # -----------------------------------------
    if mode == 'a' and check_columns and os.path.exists(file_path):
        # Read only header first (fast path)
        existing_cols = pd.read_csv(file_path, nrows=0).columns.tolist()
        new_cols = list(df.columns)

        if existing_cols == new_cols:
            # Fast path: exact match
            df.to_csv(file_path, mode='a', index=False, header=False)
            return

        # -------------------------------
        # Schema evolution path
        # -------------------------------
        logger.info(
            f"save_df_to_csv_w_mode: Schema change detected, expanding columns. file_path: {file_path}"
        )

        # Read existing file fully (only when needed)
        existing_df = pd.read_csv(file_path)

        # Union of columns (preserve order: existing first, then new)
        all_cols = list(dict.fromkeys(existing_cols + new_cols))

        # Reindex both
        existing_df = existing_df.reindex(columns=all_cols)
        df = df.reindex(columns=all_cols)

        # Backup before rewrite
        file_utils.create_a_backup(file_path)

        # Rewrite expanded file
        existing_df.to_csv(file_path, mode='w', index=False, header=True)

        # Append new rows
        df.to_csv(file_path, mode='a', index=False, header=False)
        return

    # -----------------------------------------
    # Append without column checking
    # -----------------------------------------
    header = not os.path.exists(file_path)
    df.to_csv(file_path, mode='a', index=False, header=header)
    return

    #     # mode is a, we may need to check columns
    #     if check_columns:
    #         # mode is a, check columns
    #         logger.debug(f"save_df_to_csv, file_path: {file_path}")
    #         if os.path.exists(file_path):
    #             existing_cols = pd.read_csv(file_path, nrows=0).columns.tolist()
    #             new_cols = list(df.columns)
    #             # --- Compare with new df columns
    #             if new_cols == existing_cols:
    #                 mode = 'a'
    #                 header = False
    #             else:  # columns are not same, we overwrite ...
    #                 file_utils.create_a_backup(file_path)
    #                 mode = 'w'
    #                 header = True
    #         else:
    #             header = True
    #     else:
    #         header = False
    #
    # df.to_csv(file_path, mode=mode, index=False, header=header)
    # return

def write_file_in_tabulate(src_file_path, dest_file_path= None, number_of_rows=None):
    if dest_file_path is None:
        dest_file_path = f"{src_file_path}-txt.csv"

    logger.info(f"Started write_file_in_tabulate, src_file_path: {src_file_path}, dest_file_path: {dest_file_path}, number_of_rows: {number_of_rows}")

    try:
        df = pd.read_csv(src_file_path)
    except Exception as e:
        # File is empty / only blank lines -> write an "empty table"
        empty_table = tabulate(pd.DataFrame(), headers="keys", tablefmt="psql")
        with open(dest_file_path, "w", encoding="utf-8") as f:
            f.write(empty_table + "\n")
        logger.info(f"Finished write_file_in_tabulate (empty csv), dest_file_path: {dest_file_path}")
        return

    if len(df) > 0:

        # Convert only object and bool columns to string (vectorized)
        # FIXME not happy to do that as may affect performance ...
        # for col in df.select_dtypes(include=['object', 'bool']):
        #     df[col] = df[col].astype(str)
        with open(dest_file_path, 'w') as f:
            if number_of_rows:
                # f.write(tabulate(df[-number_of_rows:].astype(str), headers='keys', tablefmt='psql')) #, numalign=None, stralign='left'
                df = df[-number_of_rows:]
                f.write(tabulate(df.astype(str), headers='keys', tablefmt='psql')) #, numalign=None, stralign='left'
            else:
                # write all
                # f.write(tabulate(df.astype(str), headers='keys', tablefmt='psql'))
                f.write(tabulate(df, headers='keys', tablefmt='psql', disable_numparse=True))

    logger.info(f"Finished write_file_in_tabulate, dest_file_path: {dest_file_path}")
    return



def move_last_x_to_position_y(df, x, y):
    if len(df) < 1:
        return df
    """
    Move the last x columns to position y (0-based index).

    Example:
        move_last_x_to_position_y(df, x=3, y=2)
        → moves last 3 cols to become columns 2,3,4.
    """

    cols = list(df.columns)

    # Safety checks
    if x <= 0 or x > len(cols):
        raise ValueError("x must be between 1 and number of columns")
    if y < 0 or y > len(cols) - x:
        raise ValueError("y out of range")

    # Extract parts
    last_x = cols[-x:]       # last X columns
    first_part = cols[:y]    # before the insertion position
    middle_part = cols[y:-x] # columns between y and the last X slice

    # Build final column order
    new_order = first_part + last_x + middle_part

    return df[new_order]


def convert_column_timezone(df, from_column='date', to_column='date_est', from_zone='UTC', to_zone='America/New_York'):
    from_column_tmp = from_column + '_tmp'
    df[from_column_tmp] = pd.to_datetime(df[from_column])
    df[from_column_tmp] = df[from_column_tmp].dt.tz_localize(from_zone)

    # Convert from UTC to Eastern Time
    df[to_column] = df[from_column_tmp].dt.tz_convert(to_zone)
    logger.debug(f"df[-3:].to_markdown():\n {df[-10:].to_markdown()}")
    df = df.drop(columns=[from_column_tmp])
    return df
