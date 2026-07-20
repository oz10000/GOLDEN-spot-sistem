# api/endpoints.py
# API pública de métricas en formato JSON

import json
import os
from typing import Dict, Any

class MetricsAPI:
    """API pública para consultar métricas y señales."""

    def __init__(self, data_path: str = "data/results/"):
        self.data_path = data_path

    def _load_json(self, filename: str) -> Dict:
        """Carga un archivo JSON."""
        path = os.path.join(self.data_path, filename)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return {"error": "No hay datos disponibles"}

    def get_top_five(self) -> Dict[str, Any]:
        """Retorna los 5 mejores activos."""
        return self._load_json("top_five.json")

    def get_signals(self) -> Dict[str, Any]:
        """Retorna señales actuales."""
        return self._load_json("signals.json")

    def get_ranking(self) -> Dict[str, Any]:
        """Retorna ranking completo."""
        return self._load_json("ranking.json")

    def get_metrics(self, market: str = None) -> Dict[str, Any]:
        """Retorna métricas de un mercado específico."""
        if market:
            return self._load_json(f"metrics_{market}.json")
        return {
            'spot': self._load_json("metrics_spot.json"),
            'margin': self._load_json("metrics_margin.json"),
            'futures': self._load_json("metrics_futures.json")
        }

    def to_json(self, data: Dict) -> str:
        """Convierte a JSON."""
        return json.dumps(data, indent=2, default=str)
