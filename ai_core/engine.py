import ee 
from google.genai import types
from .diagnostic import client, MODEL_NAME, SYSTEM_PROMPT

def consultar_agronomo(prompt, contexto_espacial, imagen_bytes=None):
    """
    Motor unificado para diagnóstico agronómico.
    
    Args:
        prompt (str): La pregunta del usuario.
        contexto_espacial (str): Texto que incluye métricas Y el Bounding Box (coordenadas).
        imagen_bytes (bytes, optional): Datos binarios de la imagen.
    """
    if not client:
        return "Error: Cliente de IA no inicializado."
    
    # 1. Configuración de sistema inmutable
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT, 
        temperature=0.3
    )
    
    # 2. Construcción limpia del Payload (Separación de preocupaciones)
    # Aquí unificamos el contexto: Métricas + Coordenadas que vienen en contexto_espacial
    full_text_context = (
        f"Contexto Espacial y Referencias:\n{contexto_espacial}\n\n"
        f"Pregunta del Usuario: {prompt}"
    )
    
    # Lista de contenidos (Textual primero, luego visual)
    contents = [full_text_context]
    
    # 3. Inyección multimodal segura
    # Si la imagen existe, se añade como parte independiente, no como string
    if imagen_bytes:
        contents.append(types.Part.from_bytes(
            data=imagen_bytes, 
            mime_type='image/png'
        ))
        
    try:
        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=contents, 
            config=config
        )
        return response.text
    except Exception as e:
        return f"Error en el motor de IA: {str(e)}"