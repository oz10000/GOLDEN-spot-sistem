# data/market_data.py
# Gestión de datos de mercado con caché y descarga desde Binance
# MODIFICADO: días históricos aumentados a 200 para indicadores de largo plazo

import ccxt
import pandas as pd
import os
import pickle
import hashlib
import time
from datetime import datetime, timedelta

class MarketData:
    def __init__(self, cache_dir="data/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.exchanges = self._init_exchanges()

    def _init_exchanges(self):
        exchanges = {}
        for market in ['spot', 'margin', 'future', 'swap']:
            try:
                ex = getattr(ccxt, 'binance')({
                    'enableRateLimit': True,
                    'options': {'defaultType': 'spot' if market == 'margin' else market}
                })
                ex.load_markets()
                exchanges[market] = ex
            except:
                exchanges[market] = None
        return exchanges

    def get_symbols(self, market):
        ex = self.exchanges.get(market)
        if not ex:
            return []
        try:
            tickers = ex.fetch_tickers()
            symbols = []
            for sym, ticker in tickers.items():
                if ticker.get('quoteVolume', 0) > 500_000:
                    symbols.append(sym)
            return symbols
        except:
            return []

    def get_historical(self, symbol, market='spot', timeframe='1h', days=200):
        """
        Descarga datos históricos con caché.
        MODIFICADO: días por defecto cambiados de 30 a 200.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        cache_key = hashlib.md5(f"{market}_{symbol}_{timeframe}_{days}".encode()).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.pkl")

        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except:
                pass

        ex = self.exchanges.get(market)
        if not ex:
            return None

        since = int(start_date.timestamp() * 1000)
        all_data = []
        while True:
            try:
                ohlcv = ex.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
                if not ohlcv:
                    break
                all_data.extend(ohlcv)
                since = ohlcv[-1][0] + 1
                if ohlcv[-1][0] >= int(end_date.timestamp() * 1000):
                    break
                time.sleep(0.1)
            except:
                break

        if not all_data:
            return None

        df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        with open(cache_path, 'wb') as f:
            pickle.dump(df, f)

        return df
