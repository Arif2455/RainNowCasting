import sys
import os
import pandas as pd
import json
from datetime import datetime

# Add the project root to sys.path to handle absolute imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from weather_service import get_weather_data, map_weather_to_features
from src.models.predictor import RainfallPredictor
from src.utils.nowcast_engine import nowcast_rainfall

# Cities to test across different regions of India
TEST_CITIES = [
    {"city": "Nagpur", "state": "Maharashtra", "region": "Central"},
    {"city": "Mumbai", "state": "Maharashtra", "region": "West/Coastal"},
    {"city": "Delhi", "state": "Delhi", "region": "North"},
    {"city": "Chennai", "state": "Tamil Nadu", "region": "South/Coastal"},
    {"city": "Kolkata", "state": "West Bengal", "region": "East/Coastal"},
    {"city": "Srinagar", "state": "Jammu and Kashmir", "region": "North/High Altitude"},
    {"city": "Jodhpur", "state": "Rajasthan", "region": "West/Desert"},
    {"city": "Guwahati", "state": "Assam", "region": "Northeast"}
]

def verify_city_weather():
    predictor = RainfallPredictor(model_path="model.pkl")
    results = []

    print(f"\n{'City':<15} | {'Region':<15} | {'Temp':<6} | {'Humid':<6} | {'Lat':<7} | {'Lon':<7} | {'Pred (mm)':<10} | {'Nowcast'}")
    print("-" * 110)

    for item in TEST_CITIES:
        city = item["city"]
        region = item["region"]
        
        weather = get_weather_data(city)
        if not weather:
            print(f"{city:<15} | {region:<15} | {'FAILED':<6} | {'N/A':<6} | {'N/A':<7} | {'N/A':<7} | {'N/A':<10} | {'N/A'}")
            continue

        # Simple coastal heuristic for the diagnostic
        is_coastal = 1 if "Coastal" in region else 0
        
        # Mapping to features for ML model
        features = map_weather_to_features(weather, {"is_coastal": is_coastal})
        # Debug: Print the feature vector
        # print(f"Features for {city}: {features}")
        
        ml_prediction = predictor.predict(features)
        
        # Heuristic nowcast
        nowcast = nowcast_rainfall(weather)
        
        results.append({
            "city": city,
            "region": region,
            "temp": weather["temp"],
            "humidity": weather["humidity"],
            "lat": weather["lat"],
            "lon": weather["lon"],
            "ml_prediction": round(ml_prediction, 2) if ml_prediction else 0,
            "nowcast_intensity": nowcast["intensity"]
        })

        print(f"{city:<15} | {region:<15} | {weather['temp']:<6.1f} | {weather['humidity']:<6} | {weather['lat']:<7.2f} | {weather['lon']:<7.2f} | {results[-1]['ml_prediction']:<10} | {results[-1]['nowcast_intensity']}")

    # Check for uniqueness
    temps = [r['temp'] for r in results]
    humids = [r['humidity'] for r in results]
    unique_temps = len(set(temps))
    unique_humids = len(set(humids))
    
    print("\n--- Summary ---")
    print(f"Total Cities Tested: {len(results)}")
    print(f"Unique Temperatures: {unique_temps}")
    print(f"Unique Humidities: {unique_humids}")
    
    if unique_temps > 1 and unique_humids > 1:
        print("\nCONCLUSION: Data is dynamically changing based on location. Real-time API integration is successful.")
    else:
        print("\nCONCLUSION: Data might be repeating. Check API connection or mock data settings.")

if __name__ == "__main__":
    verify_city_weather()
