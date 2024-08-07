"""Morning trader"""

# pylint: disable=wrong-import-order,unused-import
import activate_venv

import argparse
import datetime
import json
import math
import os
import shelve
import time
import asyncio
from dateutil import tz
from trade_symbols import symbols
from pprint import pprint
import sys
import multiprocessing
from threading import Thread
from queue import Queue
import traceback

from types import SimpleNamespace


import alpaca_trade_api as tradeapi

# global trader

class Agg(SimpleNamespace):
    pass

async def on_minute_snapshot(conn, channel, data):
    """Called every minute with snapshot data"""

    # global trader

    symbol = data.symbol

    if not trader.ready:
        trader.out(f"received for {symbol} but trader is not yet ready :-(")
        return

    now = trader.now()
    data.close = float(data.close)
    buy_ratio = data.close/data.todaysopen
    trader.out(f"{now} - {symbol:4} - c:{data.close:7.3f} - op:{data.todaysopen:7.3f} - r:{buy_ratio:5.4f} < {trader.buy_threshold:5.4f}", end="")
    # trader.out(f"received AM.{symbol}")

    if trader.force or (now < now.replace(**trader.limit_time)):
        position = trader.positions.get(symbol)
        should_buy = buy_ratio < trader.buy_threshold
        if not position:
            if should_buy:
                trader.out(" ... sending buy order")
                res = trader.buy_order(data)
                if not res:
                    trader.out(f"order=false, not buying {symbol}")
            else:
                trader.out(f" ... ratio not good")
        else:
            trader.out(f" ... we have position {symbol} (should_buy={should_buy})")
            # trader.out(trader.positions[symbol])
    else:
        trader.out(" ... to late")
        sys.exit(0)

async def on_trade_updates(conn, channel, data):
    """Called on trade_update"""

    event = data.event
    order = data.order
    side = order["side"]


    symbol = order["symbol"]

    try:
        trader.out(f"{symbol:5} - side:{side:4} event: {event}")
        if event == 'new':
            n=1
            if side == "buy":
                # buy_price = trader.positions[symbol]["suggested_price"]
                # trader.wallet -= buy_price * order["qty"]
                trader.update_position(symbol, {
                    'status': order["status"],
                    # 'buy_price': trader.positions[symbol]["suggested_price"],
                    # 'pending_qty_buy': order["qty"]
                })
            elif side == "sell":
                trader.update_position(symbol, {
                    'status': order["status"],
                    # 'buy_price': data.price,
                    # 'pending_qty_sell': order["qty"]
                })
        elif event in ["fill"]:
            data.qty = int(data.qty)
            data.price = round(float(data.price), 2)
            if symbol in trader.partials:
                p=1
            if side == "buy":
                print(f"{symbol} - buy_price: {data.price} - qty: {data.qty}")
                buy_price = trader.positions[symbol]["suggested_price"]
                trader.wallet += buy_price * data.qty
                trader.wallet -= data.price*data.qty
                trader.update_position(symbol, {
                    'status': order["status"],
                    'owned': True,
                    'buy_price': data.price,
                    'qty': data.position_qty,
                    'buy_timestamp': data.timestamp
                })
                del trader.positions[symbol]["pending_buy_qty"]
                del trader.positions[symbol]["suggested_price"]
                trader.sell_order(symbol)
            elif side == "sell":
                # trader.out(f"on sell ==== data {symbol} ======")
                # trader.pout(data)
                # trader.out(f"on sell ==== trader.POSITIONS {symbol} ======")
                # trader.pout(trader.positions[symbol])
                # trader.out(trader.positions[symbol])
                sell_price = data.price
                buy_price = trader.positions[symbol]["buy_price"]
                profit = (sell_price - buy_price)*data.qty
                print(f"{symbol} - SOLD! buy_price: {data.price} - qty: {data.qty} - profit: {profit:0.2f}")
                trader.wallet += data.price*data.qty
                del trader.positions[symbol]
                a=1
        elif event in ["partial_fill"]:
            data.qty = int(data.qty)
            data.price = round(float(data.price), 2)
            data.position_qty = int(data.position_qty)
            p = 1
            # if int(order["filled_qty"]) == int(order["qty"]):
            #     trader.out("fully filled")
            #     # sys.exit()
            #     res = trader.sell_order(symbol)
            if side == "buy":
                # trader.wallet -= data.price*data.qty
                trader.partials.append(symbol)
                trader.update_position(symbol, {
                    'status': order["status"],
                    'owned': True,
                    'buy_price': data.price,
                    'qty': data.position_qty,
                    'buy_timestamp': data.timestamp
                })
                if int(order["filled_qty"]) == int(order["qty"]):
                    trader.out("fully filled")
                    # sys.exit()
                    res = trader.sell_order(symbol)
                # res = trader.sell_order(symbol)
                a=1
            elif side == "sell":
                # trader.pout(data)
                # trader.pout(trader.positions[symbol])
                # sys.exit()
                trader.wallet += data.price*data.qty
                if int(order["filled_qty"]) == int(order["qty"]):
                    del trader.positions[symbol]
                else:
                    trader.update_position(symbol, {
                        'status': order["status"],
                        'qty': data.position_qty,
                        'owned': True,
                    })
                trader.partials.append(symbol)
                pass

        elif event in ["canceled"]:
            # trader.pout(data)
            # trader.pout(trader.positions[symbol])
            # sys.exit()
            if side == "buy":
                order["qty"] = int(order["qty"])
                data.price = round(float(data.price), 2)
                trader.wallet += float(order["price"]*order["qty"])
            del trader.positions[symbol]
            c=1
        else:
            trader.out("-----------------")
            trader.out(f"Event not handled: {event}")
            trader.out(order)
            trader.out("-----------------")
    except Exception as error:
        trader.out(error)
        trader.out('----traceback:')
        trader.out(traceback.format_exc())
        trader.out(data)
        trader.out(trader.positions[symbol])



class Trader():
    """base class for trader"""

class MorningTrader(Trader):
    """Morning Trader"""

    def __init__(self):

        self.force = False
        self.ready = False
        self.limit_time = dict(hour=12, minute=00, second=0)

        self.wallet = 400000
        self.amount_per_stock = 4000

        self.buy_threshold = 0.985
        self.sell_threshold = 1.01

        # Create an API object which can be used to submit orders, etc.
        self.api = tradeapi.REST()
        self.polygon = self.api.polygon
        # Establish streaming connection
        self.conn = tradeapi.StreamConn()

        self.today_datestr = datetime.date.today()
        self.initial_snapshot_name = f"initial-snapshot-{self.today_datestr}.json"
        self.tz = tz.gettz('America/New_York')

        self.positions = {}
        self.qcs = []
        self.partials = []

    def shelve_position(self, symbol):
        """ open a shelve for a position """

        if symbol not in self.positions:
            self.positions[symbol] = shelve.open(f'data-store/{symbol}', writeback=True)

    def update_position(self, symbol, datadict):
        """Updates a position with new dictionary"""

        if symbol not in self.positions:
            self.shelve_position(symbol)

        position = self.positions[symbol] or {}
        position.update(datadict)
        self.positions[symbol] = position

    def organize(self):
        """Tidy house"""
        self.out("============= start organize =============")
        self.out("loading current positions and orders")
        # building hash table of orders and positions
        self.api.cancel_all_orders()
        wait = 1.5
        while True:
            orders = self.api.list_orders(status="open")
            if len(orders) == 0:
                break
            print(f"waiting {wait} while cancelling all orders...")
            time.sleep(wait)


        # orders = self.api.list_orders(status="open")
        # # self.out(f"found p:{len(positions)}, o:{len(orders)}")
        # self.out(f"found o:{len(orders)}")

        # for order in orders:
        #     # if order.status == "filled":
        #     #     continue
        #     if order.side == "buy":
        #         self.out(f"Canceling {order.status} order to {order.side} symbol {order.symbol}")
        #         self.api.cancel_order(order.id)
        #         continue
        #     # elif order.side == "sell":
        #     #     self.out(f"Canceling {order.side} order for {order.symbol}")
        #     #     self.api.cancel_order(order.id)
        #     #     # orders_dict[order.symbol] = order
        #     elif order.side != 'sell':
        #         self.out("Weird order")
        #         self.out(order)

        positions = self.api.list_positions()
        positions_dict = {}
        for position in positions:
            positions_dict[position.symbol] = position


        to_delete = []
        for symbol in self.positions:
            if symbol in positions_dict:
                trader.update_position(symbol, {
                    'status': 'filled',
                    'owned': True,
                    'buy_price': float(positions_dict[symbol].avg_entry_price),
                    'qty': int(positions_dict[symbol].qty),
                    # 'buy_timestamp': data.timestamp
                })
            else:
                trader.update_position(symbol, {})
                to_delete.append(symbol)

        for symbol in to_delete:
            del self.positions[symbol]

        for symbol in self.positions:
            self.wallet -= float(positions_dict[symbol].cost_basis)

        # orders = self.api.list_orders(status="open")
        # orders_dict = {}
        # for order in orders:
        #     orders_dict[order.symbol] = order

        # all positions should have a sell order
        self.out("making sell orders")
        for symbol in positions_dict:
            qty = int(positions_dict[symbol].qty)
            # if orders_dict.get(symbol):
                # qty -= int(orders_dict[symbol].qty)
            self.positions[symbol] = {
                'owned': True,
                'buy_price': float(positions_dict[symbol].avg_entry_price),
                'qty': qty,
            }

            # if symbol not in orders_dict:
                # self.out(f"no order for {symbol}")
                # self.sell_order(symbol)
            # if qty != orders_dict[symbol].qty:
            # self.out(f"there's order for {symbol} but not whole quantity")
            self.sell_order(symbol)
        self.out("============= end organize =============")
        self.ready = True
        self.out(f"ready: {self.ready}")

    def run(self, *args, **kwargs):
        """start trading"""

        self.out("===== RUNNING =====")
        now = self.now()
        if self.force or (now < now.replace(**self.limit_time)):
            self.qcs = []

            self.out("shelving positions")
            for symbol in symbols:
                self.shelve_position(symbol)
                self.positions[symbol] = {}
                self.qcs.append(f'AM.{symbol}')

            # self.qcs.append(f'A.*')
            self.out("registering")
            self.conn.register("AM", on_minute_snapshot)
            self.conn.register("trade_updates", on_trade_updates)

            a = 1

            self.out("running...", flush=True)
            try:
                self.conn.run(self.qcs + ["trade_updates"])
            except Exception as error:
                self.out(error)
                self.out('----traceback:')
                self.out(traceback.format_exc())
                sys.exit(1)


            # ctrl c
            self.out("\n\n\n\n\n\n=================== death =======================\n\n\n\n")

    def now(self):
        """Return time in timezone self.tz"""

        return datetime.datetime.now(tz=self.tz)

    def get_snapshot(self, symbol=None, **kwargs):
        """Returns polygon snapshot of all tickers"""

        path = '/snapshot/locale/us/markets/stocks/tickers'
        snapshot = self.api.polygon.get(path, version='v2')['tickers']
        # snapshot = self.polygon.all_tickers()

        if "open_snapshot" not in self.config:
            self.config["open_snapshot"] = snapshot

        return snapshot

    def wait_until_open(self):
        """Wait until market opens"""

        now = self.now()
        clock = self.api.get_clock()
        nextopen = clock.next_open.replace(tzinfo=now.tzinfo)
        wait = 10
        daystr = now.strftime('%d')
        clockdaystr = clock.next_open.strftime('%d')
        while self.now() < nextopen and daystr == clockdaystr:
            wait = (nextopen - self.now()).total_seconds()
            self.out(f"Still not open, waiting {wait:0.2f}s ({wait/60:0.2f}min)")
            time.sleep(wait)
        print("Market is open!")

    def buy_order(self, data):
        """Submits buy order """

        symbol = data.symbol
        buy_price = round(float(data.close), 2)

        available = min(self.amount_per_stock, self.wallet)
        qty = math.floor(available / buy_price)
        # self.out(f"q:{qty}, w:{self.wallet}, p:{buy_price}")
        if qty == 0:
            return False
        if qty < 0:
            wtf = "?"
            return False


        position = self.positions.get(symbol)
        if position:
            self.out(f'Position is already in portfolio: {position}')
            # already in our portafolio
            # either owned or pending sell/buy
            return False

        try:
            self.update_position(symbol, {
                "status": "pending_buy",
                "suggested_price": buy_price,
                "pending_buy_qty": qty
            })
            o = self.api.submit_order(
                side='buy',
                symbol=symbol,
                qty=str(qty),
                type='market',
                time_in_force='day',
                # limit_price=str(q.data.askprice)
                # limit_price=limit_price
            )
            # self.out(f"post buy {symbol}")
            self.wallet -= buy_price * qty
            # self.out(f"w: {self.wallet}")
            return True
        except Exception as error:
            self.out(error)
            self.out('----traceback:')
            self.out(traceback.format_exc())

        a = 1

    def sell_order(self, symbol):
        """Post a sell order """

        buy_price = float(self.positions[symbol]["buy_price"])
        expected_sell_price = round(buy_price*self.sell_threshold, 2)
        qty = self.positions[symbol]["qty"]

        position = self.api.get_position(symbol)
        orders = self.api.list_orders()
        ordr = [o for o in orders if o.symbol == symbol]


        params = dict(
                side='sell',
                symbol=symbol,
                qty=str(qty),
                type="limit",
                time_in_force='day',
                limit_price=str(expected_sell_price)
        )

        try:
            o = self.api.submit_order(**params)
            # self.out(f"post sell {symbol}")
            self.update_position(symbol, {
                "status": "pending_sell",
                "expected_sell_price": expected_sell_price,
                "pending_sell_qty": qty
            })
        except Exception as error:
            self.out('----traceback:')
            self.out(traceback.format_exc())
            self.out(error)

            self.out(f"========= ERROR while selling  {symbol} ========")
            self.out(f"position:")
            self.pout(position)
            self.out(f"ordr:")
            self.pout(ordr)
            self.out(f"self.positions[symbol]:")
            self.pout(self.positions[symbol])
            self.out(f"params for sell:")
            self.pout(params)
            a = 1

    def sell_old_orders(self, age=30):
        """Sell orders more than `age` seconds long"""

        now = trader.now()
        if trader.force or (now < now.replace(hour=12, minute=00, second=0)):
            trader.out(" ... to late")
            sys.exit(0)

        wait = 5
        while True:
            print(f"sleeping {wait}")
            time.sleep(5)
            orders = self.api.list_orders(status="open")
            for order in orders:
                if order.side == "buy":
                    print(order)

    # def delayed_sell(self, symbol):
    #     """Submits sell after short sleep"""

    #     wait = 3
    #     print(f"waiting {wait} to sell {symbol}")
    #     p = multiprocessing.Process(target=trader.sell_order, args=(symbol,))
    #     time.sleep(wait)
    #     print(f"wait over to selling {symbol}")
    #     p.start()
    #     # res = self.sell_order(symbol)

    def out(self, msg, **kwargs):
        """Print without flush"""
        kwargs.update({"flush":True})
        print(msg, **kwargs)

    def pout(self, msg, **kwargs):
        """Pretty print without flush"""

        pprint(msg)

# def run(trader):
#     """thread worker function"""
#     trader.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--mode', type=str, choices=['paper', 'live'], default='paper',
        help='set https://paper-api.alpaca.markets if paper trading',
    )
    args = parser.parse_args()

    # mode = args.mode
    mode = 'paper'
    if mode == 'paper':
        # pylint: disable=unused-import,import-outside-toplevel
        import alpaca_conf_paper
    elif mode == 'live':
        # pylint: disable=unused-import,import-outside-toplevel
        import alpaca_conf_live

    trader = MorningTrader()
    trader.wait_until_open()
    # p = multiprocessing.Process(target=trader.run)
    # p.start()
    thread1 = Thread(target=trader.run)
    # thread2 = Thread(target=trader.sell_old_orders)
    thread1.start()
    # thread2.start()
    # time.sleep(10)
    trader.organize()
    thread1.join()
    # thread2.join()
    print('end?')