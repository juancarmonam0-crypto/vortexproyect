import ee

class SatelliteIngestor:
    """Módulo especializado para la ingesta de Sentinel-2 (Óptico)."""
    
    @staticmethod
    def get_sentinel_2(geometry, date_range):
        """Recupera la colección de Sentinel-2 armonizada y filtrada por nubes."""
        return (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(geometry)
                .filterDate(*date_range)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)))

    @staticmethod
    def get_index_url(roi, date_range, index_name):
        """Calcula el índice óptico y aplica las paletas de contraste realistas."""
        try:
            # Reducimos la colección por la mediana del año y recortamos al lote
            img = SatelliteIngestor.get_sentinel_2(roi, date_range).median().clip(roi)
            
            if index_name == "NDVI":
                computed_img = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
                vis_params = {
                    'min': 0.1, 
                    'max': 0.85, 
                    'palette': ['#FFFFFF', '#CE7E45', '#DF923D', '#F1B555', '#FCD163', '#99B718', '#74A021', '#256618', '#051803']
                }
                
            elif index_name == "NDRE":
                computed_img = img.normalizedDifference(['B8', 'B5']).rename('NDRE')
                vis_params = {
                    'min': 0.05, 
                    'max': 0.65, 
                    'palette': ['#E5E5E5', '#CCCCCC', '#99CC99', '#66BB66', '#339933', '#006600']
                }
                
            elif index_name == "NDWI":
                computed_img = img.normalizedDifference(['B3', 'B8']).rename('NDWI')
                vis_params = {
                    'min': -0.4, 
                    'max': 0.4, 
                    'palette': ['#CE7E45', '#FCD163', '#FFFFFF', '#ADC9FF', '#0044FF']
                }
                
            elif index_name == "MSI":
                computed_img = img.expression('float(B11) / float(B8)', {
                    'B11': img.select('B11'),
                    'B8': img.select('B8')
                }).rename('MSI')
                vis_params = {
                    'min': 0.4, 
                    'max': 1.8, 
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