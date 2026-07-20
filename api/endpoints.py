# api/endpoints.py
# API pública de métricas en formato JSON

import json
import pandas as pd
from typing import Dict, Any

class MetricsAPI:
    """API pública para consultar métricas y señales."""

    def __init__(self, data_path: str = "data/results/"):
        self.data_path = data_path

    def get_top_five(self) -> Dict[str, Any]:
        """Retorna los 5 mejores activos."""
        try:
            with open(f"{self.data_path}/top_five.json", 'r') as f:
                return json.load(f)
        except:
            return {"error": "No hay datos disponibles"}

    def get_current_signals(self) -> Dict[str, Any]:
        """Retorna señales actuales."""
        try:
            with open(f"{self.data_path}/signals.json", 'r') as f:
                return json.load(f)
        except:
            return {"error": "No hay señales disponibles"}

    def get_metrics(self, symbol: str = None) -> Dict[str, Any]:
        """Retorna métricas de un activo o de todos."""
        try:
            df = pd.read_csv(f"{self.data_path}/metrics.csv")
            if symbol:
                df = df[df['symbol'] == symbol]
            return df.to_dict('records')
        except:
            return {"error": "No hay métricas disponibles"}

    def get_ranking(self) -> Dict[str, Any]:
        """Retorna ranking completo."""
        try:
            with open(f"{self.data_path}/ranking.json", 'r') as f:
                return json.load(f)
        except:
            return {"error": "No hay ranking disponible"}

    def to_json(self, data: Dict) -> str:
        """Convierte a JSON."""
        return json.dumps(data, indent=2, default=str)
