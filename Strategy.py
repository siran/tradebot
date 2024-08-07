"""Abstract Strategy class"""

import datetime
import math
import statistics
from abc import ABC, abstractmethod

from matplotlib import pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

SECONDS_DAY = 24 * 60 * 60

class Accumulator():
    wallets = {}
    yields = {}
    final_yields = []
    yields_buynhold = []

    def plot_wallets(self, symbol=None):
        """plots evolution of wallet"""

        if not self.yields.get(symbol):
            return

        legends = []
        for s, yields in self.yields.items():
            if symbol and s != symbol:
                continue
            if True or yields[-1][1] > 1:
                plt.plot(*list(zip(*yields)))

            # legends.append(symbol)
            self.final_yields.append(yields[-1][1])

        plt.title(f"Avg yield: {statistics.mean(self.final_yields)} - Ave yield BnH: {statistics.mean(self.yields_buynhold)}")
        # plt.legend(legends)
        plt.show()
        a=1

class Strategy(ABC):
    """ base strategy class """

    @property
    @abstractmethod
    def strategy_name(self):
        """ strategy name """
        return ''

    def __init__(self, wallet):
        """ init default values """
        self.initial_wallet = wallet
        self.wallet = wallet
        self.wallets = []
        self.yields = []
        self.profit = 0
        self.num_purchases = 0
        self.num_sells = 0
        self.last_day_sell = False
        self.days_last_transaction = 0
        self.sell_threshold = 0
        self.low_threshold = 0

        self.buy_price = None
        self.buy_timestamp = None
        self.purchase_date = None
        self.qty = None
        self.future_sell_price = None

        self.sell_price = None
        self.sell_timestamp = None
        self.sell_date = None


        self.first_purchase = None
        self.last_sell = None

        self.yield_buynhold = None

        self.operations = []


    @abstractmethod
    def run(self, files):
        """ run strategy logic """
        pass

    # def operation(self, operation, symbol, price, when):
    #     """buys or sells"""


    def buy(self, symbol, price, when, **kwargs):
        """ performs purchase of `symbol` at `price` on date `when` """

        self.buy_price = float(price)
        self.buy_timestamp = when
        self.qty = math.floor(self.wallet / self.buy_price)
        self.future_sell_price = self.buy_price*self.sell_threshold
        self.num_purchases += 1

        if not self.first_purchase:
            self.first_purchase = (self.buy_timestamp, self.buy_price)

        self.operations.append(('buy', self.buy_price, self.buy_timestamp))


    def sell(self, symbol, price, when, **kwargs):
        """ performs sell of `symbol` at `price` on date `when` """

        self.sell_price = float(price)
        self.sell_timestamp = when
        self.num_sells += 1

        self.profit = self.qty * (self.sell_price - self.buy_price)
        self.wallet += self.profit

        self.purchase_date = datetime.datetime.fromisoformat(self.sell_timestamp)
        self.sell_date = datetime.datetime.fromisoformat(self.buy_timestamp)
        total_seconds = (self.purchase_date - self.sell_date).total_seconds()

        self.days_last_transaction = total_seconds/SECONDS_DAY

        self.buy_price = None
        self.qty = None

        self.wallets.append((self.sell_date, self.wallet,))
        self.yields.append((self.purchase_date, self.wallet / self.initial_wallet,))
        self.operations.append(('sell', self.sell_price, self.sell_timestamp))

    def end_run(self):
        """Marks the end of a run"""

        self.last_sell = (self.sell_date, self.sell_price)
        # self.yield_buynhold = 0
        if self.last_sell[1]:
            self.yield_buynhold = self.last_sell[1] / self.first_purchase[1]

        pass