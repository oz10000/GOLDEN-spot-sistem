# strategies/base.py
# Clase base para estrategias por mercado

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Optional, Tuple

class BaseStrategy(ABC):
    """Clase base para estrategias de trading."""

    def __init__(self, params: Dict):
        self.params = params
        self.name = self.__class__.__name__

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> Optional[Dict]:
        """Genera señal de trading."""
        pass

    @abstractmethod
    def get_risk_params(self) -> Dict:
        """Retorna parámetros de riesgo específicos."""
        pass

    @abstractmethod
    def get_cost_params(self) -> Dict:
        """Retorna parámetros de costes específicos."""
        pass