import ccxt
import schedule
from binance.client import Client
from time_test import binance_currencies, ccxt_currencies
import futures_test as futures
from sms import send_mail
from time_test import currencies
from datetime import datetime
import time

client = Client("m0NJtJo4u1uIv07yu7lFrcWBnVUDhqHiykLvWMe3V2PArQlsE6ja89Xm8K5ebEes","aK8eOMK1ykDqy7vw8LqYE9X1jFrULlN25kqUZEKAV0c68qoi7WIQAhsx8mUTrKkf")

import pandas as pd
pd.set_option('display.max_rows', None)


import warnings

warnings.filterwarnings('ignore')


from datetime import datetime
import time
timeframe="1h"

exchange = ccxt.binance({
    "apiKey": "m0NJtJo4u1uIv07yu7lFrcWBnVUDhqHiykLvWMe3V2PArQlsE6ja89Xm8K5ebEes",
    "secret": "aK8eOMK1ykDqy7vw8LqYE9X1jFrULlN25kqUZEKAV0c68qoi7WIQAhsx8mUTrKkf"
})


def tr(data):
    data['previous_close'] = data['close'].shift(1)
    data['high-low'] = abs(data['high'] - data['low'])
    data['high-pc'] = abs(data['high'] - data['previous_close'])
    data['low-pc'] = abs(data['low'] - data['previous_close'])

    tr = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)

    return tr


def atr(data, period):
    data['tr'] = tr(data)
    atr = data['tr'].rolling(period).mean()

    return atr


def supertrend(df, period=7, atr_multiplier=3):
    hl2 = (df['high'] + df['low']) / 2
    df['atr'] = atr(df, period)
    df['upperband'] = hl2 + (atr_multiplier * df['atr'])
    df['lowerband'] = hl2 - (atr_multiplier * df['atr'])
    df['in_uptrend'] = True

    for current in range(1, len(df.index)):
        previous = current - 1

        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current] = True
        elif df['close'][current] < df['lowerband'][previous]:
            df['in_uptrend'][current] = False
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]

            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]

            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]

    return df


in_position = False


def check_buy_sell_signals(df,symbol,cost,trade_time):
    global in_position

    print("checking for buy and sell signals")
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        print(symbol)
        futures.cancel_sell_order(symbol)
        futures.buy(symbol,cost)
        send_mail("LONG",f"""LONGED {symbol} time: {trade_time}""")
        print("changed to uptrend, buy")

    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        print(symbol)
        futures.cancel_buy_order(symbol)
        futures.sell(symbol,cost)
        send_mail("SHORT",f"""SHORTED {symbol} time: {trade_time}""")
        print("changed to downtrend, sell")


def run_bot():
    print("waiting for the candle to close")
    global timeframe
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        if int(current_time[6]) == 0 and int(current_time[7])==0:
            print(current_time)
            break
    for i in range(len(binance_currencies)):
        print(f"Fetching new bars for {datetime.now().isoformat()}  COIN:{binance_currencies[i]}")
        print("#########")
        print(current_time)
        print("#########\n")
        print(ccxt_currencies[i])
        bars = exchange.fetch_ohlcv(symbol=ccxt_currencies[i], timeframe=timeframe, limit=1000)
        df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        supertrend_data = supertrend(df)
        print(supertrend_data)
        check_buy_sell_signals(supertrend_data,symbol=binance_currencies[i],cost=10,trade_time=current_time)



def interval(timeframe):
    if len(timeframe)==3:
        num = timeframe[0] + timeframe[1]
        if timeframe[2]=='m':
            interval=60*int(num)
            return(interval)
        elif timeframe[2]=='h':
            interval=3600*int(num)
            return(interval)
    else:
        if timeframe[1]=='m':
            interval=60*int(timeframe[0])
            return(interval)
        elif timeframe[1]=='h':
            interval=3600*int(timeframe[0])
            return(interval)
        elif timeframe[1]=='d':
            interval = 3600*24*int(timeframe[0])
            return (interval)
        elif timeframe[1]=='w':
            interval = 3600*24*7*int(timeframe[0])
            return (interval)
        elif timeframe[1] == 'M':
            interval = 2628*1000*int(timeframe[0])
            return (interval)


schedule.every(20).seconds.do(run_bot)


while True:
    schedule.run_pending()
    time.sleep(1)