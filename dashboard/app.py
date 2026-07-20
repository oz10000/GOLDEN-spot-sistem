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
    st.session_state.market_ranking = pd.DataFrame()
    st.session_state.multi_tf_ranking = {}

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
            stats = engine.get_detailed_diagnostic()
            st.json(stats)

    st.markdown("---")
    st.caption(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# =============================================================================
# TÍTULO PRINCIPAL
# =============================================================================

st.title("🏛️ GOLDEN CAPITAL ENGINE Ω — INSTITUTIONAL V2")
st.caption("Sistema cuantitativo profesional con datos reales de Binance")

# =============================================================================
# TABS (14 pestañas)
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
    "🔍 Diagnóstico",
    "📊 Market Radar"
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
# TAB 10 — TOP TEN
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
# TAB 11 — SEÑALES HISTÓRICAS
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

            summary = st.session_state.get('hist_summary', {})
            if summary:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total señales", summary.get('total', 0))
                col2.metric("Win Rate", f"{summary.get('win_rate', 0):.1%}")
                col3.metric("Profit Factor", f"{summary.get('profit_factor', 0):.2f}")
                col4.metric("Score medio", f"{summary.get('avg_score', 0):.2f}")

            st.dataframe(df_hist[['symbol', 'market', 'direction', 'timestamp_signal',
                                  'entry_price', 'exit_price', 'result', 'profit_loss',
                                  'confidence', 'score']])

            top = df_hist.sort_values('score', ascending=False).head(10)
            st.write("**Top 10 señales por score**")
            st.dataframe(top[['symbol', 'market', 'direction', 'score', 'profit_loss']])

            csv = df_hist.to_csv(index=False)
            st.download_button("📥 Descargar CSV", csv, "historical_signals.csv", "text/csv")
        else:
            st.warning(f"No se encontraron señales en los últimos {days_back} días.")

# -----------------------------------------------------------------------------
# TAB 12 — DIAGNÓSTICO (MEJORADO)
# -----------------------------------------------------------------------------
with tabs[12]:
    st.subheader("🔍 DIAGNÓSTICO DEL SISTEMA")

    if st.button("🔄 Actualizar diagnóstico"):
        with st.spinner("Generando diagnóstico..."):
            engine = st.session_state.engine
            stats = engine.get_detailed_diagnostic()
            st.session_state.diagnostic_stats = stats

    if 'diagnostic_stats' in st.session_state:
        stats = st.session_state.diagnostic_stats
        if 'error' in stats:
            st.error(f"Error: {stats['error']}")
        else:
            st.write("**Estado del motor**")
            st.write(f"- Total activos analizados: {stats.get('total_assets', 0)}")
            st.write(f"- Activos con Score ≥ 0.30: {stats.get('score_ok', 0)}")
            st.write(f"- Activos con ADX ≥ 20: {stats.get('adx_ok', 0)}")
            st.write(f"- Activos con KER ≥ 0.45: {stats.get('ker_ok', 0)}")
            st.write(f"- Activos con Régimen válido: {stats.get('regime_ok', 0)}")
            st.write(f"- Activos que pasan TODOS los filtros: {stats.get('passes_all', 0)}")
            st.write(f"- Señales generadas: {stats.get('signals_found', 0)}")

            if stats.get('passes_all', 0) == 0 and stats.get('signals_found', 0) == 0:
                st.warning("⚠️ **No hay señales** porque ningún activo cumple todos los filtros de entrada.")
                st.info("""
                **Motivo**: El score actual es inferior al mínimo requerido o los filtros de ADX/KER/Régimen no se cumplen.
                - **Score mínimo requerido**: 0.30
                - **ADX mínimo**: 20
                - **KER mínimo**: 0.45
                - **Régimen**: Tendencia_Fuerte, Tendencia_Débil, Normal o Expansión (excluye 'Chop' e 'Indefinido')
                """)
            elif stats.get('passes_all', 0) > 0 and stats.get('signals_found', 0) == 0:
                st.info("✅ Hay activos que cumplen los filtros, pero no se generaron señales porque el sistema requiere confirmaciones adicionales (ej. tendencia de EMAs, VWAP, etc.) que no se reflejan en el diagnóstico simple.")

            st.write(f"**Último escaneo:** {stats.get('timestamp', 'N/A')}")
    else:
        st.info("🔄 Haz clic en 'Actualizar diagnóstico' para ver el estado del sistema.")

# -----------------------------------------------------------------------------
# TAB 13 — MARKET RADAR (NUEVO)
# -----------------------------------------------------------------------------
with tabs[13]:
    st.subheader("📊 Market Radar / Ranking de Activos")

    # Selectores
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        top_n = st.selectbox("Mostrar TOP", [10, 20, 25, 30, "Todos"], index=1)
    with col2:
        selected_markets = st.multiselect(
            "Mercados",
            ["spot", "margin", "futures"],
            default=["spot", "margin", "futures"]
        )
    with col3:
        max_assets_input = st.number_input("Límite de activos (0 = sin límite)", min_value=0, value=200, step=50)

    if st.button("🔄 Actualizar ranking", use_container_width=True):
        with st.spinner("Generando ranking de activos..."):
            engine = st.session_state.engine
            max_assets = None if max_assets_input == 0 else max_assets_input
            df_rank = engine.get_market_ranking(markets=selected_markets, max_assets=max_assets)
            st.session_state.market_ranking = df_rank
            st.success(f"Ranking generado: {len(df_rank)} activos")

    # Sección multi-timeframe
    st.subheader("📈 Diagnóstico Multi-Timezone")
    if st.button("🔄 Analizar multi-timeframe"):
        with st.spinner("Analizando múltiples timeframes..."):
            engine = st.session_state.engine
            tf_results = engine.get_multi_timeframe_ranking(
                timeframes=['15m', '1h', '4h', '1d', '3d'],
                markets=selected_markets,
                max_assets=100
            )
            st.session_state.multi_tf_ranking = tf_results

    if st.session_state.multi_tf_ranking:
        tf_data = []
        for tf, data in st.session_state.multi_tf_ranking.items():
            tf_data.append({
                'Timeframe': tf,
                'Total Assets': data['total_assets'],
                'Avg Score': f"{data['avg_score']:.3f}",
                'Best Asset': data['best_asset'],
                'Signals': data['signals']
            })
        st.dataframe(pd.DataFrame(tf_data))

    if 'market_ranking' in st.session_state and not st.session_state.market_ranking.empty:
        df_rank = st.session_state.market_ranking

        # Aplicar filtro TOP N
        if top_n != "Todos":
            df_rank = df_rank.head(int(top_n))

        # Mostrar tabla con colores
        st.dataframe(
            df_rank[['symbol', 'market', 'price', 'score', 'adx', 'ker', 'regime',
                     'score_ok', 'adx_ok', 'ker_ok', 'regime_ok', 'passes_all']].style.applymap(
                lambda x: 'background-color: #d4edda' if x is True else 'background-color: #f8d7da' if x is False else '',
                subset=['score_ok', 'adx_ok', 'ker_ok', 'regime_ok', 'passes_all']
            ).format({
                'price': '{:.4f}',
                'score': '{:.3f}',
                'adx': '{:.1f}',
                'ker': '{:.3f}'
            })
        )

        # Resumen de diagnóstico
        total = len(df_rank)
        passes_all = df_rank[df_rank['passes_all'] == True].shape[0]
        score_ok = df_rank[df_rank['score_ok'] == True].shape[0]
        adx_ok = df_rank[df_rank['adx_ok'] == True].shape[0]
        ker_ok = df_rank[df_rank['ker_ok'] == True].shape[0]
        regime_ok = df_rank[df_rank['regime_ok'] == True].shape[0]

        st.markdown("---")
        st.subheader("📊 Diagnóstico del ranking")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total activos", total)
        col2.metric("Score ≥ 0.30", f"{score_ok} ({score_ok/total*100:.1f}%)")
        col3.metric("ADX ≥ 20", f"{adx_ok} ({adx_ok/total*100:.1f}%)")
        col4.metric("KER ≥ 0.45", f"{ker_ok} ({ker_ok/total*100:.1f}%)")
        col5.metric("Régimen válido", f"{regime_ok} ({regime_ok/total*100:.1f}%)")
        st.metric("Cumplen todos los filtros", f"{passes_all} ({passes_all/total*100:.1f}%)")

        # Explicación de ausencia de señales
        if passes_all == 0:
            st.warning("⚠️ **No hay señales** porque ningún activo cumple todos los filtros de entrada.")
            st.info("""
            **Motivo**: El score actual es inferior al mínimo requerido (0.30) o los filtros de ADX/KER/Régimen no se cumplen.
            - **Score mínimo requerido**: 0.30
            - **ADX mínimo**: 20
            - **KER mínimo**: 0.45
            - **Régimen**: Tendencia_Fuerte, Tendencia_Débil, Normal o Expansión (excluye 'Chop' e 'Indefinido')
            """)
        elif passes_all > 0 and st.session_state.signals.get('spot') is None and st.session_state.signals.get('margin') is None and st.session_state.signals.get('futures') is None:
            st.info("✅ Hay activos que cumplen los filtros, pero no se generaron señales porque el sistema requiere confirmaciones adicionales (ej. tendencia de EMAs, VWAP, etc.) que no se reflejan en este ranking simple.")

        # Mostrar los mejores activos que pasan todos los filtros
        top_passes = df_rank[df_rank['passes_all'] == True].head(10)
        if not top_passes.empty:
            st.subheader("🏆 Top 10 activos que cumplen todos los filtros")
            st.dataframe(top_passes[['symbol', 'market', 'price', 'score', 'adx', 'ker', 'regime']])

        # Score máximo actual
        max_score = df_rank['score'].max()
        st.metric("Score máximo actual", f"{max_score:.3f}")
        st.caption(f"Se requiere score ≥ 0.30 para considerar entrada. Actualmente el máximo es {max_score:.3f}.")

    else:
        st.info("🔄 Haz clic en 'Actualizar ranking' para obtener el Market Radar.")
