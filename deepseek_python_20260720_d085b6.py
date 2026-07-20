# optimization/top_assets.py
# Ranking de activos por calidad (independiente de señales)

import pandas as pd
import numpy as np
from data.market_data import MarketData
from signals.signal_engine import compute_pidelta_score, classify_regime
from indicators import atr, adx, ker, ema
import logging

logger = logging.getLogger(__name__)

class TopAssetsRanker:
    """
    Clasifica todos los activos por métricas de calidad:
    - Volumen
    - Volatilidad
    - Tendencia (ADX)
    - Eficiencia (KER)
    - Score PiDelta
    - Régimen
    """

    def __init__(self):
        self.market_data = MarketData()

    def rank(self, markets: List[str] = ['spot', 'margin', 'futures'],
             max_assets: int = 200) -> pd.DataFrame:
        """
        Genera ranking de activos para cada mercado.
        """
        all_assets = []

        for market in markets:
            symbols = self.market_data.get_symbols(market)
            if max_assets:
                symbols = symbols[:max_assets]
            logger.info(f"Clasificando activos en {market}: {len(symbols)}")

            for symbol in symbols:
                try:
                    df = self.market_data.get_historical(symbol, market, max_days=30)
                    if df is None or len(df) < 60:
                        continue

                    # Métricas
                    close = df['close']
                    volume = df['volume'].mean()
                    volatility = close.pct_change().std() * np.sqrt(252) * 100
                    adx_val = adx(df, 14).iloc[-1]
                    ker_val = ker(close, 10).iloc[-1]
                    score = compute_pidelta_score(df)
                    regime = classify_regime(df)

                    # Tendencia (precio vs EMAs)
                    ema50 = ema(close, 50).iloc[-1]
                    ema200 = ema(close, 200).iloc[-1]
                    current = close.iloc[-1]
                    trend_strength = 0.0
                    if current > ema50:
                        trend_strength += 0.5
                    if current > ema200:
                        trend_strength += 0.5

                    # Score compuesto (normalizado)
                    volume_score = min(1.0, volume / 1_000_000)
                    volatility_score = min(1.0, volatility / 100)
                    adx_score = min(1.0, adx_val / 40)
                    ker_score = ker_val
                    score_norm = min(1.0, abs(score) / 0.5)

                    quality_score = (
                        volume_score * 0.20 +
                        volatility_score * 0.10 +
                        adx_score * 0.25 +
                        ker_score * 0.20 +
                        score_norm * 0.15 +
                        trend_strength * 0.10
                    )

                    all_assets.append({
                        'symbol': symbol,
                        'market': market,
                        'volume_score': volume_score,
                        'volatility': volatility,
                        'adx': adx_val,
                        'ker': ker_val,
                        'score': score,
                        'regime': regime,
                        'trend_strength': trend_strength,
                        'quality_score': quality_score,
                        'current_price': current,
                    })

                except Exception as e:
                    logger.debug(f"Error con {symbol}: {e}")
                    continue

        df_rank = pd.DataFrame(all_assets)
        if not df_rank.empty:
            df_rank = df_rank.sort_values('quality_score', ascending=False)
        return df_rank

    def get_top_ten(self, df_rank: pd.DataFrame, market: Optional[str] = None) -> pd.DataFrame:
        """Retorna Top 10 de un mercado específico o global."""
        if df_rank.empty:
            return pd.DataFrame()
        if market:
            df_rank = df_rank[df_rank['market'] == market]
        return df_rank.head(10)

    def get_top_ten_by_market(self, df_rank: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Retorna Top 10 para cada mercado."""
        if df_rank.empty:
            return {}
        result = {}
        for market in df_rank['market'].unique():
            result[market] = df_rank[df_rank['market'] == market].head(10)
        return result