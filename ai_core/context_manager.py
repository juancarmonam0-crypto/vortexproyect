# ai_core/context_manager.py
import streamlit as st
from ai_core import prep
from pipeline_manager import PipelineManager

def preparar_contexto_para_ia(roi):
    """Prepara texto, Bounding Box y busca la imagen para la IA."""
    
    # 1. Obtener contexto textual
    texto = prep.preparar_contexto_espacial()
    
    # 2. Inyección de Coordenadas
    # Usamos el objeto roi directamente o desde session_state
    coords_info = roi.bounds().getInfo()['coordinates'][0] 
    contexto_geografico = f"\nREFERENCIA ESPACIAL (Bounding Box): {coords_info}"
    
    # 3. Obtener imagen bytes con validación
    # Aseguramos que el ROI sea válido antes de llamar al Pipeline
    try:
        bytes_img = PipelineManager.get_image_bytes(roi, ('2026-01-01', '2026-12-31'), "NDVI")
        st.session_state["temp_img_bytes"] = bytes_img
    except Exception as e:
        print(f"Error al descargar imagen: {e}")
        st.session_state["temp_img_bytes"] = None
    
    return f"{texto}\n{contexto_geografico}"