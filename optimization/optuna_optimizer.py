# optimization/optuna_optimizer.py
# Optimización avanzada con Optuna

import optuna
import pandas as pd
import numpy as np
from typing import Dict, Optional
from strategies.spot_strategy import SpotStrategy
from backtester import Backtester

class OptunaOptimizer:
    """Optimizador con Optuna y Bayesian Optimization."""

    def __init__(self, df: pd.DataFrame, market: str = 'spot', n_trials: int = 100):
        self.df = df
        self.market = market
        self.n_trials = n_trials
        self.best_params = {}
        self.study = None

    def objective(self, trial: optuna.Trial) -> float:
        """Función objetivo para Optuna."""

        # Parámetros a optimizar
        params = {
            'tp_mult': trial.suggest_float('tp_mult', 1.5, 4.0),
            'sl_mult': trial.suggest_float('sl_mult', 0.5, 1.5),
            'trail_activation': trial.suggest_float('trail_activation', 0.001, 0.01),
            'trail_distance': trial.suggest_float('trail_distance', 0.5, 3.0),
            'be_activation': trial.suggest_float('be_activation', 0.002, 0.01),
            'be_buffer': trial.suggest_float('be_buffer', 0.001, 0.005),
            'max_duration_hours': trial.suggest_int('max_duration_hours', 12, 120),
            'min_score': trial.suggest_float('min_score', 0.30, 0.50),
            'adx_threshold': trial.suggest_int('adx_threshold', 18, 32),
            'ker_threshold': trial.suggest_float('ker_threshold', 0.40, 0.65),
            'leverage': trial.suggest_int('leverage', 1, 5),
        }

        # Walk-Forward (70/30)
        split = int(len(self.df) * 0.7)
        train_df = self.df.iloc[:split]
        test_df = self.df.iloc[split:]

        # Entrenamiento
        bt_train = Backtester(train_df, params, self.market)
        res_train = bt_train.run()

        # Validación
        bt_test = Backtester(test_df, params, self.market)
        res_test = bt_test.run()

        # Score: PF * WR / (DD + 0.01) en test
        score = (res_test['profit_factor'] * res_test['win_rate']) / (res_test['max_drawdown'] / 100 + 0.01)

        return score

    def optimize(self) -> Dict:
        """Ejecuta optimización."""
        self.study = optuna.create_study(
            direction='maximize',
            sampler=optuna.samplers.TPESampler(seed=42),
            pruner=optuna.pruners.MedianPruner()
        )
        self.study.optimize(self.objective, n_trials=self.n_trials)

        self.best_params = self.study.best_params
        return self.best_params

    def get_best_trials(self, n: int = 5) -> pd.DataFrame:
        """Retorna los mejores trials."""
        if not self.study:
            return pd.DataFrame()
        trials = self.study.trials
        best = sorted([t for t in trials if t.value is not None], key=lambda x: x.value, reverse=True)[:n]
        data = []
        for t in best:
            row = t.params.copy()
            row['value'] = t.value
            data.append(row)
        return pd.DataFrame(data)

    def plot_optimization_history(self):
        """Genera gráfico de historial de optimización."""
        if not self.study:
            return None
        import plotly.graph_objects as go
        values = [t.value for t in self.study.trials if t.value is not None]
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=values, mode='lines+markers', name='Valor'))
        fig.update_layout(title='Historial de optimización', xaxis_title='Trial', yaxis_title='Score')
        return fig
