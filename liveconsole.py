# import stockhelper as sh
import alpaca_trade_api as tradeapi
import math
import alpaca_conf_live
import code
import importlib

def reload():
    importlib.reload(functions)

api = tradeapi.REST()
account = api.get_account()

code.interact(local=dict(globals(), **locals()))


# def purchase(symbol):
#     quote = sh.get_last_quote(symbol)
#     price = float(quote.askprice)
#     quantity = math.floor(float(account.cash)/price)
#     print(account.cash)
#     print(price)
#     print(quantity)
#     # input("?")
#     ans = api.submit_order(
#                 symbol=symbol,
#                 qty=quantity,
#                 side='buy',
#                 type='limit',
#                 time_in_force='day',
#                 limit_price=price,
#                 stop_price=None)

stop=1
