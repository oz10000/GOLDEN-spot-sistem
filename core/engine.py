# core/engine.py
# Motor principal del Golden Capital Engine Ω — CORREGIDO (sin límite de activos)

import pandas as pd
import json
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

from strategies.spot_strategy import SpotStrategy
from strategies.margin_strategy import MarginStrategy
from strategies.futures_strategy import FuturesStrategy
from optimization.top_five import TopFiveOptimizer
from risk.position_sizing import PositionSizing
from analytics.statistics import StatisticsCalculator
from data.market_data import MarketData
from core.backtester import Backtester

logger = logging.getLogger(__name__)

class GoldenEngine:
    """Motor principal del Golden Capital Engine Ω."""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.market_data = MarketData()
        self.top_five = TopFiveOptimizer()
        self.position_sizing = PositionSizing(
            capital=self.config.get('capital', 1000.0),
            risk_per_trade=self.config.get('risk_per_trade', 0.02)
        )
        self.strategies = {
            'spot': SpotStrategy(self.config.get('spot_params', {})),
            'margin': MarginStrategy(self.config.get('margin_params', {})),
            'futures': FuturesStrategy(self.config.get('futures_params', {}))
        }
        self.results = {}
        self.results_dir = "data/results"
        os.makedirs(self.results_dir, exist_ok=True)

    def scan_universe(self, markets: List[str] = ['spot', 'margin', 'futures'],
                      max_assets: Optional[int] = None) -> List[Dict]:
        """
        Escanea el universo completo de Binance con datos reales.
        Si max_assets es None, analiza TODOS los activos disponibles.
        """
        all_results = []
        for market in markets:
            symbols = self.market_data.get_symbols(market)
            if max_assets is not None:
                symbols = symbols[:max_assets]  # Para pruebas
            logger.info(f"Escaneando {market}: {len(symbols)} activos")

            filtered_count = 0
            signal_count = 0
            no_data_count = 0
            no_signal_count = 0

            for symbol in symbols:
                try:
                    df = self.market_data.get_historical(symbol, market)
                    if df is None or len(df) < 100:
                        no_data_count += 1
                        continue

                    strategy = self.strategies.get(market)
                    if not strategy:
                        continue

                    signal = strategy.generate_signal(df)
                    if not signal:
                        no_signal_count += 1
                        continue

                    signal_count += 1
                    # Backtesting real con datos históricos
                    bt = Backtester(df, self.config)
                    metrics = bt.run(signal)

                    result = {
                        'symbol': symbol,
                        'market': market,
                        'signal': signal,
                        'metrics': metrics,
                        'score': signal.get('confidence', 0) * metrics.get('profit_factor', 1.0),
                        'win_rate': metrics.get('win_rate', 0),
                        'profit_factor': metrics.get('profit_factor', 0),
                        'sharpe': metrics.get('sharpe', 0),
                        'max_drawdown': metrics.get('max_drawdown', 0),
                        'total_trades': metrics.get('total_trades', 0),
                        'timestamp': datetime.now().isoformat()
                    }
                    all_results.append(result)

                except Exception as e:
                    logger.debug(f"Error con {symbol}: {e}")
                    continue

            logger.info(f"{market}: {signal_count} señales de {len(symbols)} activos "
                       f"(sin datos: {no_data_count}, sin señal: {no_signal_count})")

        return all_results

    def get_top_five(self, assets: List[Dict]) -> pd.DataFrame:
        """Retorna TOP FIVE activos."""
        return self.top_five.rank(assets)

    def get_signals(self, assets: List[Dict]) -> Dict:
        """Retorna señales por mercado."""
        signals = {'spot': None, 'margin': None, 'futures': None}
        for asset in assets:
            market = asset.get('market')
            if market in signals and signals[market] is None:
                signals[market] = asset.get('signal')
        return signals

    def save_results(self, assets: List[Dict], top5: pd.DataFrame):
        """Guarda resultados en archivos JSON."""
        # Guardar ranking completo
        ranking_path = os.path.join(self.results_dir, 'ranking.json')
        with open(ranking_path, 'w') as f:
            json.dump(assets, f, indent=2, default=str)

        # Guardar TOP FIVE
        top5_path = os.path.join(self.results_dir, 'top_five.json')
        if not top5.empty:
            top5.to_json(top5_path, orient='records', indent=2)

        # Guardar señales
        signals = self.get_signals(assets)
        signals_path = os.path.join(self.results_dir, 'signals.json')
        with open(signals_path, 'w') as f:
            json.dump(signals, f, indent=2, default=str)

        logger.info(f"Resultados guardados en {self.results_dir}")

    def run(self) -> Dict:
        """Ejecuta el sistema completo con datos reales."""
        logger.info("Iniciando escaneo del universo...")

        # Escanear universo (sin límite)
        assets = self.scan_universe(max_assets=None)

        if not assets:
            logger.warning("No se encontraron activos con señales válidas.")
            return {'assets': [], 'top5': pd.DataFrame(), 'signals': {}, 'metrics': {}}

        # TOP FIVE
        top5 = self.get_top_five(assets)

        # Señales
        signals = self.get_signals(assets)

        # Métricas globales (a partir de trades reales)
        all_trades = []
        for asset in assets:
            if asset.get('metrics', {}).get('trades_df') is not None:
                df_trades = asset['metrics']['trades_df']
                if not df_trades.empty:
                    all_trades.append(df_trades)

        if all_trades:
            combined_trades = pd.concat(all_trades, ignore_index=True)
            metrics = StatisticsCalculator.compute_all(combined_trades, self.config.get('capital', 1000.0))
        else:
            metrics = {}

        self.results = {
            'assets': assets,
            'top5': top5,
            'signals': signals,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }

        # Guardar resultados
        self.save_results(assets, top5)

        return self.results
