# strategies/spot_strategy.py
# Estrategia para Spot (LONG) — CORREGIDA (umbrales más flexibles)

import pandas as pd
import numpy as np
from .base import BaseStrategy
from signals.signal_engine import compute_pidelta_score, classify_regime

class SpotStrategy(BaseStrategy):
    """Estrategia optimizada para Spot: LONG con bajo riesgo."""

    def generate_signal(self, df: pd.DataFrame) -> Optional[Dict]:
        if df is None or len(df) < 60:
            return None

        # 1. Score PiDelta (más permisivo)
        score = compute_pidelta_score(df)
        if score < self.params.get('min_score', 0.30):
            return None

        # 2. Filtros de tendencia (más flexibles)
        adx_val = self._adx(df).iloc[-1]
        ker_val = self._ker(df['close']).iloc[-1]
        if adx_val < self.params.get('adx_threshold', 20) or ker_val < self.params.get('ker_threshold', 0.45):
            return None

        # 3. Régimen (permitir Normal y Tendencia Débil)
        regime = classify_regime(df)
        if regime in ['Chop', 'Indefinido']:
            return None

        # 4. Solo LONG
        if score < 0:
            return None

        # 5. Confirmación de tendencia (más laxa)
        current = df['close'].iloc[-1]
        ema50 = self._ema(df['close'], 50).iloc[-1]
        ema200 = self._ema(df['close'], 200).iloc[-1]
        if current < ema50 * 0.98 or current < ema200 * 0.98:
            return None

        # 6. VWAP (tolerancia 2%)
        vwap_val = vwap(df).iloc[-1]
        if current < vwap_val * 0.98:
            return None

        # 7. Entrada
        atr_val = self._atr(df).iloc[-1]
        tp_mult = self.params.get('tp_mult', 2.0)
        sl_mult = self.params.get('sl_mult', 0.8)

        return {
            'direction': 'LONG',
            'entry': current,
            'tp': current + atr_val * tp_mult,
            'sl': current - atr_val * sl_mult,
            'score': score,
            'regime': regime,
            'confidence': min(1.0, score / 0.4),
            'leverage': 1.0,
            'risk': self.params.get('risk_per_trade', 0.02)
        }

    def get_risk_params(self) -> Dict:
        return {
            'max_leverage': 1.0,
            'risk_per_trade': 0.02,
            'max_positions': 3,
            'allow_short': False
        }

    def get_cost_params(self) -> Dict:
        return {
            'commission': 0.001,
            'slippage': 0.0005,
            'funding': 0.0,
            'margin_interest': 0.0
        }

    # Helper methods (sin cambios)
    def _atr(self, df, period=14):
        tr = np.maximum(df['high'] - df['low'],
                        np.maximum(abs(df['high'] - df['close'].shift()),
                                   abs(df['low'] - df['close'].shift())))
        return tr.rolling(period).mean()

    def _adx(self, df, period=14):
        up = df['high'].diff()
        down = -df['low'].diff()
        plus = pd.Series(0.0, index=df.index)
        minus = pd.Series(0.0, index=df.index)
        plus[(up > down) & (up > 0)] = up
        minus[(down > up) & (down > 0)] = down
        atr_val = self._atr(df, period)
        plus_di = 100 * plus.rolling(period).mean() / atr_val
        minus_di = 100 * minus.rolling(period).mean() / atr_val
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
        return dx.rolling(period).mean()

    def _ker(self, close, period=10):
        abs_diff = abs(close.diff(period))
        sum_abs = close.diff().abs().rolling(period).sum()
        return (abs_diff / (sum_abs + 1e-9)).fillna(0)

    def _ema(self, series, period):
        return series.ewm(span=period, adjust=False).mean()
