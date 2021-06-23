import time

import pandas as pd
from datetime import datetime
import ccxt
from time_test import binance_currencies,ccxt_currencies

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


def check_buy_sell_signals(df,symbol,cost):
    global in_position

    print("checking for buy and sell signals")
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        print("buy")

    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        print("sell")

exchange = ccxt.binance({
    "apiKey": "m0NJtJo4u1uIv07yu7lFrcWBnVUDhqHiykLvWMe3V2PArQlsE6ja89Xm8K5ebEes",
    "secret": "aK8eOMK1ykDqy7vw8LqYE9X1jFrULlN25kqUZEKAV0c68qoi7WIQAhsx8mUTrKkf"
})
for i in range(len(binance_currencies)):
    print(f"Fetching new bars for {binance_currencies[i]}")

    bars = exchange.fetch_ohlcv(f'{ccxt_currencies[i]}', timeframe="1m", limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    supertrend_data = supertrend(df)
    print(supertrend_data)

    check_buy_sell_signals(supertrend_data, symbol=binance_currencies[i], cost=10)
    print("####################"+"\n")
    time.sleep(1)