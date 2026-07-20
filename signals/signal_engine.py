# signals/signal_engine.py
# Motor de señales común

import numpy as np
import pandas as pd

def compute_pidelta_score(df: pd.DataFrame) -> float:
    """PiDelta Score (7 factores). Rango: -1 a 1."""
    if len(df) < 50:
        return 0.0

    close = df['close']
    a = _atr(df, 12)
    ema22 = _ema(close, 22)

    trend = np.tanh((close - ema22) / (a + 1e-9)).iloc[-1]
    adx_val = _adx(df, 14).iloc[-1]
    strength = min(1.0, adx_val / 40.0)
    ker_val = _ker(close, 10).iloc[-1]
    atr_rel = min(1.0, (a.iloc[-1] / close.iloc[-1] * 100) / 3.5)
    mom = close.pct_change(5).iloc[-1] * 100
    mom_norm = min(1.0, abs(mom) / 5.0)

    raw = (0.25 * trend + 0.20 * strength + 0.15 * ker_val +
           0.20 * atr_rel + 0.20 * mom_norm)
    return float(np.tanh(raw))

def classify_regime(df: pd.DataFrame) -> str:
    """Clasifica el régimen de mercado."""
    if len(df) < 60:
        return 'Indefinido'

    adx_val = _adx(df, 14).iloc[-1]
    ker_val = _ker(df['close'], 10).iloc[-1]
    atr_pct = _atr(df, 12).iloc[-1] / df['close'].iloc[-1] * 100
    vol = df['close'].pct_change().std() * np.sqrt(252) * 100

    if adx_val > 28 and ker_val > 0.6:
        return 'Tendencia_Fuerte'
    if adx_val > 22 and ker_val > 0.5:
        return 'Tendencia_Débil'
    if ker_val < 0.4 or adx_val < 20:
        return 'Chop'
    if atr_pct > 2.0 and adx_val > 25:
        return 'Expansión'
    if vol > 50:
        return 'Alta_Volatilidad'
    if vol < 20:
        return 'Baja_Volatilidad'
    return 'Normal'

def _atr(df, period=14):
    tr = np.maximum(df['high'] - df['low'],
                    np.maximum(abs(df['high'] - df['close'].shift()),
                               abs(df['low'] - df['close'].shift())))
    return tr.rolling(period).mean()

def _adx(df, period=14):
    up = df['high'].diff()
    down = -df['low'].diff()
    plus = pd.Series(0.0, index=df.index)
    minus = pd.Series(0.0, index=df.index)
    plus[(up > down) & (up > 0)] = up
    minus[(down > up) & (down > 0)] = down
    atr_val = _atr(df, period)
    plus_di = 100 * plus.rolling(period).mean() / atr_val
    minus_di = 100 * minus.rolling(period).mean() / atr_val
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
    return dx.rolling(period).mean()

def _ker(close, period=10):
    abs_diff = abs(close.diff(period))
    sum_abs = close.diff().abs().rolling(period).sum()
    return (abs_diff / (sum_abs + 1e-9)).fillna(0)

def _ema(series, period):
    return series.ewm(span=period, adjust=False).mean()
