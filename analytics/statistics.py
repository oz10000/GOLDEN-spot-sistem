# analytics/statistics.py
# Cálculo de métricas estadísticas profesionales

import numpy as np
import pandas as pd
from typing import Dict, List, Optional

class StatisticsCalculator:
    """Calculadora de métricas estadísticas profesionales."""

    @staticmethod
    def compute_all(trades_df: pd.DataFrame, capital: float = 1000.0) -> Dict:
        """Calcula todas las métricas."""
        if trades_df.empty:
            return StatisticsCalculator._empty_metrics()

        df = trades_df.copy()
        wins = df[df['result'] == 'win']
        losses = df[df['result'] == 'loss']
        total = len(df)
        win_count = len(wins)
        loss_count = len(losses)

        # Métricas básicas
        win_rate = win_count / total if total > 0 else 0
        avg_win = wins['pnl'].mean() if win_count > 0 else 0
        avg_loss = losses['pnl'].mean() if loss_count > 0 else 0
        total_win = wins['pnl'].sum() if win_count > 0 else 0
        total_loss = abs(losses['pnl'].sum()) if loss_count > 0 else 1e-9

        # Profit Factor
        profit_factor = total_win / total_loss

        # Reward/Risk Ratio
        rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0

        # Expectancy
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)

        # PnL total
        total_pnl = df['pnl'].sum()

        # Drawdown
        equity = df['pnl'].cumsum() + capital
        peak = equity.expanding().max()
        drawdown = (peak - equity) / peak * 100
        max_drawdown = drawdown.max()
        avg_drawdown = drawdown.mean()
        max_drawdown_duration = (drawdown > 0).sum()

        # Sharpe (anualizado)
        returns = df['pnl'] / capital
        sharpe = returns.mean() / (returns.std() + 1e-9) * np.sqrt(252)

        # Sortino
        downside = returns[returns < 0]
        sortino = returns.mean() / (downside.std() + 1e-9) * np.sqrt(252) if len(downside) > 0 else 0

        # Calmar
        cagr = ((equity.iloc[-1] / capital) ** (365 / max(1, len(equity))) - 1) * 100
        calmar = cagr / (max_drawdown + 0.01)

        # Recovery Factor
        recovery_factor = (equity.iloc[-1] - capital) / (max_drawdown / 100 * capital) if max_drawdown > 0 else 0

        # Omega Ratio (umbral 0)
        sorted_pnls = df['pnl'].sort_values().values
        positive = sorted_pnls[sorted_pnls > 0]
        negative = sorted_pnls[sorted_pnls < 0]
        omega = np.sum(positive) / (np.sum(-negative) + 1e-9)

        # SQN (System Quality Number)
        sqn = df['pnl'].mean() / (df['pnl'].std() + 1e-9) * np.sqrt(total)

        # VaR y CVaR (95%)
        var_95 = np.percentile(df['pnl'], 5)
        cvar_95 = df['pnl'][df['pnl'] <= var_95].mean() if any(df['pnl'] <= var_95) else var_95

        # MFE/MAE
        mfe_mean = df['mfe'].mean() if 'mfe' in df.columns else 0
        mae_mean = df['mae'].mean() if 'mae' in df.columns else 0

        # Duración
        avg_duration = df['duration_hours'].mean() if 'duration_hours' in df.columns else 0

        # Mejor / Peor operación
        best_trade = df['pnl'].max()
        worst_trade = df['pnl'].min()

        return {
            'total_trades': total,
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'rr_ratio': rr_ratio,
            'expectancy': expectancy,
            'total_pnl': total_pnl,
            'max_drawdown': max_drawdown,
            'avg_drawdown': avg_drawdown,
            'max_drawdown_duration': max_drawdown_duration,
            'sharpe': sharpe,
            'sortino': sortino,
            'calmar': calmar,
            'recovery_factor': recovery_factor,
            'omega': omega,
            'sqn': sqn,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'mfe_mean': mfe_mean,
            'mae_mean': mae_mean,
            'avg_duration': avg_duration,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'final_capital': equity.iloc[-1] if len(equity) > 0 else capital,
        }

    @staticmethod
    def _empty_metrics() -> Dict:
        return {k: 0.0 for k in [
            'total_trades', 'win_count', 'loss_count', 'win_rate',
            'avg_win', 'avg_loss', 'profit_factor', 'rr_ratio', 'expectancy',
            'total_pnl', 'max_drawdown', 'avg_drawdown', 'max_drawdown_duration',
            'sharpe', 'sortino', 'calmar', 'recovery_factor', 'omega', 'sqn',
            'var_95', 'cvar_95', 'mfe_mean', 'mae_mean', 'avg_duration',
            'best_trade', 'worst_trade', 'final_capital'
        ]}

    @staticmethod
    def to_dataframe(metrics: Dict) -> pd.DataFrame:
        """Convierte métricas a DataFrame."""
        return pd.DataFrame([metrics])
