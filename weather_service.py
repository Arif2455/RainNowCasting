import requests
import time
from datetime import datetime
from src.config import OPENWEATHER_API_KEY, DEFAULT_CITY

# OpenWeatherMap API Endpoints
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
GEOCODING_URL = "http://api.openweathermap.org/geo/1.0/direct"

# Simple in-memory cache for weather data (15 minutes expiry)
_WEATHER_CACHE = {}
CACHE_EXPIRY = 900 # 15 minutes in seconds

def get_lat_lon(city_name):
    """
    Fetches latitude and longitude for a city name using OWM Geocoding API.
    """
    if not city_name:
        return None, None
        
    try:
        url = f"{GEOCODING_URL}?q={requests.utils.quote(city_name)},IN&limit=1&appid={OPENWEATHER_API_KEY}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0]['lat'], data[0]['lon']
            else:
                return None, None
        else:
            print(f"Geocoding API Error: {response.status_code} - {response.text}")
            return None, None
    except Exception as e:
        print(f"Error in geocoding for {city_name}: {e}")
        return None, None

def get_weather_data(city_name):
    """
    Fetches real-time weather data (temp, humidity, pressure, etc.) for a city.
    Uses caching to avoid repeated API calls.
    """
    if not city_name:
        return None
        
    # Check cache
    current_time = time.time()
    if city_name in _WEATHER_CACHE:
        cached_data, timestamp = _WEATHER_CACHE[city_name]
        if current_time - timestamp < CACHE_EXPIRY:
            print(f"Returning cached weather for {city_name}")
            return cached_data
            
    try:
        url = f"{WEATHER_URL}?q={requests.utils.quote(city_name)},IN&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            main = data.get("main", {})
            wind = data.get("wind", {})
            clouds = data.get("clouds", {})
            weather = data.get("weather", [{}])[0]
            coord = data.get("coord", {})
            
            weather_info = {
                "temp": main.get("temp", 0),
                "humidity": main.get("humidity", 0),
                "pressure": main.get("pressure", 0),
                "wind_speed": wind.get("speed", 0),
                "clouds": clouds.get("all", 0),
                "description": weather.get("description", "N/A").capitalize(),
                "city": data.get("name", city_name),
                "lat": coord.get("lat", 0),
                "lon": coord.get("lon", 0),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            # Update cache
            _WEATHER_CACHE[city_name] = (weather_info, current_time)
            return weather_info
        elif response.status_code == 401:
            print(f"Weather API Error: 401 - Invalid API Key. Please check OPENWEATHER_API_KEY in src/config.py")
            return None
        elif response.status_code == 404:
            print(f"Weather API Error: 404 - City '{city_name}' not found in India.")
            return None
        elif response.status_code == 429:
            print("Rate limit exceeded for OpenWeatherMap API.")
            return None
        else:
            print(f"Weather API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error fetching weather for {city_name}: {e}")
        return None

def map_weather_to_features(weather_data, additional_features=None):
    """
    Maps real-time weather data and additional features to the model's input format.
    Model expects: ['Year', 'Month', 'Season', 'Lag_1', 'Rolling_Avg_3', 'Lat', 'Lon', 'Is_Coastal', 'Elevation']
    """
    if not weather_data:
        return None
        
    now = datetime.now()
    year = now.year
    month = now.month
    
    # Season mapping
    if month in [1, 2]: season = 1  # Winter
    elif month in [3, 4, 5]: season = 2  # Summer
    elif month in [6, 7, 8, 9]: season = 3  # Monsoon
    else: season = 4  # Post-Monsoon
    
    # Defaults for historical features if not provided
    lag_1 = additional_features.get('lag_1', 0) if additional_features else 0
    rolling_3 = additional_features.get('rolling_3', 0) if additional_features else 0
    
    # Location features from weather data
    lat = weather_data.get('lat', 0)
    lon = weather_data.get('lon', 0)
    
    # Heuristic for coastal and elevation (as per previous instructions)
    # Coastal if lat/lon is near coastline or subdivision mapping
    is_coastal = additional_features.get('is_coastal', 0) if additional_features else 0
    elevation = additional_features.get('elevation', 0) if additional_features else 0
    
    return [year, month, season, lag_1, rolling_3, lat, lon, is_coastal, elevation]
