# strategies/margin_strategy.py
# Estrategia específica para Margin (LONG con apalancamiento moderado)

import pandas as pd
import numpy as np
from .base import BaseStrategy
from signals.signal_engine import compute_pidelta_score, classify_regime

class MarginStrategy(BaseStrategy):
    """Estrategia optimizada para Margin: LONG con leverage 2-3x y control de interés."""

    def generate_signal(self, df: pd.DataFrame) -> Optional[Dict]:
        if df is None or len(df) < 60:
            return None

        # 1. Score PiDelta (más exigente que spot)
        score = compute_pidelta_score(df)
        if score < self.params.get('min_score', 0.42):
            return None

        # 2. Filtros de tendencia
        adx_val = self._adx(df).iloc[-1]
        ker_val = self._ker(df['close']).iloc[-1]
        if adx_val < self.params.get('adx_threshold', 24) or ker_val < self.params.get('ker_threshold', 0.52):
            return None

        # 3. Régimen (evitar chop y alta volatilidad)
        regime = classify_regime(df)
        if regime in ['Chop', 'Alta_Volatilidad']:
            return None

        # 4. Solo LONG
        if score < 0:
            return None

        # 5. Volatilidad (ATR% entre 1% y 4%)
        atr_val = self._atr(df).iloc[-1]
        current = df['close'].iloc[-1]
        atr_pct = atr_val / current * 100
        if atr_pct < 0.5 or atr_pct > 4.0:
            return None

        # 6. Coste de interés
        holding_hours = self.params.get('holding_hours', 24)
        interest_cost = 0.0001 * (holding_hours / 24)
        required_return = interest_cost * 1.5  # al menos 1.5x el coste

        tp_mult = self.params.get('tp_mult', 2.5)
        sl_mult = self.params.get('sl_mult', 0.9)

        if tp_mult * atr_val / current < required_return:
            return None

        return {
            'direction': 'LONG',
            'entry': current,
            'tp': current + atr_val * tp_mult,
            'sl': current - atr_val * sl_mult,
            'score': score,
            'regime': regime,
            'confidence': min(1.0, score / 0.45),
            'max_leverage': self.params.get('max_leverage', 3),
            'holding_hours': holding_hours,
            'interest_cost': interest_cost
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
