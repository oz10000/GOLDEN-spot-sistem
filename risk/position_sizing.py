# risk/position_sizing.py
# Position sizing dinámico

import numpy as np

class PositionSizing:
    """Gestión dinámica del tamaño de posición."""

    def __init__(self, capital: float, risk_per_trade: float = 0.02):
        self.capital = capital
        self.risk_per_trade = risk_per_trade
        self.current_drawdown = 0.0
        self.consecutive_losses = 0

    def update_capital(self, new_capital: float, peak_capital: float):
        """Actualiza capital y drawdown."""
        self.capital = new_capital
        self.current_drawdown = (peak_capital - new_capital) / peak_capital if peak_capital > 0 else 0

    def record_trade(self, result: str):
        """Registra resultado para ajustar riesgo."""
        if result == 'loss':
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

    def calculate_size(self, entry_price: float, sl_distance: float,
                       leverage: float = 1.0) -> float:
        """
        Calcula tamaño de posición (unidades del activo).
        """
        # Riesgo ajustado por drawdown
        risk = self.risk_per_trade
        if self.current_drawdown > 0.10:
            risk *= 0.5
        elif self.current_drawdown > 0.05:
            risk *= 0.7

        # Ajuste por pérdidas consecutivas
        if self.consecutive_losses >= 3:
            risk *= 0.5
        elif self.consecutive_losses >= 2:
            risk *= 0.7

        # Tamaño base
        risk_amount = self.capital * risk
        size = risk_amount / (sl_distance * leverage)

        return max(size, 0.0)

    def calculate_leverage(self, volatility_pct: float, regime: str) -> float:
        """Calcula leverage dinámico."""
        base = 3.0
        if regime == 'Alta_Volatilidad':
            return min(2.0, base * 0.5)
        if regime == 'Tendencia_Fuerte':
            return min(5.0, base * 1.2)
        if volatility_pct > 3.0:
            return max(1.0, base * 0.6)
        return min(5.0, max(1.0, base * (1.5 / (volatility_pct + 0.5))))

    def get_risk_metrics(self) -> dict:
        """Retorna métricas de riesgo actuales."""
        return {
            'capital': self.capital,
            'risk_per_trade': self.risk_per_trade,
            'current_drawdown': self.current_drawdown * 100,
            'consecutive_losses': self.consecutive_losses,
            'risk_adjustment': 1.0 - (self.current_drawdown * 2 + self.consecutive_losses * 0.05)
        }
