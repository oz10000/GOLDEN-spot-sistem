# analytics/metrics_tables.py
# Tablas de métricas por mercado

import pandas as pd
from typing import Dict, List

class MetricsTables:
    """Genera tablas de métricas separadas por mercado."""

    @staticmethod
    def create_table(asset_metrics: List[Dict], market_type: str) -> pd.DataFrame:
        """Crea tabla de métricas para un mercado específico."""
        if not asset_metrics:
            return pd.DataFrame()

        df = pd.DataFrame(asset_metrics)
        df = df[df['market'] == market_type]

        if df.empty:
            return df

        # Seleccionar columnas clave
        columns = [
            'symbol', 'win_rate', 'profit_factor', 'sharpe',
            'sortino', 'calmar', 'max_drawdown', 'expectancy',
            'total_pnl', 'total_trades', 'sqn', 'omega'
        ]

        available = [c for c in columns if c in df.columns]
        return df[available].sort_values('profit_factor', ascending=False)

    @staticmethod
    def create_all_tables(asset_metrics: List[Dict]) -> Dict[str, pd.DataFrame]:
        """Crea tablas para Spot, Margin y Futures."""
        return {
            'spot': MetricsTables.create_table(asset_metrics, 'spot'),
            'margin': MetricsTables.create_table(asset_metrics, 'margin'),
            'futures': MetricsTables.create_table(asset_metrics, 'futures'),
        }

    @staticmethod
    def generate_csv(asset_metrics: List[Dict], output_dir: str = "data/results"):
        """Genera archivos CSV separados por mercado."""
        import os
        os.makedirs(output_dir, exist_ok=True)

        tables = MetricsTables.create_all_tables(asset_metrics)
        for market, df in tables.items():
            if not df.empty:
                df.to_csv(f"{output_dir}/metrics_{market}.csv", index=False)

        return tables
