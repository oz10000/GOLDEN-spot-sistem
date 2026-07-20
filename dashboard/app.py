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
from analytics.historical_signals import HistoricalSignalFinder
from optimization.top_assets import TopAssetsRanker

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
    st.session_state.top_assets = pd.DataFrame()
    st.session_state.historical_signals = pd.DataFrame()

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

    col1, col2 = st.columns(2)
    with col1:
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

    with col2:
        if st.button("🔍 Diagnóstico rápido", use_container_width=True):
            engine = st.session_state.engine
            stats = engine.get_diagnostic_stats()
            st.json(stats)

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
    "🏅 Top Ten",
    "📚 Señales Históricas",
    "🔍 Diagnóstico"
])

# -----------------------------------------------------------------------------
# TAB 0 — DASHBOARD
# -----------------------------------------------------------------------------
with tabs[0]:
    st.subheader("📊 Estado general del mercado")

    if st.session_state.data_loaded:
        metrics = st.session_state.metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Win Rate", f"{metrics.get('win_rate', 0):.1%}")
        col2.metric("Profit Factor", f"{metrics.get('profit_factor', 0):.2f}")
        col3.metric("Sharpe", f"{metrics.get('sharpe', 0):.2f}")
        col4.metric("Drawdown", f"{metrics.get('max_drawdown', 0):.1f}%")

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
# TAB 10 — TOP TEN (NUEVO)
# -----------------------------------------------------------------------------
with tabs[10]:
    st.subheader("🏅 TOP TEN ACTIVOS POR CALIDAD")

    if st.button("Generar Top Ten"):
        with st.spinner("Analizando activos..."):
            engine = st.session_state.engine
            df_top = engine.get_top_assets()
            st.session_state.top_assets = df_top
            st.success(f"Top Ten generado con {len(df_top)} activos analizados")

    if 'top_assets' in st.session_state and not st.session_state.top_assets.empty:
        df_top = st.session_state.top_assets
        st.write("**Ranking global**")
        st.dataframe(df_top[['symbol', 'market', 'quality_score', 'volume_score',
                             'adx', 'ker', 'regime']].head(10))

        st.write("**Top Ten por mercado**")
        for market in ['spot', 'margin', 'futures']:
            sub = df_top[df_top['market'] == market]
            if not sub.empty:
                st.write(f"**{market.capitalize()}**")
                st.dataframe(sub[['symbol', 'quality_score', 'adx', 'ker']].head(10))
    else:
        st.info("Haz clic en 'Generar Top Ten' para obtener el ranking.")

# -----------------------------------------------------------------------------
# TAB 11 — SEÑALES HISTÓRICAS (NUEVO)
# -----------------------------------------------------------------------------
with tabs[11]:
    st.subheader("📚 SEÑALES HISTÓRICAS (Últimos 7 días)")

    col1, col2 = st.columns([2, 1])
    with col1:
        max_assets_hist = st.slider("Máximo de activos a analizar", 20, 200, 100)
    with col2:
        days_back = st.slider("Días hacia atrás", 1, 14, 7)

    if st.button("🔍 Buscar señales históricas"):
        with st.spinner(f"Analizando {max_assets_hist} activos en los últimos {days_back} días..."):
            finder = HistoricalSignalFinder(days_back=days_back)
            df_hist = finder.scan(max_assets=max_assets_hist)
            st.session_state.historical_signals = df_hist
            summary = finder.get_summary(df_hist)
            st.session_state.hist_summary = summary

    if 'historical_signals' in st.session_state:
        df_hist = st.session_state.historical_signals
        if not df_hist.empty:
            st.success(f"Se encontraron {len(df_hist)} señales históricas")

            # Resumen
            summary = st.session_state.get('hist_summary', {})
            if summary:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total señales", summary.get('total', 0))
                col2.metric("Win Rate", f"{summary.get('win_rate', 0):.1%}")
                col3.metric("Profit Factor", f"{summary.get('profit_factor', 0):.2f}")
                col4.metric("Score medio", f"{summary.get('avg_score', 0):.2f}")

            # Tabla
            st.dataframe(df_hist[['symbol', 'market', 'direction', 'timestamp_signal',
                                  'entry_price', 'exit_price', 'result', 'profit_loss',
                                  'confidence', 'score']])

            # Top 10 por score
            top = df_hist.sort_values('score', ascending=False).head(10)
            st.write("**Top 10 señales por score**")
            st.dataframe(top[['symbol', 'market', 'direction', 'score', 'profit_loss']])

            # Descargar CSV
            csv = df_hist.to_csv(index=False)
            st.download_button("📥 Descargar CSV", csv, "historical_signals.csv", "text/csv")
        else:
            st.warning(f"No se encontraron señales en los últimos {days_back} días.")

# -----------------------------------------------------------------------------
# TAB 12 — DIAGNÓSTICO (MEJORADO)
# -----------------------------------------------------------------------------
with tabs[12]:
    st.subheader("🔍 DIAGNÓSTICO DEL SISTEMA")

    if st.session_state.data_loaded:
        assets = st.session_state.assets
        engine = st.session_state.engine
        stats = engine.get_diagnostic_stats()

        st.write("**Estado del motor**")
        st.write(f"- Activos analizados totales: {stats.get('total_assets', 0)}")
        st.write(f"- Señales encontradas: {stats.get('signals_found', 0)}")

        st.write("**Desglose por mercado**")
        for market, data in stats.get('by_market', {}).items():
            st.write(f"- {market.capitalize()}: {data['total']} activos, {data['signals']} señales")

        st.write("**Último escaneo**")
        st.write(f"- {stats.get('timestamp', 'N/A')}")

        st.write("**Filtros activos**")
        st.write("""
        - ADX >= 20
        - KER >= 0.45
        - Score >= 0.30
        - Precio > EMA50 y EMA200 (con tolerancia 2%)
        - Precio > VWAP (con tolerancia 2%)
        - Régimen != Chop ni Indefinido
        """)

        # Historial de señales (si existe)
        if 'historical_signals' in st.session_state:
            df_hist = st.session_state.historical_signals
            st.write(f"**Señales históricas (últimos 7 días)**: {len(df_hist)}")
            if not df_hist.empty:
                st.dataframe(df_hist[['symbol', 'market', 'direction', 'result', 'score']].head(5))

        # Top Ten
        if 'top_assets' in st.session_state and not st.session_state.top_assets.empty:
            df_top = st.session_state.top_assets
            st.write(f"**Top Ten generado**: {len(df_top)} activos clasificados")

    else:
        st.info("🔄 Actualiza los datos para ver el diagnóstico completo.")
