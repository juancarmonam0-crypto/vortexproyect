# map_engine.py
import folium
from folium.plugins import Draw
import ee

def get_map():
    """Genera el mapa base interactivo para dibujar."""
    m = folium.Map(location=[4.71, -74.07], zoom_start=12)
    draw = Draw(
        draw_options={"polyline": False, "rectangle": True, "polygon": True, "circle": False, "marker": False}
    )
    draw.add_to(m)
    return m

def add_gee_layer(mapa, ee_image_object, vis_params, name):
    """Añade capas dinámicas de Earth Engine al mapa como azulejos (Tiles)."""
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Google Earth Engine',
        name=name,
        overlay=True,
        control=True
    ).add_to(mapa)
    return mapa