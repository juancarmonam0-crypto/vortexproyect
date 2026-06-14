# pipeline_manager.py
import ee
from vortex_core.ingestor_sat import SatelliteIngestor

class PipelineManager:
    
    @staticmethod
    def get_layer_url(roi, rango_fechas, selected_layer, banda_visual):
        """Obtiene de forma segura la URL de la miniatura satelital según el sensor."""
        try:
            if "Radar" not in selected_layer:
                # CORRECCIÓN: Llamamos al Analyzer que maneja los índices y mapas
                from vortex_core.analisis_sat import SatelliteAnalyzer
                return SatelliteAnalyzer.get_index_url(roi, rango_fechas, selected_layer)
            else:
                from vortex_core.ingestor_sat_radar import SatelliteIngestorRadar
                return SatelliteIngestorRadar.get_radar_url(roi, rango_fechas, banda_visual)
        except Exception:
            return None

    @staticmethod
    def calculate_current_metrics(roi, rango_fechas, capas):
        """Calcula las métricas unificadas actuales incluyendo desviación estándar y radar real."""
        from vortex_core.analisis_sat import SatelliteAnalyzer
        resultados = {}
        
        # 1. Dataset Óptico (Sentinel-2)
        try:
            img_s2 = SatelliteIngestor.get_sentinel_2(roi, rango_fechas)
            cube = SatelliteAnalyzer.prepare_dataset(img_s2)
        except Exception:
            cube = None

        # 2. Dataset Radar Nativo (Sentinel-1)
        try:
            from vortex_core.ingestor_sat_radar import SatelliteIngestorRadar
            img_s1 = SatelliteIngestorRadar.get_sentinel_1(roi, rango_fechas)
            radar_img = img_s1.median()
        except Exception:
            radar_img = None

        reducer_combi = ee.Reducer.mean().combine(reducer2=ee.Reducer.stdDev(), sharedInputs=True)

        # 3. Extracción y mapeo de estadísticas
        for nombre, banda_key in capas.items():
            resultados[nombre] = {"mean": 0.0, "std": 0.0}
            
            if "Radar" not in nombre and cube is not None:
                try:
                    img_banda = cube.select(banda_key)
                    stats = img_banda.reduceRegion(reducer=reducer_combi, geometry=roi, scale=10).getInfo()
                    
                    resultados[nombre] = {
                        "mean": float(stats.get(f"{banda_key}_mean") or 0.0), 
                        "std": float(stats.get(f"{banda_key}_stdDev") or 0.0)
                    }
                except Exception:
                    pass
                    
            elif "Radar" in nombre and radar_img is not None:
                try:
                    banda_pura = banda_key.replace('_dB', '')
                    img_radar_banda = radar_img.select(banda_pura)
                    stats = img_radar_banda.reduceRegion(reducer=reducer_combi, geometry=roi, scale=30).getInfo()
                    
                    resultados[nombre] = {
                        "mean": float(stats.get(f"{banda_pura}_mean") or 0.0),
                        "std": float(stats.get(f"{banda_pura}_stdDev") or 0.0)
                    }
                except Exception:
                    pass
                    
        return resultados
    
    @staticmethod
    def get_multimodal_bytes(roi, rango_fechas):
        """Genera y descarga la imagen fusionada (Óptico + Radar) para la IA."""
        import requests
        from vortex_core.ingestor_sat import SatelliteIngestor
        from vortex_core.analisis_sat import SatelliteAnalyzer
        from vortex_core.ingestor_sat_radar import SatelliteIngestorRadar
        from vortex_core.analisis_sat_radar import SatelliteAnalyzerRadar

        try:
            # 1. Óptico (Sentinel-2)
            img_s2 = SatelliteIngestor.get_sentinel_2(roi, rango_fechas).median().clip(roi)
            img_s2_masked = SatelliteAnalyzer.mask_non_vegetation(img_s2)
            optica_norm = img_s2_masked.select(['B8', 'B4', 'B3']).unitScale(0, 3000)

            # 2. Radar (Sentinel-1)
            img_s1 = SatelliteIngestorRadar.get_sentinel_1(roi, rango_fechas).median().clip(roi)
            img_s1_proc = SatelliteAnalyzerRadar.process_radar(img_s1)
            radar_norm = img_s1_proc.select(['VV_dB', 'VH_dB']).unitScale(-25, 0)

            # 3. Fusión (Stacking)
            compuesto = ee.Image.cat([optica_norm, radar_norm])

            # 4. Generar URL y convertir a bytes
            url = compuesto.getThumbURL({
                'region': roi, 'dimensions': 512, 'format': 'png',
                'bands': ['B8', 'B4', 'VV_dB'] # RGB: NIR, Rojo, Radar
            })
            
            response = requests.get(url)
            return response.content if response.status_code == 200 else None
        except Exception:
            return None
    # Agregar esto dentro de la clase PipelineManager en pipeline_manager.py
    @staticmethod
    
    def get_image_bytes(roi, rango_fechas, selected_layer):
        """Descarga bytes de la imagen para la IA."""
        import requests
        from vortex_core.analisis_sat import SatelliteAnalyzer
        
        try:
            url = SatelliteAnalyzer.get_index_url(roi, rango_fechas, selected_layer)
            if url:
                response = requests.get(url)
                return response.content if response.status_code == 200 else None
        except Exception:
            return None