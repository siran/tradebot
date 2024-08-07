"""
Download historical minute by minute data for a symbol between a range of dates
"""
import os

import pandas as pd
from tqdm import tqdm

import alpaca_trade_api as tradeapi
import alpaca_conf_paper # loads API Keys as environment variables

from trade_symbols import symbols

api = tradeapi.REST()

DATADIR = os.path.join('..', 'historical-market-data') # download directory for the data
# SYMBOLS = ['AAPL']  # list of symbols we're interested
SYMBOLS = symbols  # list of symbols we're interested
FROM_DATE = '2020-01-02'
TO_DATE = '2020-05-15'

# create data directory if it doesn't exist
if not os.path.exists(DATADIR):
    os.mkdir(DATADIR)

date_range = pd.date_range(FROM_DATE, TO_DATE)
for symbol in SYMBOLS:
    tqdm.write(symbol)
    if symbol in ["AABA", "ARRY"]:
        continue

    errors = 0
    for fromdate in tqdm(date_range):
        if fromdate.dayofweek > 4:
            # it's a weekend
            continue
        if str(fromdate)[0:10] == '2020-04-10':
            continue

        _from = fromdate.strftime('%Y-%m-%d')
        _to = (fromdate + pd.Timedelta(days=1)).strftime('%Y-%m-%d')

        fname = f'{symbol}-{_from}.csv'  # for example, AAPL-2016-01-04.csv
        full_name = os.path.join(DATADIR, fname)
        if os.path.exists(full_name):
            # data file already exists, not necessary to download
            continue

        # download data as a pandas dataframe format
        df = api.polygon.historic_agg_v2(
            symbol=symbol,
            multiplier=1,
            timespan='minute',
            _from=_from,
            to=_to,
            unadjusted=False
        ).df

        if df.empty:
            tqdm.write(f'Error downloading data for date {_from}')
            errors += 1
            if errors >= 5:
                break
            continue

        # filter times in which the market in open
        df = df.between_time('9:30', '16:00')

        # saving csv for the data of the day in DATADIR/fname
        df.to_csv(full_name)
