# strategies/futures_strategy.py
# Estrategia para Futures (LONG/SHORT) — CORREGIDA (umbrales más flexibles)

import pandas as pd
import numpy as np
from .base import BaseStrategy
from signals.signal_engine import compute_pidelta_score, classify_regime

class FuturesStrategy(BaseStrategy):
    """Estrategia optimizada para Futures: LONG/SHORT con leverage dinámico."""

    def generate_signal(self, df: pd.DataFrame) -> Optional[Dict]:
        if df is None or len(df) < 60:
            return None

        # 1. Score PiDelta (más permisivo)
        score = compute_pidelta_score(df)
        if abs(score) < self.params.get('min_score', 0.25):
            return None

        # 2. Filtros de tendencia (más flexibles)
        adx_val = self._adx(df).iloc[-1]
        ker_val = self._ker(df['close']).iloc[-1]
        if adx_val < self.params.get('adx_threshold', 18) or ker_val < self.params.get('ker_threshold', 0.40):
            return None

        # 3. Régimen
        regime = classify_regime(df)
        if regime == 'Chop':
            return None

        # 4. Dirección (LONG o SHORT)
        direction = 'LONG' if score > 0 else 'SHORT'

        # 5. Volatilidad y funding
        atr_val = self._atr(df).iloc[-1]
        current = df['close'].iloc[-1]
        atr_pct = atr_val / current * 100
        if atr_pct < 0.3 or atr_pct > 5.0:
            return None

        # 6. Confirmación de tendencia (solo para LONG)
        if direction == 'LONG':
            ema50 = self._ema(df['close'], 50).iloc[-1]
            ema200 = self._ema(df['close'], 200).iloc[-1]
            if current < ema50 * 0.98 or current < ema200 * 0.98:
                return None
        else:  # SHORT
            ema50 = self._ema(df['close'], 50).iloc[-1]
            ema200 = self._ema(df['close'], 200).iloc[-1]
            if current > ema50 * 1.02 or current > ema200 * 1.02:
                return None

        # 7. Leverage dinámico
        leverage = self._calculate_leverage(atr_pct, regime)
        tp_mult = self.params.get('tp_mult', 2.0)
        sl_mult = self.params.get('sl_mult', 0.8)

        if direction == 'LONG':
            tp = current + atr_val * tp_mult
            sl = current - atr_val * sl_mult
        else:
            tp = current - atr_val * tp_mult
            sl = current + atr_val * sl_mult

        return {
            'direction': direction,
            'entry': current,
            'tp': tp,
            'sl': sl,
            'score': score,
            'regime': regime,
            'confidence': min(1.0, abs(score) / 0.35),
            'leverage': leverage,
            'funding': self.params.get('funding_rate', 0.0001),
            'atr_pct': atr_pct,
            'holding_hours': self.params.get('holding_hours', 24),
            'risk': self.params.get('risk_per_trade', 0.03)
        }

    def _calculate_leverage(self, atr_pct: float, regime: str) -> float:
        """Calcula leverage dinámico basado en volatilidad y régimen."""
        base = self.params.get('max_leverage', 5)
        if regime == 'Alta_Volatilidad':
            return max(1.0, base * 0.3)
        if regime == 'Tendencia_Fuerte':
            return min(base, base * 0.8)
        if atr_pct > 3.0:
            return max(1.0, base * 0.4)
        return min(base, max(1.0, base * (1.5 / (atr_pct + 0.5))))

    def get_risk_params(self) -> Dict:
        return {
            'max_leverage': 5.0,
            'risk_per_trade': 0.03,
            'max_positions': 2,
            'allow_short': True,
            'max_holding_hours': 48
        }

    def get_cost_params(self) -> Dict:
        return {
            'commission': 0.0005,
            'slippage': 0.0005,
            'funding': 0.0001,
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
