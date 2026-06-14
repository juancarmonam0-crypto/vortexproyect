import ee

class SatelliteAnalyzerRadar:
    @staticmethod
    def process_radar(sar_img):
        # COPERNICUS/S1_GRD ya viene en dB de forma nativa. 
        # NO aplicar .log10(). Solo renombramos para mantener tu estándar.
        sar_db = sar_img.select(['VV', 'VH']).rename(['VV_dB', 'VH_dB'])
        
        # Mantenemos el recorte de seguridad para evitar picos extraños
        return sar_db.clamp(-30, 0)