# strategies/futures_strategy.py
# Estrategia específica para Futures (LONG y SHORT con apalancamiento)

import pandas as pd
import numpy as np
from .base import BaseStrategy
from signals.signal_engine import compute_pidelta_score, classify_regime

class FuturesStrategy(BaseStrategy):
    """Estrategia optimizada para Futures: LONG/SHORT con leverage dinámico."""

    def generate_signal(self, df: pd.DataFrame) -> Optional[Dict]:
        if df is None or len(df) < 60:
            return None

        # 1. Score PiDelta
        score = compute_pidelta_score(df)
        if abs(score) < self.params.get('min_score', 0.35):
            return None

        # 2. Filtros de tendencia
        adx_val = self._adx(df).iloc[-1]
        ker_val = self._ker(df['close']).iloc[-1]
        if adx_val < self.params.get('adx_threshold', 20) or ker_val < self.params.get('ker_threshold', 0.45):
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
        funding = self.params.get('funding_rate', 0.0001)
        if atr_pct < 0.3 or atr_pct > 5.0:
            return None

        # 6. Tamaño de posición y leverage
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
            'confidence': min(1.0, abs(score) / 0.4),
            'leverage': leverage,
            'funding': funding,
            'atr_pct': atr_pct,
            'holding_hours': self.params.get('holding_hours', 24)
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
