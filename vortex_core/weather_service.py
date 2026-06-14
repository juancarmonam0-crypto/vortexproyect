import requests
import ee

class WeatherService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def get_weather_by_geometry(self, roi: ee.Geometry):
        centroid = roi.centroid().coordinates().getInfo()
        lon, lat = centroid[0], centroid[1]
        params = {'lat': lat, 'lon': lon, 'appid': self.api_key, 'units': 'metric'}
        try:
            response = requests.get(self.base_url, params=params, timeout=5)
            response.raise_for_status() # Lanza error si la API responde con código de error
            data = response.json()
            return {
                "temp": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "condition": data["weather"][0]["main"],
                "precipitation": data.get("rain", {}).get("1h", 0)
            }
        except Exception as e:
            print(f"Error clima: {e}") # Debugging en consola
            return {"temp": 0.0, "humidity": 0.0, "condition": "N/A", "precipitation": 0.0}