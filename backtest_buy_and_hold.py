"""
Backtest of a Buy and Hold strategy
"""

import os
import glob
import sys

import pandas as pd

DATADIR = os.path.join('..', 'historical-market-data')  # download directory for the data
SYMBOLS = ['FTEC']  # list of symbols we're interested
if len(sys.argv) > 1:
    SYMBOLS = sys.argv[1:]
YEAR = '2019'

for symbol in SYMBOLS:
    files = glob.glob(os.path.join(DATADIR, f'{symbol}-{YEAR}*.csv'))

    first_day = pd.read_csv(files[0])
    last_day = pd.read_csv(files[-1])

    last_close = last_day.iloc[-1]["close"]
    first_open = first_day.iloc[-1]["close"]
    profit = last_close / first_open

    print(
        f"{symbol}'s {YEAR}'s Buy-n-Hold strategy return profit is: "
        f"{profit:.3f}\n"
        f"last day: {last_close} / first day: {first_open} = {profit:.3f}"
    )
