# optimization/monte_carlo.py
# Monte Carlo con block bootstrap y stress testing

import numpy as np
import pandas as pd
from typing import Dict, List

class MonteCarloEngine:
    """Simulación Monte Carlo profesional."""

    @staticmethod
    def block_bootstrap(trades_df: pd.DataFrame, block_size: int = 5,
                        n_simulations: int = 1000, capital: float = 1000.0) -> Dict:
        """
        Block bootstrap para mantener autocorrelación.
        """
        if trades_df.empty:
            return {'ruin_risk': 0.0, 'mean_pnl': 0.0, 'std_pnl': 0.0}

        pnls = trades_df['pnl'].values
        n = len(pnls)

        if n == 0:
            return {'ruin_risk': 0.0, 'mean_pnl': 0.0, 'std_pnl': 0.0}

        final_pnls = []
        for _ in range(n_simulations):
            blocks = []
            n_blocks = max(1, n // block_size)
            for _ in range(n_blocks + 1):
                idx = np.random.randint(0, max(1, n - block_size))
                blocks.extend(pnls[idx:idx + block_size])
            seq = np.array(blocks[:n])
            final_pnls.append(np.sum(seq))

        final_pnls = np.array(final_pnls)

        ruin_risk = np.mean(final_pnls < -capital * 0.5) * 100

        return {
            'ruin_risk': ruin_risk,
            'mean_pnl': np.mean(final_pnls),
            'std_pnl': np.std(final_pnls),
            'p5': np.percentile(final_pnls, 5),
            'p95': np.percentile(final_pnls, 95),
            'histogram': np.histogram(final_pnls, bins=50)
        }

    @staticmethod
    def stress_test(trades_df: pd.DataFrame, shock_pct: float = -0.20) -> Dict:
        """
        Simula un shock de mercado (ej: caída del 20%).
        """
        if trades_df.empty:
            return {'impact': 0.0, 'survival_rate': 1.0}

        pnls = trades_df['pnl'].values
        # Aplicar shock a todas las operaciones abiertas
        impacted = pnls * (1 + shock_pct)
        total_impact = np.sum(impacted) - np.sum(pnls)

        survival = np.mean(impacted > -0.5 * 1000)  # capital > 500

        return {
            'impact': total_impact,
            'survival_rate': survival,
            'worst_case': np.min(impacted),
            'best_case': np.max(impacted)
        }
