# analytics/historical_signals.py
# Busca señales válidas en datos históricos recientes (últimos 7 días)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from data.market_data import MarketData
from strategies.spot_strategy import SpotStrategy
from strategies.margin_strategy import MarginStrategy
from strategies.futures_strategy import FuturesStrategy
from core.backtester import Backtester
import logging

logger = logging.getLogger(__name__)

class HistoricalSignalFinder:
    """
    Busca señales que ocurrieron en los últimos N días (por defecto 7)
    y las almacena con sus resultados.
    """

    def __init__(self, days_back: int = 7):
        self.days_back = days_back
        self.market_data = MarketData()
        self.strategies = {
            'spot': SpotStrategy({}),
            'margin': MarginStrategy({}),
            'futures': FuturesStrategy({})
        }
        self.signals = []

    def scan(self, markets: List[str] = ['spot', 'margin', 'futures'],
             max_assets: int = 100) -> pd.DataFrame:
        """
        Escanea activos en busca de señales en los últimos 'days_back' días.
        Retorna DataFrame con las señales encontradas.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.days_back)

        all_signals = []

        for market in markets:
            symbols = self.market_data.get_symbols(market)
            if max_assets:
                symbols = symbols[:max_assets]
            logger.info(f"Buscando señales históricas en {market}: {len(symbols)} activos")

            for symbol in symbols:
                try:
                    # Descargar datos históricos completos
                    df = self.market_data.get_historical(symbol, market, max_days=30)
                    if df is None or len(df) < 60:
                        continue

                    # Generar señal con la estrategia
                    strategy = self.strategies.get(market)
                    if not strategy:
                        continue

                    signal = strategy.generate_signal(df)
                    if not signal:
                        continue

                    # Simular backtesting para obtener resultado
                    bt = Backtester(df, {})
                    metrics = bt.run(signal)

                    # Determinar si la señal ocurrió en los últimos días
                    # (usamos la fecha de la última vela como referencia)
                    signal_time = df.index[-1]
                    if (end_date - signal_time).days > self.days_back:
                        continue

                    all_signals.append({
                        'symbol': symbol,
                        'market': market,
                        'timestamp_signal': signal_time,
                        'direction': signal.get('direction', 'LONG'),
                        'entry_price': signal.get('entry', 0),
                        'exit_price': metrics.get('exit_price', 0),
                        'result': 'win' if metrics.get('win_rate', 0) > 0.5 else 'loss',
                        'profit_loss': metrics.get('total_pnl', 0),
                        'mfe': metrics.get('max_mfe', 0),
                        'mae': metrics.get('max_mae', 0),
                        'duration': metrics.get('duration_hours', 0),
                        'confidence': signal.get('confidence', 0),
                        'score': signal.get('score', 0),
                        'regime': signal.get('regime', 'N/A'),
                        'exit_reason': metrics.get('exit_reason', 'N/A'),
                    })

                except Exception as e:
                    logger.debug(f"Error con {symbol}: {e}")
                    continue

        self.signals = all_signals
        df_signals = pd.DataFrame(all_signals)
        return df_signals

    def get_summary(self, df_signals: pd.DataFrame) -> Dict:
        """Genera resumen estadístico de las señales encontradas."""
        if df_signals.empty:
            return {
                'total': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'avg_score': 0,
                'by_market': {}
            }

        wins = df_signals[df_signals['result'] == 'win']
        total = len(df_signals)
        win_rate = len(wins) / total if total > 0 else 0

        total_win = wins['profit_loss'].sum() if not wins.empty else 0
        total_loss = abs(df_signals[df_signals['result'] == 'loss']['profit_loss'].sum()) if len(df_signals[df_signals['result'] == 'loss']) > 0 else 1e-9
        pf = total_win / total_loss

        avg_score = df_signals['score'].mean() if not df_signals.empty else 0

        by_market = {}
        for market in df_signals['market'].unique():
            sub = df_signals[df_signals['market'] == market]
            by_market[market] = {
                'total': len(sub),
                'win_rate': len(sub[sub['result'] == 'win']) / len(sub) if len(sub) > 0 else 0
            }

        return {
            'total': total,
            'win_rate': win_rate,
            'profit_factor': pf,
            'avg_score': avg_score,
            'by_market': by_market
        }

    def get_top_signals(self, df_signals: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """Retorna las N mejores señales por score."""
        if df_signals.empty:
            return pd.DataFrame()
        return df_signals.sort_values('score', ascending=False).head(n)
