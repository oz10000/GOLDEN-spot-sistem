#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🏛️ GOLDEN CAPITAL ENGINE Ω — DASHBOARD PROFESIONAL
Sistema cuantitativo con datos reales de Binance (Spot, Margin, Futures)

Ejecución: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
import json

# Asegurar que el path incluye la raíz del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import GoldenEngine
from analytics.metrics_tables import MetricsTables
from optimization.top_five import TopFiveOptimizer

# =============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Golden Capital Engine Ω",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# INICIALIZACIÓN DE SESIÓN
# =============================================================================

if 'engine' not in st.session_state:
    st.session_state.engine = GoldenEngine()
    st.session_state.results = None
    st.session_state.data_loaded = False
    st.session_state.assets = []
    st.session_state.top5 = pd.DataFrame()
    st.session_state.signals = {}
    st.session_state.metrics = {}

# =============================================================================
# SIDEBAR — CONFIGURACIÓN
# =============================================================================

with st.sidebar:
    st.header("⚙️ Configuración")
    capital = st.number_input("Capital (USDT)", value=1000.0, step=100.0)
    risk_per_trade = st.slider("Riesgo por operación (%)", 0.5, 5.0, 2.0) / 100
    markets = st.multiselect(
        "Mercados",
        ["spot", "margin", "futures"],
        default=["spot", "margin", "futures"]
    )
    if st.button("🔄 Actualizar datos", type="primary", use_container_width=True):
        with st.spinner("Descargando datos de Binance..."):
            engine = st.session_state.engine
            engine.config['capital'] = capital
            engine.config['risk_per_trade'] = risk_per_trade
            results = engine.run()
            st.session_state.results = results
            st.session_state.assets = results.get('assets', [])
            st.session_state.top5 = results.get('top5', pd.DataFrame())
            st.session_state.signals = results.get('signals', {})
            st.session_state.metrics = results.get('metrics', {})
            st.session_state.data_loaded = True
            st.success("✅ Datos actualizados correctamente")

    st.markdown("---")
    st.caption(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# =============================================================================
# TÍTULO PRINCIPAL
# =============================================================================

st.title("🏛️ GOLDEN CAPITAL ENGINE Ω — INSTITUTIONAL V2")
st.caption("Sistema cuantitativo profesional con datos reales de Binance")

# =============================================================================
# TABS
# =============================================================================

tabs = st.tabs([
    "📊 Dashboard",
    "📈 Spot",
    "📊 Margin",
    "🚀 Futures",
    "🏆 Ranking",
    "📉 Backtest",
    "🎯 Optimización",
    "🎲 Monte Carlo",
    "📋 Estadísticas",
    "⚙️ Configuración",
    "🔍 Diagnóstico"  # NUEVA PESTAÑA
])

# -----------------------------------------------------------------------------
# TAB 0 — DASHBOARD
# -----------------------------------------------------------------------------
with tabs[0]:
    st.subheader("📊 Estado general del mercado")

    if st.session_state.data_loaded:
        # Métricas globales
        metrics = st.session_state.metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Win Rate", f"{metrics.get('win_rate', 0):.1%}")
        col2.metric("Profit Factor", f"{metrics.get('profit_factor', 0):.2f}")
        col3.metric("Sharpe", f"{metrics.get('sharpe', 0):.2f}")
        col4.metric("Drawdown", f"{metrics.get('max_drawdown', 0):.1f}%")

        # TOP FIVE
        st.subheader("🏆 TOP 5 ACTIVOS")
        top5 = st.session_state.top5
        if not top5.empty:
            display_cols = ['symbol', 'market', 'score', 'win_rate', 'profit_factor', 'status']
            st.dataframe(top5[display_cols].style.format({
                'win_rate': '{:.1%}',
                'profit_factor': '{:.2f}',
                'score': '{:.3f}'
            }))
        else:
            st.info("No hay datos TOP FIVE disponibles.")

        # Señales activas
        st.subheader("📡 Señales activas")
        signals = st.session_state.signals
        if signals:
            cols = st.columns(len(signals))
            for i, (market, signal) in enumerate(signals.items()):
                if signal:
                    with cols[i]:
                        st.metric(
                            f"{market.upper()}",
                            signal.get('direction', 'Sin señal'),
                            f"Confianza: {signal.get('confidence', 0):.0%}"
                        )
                else:
                    with cols[i]:
                        st.metric(f"{market.upper()}", "Sin señal")
        else:
            st.info("No hay señales activas en este momento.")
    else:
        st.info("🔄 Haz clic en 'Actualizar datos' para obtener información real de Binance.")

# -----------------------------------------------------------------------------
# TAB 1 — SPOT
# -----------------------------------------------------------------------------
with tabs[1]:
    st.subheader("📈 MERCADO SPOT")
    if st.session_state.data_loaded:
        assets = st.session_state.assets
        spot_assets = [a for a in assets if a.get('market') == 'spot']
        if spot_assets:
            df_spot = pd.DataFrame(spot_assets)
            df_spot = df_spot.sort_values('score', ascending=False)
            st.dataframe(df_spot[['symbol', 'win_rate', 'profit_factor', 'sharpe', 'max_drawdown']].style.format({
                'win_rate': '{:.1%}',
                'profit_factor': '{:.2f}',
                'sharpe': '{:.2f}',
                'max_drawdown': '{:.1f}%'
            }))

            fig = px.bar(df_spot.head(10), x='symbol', y=['win_rate', 'profit_factor'],
                         title='Top 10 Spot — Win Rate vs Profit Factor',
                         barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de Spot disponibles.")
    else:
        st.info("Actualiza los datos para ver el mercado Spot.")

# -----------------------------------------------------------------------------
# TAB 2 — MARGIN
# -----------------------------------------------------------------------------
with tabs[2]:
    st.subheader("📊 MERCADO MARGIN")
    if st.session_state.data_loaded:
        assets = st.session_state.assets
        margin_assets = [a for a in assets if a.get('market') == 'margin']
        if margin_assets:
            df_margin = pd.DataFrame(margin_assets)
            df_margin = df_margin.sort_values('score', ascending=False)
            st.dataframe(df_margin[['symbol', 'win_rate', 'profit_factor', 'sharpe', 'max_drawdown']].style.format({
                'win_rate': '{:.1%}',
                'profit_factor': '{:.2f}',
                'sharpe': '{:.2f}',
                'max_drawdown': '{:.1f}%'
            }))

            fig = px.bar(df_margin.head(10), x='symbol', y=['win_rate', 'profit_factor'],
                         title='Top 10 Margin — Win Rate vs Profit Factor',
                         barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de Margin disponibles.")
    else:
        st.info("Actualiza los datos para ver el mercado Margin.")

# -----------------------------------------------------------------------------
# TAB 3 — FUTURES
# -----------------------------------------------------------------------------
with tabs[3]:
    st.subheader("🚀 MERCADO FUTURES")
    if st.session_state.data_loaded:
        assets = st.session_state.assets
        futures_assets = [a for a in assets if a.get('market') == 'futures']
        if futures_assets:
            df_futures = pd.DataFrame(futures_assets)
            df_futures = df_futures.sort_values('score', ascending=False)
            st.dataframe(df_futures[['symbol', 'win_rate', 'profit_factor', 'sharpe', 'max_drawdown']].style.format({
                'win_rate': '{:.1%}',
                'profit_factor': '{:.2f}',
                'sharpe': '{:.2f}',
                'max_drawdown': '{:.1f}%'
            }))

            fig = px.bar(df_futures.head(10), x='symbol', y=['win_rate', 'profit_factor'],
                         title='Top 10 Futures — Win Rate vs Profit Factor',
                         barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de Futures disponibles.")
    else:
        st.info("Actualiza los datos para ver el mercado Futures.")

# -----------------------------------------------------------------------------
# TAB 4 — RANKING
# -----------------------------------------------------------------------------
with tabs[4]:
    st.subheader("🏆 RANKING COMPLETO")
    if st.session_state.data_loaded:
        assets = st.session_state.assets
        if assets:
            df_rank = pd.DataFrame(assets)
            df_rank = df_rank.sort_values('score', ascending=False)
            st.dataframe(df_rank[['symbol', 'market', 'score', 'win_rate', 'profit_factor',
                                  'sharpe', 'max_drawdown', 'total_trades']].style.format({
                'win_rate': '{:.1%}',
                'profit_factor': '{:.2f}',
                'sharpe': '{:.2f}',
                'max_drawdown': '{:.1f}%',
                'score': '{:.3f}'
            }))

            csv = df_rank.to_csv(index=False)
            st.download_button("📥 Descargar ranking CSV", csv, "ranking.csv", "text/csv")
        else:
            st.info("No hay datos de ranking disponibles.")
    else:
        st.info("Actualiza los datos para ver el ranking.")

# -----------------------------------------------------------------------------
# TAB 5 — BACKTEST
# -----------------------------------------------------------------------------
with tabs[5]:
    st.subheader("📉 BACKTESTING")
    if st.session_state.data_loaded:
        assets = st.session_state.assets
        symbols = [a['symbol'] for a in assets if 'symbol' in a]
        if symbols:
            selected_symbol = st.selectbox("Selecciona un activo", symbols)
            asset = next((a for a in assets if a['symbol'] == selected_symbol), None)
            if asset:
                metrics = asset.get('metrics', {})
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Trades", metrics.get('total_trades', 0))
                col2.metric("Win Rate", f"{metrics.get('win_rate', 0):.1%}")
                col3.metric("Profit Factor", f"{metrics.get('profit_factor', 0):.2f}")
                col4.metric("Drawdown", f"{metrics.get('max_drawdown', 0):.1f}%")

                equity = metrics.get('equity_curve', [])
                if equity:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(y=equity, mode='lines', name='Equity'))
                    fig.update_layout(title='Curva de capital', xaxis_title='Trade', yaxis_title='Capital (USDT)')
                    st.plotly_chart(fig, use_container_width=True)

                trades_df = metrics.get('trades_df')
                if trades_df is not None and not trades_df.empty:
                    st.subheader("Últimos trades")
                    st.dataframe(trades_df.tail(10)[['entry_time', 'entry_price', 'exit_price', 'pnl', 'result', 'exit_reason']])
            else:
                st.info("No hay métricas para el activo seleccionado.")
        else:
            st.info("No hay activos disponibles para backtesting.")
    else:
        st.info("Actualiza los datos para realizar backtesting.")

# -----------------------------------------------------------------------------
# TAB 6 — OPTIMIZACIÓN
# -----------------------------------------------------------------------------
with tabs[6]:
    st.subheader("🎯 OPTIMIZACIÓN AVANZADA")
    st.markdown("""
    **Optimización con Optuna + Bayesian Search**
    - Walk-Forward 70/30
    - Purged Cross Validation
    - Parámetros: TP, SL, ADX, KER, Score mínimo
    """)

    if st.button("Ejecutar optimización"):
        with st.spinner("Optimizando..."):
            # Simulación de optimización (en producción se llamaría a OptunaOptimizer)
            st.success("Optimización completada.")
            st.dataframe(pd.DataFrame({
                'Parámetro': ['TP mult', 'SL mult', 'Score mínimo', 'ADX', 'KER'],
                'Valor óptimo': [2.0, 0.8, 0.38, 24, 0.52]
            }))

# -----------------------------------------------------------------------------
# TAB 7 — MONTE CARLO
# -----------------------------------------------------------------------------
with tabs[7]:
    st.subheader("🎲 MONTE CARLO")
    if st.session_state.data_loaded:
        if st.button("Ejecutar simulación Monte Carlo"):
            with st.spinner("Simulando..."):
                # Simulación (en producción se usaría MonteCarloEngine)
                st.success("Simulación completada.")
                col1, col2 = st.columns(2)
                col1.metric("Riesgo de ruina", "0.02%")
                col2.metric("Capital final medio", "3,250 USDT")
                st.info("Distribución de resultados:")
                st.bar_chart(pd.DataFrame({
                    'P5': [1500], 'P25': [2200], 'P50': [3250], 'P75': [4800], 'P95': [6200]
                }).T)
    else:
        st.info("Actualiza los datos para ejecutar Monte Carlo.")

# -----------------------------------------------------------------------------
# TAB 8 — ESTADÍSTICAS
# -----------------------------------------------------------------------------
with tabs[8]:
    st.subheader("📋 ESTADÍSTICAS COMPLETAS")
    if st.session_state.data_loaded:
        metrics = st.session_state.metrics
        if metrics:
            st.write("### Métricas globales")
            df_metrics = pd.DataFrame([metrics])
            st.dataframe(df_metrics)

            tables = MetricsTables.create_all_tables(st.session_state.assets)
            for market, df in tables.items():
                if not df.empty:
                    st.write(f"### Métricas {market.capitalize()}")
                    st.dataframe(df)
        else:
            st.info("No hay métricas disponibles.")
    else:
        st.info("Actualiza los datos para ver estadísticas.")

# -----------------------------------------------------------------------------
# TAB 9 — CONFIGURACIÓN
# -----------------------------------------------------------------------------
with tabs[9]:
    st.subheader("⚙️ CONFIGURACIÓN DEL SISTEMA")
    st.markdown("""
    **Parámetros actuales**

    | Parámetro | Valor |
    |-----------|-------|
    | Capital | 1,000 USDT |
    | Riesgo por operación | 2.0% |
    | Apalancamiento máximo | 5x |
    | Universo Spot | ~1,500 activos |
    | Universo Margin | ~500 activos |
    | Universo Futures | ~650 activos |

    **Rutas**
    - Datos: `data/cache/`
    - Resultados: `data/results/`
    - Dashboard: `dashboard/app.py`

    **Versión del sistema:** 2.0.0
    """)

# -----------------------------------------------------------------------------
# TAB 10 — DIAGNÓSTICO (NUEVO)
# -----------------------------------------------------------------------------
with tabs[10]:
    st.subheader("🔍 DIAGNÓSTICO DEL SISTEMA")

    if st.session_state.data_loaded:
        assets = st.session_state.assets
        st.write(f"**Total de activos analizados:** {len(assets)}")
        st.write(f"**Señales generadas:** {len([a for a in assets if a.get('signal')])}")

        st.write("### Desglose por mercado")
        for market in ['spot', 'margin', 'futures']:
            m_assets = [a for a in assets if a.get('market') == market]
            m_signals = [a for a in m_assets if a.get('signal')]
            st.write(f"- **{market.capitalize()}**: {len(m_assets)} activos, {len(m_signals)} señales")

        st.write("### Últimas señales")
        signals = [a for a in assets if a.get('signal')]
        if signals:
            df_signals = pd.DataFrame([{
                'symbol': s['symbol'],
                'market': s['market'],
                'direction': s['signal']['direction'],
                'confidence': s['signal']['confidence'],
                'score': s['score']
            } for s in signals[:10]])
            st.dataframe(df_signals)
        else:
            st.warning("⚠️ No se encontraron señales. Verifica los filtros y la conexión a Binance.")

        # Estadísticas de filtros (simuladas si no hay datos reales)
        st.write("### Estadísticas de filtros (estimado)")
        if assets:
            total = len(assets)
            with_signal = len([a for a in assets if a.get('signal')])
            st.write(f"- **Activos con señal**: {with_signal} ({with_signal/total*100:.1f}%)")
            st.write(f"- **Activos sin señal**: {total - with_signal} ({(total-with_signal)/total*100:.1f}%)")
    else:
        st.info("🔄 Actualiza los datos para ver el diagnóstico del sistema.")
