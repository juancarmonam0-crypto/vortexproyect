# historial_manager.py
import ee
from datetime import datetime, timedelta

class HistorialManager:
    
    @staticmethod
    def mask_s2_clouds(image):
        """Aplica una máscara estricta para remover nubes y cirros usando la banda QA60."""
        qa = image.select('QA60')
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11
        no_clouds = qa.bitwiseAnd(cloud_bit_mask).eq(0)
        no_cirrus = qa.bitwiseAnd(cirrus_bit_mask).eq(0)
        return image.updateMask(no_clouds.multiply(no_cirrus))

    @staticmethod
    def get_all_time_series(roi):
        """
        Consulta la serie temporal de TODAS las capas al mismo tiempo 
        con filtros estricto de órbita e instrumento para Sentinel-1.
        """
        series_completas = {
            "NDVI": {}, "NDRE": {}, "NDWI": {}, "MSI": {},
            "Radar (VV)": {}, "Radar (VH)": {}
        }
        
        hoy = datetime.now()
        
        for i in range(24, 0, -1):
            fin = hoy - timedelta(days=30 * (i-1))
            inicio = fin - timedelta(days=30)
            fecha_str = fin.strftime("%Y-%m-%d")
            
            # --- 1. PROCESAMIENTO ÓPTICO MASIVO (S2) ---
            col_s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                     .filterBounds(roi)
                     .filterDate(inicio.strftime("%Y-%m-%d"), fin.strftime("%Y-%m-%d"))
                     .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                     .map(HistorialManager.mask_s2_clouds))
            
            if col_s2.size().getInfo() > 0:
                img_optica = col_s2.sort('CLOUDY_PIXEL_PERCENTAGE').first()
                
                ndvi = img_optica.normalizedDifference(['B8', 'B4']).rename('NDVI')
                ndre = img_optica.normalizedDifference(['B8', 'B5']).rename('NDRE')
                ndwi = img_optica.normalizedDifference(['B3', 'B8']).rename('NDWI')
                msi = img_optica.select('B11').divide(img_optica.select('B8')).rename('MSI')
                
                img_indices = img_optica.addBands([ndvi, ndre, ndwi, msi])
                
                try:
                    stats = img_indices.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=roi,
                        scale=30
                    ).getInfo()
                    
                    if stats.get('NDVI') and stats['NDVI'] >= 0.1:
                        series_completas["NDVI"][fecha_str] = float(stats['NDVI'])
                    if stats.get('NDRE'): series_completas["NDRE"][fecha_str] = float(stats['NDRE'])
                    if stats.get('NDWI'): series_completas["NDWI"][fecha_str] = float(stats['NDWI'])
                    if stats.get('MSI'):  series_completas["MSI"][fecha_str] = float(stats['MSI'])
                except Exception:
                    pass

           # --- 2. PROCESAMIENTO RADAR MASIVO (S1) RESTAURADO Y ESTABILIZADO ---
            col_s1 = (ee.ImageCollection("COPERNICUS/S1_GRD")
                     .filterBounds(roi)
                     .filterDate(inicio.strftime("%Y-%m-%d"), fin.strftime("%Y-%m-%d"))
                     # Filtros requeridos para estabilizar la respuesta de datos GRD 
                     .filter(ee.Filter.eq('instrumentMode', 'IW'))
                     .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                     .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
                     # CRUCIAL: Filtramos para usar solo órbitas DESCENDIENTES. 
                     # Esto elimina el 90% de los picos artificiales de radar de un mes a otro.
                     .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING')))
            
            if col_s1.size().getInfo() > 0:
                try:
                    # Tomamos el compuesto mediano nativo del catálogo (ya viene en dB)
                    radar_img = col_s1.median()
                    
                    stats_radar = radar_img.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=roi,
                        scale=30
                    ).getInfo()
                    
                    if stats_radar.get('VV'): series_completas["Radar (VV)"][fecha_str] = float(stats_radar['VV'])
                    if stats_radar.get('VH'): series_completas["Radar (VH)"][fecha_str] = float(stats_radar['VH'])
                except Exception:
                    pass
                    
        return series_completas