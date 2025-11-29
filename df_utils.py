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
    mask_time = df['date'].dt.time >= pd.to_datetime(cutoff_time).time()
    mask_day = df['date'].dt.normalize() == last_day

    # Keep everything aftere that cutoff on the last day, and all prior days
    cut_df = df[(mask_day & mask_time)]
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

def save_df_to_csv_a_tabular(df=None, file_path='', mode='w', drop_dupplicates=True, unique_columns=[]):
    # TODO unique_column should be a list
    if df is not None and len(df) > 0:

        if mode == 'w':
            header = True

        else:
            # moed is a, check columns
            logger.debug(f"save_df_to_csv_a_tabular, file_path: {file_path}")
            if os.path.exists(file_path):
                existing_cols = pd.read_csv(file_path, nrows=0).columns.tolist()
                # --- Compare with new df columns
                if list(df.columns) == existing_cols:
                    mode = 'a'
                    header = False
                else: # columns are not same, we overwrite ...
                    file_utils.create_a_backup(file_path)
                    mode = 'w'
                    header = True
            else:
                header = True

        df.to_csv(file_path, mode=mode, index=False, header=header)

        # if drop_dupplicates:
        #     if unique_column != '' and unique_column in df.columns:
        #         drop_dupplicates_in_file(file_path, unique_column=unique_column)  # 'event'
        #     else:
        #         drop_dupplicates_in_file(file_path)  # 'event'
        if drop_dupplicates:
            if unique_columns == [] and 'unique_id' in df.columns: # it is passeD_empty, but uunique_id is there we add it
                unique_columns = ['unique_id']
            drop_dupplicates_in_file(file_path, unique_columns=unique_columns)

        write_file_in_tabulate(src_file_path=file_path)
    return


def write_file_in_tabulate(src_file_path, dest_file_path= None, number_of_rows=0):

    df = pd.read_csv(src_file_path)
    if len(df) > 0:
        if dest_file_path is None:
            dest_file_path = f"{src_file_path}-txt.csv"
        # Convert only object and bool columns to string (vectorized)
        # FIXME not happy to do that as may affect performance ...
        # for col in df.select_dtypes(include=['object', 'bool']):
        #     df[col] = df[col].astype(str)
        with open(dest_file_path, 'w') as f:
            if number_of_rows == 0:
                # write all
                f.write(tabulate(df.astype(str), headers='keys', tablefmt='psql'))
            else:
                f.write(tabulate(df[-number_of_rows:].astype(str), headers='keys', tablefmt='psql')) #, numalign=None, stralign='left'
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
