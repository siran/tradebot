"""
Backtest of a Buy and Hold strategy
"""

# todo: increase the holding position in the 2x2x scenario, adjusting for profits

import datetime
import math
import os
import glob
import random
import re
import sys
import statistics
from multiprocessing import Process, Queue
from collections import OrderedDict

from pprint import pprint

import pandas as pd
from tqdm import tqdm

from Strategy import Strategy, Accumulator

from trade_symbols import symbols
# from symbols_sp500 import symbols

class BacktestStrategyBuynhold2x(Strategy):
    """ buy and hold 2x strategy """

    strategy_name = "buynhold2x"

    def run(self, files):
        """ Run strategy """

        symbol = re.match('.*/([^-]*)-', files[0])[1]

        start_day = pd.read_csv(files[0])
        final_day = pd.read_csv(files[-1])

        initial_price = start_day.iloc[0]["open"]
        buy_timestamp = start_day.iloc[0]["timestamp"]

        self.buy(symbol=symbol, price=initial_price, when=buy_timestamp)

        final_price = final_day.iloc[-1]["close"]
        sell_timestamp = final_day.iloc[0]["timestamp"]

        self.sell(symbol=symbol, price=final_price, when=sell_timestamp)

        qty = math.floor(2*self.wallet/initial_price)

        self.profit = (final_price - initial_price) * qty
        self.wallet += self.profit

        self.days_last_transaction = (
            datetime.datetime.fromisoformat(sell_timestamp) - datetime.datetime.fromisoformat(buy_timestamp)
        ).total_seconds() / SECONDS_DAY

        self.wallet -= (qty * initial_price) * .0375/365*self.days_last_transaction

class BacktestStrategyBuynhold(Strategy):
    """ buy and hold strategy """

    strategy_name = "buynhold"

    def run(self, files):
        """ Run strategy """
        start_day = pd.read_csv(files[0])
        final_day = pd.read_csv(files[-1])

        initial_price = start_day.iloc[0]["open"]
        buy_timestamp = start_day.iloc[0]["timestamp"]

        final_price = final_day.iloc[-1]["close"]
        sell_timestamp = final_day.iloc[0]["timestamp"]

        qty = math.floor(self.wallet/initial_price)

        self.profit = (final_price - initial_price) * qty
        self.wallet += self.profit

        self.days_last_transaction = (
            datetime.datetime.fromisoformat(sell_timestamp) - datetime.datetime.fromisoformat(buy_timestamp)
        ).total_seconds()/SECONDS_DAY

class BacktestStrategyMorningFall(Strategy):
    """ buy and hold strategy """

    strategy_name = "morning-fall"

    def run(self, files):
        """ Run strategy """

        date_start = globals().get('DATE_START')
        date_end = globals().get('DATE_END')
        if date_start:
            date_file = re.match('.*/[^-]*-([^.]*).', files[0])[1]
            if not date_file <= date_start:
                print(f"Not enough data. First file's date is {date_file} and DATE_START is {date_start}")
                sys.exit(1)
        if date_end:
            date_file = re.match('.*/[^-]*-([^.]*).', files[-1])[1]
            if not date_file >= date_end:
                print(f"Not enough data. Last file's date is {date_file} and DATE_END is {date_end}")
                sys.exit(1)


        symbol = re.match('.*/([^-]*)-', files[0])[1]



        # initial_price = pd.read_csv(files[0]).iloc[0]["open"]
        # final_price = pd.read_csv(files[-1]).iloc[-1]["close"]
        # qty = math.floor(self.wallet / initial_price)

        buy_price = None

        self.low_threshold = 0.985
        self.sell_threshold = 1.01
        columns = {
            "timestamp": 0,
            "open": 1,
        }
        for file in tqdm(files):
            date = None
            day = open(file).read().splitlines()
            if len(day) < 10:
                continue

            date = None
            open_price = None
            for r, row in enumerate(day):
                if r == 0:
                    continue
                cols = row.split(",")

                if globals().get("DATE_START") and cols[columns["timestamp"]] < DATE_START:
                    continue
                if globals().get("DATE_END") and cols[columns["timestamp"]] > DATE_END:
                    continue

                if not open_price:
                    open_price = float(cols[columns["open"]])
                if not date:
                    date = cols[columns["timestamp"]].split(" ")[0]

                if cols[columns["timestamp"]] < f"{date} 12:00:00-05:00":
                    if not self.buy_price:
                        if float(cols[columns["open"]]) < open_price * self.low_threshold:
                            buy_price = float(cols[columns["open"]])
                            buy_timestamp = cols[columns["timestamp"]]
                            # qty = math.floor(self.wallet / buy_price)
                            # future_sell_price = buy_price*self.sell_threshold
                            # self.num_purchases += 1
                            self.buy(symbol=symbol, price=buy_price, when=buy_timestamp)
                        continue

                if self.buy_price:
                    if float(cols[columns["open"]]) > self.future_sell_price:
                        sell_price = float(cols[columns["open"]])
                        sell_timestamp = cols[columns["timestamp"]]
                        # self.num_sells += 1

                        # self.profit = qty * (sell_price - buy_price)
                        # self.wallet += self.profit

                        # self.days_last_transaction = (
                            # datetime.datetime.fromisoformat(sell_timestamp) - datetime.datetime.fromisoformat(buy_timestamp)
                        # ).total_seconds()/SECONDS_DAY

                        self.sell(symbol=symbol, price=sell_price, when=sell_timestamp)

                        # buy_price = None
                        # qty = None

        if self.buy_price:
            sell_price = float(cols[columns["open"]])
            sell_timestamp = cols[columns["timestamp"]]
            self.sell(symbol=symbol, price=sell_price, when=sell_timestamp)
            self.last_day_sell = True
            # if len(day) < 10:
            #     self.undo_last_purchase
            #     self.wallet += self.qty*self.buy_price
            #     self.num_purchases -= 1
            #     self.last_day_sell = "removed-last-purchase"
            # else:
            #     sell_price = float(cols[columns["open"]])
            #     self.num_sells += 1
            #     self.last_day_sell = True

            #     self.profit = qty * (sell_price - buy_price)
            #     self.wallet += self.profit

        # self.plot_wallets()

        self.end_run()
        return

def main():
    """ main """

    total_investment = 0
    total_return = 0

    summary = []

    accumulator = Accumulator()

    for i, symbol in enumerate(SYMBOLS):
        files = sorted(glob.glob(os.path.join(DATADIR, f'{symbol}-{YEAR}*.csv')))

        # if len(files) < 200:
        #     continue
        if len(files) < 90:
            continue
        # print(f"Symbol: {symbol}")

        strategies = [
            BacktestStrategyMorningFall,
            # BacktestStrategyBuynhold,
            # BacktestStrategyBuynhold2x
            # BacktestStrategyMorningFall,
        ]

        for strategy in strategies:
            current_strategy = strategy(wallet=WALLET)

            total_investment += current_strategy.initial_wallet
            total_return -= current_strategy.initial_wallet
            # print(f"Strategy: {current_strategy.strategy_name}")
            # print(f"Year: {YEAR}")
            current_strategy.run(files)

            if not current_strategy.yield_buynhold:
                current_strategy.yield_buynhold = 1

            accumulator.yields[symbol] = current_strategy.yields
            accumulator.yields_buynhold.append(current_strategy.yield_buynhold)
            total_return += current_strategy.wallet
            # print(
                # f"wa/let: {current_strategy.wallet:.2f}, "
                # f"yield: {current_strategy.wallet/current_strategy.initial_wallet-1:.2f}"
            # )

            avg_yield_bnh = statistics.mean(accumulator.yields_buynhold)

            tqdm.write(
                f"i: {total_investment:0.2f} "
                f"r: {total_return:0.2f} "
                f"y: {total_return / total_investment + 1:0.4f} "
                f"avg ybnh: {avg_yield_bnh:0.4f} "
            )


            summary_row = OrderedDict(**{
                "rownum": i,
                "strategy_name": current_strategy.strategy_name,
                "symbol": symbol,
                "initial_wallet": f"{current_strategy.initial_wallet:0.2f}",
                "final_wallet": f"{current_strategy.wallet:0.2f}",
                "yield": f"{current_strategy.wallet/current_strategy.initial_wallet:0.2f}",
                "last_day_sell": current_strategy.last_day_sell,
                "num_purchases": current_strategy.num_purchases,
                "days_last_transaction": f"{current_strategy.days_last_transaction:0.1f}",
                "buy_threshold": current_strategy.low_threshold,
                "sell_threshold": current_strategy.sell_threshold,
            })

            if hasattr(current_strategy, 'yields_buynhold'):
                summary_row["yields_buynhold"] = current_strategy.first_purchase

            summary.append(summary_row)

            print('start write summary ...', end="")
            summary_df = pd.DataFrame(summary)
            summary_df.to_csv(f'summary_{current_strategy.strategy_name}_{YEAR}_lt-{current_strategy.low_threshold}_st-{current_strategy.sell_threshold}.csv', index=False)
            print('... end write summary ...')

            # accumulator.plot_wallets(symbol=symbol)
            accumulator.plot_wallets()
            a=1


if __name__ == '__main__':
    DATADIR = os.path.join('..', 'historical-market-data')  # download directory for the data
    SYMBOLS = ['FTEC']  # list of symbols we're interested
    random.shuffle(symbols)
    SYMBOLS = symbols  # list of symbols we're interested
    if len(sys.argv) > 1:
        SYMBOLS = sys.argv[1:]
    YEAR = '2020'
    DATE_START = '2020-05-01'
    DATE_END = '2020-05-15'

    WALLET = 1000
    # SECONDS_DAY = 24 * 60 * 60
    main()
