"""
Backtest of a Buy and Hold strategy
"""

# todo: increase the holding position in the 2x2x scenario, adjusting for profits

import math
import os
import glob
import sys
from pprint import pprint

import pandas as pd
from tqdm import tqdm

from Strategy import Strategy
from trade_symbols import symbols

DATADIR = os.path.join('..', 'historical-market-data')  # download directory for the data
# SYMBOLS = ['FTEC']  # list of symbols we're interested
SYMBOLS = symbols  # list of symbols we're interested
if len(sys.argv) > 1:
    SYMBOLS = sys.argv[1:]
YEAR = '2020'

WALLET = 1000


class BacktestStrategyBuynhold(Strategy):
    """ buy and hold strategy """

    strategy_name = "buynhold"

    def run(self, files):
        """ Run strategy """
        initial_price = pd.read_csv(files[0]).iloc[0]["open"]
        final_price = pd.read_csv(files[-1]).iloc[-1]["close"]
        qty = math.floor(self.wallet/initial_price)

        self.profit = (final_price - initial_price) * qty
        self.wallet += self.profit


class BacktestStrategy4x(Strategy):
    """
    buy/sell everyday 4x the available account
    no interest
    """

    strategy_name = "everyday4x"

    def run(self, files):
        """ Run strategy """
        for file in tqdm(files):
            day = pd.read_csv(file)
            open_day = day.iloc[0]["open"]
            qty = math.floor(4 * self.wallet / open_day)
            close_day = day.iloc[-1]["close"]
            self.profit = (close_day - open_day) * qty
            self.wallet += self.profit

class BacktestStrategy2x(Strategy):
    """
    buy/sell everyday 2x the available account
    no interest
    """

    strategy_name = "everyday2x"

    def run(self, files):
        """ Run strategy """
        for file in tqdm(files):
            day = pd.read_csv(file)
            open_day = day.iloc[0]["open"]
            qty = math.floor(2 * self.wallet / open_day)
            close_day = day.iloc[-1]["close"]
            self.profit = (close_day - open_day) * qty
            self.wallet += self.profit


class BacktestStrategy2x2x(Strategy):
    """
    buy/hold 2x, buy/sell extra 2x everyday
    we have to pay interest every month
    """

    strategy_name = "everyday2x2x"

    def run(self, files):
        """ Run strategy """

        # day0 = pd.read_csv(file)
        # initial_buy
        with tqdm(files) as t:
            n=0
            for file in t:
                n+=1
                day = pd.read_csv(file)
                if n == 1:
                    initial_price = day.iloc[0]["open"]
                    initial_qty = math.floor(2 * self.wallet / initial_price)
                    initial_loan = initial_qty * initial_price
                elif n == t.total:
                    final_price = day.iloc[-1]["close"]

                open_day = day.iloc[0]["open"]
                close_day = day.iloc[-1]["close"]
                qty = math.floor(2*self.wallet / open_day)
                self.profit = (close_day - open_day) * qty
                # self.wallet -= open_day * qty
                self.wallet += self.profit

        self.profit = (final_price - initial_price) * initial_qty
        self.wallet += self.profit
        self.wallet -= initial_loan * (0.0375)

class BacktestStrategyBuynhold2x(Strategy):
    """ buy and hold 2x strategy """

    strategy_name = "buynhold2x"

    def run(self, files):
        """ Run strategy """
        initial_price = pd.read_csv(files[0]).iloc[0]["open"]
        qty = math.floor(2*self.wallet / initial_price)
        final_price = pd.read_csv(files[-1]).iloc[-1]["close"]

        self.profit = (final_price - initial_price) * qty
        self.wallet += self.profit
        self.wallet -= (qty * initial_price) * .0375




def main():
    """ main """
    for symbol in SYMBOLS:
        files = sorted(glob.glob(os.path.join(DATADIR, f'{symbol}-{YEAR}*.csv')))
        if len(files) < 30:
            continue
        strategies = [
            BacktestStrategyBuynhold,
            # BacktestStrategy2x,
            # BacktestStrategy4x,
            # BacktestStrategy2x2x,
            # BacktestStrategyBuynhold2x,
        ]
        for strategy in strategies:
            s = strategy(wallet=WALLET)
            s.run(files)
            print(f'Strategy: {s.strategy_name}, wallet: {s.wallet:.2f}, yield: {s.wallet/WALLET-1:.2f}')
        # backtest_strategy_buynhold(files)
        # backtest_strategy_4x(files)

if __name__ == '__main__':
    main()
