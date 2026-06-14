import os
import streamlit as st
from google import genai

# Identificador oficial para tu proyecto
MODEL_NAME = 'gemini-2.5-flash'

def get_client():
    """
    Obtiene el cliente de Gemini priorizando Streamlit Secrets (nube) 
    y usando variables de entorno (.env) como respaldo (local).
    """
    # 1. Intentamos obtener de st.secrets primero
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except (FileNotFoundError, KeyError):
        # 2. Si no existe, buscamos en las variables de entorno
        api_key = os.getenv("GEMINI_API_KEY")
    
    return genai.Client(api_key=api_key) if api_key else None

client = get_client()

SYSTEM_PROMPT = """Actúa como un Agrónomo Senior experto en teledetección.
TU TAREA PRINCIPAL: Siempre analiza la imagen satelital/radar adjunta en conjunto con los datos numéricos.
- Si ves una discrepancia entre los números y la imagen (ej: el radar muestra una mancha y el NDVI no), explícala.
- Describe patrones visuales específicos (formas, texturas) que veas en la imagen.
- No realices simulaciones si tienes la imagen a mano."""