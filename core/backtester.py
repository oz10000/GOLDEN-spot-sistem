# core/backtester.py
# Motor de backtesting real con costes, slippage y registro de operaciones

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime

class Backtester:
    """Motor de backtesting profesional."""

    def __init__(self, df: pd.DataFrame, config: Dict = None):
        self.df = df.copy()
        self.config = config or {}
        self.commission = self.config.get('commission', 0.001)
        self.slippage = self.config.get('slippage', 0.0005)
        self.capital = self.config.get('capital', 1000.0)
        self.initial_capital = self.capital
        self.trades = []
        self.equity_curve = [self.capital]

    def run(self, signal: Dict) -> Dict:
        """
        Ejecuta backtesting de una señal.
        Retorna métricas y lista de trades.
        """
        if not signal:
            return self._empty_result()

        direction = signal.get('direction', 'LONG')
        entry_price = signal.get('entry', 0)
        tp = signal.get('tp', entry_price * 1.02)
        sl = signal.get('sl', entry_price * 0.98)
        leverage = signal.get('leverage', 1.0)

        # Simular entrada con slippage
        entry_price_exec = entry_price * (1 + np.random.uniform(-self.slippage, self.slippage))

        # Simular evolución del precio (usando datos históricos reales)
        # Buscar la vela más cercana al precio de entrada
        df = self.df.copy()
        # Encontrar el índice más cercano al precio de entrada
        closest_idx = (df['close'] - entry_price).abs().idxmin()
        start_idx = df.index.get_loc(closest_idx)

        trade = {
            'entry_time': df.index[start_idx],
            'entry_price': entry_price_exec,
            'direction': direction,
            'leverage': leverage,
            'tp': tp,
            'sl': sl,
            'exit_time': None,
            'exit_price': None,
            'pnl': 0.0,
            'result': 'open',
            'duration_hours': 0.0,
            'mfe': 0.0,
            'mae': 0.0,
            'fees': 0.0,
            'slippage_cost': 0.0,
        }

        # Simular evolución
        max_price = entry_price_exec
        min_price = entry_price_exec
        exit_price = entry_price_exec
        exit_time = df.index[start_idx]
        exit_reason = 'Timeout'

        for i in range(start_idx, len(df)):
            current_price = df['close'].iloc[i]
            high = df['high'].iloc[i]
            low = df['low'].iloc[i]

            if direction == 'LONG':
                if high >= tp:
                    exit_price = tp
                    exit_reason = 'TP'
                    exit_time = df.index[i]
                    break
                if low <= sl:
                    exit_price = sl
                    exit_reason = 'SL'
                    exit_time = df.index[i]
                    break
                max_price = max(max_price, high)
                min_price = min(min_price, low)
            else:  # SHORT
                if low <= tp:
                    exit_price = tp
                    exit_reason = 'TP'
                    exit_time = df.index[i]
                    break
                if high >= sl:
                    exit_price = sl
                    exit_reason = 'SL'
                    exit_time = df.index[i]
                    break
                max_price = max(max_price, high)
                min_price = min(min_price, low)

        # Calcular PnL
        if direction == 'LONG':
            raw_pnl = (exit_price - entry_price_exec) / entry_price_exec
        else:
            raw_pnl = (entry_price_exec - exit_price) / entry_price_exec

        fees = abs(raw_pnl) * self.commission * 2
        slippage_cost = abs(raw_pnl) * self.slippage
        pnl = raw_pnl * leverage - fees - slippage_cost

        trade.update({
            'exit_time': exit_time,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'pnl': pnl,
            'result': 'win' if pnl > 0 else 'loss',
            'duration_hours': (exit_time - trade['entry_time']).total_seconds() / 3600,
            'mfe': (max_price - entry_price_exec) / entry_price_exec * 100 if direction == 'LONG' else (entry_price_exec - min_price) / entry_price_exec * 100,
            'mae': (min_price - entry_price_exec) / entry_price_exec * 100 if direction == 'LONG' else (entry_price_exec - max_price) / entry_price_exec * 100,
            'fees': fees,
            'slippage_cost': slippage_cost
        })

        self.trades.append(trade)
        self.capital += pnl * self.capital
        self.equity_curve.append(self.capital)

        return self._compute_metrics()

    def _compute_metrics(self) -> Dict:
        """Calcula métricas a partir de los trades."""
        if not self.trades:
            return self._empty_result()

        df_trades = pd.DataFrame(self.trades)
        wins = df_trades[df_trades['result'] == 'win']
        losses = df_trades[df_trades['result'] == 'loss']

        total = len(df_trades)
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = win_count / total if total > 0 else 0

        total_win = wins['pnl'].sum() if win_count > 0 else 0
        total_loss = abs(losses['pnl'].sum()) if loss_count > 0 else 1e-9
        profit_factor = total_win / total_loss

        equity = np.array(self.equity_curve)
        peak = np.maximum.accumulate(equity)
        drawdown = (peak - equity) / peak * 100
        max_drawdown = drawdown.max()

        returns = np.diff(equity) / equity[:-1]
        sharpe = returns.mean() / (returns.std() + 1e-9) * np.sqrt(252) if len(returns) > 1 else 0

        total_pnl = self.capital - self.initial_capital

        return {
            'total_trades': total,
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_pnl': total_pnl,
            'max_drawdown': max_drawdown,
            'sharpe': sharpe,
            'final_capital': self.capital,
            'trades_df': df_trades,
            'equity_curve': self.equity_curve,
        }

    def _empty_result(self) -> Dict:
        return {
            'total_trades': 0,
            'win_count': 0,
            'loss_count': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'sharpe': 0.0,
            'final_capital': self.capital,
            'trades_df': pd.DataFrame(),
            'equity_curve': [self.capital],
        }

    def get_trades(self) -> List[Dict]:
        """Retorna lista de trades."""
        return self.trades
