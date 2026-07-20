# optimization/top_five.py
# Sistema TOP FIVE para selección de los mejores activos

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class TopFiveOptimizer:
    """
    Analiza el universo completo y selecciona los 5 mejores activos
    según ranking multicriterio.
    """

    def __init__(self, params: Dict = None):
        self.params = params or {}
        self.weights = self.params.get('weights', {
            'profit_factor': 0.25,
            'sharpe': 0.20,
            'sortino': 0.15,
            'calmar': 0.10,
            'win_rate': 0.10,
            'sqn': 0.10,
            'omega': 0.10
        })

    def rank(self, assets_data: List[Dict]) -> pd.DataFrame:
        """
        Rankea activos según métricas estadísticas.
        """
        if not assets_data:
            return pd.DataFrame()

        df = pd.DataFrame(assets_data)

        # Normalizar métricas (min-max)
        for metric in self.weights.keys():
            if metric in df.columns:
                if df[metric].std() > 0:
                    df[f'{metric}_norm'] = (df[metric] - df[metric].min()) / (df[metric].max() - df[metric].min() + 1e-9)
                else:
                    df[f'{metric}_norm'] = 0.5

        # Score compuesto
        df['score'] = 0.0
        for metric, weight in self.weights.items():
            col = f'{metric}_norm'
            if col in df.columns:
                df['score'] += weight * df[col]

        # Penalización por drawdown
        if 'max_drawdown' in df.columns:
            dd_penalty = df['max_drawdown'] / 100
            df['score'] *= (1 - dd_penalty * 0.3)

        # Ordenar
        df = df.sort_values('score', ascending=False)

        # Top 5
        top5 = df.head(5).copy()

        # Agregar estado
        top5['status'] = 'RECOMENDADO'
        top5.loc[top5['score'] < 0.5, 'status'] = 'OBSERVAR'
        top5.loc[top5['score'] < 0.3, 'status'] = 'EVITAR'

        return top5[['symbol', 'market', 'score', 'win_rate', 'profit_factor',
                     'sharpe', 'max_drawdown', 'status']]

    def get_best_asset(self, assets_data: List[Dict]) -> Dict:
        """Retorna el mejor activo."""
        df = self.rank(assets_data)
        if df.empty:
            return {}
        return df.iloc[0].to_dict()

    def update_ranking(self, assets_data: List[Dict], save_path: str = None):
        """Genera ranking y guarda en JSON."""
        df = self.rank(assets_data)
        if save_path and not df.empty:
            import json
            with open(save_path, 'w') as f:
                json.dump(df.to_dict('records'), f, indent=2)
        return df
