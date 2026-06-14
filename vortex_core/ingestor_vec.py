import ee
import json

class VectorIngestor:
    """Módulo centralizado para la gestión de áreas de interés (AOI)."""
    
    @staticmethod
    def geojson_to_ee(coords):
        """Convierte una lista de coordenadas crudas en un Polygon de Earth Engine."""
        return ee.Geometry.Polygon(coords)

    @staticmethod
    def get_area_hectares(coords):
        """Calcula el área de la geometría en hectáreas de manera directa."""
        return ee.Geometry.Polygon(coords).area().divide(10000).getInfo()

    @staticmethod
    def get_geometry_from_geojson(file_path):
        """Carga un archivo GeoJSON del disco local y lo convierte en FeatureCollection."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return ee.FeatureCollection(data)

    @staticmethod
    def create_point_buffer(lat, lon, meters):
        """Crea un búfer circular (envoltura rectangular) sobre un punto."""
        return ee.Geometry.Point([lon, lat]).buffer(meters).bounds()
    
    @staticmethod
    def create_geometry_from_coords(lat, lon, buffer_meters=500):
        """Genera un polígono cuadrado alrededor de coordenadas dadas."""
        return ee.Geometry.Point([lon, lat]).buffer(buffer_meters).bounds()