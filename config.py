# config.py

# ID del proyecto (Configúralo aquí para no quemarlo en el app.py)
GEE_PROJECT = 'project-5845063f-4029-4028-b1e'

# Lista maestra de bandas para los modelos de IA
MODEL_FEATURES = [
    'NDVI', 'NDRE', 'NDWI', 'MSI', 
    'VV_dB', 'VH_dB', 'VH_VV_ratio'
]

# Configuración de visualización por defecto
VIZ_PARAMS = {
    'NDVI': {'min': 0, 'max': 1, 'palette': ['blue', 'white', 'green']},
    'VV_dB': {'min': -25, 'max': 0, 'palette': ['black', 'white']}
}