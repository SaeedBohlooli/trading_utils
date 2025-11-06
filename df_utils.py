import sys
import time
from tabulate import tabulate
sys.path.insert(0, f'../')


import logging
import os.path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import configparser

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



def drop_dupplicates_in_file(file_path, unique_column=None, keep='last'):
    # Drop dupplicaes
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        if unique_column is None:
            df = df.drop_duplicates(keep=f'{keep}')
        else: # has fields ...
            df = df.drop_duplicates(subset=[f'{unique_column}'], keep=f'{keep}')
        df.to_csv(file_path, index=False, mode='w')
    return

def save_df_to_csv_a_tabular(df=None, file_path='', mode='w', drop_dupplicates=True, unique_column='unique_id'):
    # TODO unique_column should be a list
    if len(df) > 0:

        if mode == 'w':
            header = True

        else:
            # moed is a, check columns
            if os.path.exists(file_path):
                existing_cols = pd.read_csv(file_path, nrows=0).columns.tolist()
                # --- Compare with new df columns
                if list(df.columns) == existing_cols:
                    mode = 'a'
                    header = False
                else: # columns are not same, we overwrite ...
                    mode = 'w'
                    header = True
            else:
                header = True

        df.to_csv(file_path, mode=mode, index=False, header=header)

        if drop_dupplicates:
            if unique_column != '' and unique_column in df.columns:
                drop_dupplicates_in_file(file_path, unique_column=unique_column)  # 'event'
            else:
                drop_dupplicates_in_file(file_path)  # 'event'

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