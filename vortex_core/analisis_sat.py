# vortex_core/analisis_sat.py
import ee

class SatelliteAnalyzer:
    """Módulo especializado para el análisis, procesamiento matemático y renderizado de índices ópticos."""
    
    @staticmethod
    def get_sentinel_2(geometry, date_range):
        """Recupera la colección de Sentinel-2 armonizada de reflectancia de superficie."""
        return (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(geometry)
                .filterDate(*date_range)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)))
    @staticmethod
    def mask_non_vegetation(img):
        """Aplica una máscara para excluir caminos y áreas sin vegetación basándose en el NDVI."""
        # Filtramos píxeles con NDVI menor a 0.2 (típico de caminos o suelo desnudo)
        ndvi = img.normalizedDifference(['B8', 'B4'])
        mask = ndvi.gt(0.2) 
        return img.updateMask(mask)
    
    @staticmethod
    def get_mean_value(image, geometry, band_name):
        """Calcula la media de una banda aplicando la máscara de vegetación para ignorar caminos/suelo."""
        # Aplicamos la máscara de vegetación creada anteriormente
        img_limpia = SatelliteAnalyzer.mask_non_vegetation(image)
        
        # Calculamos la media solo sobre los píxeles que pasaron el filtro (la palma)
        stats = img_limpia.select(band_name).reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=10,
            maxPixels=1e9
        )
        return stats.get(band_name)

    @staticmethod
    def prepare_dataset(image_collection_or_img):
        """Genera un cubo multibanda local con las fórmulas e índices ópticos corregidos."""
        if isinstance(image_collection_or_img, ee.ImageCollection):
            img = image_collection_or_img.median()
        else:
            img = image_collection_or_img
            
        ndvi = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
        ndre = img.normalizedDifference(['B8', 'B5']).rename('NDRE')
        # NDWI Estándar de Gao (NIR - SWIR) para humedad foliar real en palma aceitera
        ndwi = img.normalizedDifference(['B8', 'B11']).rename('NDWI')
        msi = img.expression('float(B11) / float(B8)', {
            'B11': img.select('B11'), 'B8': img.select('B8')
        }).rename('MSI')
        
        return ee.Image([ndvi, ndre, ndwi, msi])

    @staticmethod
    def get_index_url(roi, date_range, index_name):
        """Calcula el índice óptico y aplica parámetros de visualización agrícola."""
        try:
            img = SatelliteAnalyzer.get_sentinel_2(roi, date_range).median().clip(roi)
            
            if index_name == "NDVI":
                computed_img = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
                vis_params = {
                    'min': 0.1, 'max': 0.85, 
                    'palette': ['#FFFFFF', '#CE7E45', '#DF923D', '#F1B555', '#FCD163', '#99B718', '#74A021', '#256618', '#051803']
                }
            elif index_name == "NDRE":
                computed_img = img.normalizedDifference(['B8', 'B5']).rename('NDRE')
                vis_params = {
                    'min': 0.05, 'max': 0.65, 
                    'palette': ['#E5E5E5', '#CCCCCC', '#99CC99', '#66BB66', '#339933', '#006600']
                }
            elif index_name == "NDWI":
                # NDWI de Gao balanceado para cultivos densos y perennes
                computed_img = img.normalizedDifference(['B8', 'B11']).rename('NDWI')
                vis_params = {
                    'min': 0.0, 'max': 0.5, 
                    'palette': ['#CE7E45', '#FCD163', '#FFFFFF', '#ADC9FF', '#0044FF']
                }
            elif index_name == "MSI":
                computed_img = img.expression('float(B11) / float(B8)', {
                    'B11': img.select('B11'), 'B8': img.select('B8')
                }).rename('MSI')
                vis_params = {
                    'min': 0.4, 'max': 1.8, 
                    'palette': ['#006600', '#339933', '#99CC99', '#FFFFCC', '#CE7E45', '#FF0000']
                }
            else:
                return None

            return computed_img.getThumbURL({
                'region': roi,
                'dimensions': 512,
                'format': 'png',
                **vis_params
            })
        except Exception:
            return None
            
class DataProcessor:
    @staticmethod
    def clean_and_flag(data_dict, is_radar=False):
        import pandas as pd
        df = pd.DataFrame(list(data_dict.items()), columns=["Fecha", "Valor"])
        df["Fecha"] = pd.to_datetime(df["Fecha"])
        df = df.sort_values("Fecha")
        
        # Suavizado para detección de ruido
        df["Rolling_Median"] = df["Valor"].rolling(window=3, center=True, min_periods=1).median()
        
        # Detección de interferencia (Lógica unificada)
        if not is_radar:
            df["Interferencia"] = df["Valor"] < (df["Rolling_Median"] * 0.80)
        else:
            df["Interferencia"] = (df["Valor"] - df["Rolling_Median"]).abs() > 4.0
            
        df.loc[df["Interferencia"], "Valor"] = df["Rolling_Median"]
        return df
