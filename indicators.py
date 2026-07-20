# indicators.py
# Funciones de indicadores técnicos reutilizables

import pandas as pd
import numpy as np

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range"""
    tr = np.maximum(df['high'] - df['low'],
                    np.maximum(abs(df['high'] - df['close'].shift()),
                               abs(df['low'] - df['close'].shift())))
    return tr.rolling(period).mean()

def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average Directional Index"""
    up = df['high'].diff()
    down = -df['low'].diff()
    plus = pd.Series(0.0, index=df.index)
    minus = pd.Series(0.0, index=df.index)
    plus[(up > down) & (up > 0)] = up
    minus[(down > up) & (down > 0)] = down
    atr_val = atr(df, period)
    plus_di = 100 * plus.rolling(period).mean() / atr_val
    minus_di = 100 * minus.rolling(period).mean() / atr_val
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
    return dx.rolling(period).mean()

def ker(close: pd.Series, period: int = 10) -> pd.Series:
    """Kaufman Efficiency Ratio"""
    abs_diff = abs(close.diff(period))
    sum_abs = close.diff().abs().rolling(period).sum()
    return (abs_diff / (sum_abs + 1e-9)).fillna(0)

def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()

def vwap(df: pd.DataFrame) -> pd.Series:
    """Volume Weighted Average Price (acumulado)"""
    return (df['close'] * df['volume']).cumsum() / (df['volume'].cumsum() + 1e-9)

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index"""
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD (línea, señal, histograma)"""
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist
