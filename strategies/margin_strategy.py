# strategies/margin_strategy.py
# Estrategia para Margin (LONG) — CORREGIDA (umbrales flexibles)

import pandas as pd
import numpy as np
from typing import Optional, Dict
from .base import BaseStrategy
from signals.signal_engine import compute_pidelta_score, classify_regime
from indicators import vwap


class MarginStrategy(BaseStrategy):
    """Estrategia optimizada para Margin: LONG con leverage moderado y control de interés."""

    def generate_signal(self, df: pd.DataFrame) -> Optional[Dict]:
        if df is None or len(df) < 60:
            return None

        # 1. Score PiDelta (más permisivo)
        score = compute_pidelta_score(df)
        if score < self.params.get('min_score', 0.32):
            return None

        # 2. Filtros de tendencia (más flexibles)
        adx_val = self._adx(df).iloc[-1]
        ker_val = self._ker(df['close']).iloc[-1]
        if adx_val < self.params.get('adx_threshold', 22) or ker_val < self.params.get('ker_threshold', 0.48):
            return None

        # 3. Régimen (permitir Normal y Tendencia Débil)
        regime = classify_regime(df)
        if regime in ['Chop', 'Indefinido', 'Alta_Volatilidad']:
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

        # 7. Volatilidad
        atr_val = self._atr(df).iloc[-1]
        atr_pct = atr_val / current * 100
        if atr_pct < 0.5 or atr_pct > 4.0:
            return None

        # 8. Coste de interés
        holding_hours = self.params.get('holding_hours', 24)
        interest_rate = self.params.get('interest_rate', 0.0001)
        interest_cost = interest_rate * (holding_hours / 24)
        required_return = interest_cost * 1.5

        tp_mult = self.params.get('tp_mult', 2.2)
        sl_mult = self.params.get('sl_mult', 0.9)

        if tp_mult * atr_val / current < required_return:
            return None

        tp = current + atr_val * tp_mult
        sl = current - atr_val * sl_mult

        return {
            'direction': 'LONG',
            'entry': current,
            'tp': tp,
            'sl': sl,
            'score': score,
            'regime': regime,
            'confidence': min(1.0, max(0.0, score / 0.4)),
            'leverage': self.params.get('leverage', 3),
            'interest_cost': interest_cost,
            'holding_hours': holding_hours,
            'risk': self.params.get('risk_per_trade', 0.025),
            'atr': atr_val,
            'market_type': 'margin'
        }

    def get_risk_params(self) -> Dict:
        return {
            'max_leverage': 3.0,
            'risk_per_trade': 0.025,
            'max_positions': 2,
            'allow_short': False,
            'max_holding_hours': 72
        }

    def get_cost_params(self) -> Dict:
        return {
            'commission': 0.001,
            'slippage': 0.0005,
            'funding': 0.0,
            'margin_interest': 0.0001  # 0.01% diario
        }

    # Helper methods
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
