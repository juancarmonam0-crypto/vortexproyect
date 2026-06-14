import ee

class SatelliteIngestorRadar:
    """Módulo especializado para la ingesta y procesamiento de Sentinel-1 (Radar SAR)."""
    
    @staticmethod
    def get_sentinel_1(geometry, date_range):
        return (ee.ImageCollection("COPERNICUS/S1_GRD")
                .filterBounds(geometry)
                .filterDate(*date_range)
                .filter(ee.Filter.eq('instrumentMode', 'IW'))
                .median())

    @staticmethod
    def get_radar_url(roi, date_range, band_name):
        from vortex_core.analisis_sat_radar import SatelliteAnalyzerRadar
        
        s1 = SatelliteIngestorRadar.get_sentinel_1(roi, date_range)
        img = SatelliteAnalyzerRadar.process_radar(s1).select(band_name).unmask(-30)
        
        if 'VH' in band_name:
            vis_params = {'min': -25, 'max': -10}
        else:
            vis_params = {'min': -18, 'max': 0}
            
        return img.getThumbURL({
            'region': roi,
            'dimensions': 512,
            'format': 'png',
            **vis_params,
            'palette': ['#050505', '#4a4a4a', '#9a9a9a', '#ffffff']
        })