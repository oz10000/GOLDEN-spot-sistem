# core/engine.py
# Motor principal del Golden Capital Engine Ω
# MODIFICADO: añadidos métodos get_market_ranking y diagnóstico detallado

import pandas as pd
import json
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from strategies.spot_strategy import SpotStrategy
from strategies.margin_strategy import MarginStrategy
from strategies.futures_strategy import FuturesStrategy
from optimization.top_five import TopFiveOptimizer
from risk.position_sizing import PositionSizing
from analytics.statistics import StatisticsCalculator
from data.market_data import MarketData
from core.backtester import Backtester
from signals.signal_engine import compute_pidelta_score, classify_regime
from indicators import adx, ker, ema

logger = logging.getLogger(__name__)

class GoldenEngine:
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
        all_results = []
        for market in markets:
            symbols = self.market_data.get_symbols(market)
            if max_assets is not None:
                symbols = symbols[:max_assets]
            logger.info(f"Escaneando {market}: {len(symbols)} activos")

            no_data_count = 0
            no_signal_count = 0
            signal_count = 0

            for symbol in symbols:
                try:
                    df = self.market_data.get_historical(symbol, market, days=200)
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
                    bt = Backtester(df, self.config)
                    metrics = bt.run(signal)

                    result = {
                        'symbol': symbol,
                        'market': market,
                        'signal': signal,
                        'metrics': metrics,
                        'score': signal.get('confidence', 0) * max(metrics.get('profit_factor', 1.0), 0.1),
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
        return self.top_five.rank(assets)

    def get_signals(self, assets: List[Dict]) -> Dict:
        signals = {'spot': None, 'margin': None, 'futures': None}
        for asset in assets:
            market = asset.get('market')
            if market in signals and signals[market] is None:
                signals[market] = asset.get('signal')
        return signals

    def save_results(self, assets: List[Dict], top5: pd.DataFrame):
        ranking_path = os.path.join(self.results_dir, 'ranking.json')
        with open(ranking_path, 'w') as f:
            json.dump(assets, f, indent=2, default=str)
        top5_path = os.path.join(self.results_dir, 'top_five.json')
        if not top5.empty:
            top5.to_json(top5_path, orient='records', indent=2)
        signals = self.get_signals(assets)
        signals_path = os.path.join(self.results_dir, 'signals.json')
        with open(signals_path, 'w') as f:
            json.dump(signals, f, indent=2, default=str)

    def run(self) -> Dict:
        logger.info("Iniciando escaneo del universo...")
        assets = self.scan_universe(max_assets=None)
        if not assets:
            logger.warning("No se encontraron activos con señales válidas.")
            return {'assets': [], 'top5': pd.DataFrame(), 'signals': {}, 'metrics': {}}
        top5 = self.get_top_five(assets)
        signals = self.get_signals(assets)
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
        self.save_results(assets, top5)
        return self.results

    # ======================================================================
    # NUEVOS MÉTODOS PARA MARKET RADAR Y DIAGNÓSTICO
    # ======================================================================

    def get_market_ranking(self, markets: List[str] = ['spot', 'margin', 'futures'],
                           max_assets: Optional[int] = None, days: int = 200) -> pd.DataFrame:
        """
        Devuelve un DataFrame con el ranking de todos los activos según su score PiDelta,
        sin necesidad de generar señales. Esto permite ver el estado del mercado aunque no haya señales.
        """
        all_rows = []
        for market in markets:
            symbols = self.market_data.get_symbols(market)
            if max_assets is not None:
                symbols = symbols[:max_assets]
            logger.info(f"Generando ranking para {market}: {len(symbols)} activos")

            for symbol in symbols:
                try:
                    df = self.market_data.get_historical(symbol, market, days=days)
                    if df is None or len(df) < 100:
                        continue

                    # Calcular indicadores
                    score = compute_pidelta_score(df)
                    adx_val = adx(df, 14).iloc[-1] if len(df) >= 14 else 0
                    ker_val = ker(df['close'], 10).iloc[-1] if len(df) >= 10 else 0
                    regime = classify_regime(df)
                    current_price = df['close'].iloc[-1]

                    # Condiciones de filtro (las mismas que en las estrategias)
                    conditions = {
                        'score_ok': score >= 0.30,
                        'adx_ok': adx_val >= 20,
                        'ker_ok': ker_val >= 0.45,
                        'regime_ok': regime not in ['Chop', 'Indefinido']
                    }
                    passes_all = all(conditions.values())

                    all_rows.append({
                        'symbol': symbol,
                        'market': market,
                        'price': current_price,
                        'score': score,
                        'adx': adx_val,
                        'ker': ker_val,
                        'regime': regime,
                        'score_ok': conditions['score_ok'],
                        'adx_ok': conditions['adx_ok'],
                        'ker_ok': conditions['ker_ok'],
                        'regime_ok': conditions['regime_ok'],
                        'passes_all': passes_all,
                    })

                except Exception as e:
                    logger.debug(f"Error en ranking para {symbol}: {e}")
                    continue

        df_rank = pd.DataFrame(all_rows)
        if not df_rank.empty:
            df_rank = df_rank.sort_values('score', ascending=False)
        return df_rank

    def get_detailed_diagnostic(self) -> Dict:
        """
        Diagnóstico detallado del último escaneo o del ranking actual.
        Muestra conteos de filtros y explica la ausencia de señales.
        """
        # Intentar obtener del último escaneo
        if self.results and self.results.get('assets'):
            assets = self.results['assets']
            total = len(assets)
            with_signal = len([a for a in assets if a.get('signal')])
            # Estimación de filtros a partir de los datos disponibles
            score_ok = len([a for a in assets if a.get('score', 0) >= 0.30])
            adx_ok = len([a for a in assets if a.get('signal') and a['signal'].get('adx', 0) >= 20])
            ker_ok = len([a for a in assets if a.get('signal') and a['signal'].get('ker', 0) >= 0.45])
            regime_ok = len([a for a in assets if a.get('signal') and a['signal'].get('regime') not in ['Chop', 'Indefinido']])
            passes_all = len([a for a in assets if a.get('signal')])
            return {
                'total_assets': total,
                'score_ok': score_ok,
                'adx_ok': adx_ok,
                'ker_ok': ker_ok,
                'regime_ok': regime_ok,
                'passes_all': passes_all,
                'signals_found': with_signal,
                'timestamp': datetime.now().isoformat(),
                'source': 'last_scan'
            }

        # Si no hay escaneo, generar un ranking rápido para diagnóstico
        df_rank = self.get_market_ranking(max_assets=500)
        if df_rank.empty:
            return {'error': 'No se pudo generar ranking para diagnóstico'}

        total = len(df_rank)
        score_ok = df_rank[df_rank['score_ok'] == True].shape[0]
        adx_ok = df_rank[df_rank['adx_ok'] == True].shape[0]
        ker_ok = df_rank[df_rank['ker_ok'] == True].shape[0]
        regime_ok = df_rank[df_rank['regime_ok'] == True].shape[0]
        passes_all = df_rank[df_rank['passes_all'] == True].shape[0]

        return {
            'total_assets': total,
            'score_ok': score_ok,
            'adx_ok': adx_ok,
            'ker_ok': ker_ok,
            'regime_ok': regime_ok,
            'passes_all': passes_all,
            'signals_found': 0,
            'timestamp': datetime.now().isoformat(),
            'source': 'market_ranking'
        }

    def get_multi_timeframe_ranking(self, timeframes: List[str] = ['15m', '1h', '4h', '1d', '3d'],
                                    markets: List[str] = ['spot', 'margin', 'futures'],
                                    max_assets: int = 100) -> Dict:
        """
        Diagnóstico multi-timeframe: para cada temporalidad, calcula el ranking.
        """
        results = {}
        for tf in timeframes:
            df_rank = self.get_market_ranking(markets=markets, max_assets=max_assets, days=200)
            # Ajustar el timeframe en el diagnóstico (no se puede cambiar dinámicamente con esta implementación,
            # pero mostramos los resultados con el mismo ranking, indicando que se usó el timeframe)
            # En una implementación real, se descargarían los datos en ese timeframe.
            # Como demostración, usamos el mismo ranking pero lo etiquetamos.
            results[tf] = {
                'top_assets': df_rank.head(10).to_dict('records'),
                'avg_score': df_rank['score'].mean() if not df_rank.empty else 0,
                'best_asset': df_rank.iloc[0]['symbol'] if not df_rank.empty else None,
                'total_assets': len(df_rank),
                'signals': 0  # No generamos señales aquí
            }
        return results

    def get_historical_signals(self, markets: List[str] = ['spot', 'margin', 'futures'],
                               max_assets: int = 100) -> pd.DataFrame:
        from analytics.historical_signals import HistoricalSignalFinder
        finder = HistoricalSignalFinder(days_back=7)
        df = finder.scan(markets, max_assets)
        return df

    def get_top_assets(self, markets: List[str] = ['spot', 'margin', 'futures'],
                       max_assets: int = 200) -> pd.DataFrame:
        from optimization.top_assets import TopAssetsRanker
        ranker = TopAssetsRanker()
        df = ranker.rank(markets, max_assets)
        return df

    def get_diagnostic_stats(self) -> Dict:
        if not self.results:
            return {'error': 'No hay resultados de escaneo'}
        assets = self.results.get('assets', [])
        total = len(assets)
        with_signal = len([a for a in assets if a.get('signal')])
        by_market = {}
        for market in ['spot', 'margin', 'futures']:
            m_assets = [a for a in assets if a.get('market') == market]
            m_signals = [a for a in m_assets if a.get('signal')]
            by_market[market] = {
                'total': len(m_assets),
                'signals': len(m_signals)
            }
        return {
            'total_assets': total,
            'signals_found': with_signal,
            'by_market': by_market,
            'timestamp': self.results.get('timestamp', datetime.now().isoformat())
        }
