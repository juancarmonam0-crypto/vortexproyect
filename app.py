import streamlit as st
from streamlit_folium import st_folium
import ee
import pandas as pd 
import plotly.express as px  
from config import GEE_PROJECT
import importlib

# Módulos de control, mapeo e interfaz estables
import map_engine
import vortex_ui
from historial_manager import HistorialManager
from vortex_core.ingestor_vec import VectorIngestor
from vortex_core.weather_service import WeatherService
from vortex_core.analisis_sat import SatelliteAnalyzer

# Inicialización segura de Google Earth Engine
try:
    ee.Initialize(project=GEE_PROJECT)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=GEE_PROJECT)

try:
    weather_api_key = st.secrets["WEATHER_API_KEY"]
    weather_engine = WeatherService(api_key=weather_api_key)
except Exception as e:
    st.error("No se encontró la clave de API climática. Verifica tus secretos.")
    weather_engine = None # O maneja el error según tu lógica
    
st.set_page_config(page_title="Vortex 2.0", layout="wide")
st.title("🛰️ Vortex 2.0")

# Diccionario Maestro de Capas del Sistema
capas = {
    "NDVI": "NDVI", "NDRE": "NDRE", "NDWI": "NDWI", 
    "MSI": "MSI", "Radar (VV)": "VV_dB", "Radar (VH)": "VH_dB"
}

# 1. Definición de Pestañas Principales
tab_monitoreo, tab_ia = st.tabs(["🛰️ Panel de Monitoreo Espacial", "🤖 Consultoría IA Gemini"])

with tab_monitoreo:
    col_mapa, col_capa = st.columns([1, 1])

    with col_mapa:
        st.subheader("🗺️ Mapa Base Interactivo")
        map_data = st_folium(map_engine.get_map(), width="100%", height=450, key="vortex_folium_map")

    # Flujo de Procesamiento y Renderizado Dinámico Modularizado
    if map_data and map_data.get("last_active_drawing"):
        geometry_data = map_data["last_active_drawing"]["geometry"]
        coords = geometry_data["coordinates"][0]
        
        # Ingesta espacial vectorial
        roi = VectorIngestor.geojson_to_ee(coords)
        area_ha = VectorIngestor.get_area_hectares(coords)
        rango_fechas = ('2026-01-01', '2026-12-31')

        # === CAMBIO APLICADO: Guardado en sesión para persistencia ===
        st.session_state["roi"] = roi
        st.session_state["current_coords"] = coords
        st.session_state["current_area"] = area_ha
        # ===========================================================

        # A. Visualizador de la Capa Activa (Derecha)
        with col_capa:
            st.subheader("🖼️ Visualizador de Capa Activa")
            
            with st.spinner("Cargando renderizado satelital..."):
                if "selected_layer" not in st.session_state:
                    st.session_state["selected_layer"] = "NDVI"
                
                selected_layer = st.session_state["selected_layer"]
                
                # Consumo directo del backend desacoplado
                if "Radar" not in selected_layer:
                    img_url = SatelliteAnalyzer.get_index_url(roi, rango_fechas, selected_layer)
                else:
                    from vortex_core.ingestor_sat_radar import SatelliteIngestorRadar
                    # CORRECCIÓN DE BANDAS: Enviamos el formato exacto que espera el backend
                    banda_radar = "VV_dB" if "VV" in selected_layer else "VH_dB"
                    img_url = SatelliteIngestorRadar.get_radar_url(roi, rango_fechas, banda_radar)
            
            if img_url:
                st.image(img_url, use_container_width=True)
            else:
                st.warning("No se pudo recuperar la miniatura de esta capa.")
                
            st.selectbox(
                "Selecciona la capa a renderizar en el lote:", 
                list(capas.keys()), 
                key="selected_layer"
            )

        # B. Panel de Métricas Biofísicas
        st.markdown("---")
        st.subheader("📊 Diagnóstico Biofísico del Lote")
        st.metric("📐 Superficie del Área Seleccionada", f"{area_ha:.2f} Hectáreas")
        
        with st.spinner("Calculando estadísticas biofísicas de la escena..."):
            resultados_metrica = {}
            
            # Llamado modular al generador del cubo óptico
            try:
                cube = SatelliteAnalyzer.prepare_dataset(SatelliteAnalyzer.get_sentinel_2(roi, rango_fechas))
            except Exception:
                cube = None

            try:
                from vortex_core.ingestor_sat_radar import SatelliteIngestorRadar
                radar_img = SatelliteIngestorRadar.get_sentinel_1(roi, rango_fechas)
            except Exception:
                radar_img = None

            reducer_combi = ee.Reducer.mean().combine(reducer2=ee.Reducer.stdDev(), sharedInputs=True)

            # Reducción de regiones unificada
            for nombre, banda_key in capas.items():
                if "Radar" not in nombre and cube is not None:
                    try:
                        stats = cube.select(banda_key).reduceRegion(reducer=reducer_combi, geometry=roi, scale=10).getInfo()
                        resultados_metrica[nombre] = {
                            "mean": float(stats.get(f"{banda_key}_mean") or 0.0),
                            "std": float(stats.get(f"{banda_key}_stdDev") or 0.0)
                        }
                    except Exception:
                        resultados_metrica[nombre] = {"mean": 0.0, "std": 0.0}
                elif "Radar" in nombre and radar_img is not None:
                    try:
                        stats = radar_img.reduceRegion(reducer=reducer_combi, geometry=roi, scale=30).getInfo()
                        banda_pura = banda_key.replace('_dB', '')
                        resultados_metrica[nombre] = {
                            "mean": float(stats.get(f"{banda_pura}_mean") or 0.0),
                            "std": float(stats.get(f"{banda_pura}_stdDev") or 0.0)
                        } 
                    except Exception:
                        resultados_metrica[nombre] = {"mean": 0.0, "std": 0.0}

            st.session_state["resultados_metrica_global"] = resultados_metrica

        # Mostrar métricas en columnas
        cols = st.columns(3)
        for idx, (capa_nom, vals) in enumerate(resultados_metrica.items()):
            with cols[idx % 3]:
                st.metric(
                    label=f"Índice {capa_nom}", 
                    value=f"{vals['mean']:.4f}", 
                    delta=f"± {vals['std']:.4f} (Disp.)",
                    delta_color="gray"
                )

        # C. Análisis Histórico (Suavizado y marcas corregidas)
        st.markdown("---")
        st.markdown("### 📈 Análisis Cronológico Avanzado")
        btn_hist = st.button("📊 Generar Análisis Histórico Multicapa", use_container_width=True)

        if btn_hist or st.session_state.get('historial_calculado', False):
            if btn_hist:
                st.session_state['historial_calculado'] = False
                
            if 'datos_historial_completos' not in st.session_state or btn_hist:
                with st.spinner("Extrayendo series de tiempo unificadas..."):
                    st.session_state['datos_historial_completos'] = HistorialManager.get_all_time_series(roi)
                    st.session_state['historial_calculado'] = True

            capa_grafico = st.selectbox("Selecciona qué historial deseas visualizar:", list(capas.keys()), key="selector_grafico")
            datos_a_graficar = st.session_state['datos_historial_completos'].get(capa_grafico, {})
            
            if datos_a_graficar:
                df = pd.DataFrame(list(datos_a_graficar.items()), columns=["Fecha", "Valor"])
                df = df.dropna().sort_values(by="Fecha")
                df["Fecha"] = pd.to_datetime(df["Fecha"])
                df["Valor Original"] = df["Valor"]
                df["Estado"] = "Dato Clean"
                
                if len(df) > 3:
                    # Generamos el suavizado por mediana móvil
                    rolling_median = df["Valor"].rolling(window=3, center=True, min_periods=1).median()
                    
                    # Identificación matemática de anomalías según tipo de capa
                    if "Radar" not in capa_grafico:
                        if capa_grafico == "MSI":
                            anomalos = (df["Valor"] > (rolling_median * 1.20))
                        elif capa_grafico == "NDWI":
                            anomalos = (df["Valor"] - rolling_median).abs() > 0.15
                        else:
                            anomalos = (df["Valor"] < (rolling_median * 0.80))
                    else:
                        anomalos = (df["Valor"] - rolling_median).abs() > 1.8
                    
                    # Marcamos el estado ruidoso para las X rojas
                    df.loc[anomalos, "Estado"] = "Ruido/Nube Detectada"
                    
                    # GARANTÍA DE SUAVIZADO: Toda la línea principal pasa a tomar el valor de la mediana suavizada
                    df["Valor"] = rolling_median

                # El gráfico principal de líneas renderiza SIEMPRE los valores suavizados y limpios
                fig = px.line(df, x="Fecha", y="Valor", title=f"Evolución Histórica Dinámica (Suavizada): {capa_grafico}", markers=True) 
                
                # Se clavan las "X" rojas mapeando el Valor Original ruidoso donde se detectó la interferencia
                if df["Estado"].str.contains("Ruido/Nube Detectada").any():
                    df_anomalos = df[df["Estado"] == "Ruido/Nube Detectada"]
                    fig.add_scatter(
                        x=df_anomalos["Fecha"], y=df_anomalos["Valor Original"],
                        mode="markers", name="⚠️ Capturas con Interferencia",
                        marker=dict(color="crimson", size=10, symbol="x")
                    )
                
                fig.update_layout(hovermode="x unified", height=400, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"No se encontraron suficientes datos históricos estables para {capa_grafico}.")

        # D. Módulo Climático
        st.markdown("---")
        try:
            weather_data = weather_engine.get_weather_by_geometry(roi)
            vortex_ui.render_weather_dashboard(weather_data) 
        except Exception:
            st.warning("Servicio meteorológico fuera de línea temporalmente.")
    else:
        with col_capa:
            st.info("👈 Esperando que dibujes un polígono en el mapa base para inicializar el visualizador satelital.")
        st.info("👈 Dibuja un polígono en el mapa superior para iniciar el pipeline de análisis computacional.")

# En app.py

# Importa solo los módulos necesarios una vez al inicio del archivo
from ai_core import diagnostic, context_manager 

with tab_ia:
    # Verificación simple de que el ROI existe
    if 'roi' in st.session_state:
        vortex_ui.render_ai_chat_tab(
            api_configurada=diagnostic.client is not None,
            system_prompt=diagnostic.SYSTEM_PROMPT,
            # Se delega la preparación al orquestador
            obtener_contexto_fn=lambda: context_manager.preparar_contexto_para_ia(st.session_state.roi)
        )
    else:
        st.info("Por favor, selecciona un área en el mapa para iniciar el diagnóstico.")