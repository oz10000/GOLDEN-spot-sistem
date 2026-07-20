# optimization/optuna_optimizer.py
# Optimización avanzada con Optuna y Bayesian Optimization

import optuna
import pandas as pd
import numpy as np
from typing import Dict, Optional
from core.backtester import Backtester
from strategies.spot_strategy import SpotStrategy

class OptunaOptimizer:
    """Optimizador con Optuna y Bayesian Optimization."""

    def __init__(self, df: pd.DataFrame, market: str = 'spot', n_trials: int = 50):
        self.df = df
        self.market = market
        self.n_trials = n_trials
        self.best_params = {}
        self.study = None

    def objective(self, trial: optuna.Trial) -> float:
        """Función objetivo para Optuna."""
        params = {
            'tp_mult': trial.suggest_float('tp_mult', 1.5, 4.0),
            'sl_mult': trial.suggest_float('sl_mult', 0.5, 1.5),
            'min_score': trial.suggest_float('min_score', 0.30, 0.50),
            'adx_threshold': trial.suggest_int('adx_threshold', 18, 32),
            'ker_threshold': trial.suggest_float('ker_threshold', 0.40, 0.65),
        }

        # Walk-Forward (70/30)
        split = int(len(self.df) * 0.7)
        train_df = self.df.iloc[:split]
        test_df = self.df.iloc[split:]

        # Entrenar en train
        strategy = SpotStrategy(params)
        signal = strategy.generate_signal(train_df)
        if not signal:
            return 0.0

        bt_train = Backtester(train_df, params)
        metrics_train = bt_train.run(signal)

        # Validar en test
        bt_test = Backtester(test_df, params)
        metrics_test = bt_test.run(signal)

        # Score: PF * WR / (DD + 0.01) en test
        score = (metrics_test.get('profit_factor', 0) * metrics_test.get('win_rate', 0)) / (metrics_test.get('max_drawdown', 0) / 100 + 0.01)
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
