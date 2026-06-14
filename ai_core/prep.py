# prep.py
import streamlit as st
import requests
from vortex_core.analisis_sat import SatelliteAnalyzer

def preparar_contexto_espacial(roi=None):
    """Extrae métricas y descarga la imagen para la ingesta de IA."""
    coords = st.session_state.get("current_coords", [])
    metrics = st.session_state.get("resultados_metrica_global", {})
    area = st.session_state.get("current_area", 0)
    
    # 1. Generar el contexto textual (lo que ya tenías)
    if not coords or not metrics:
        return "No hay datos de lote cargados en la sesión.", None

    contexto = f"Lote de {area:.2f} hectáreas. Métricas:\n"
    for nombre, vals in metrics.items():
        contexto += f"- {nombre}: Media {vals['mean']:.4f} (Desviación: {vals['std']:.4f}).\n"

    # 2. Obtener la imagen bytes (Multimodalidad)
    imagen_bytes = None
    if roi:
        try:
            # Obtenemos la URL de la capa principal (ej: NDVI)
            url = SatelliteAnalyzer.get_index_url(roi, ('2026-01-01', '2026-12-31'), "NDVI")
            if url:
                response = requests.get(url)
                if response.status_code == 200:
                    imagen_bytes = response.content
        except Exception as e:
            st.error(f"Error cargando imagen para IA: {e}")

    return contexto, imagen_bytes