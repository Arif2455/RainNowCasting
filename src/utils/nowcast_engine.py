import requests
import pandas as pd
import numpy as np
from datetime import datetime

# OpenWeatherMap API Key (Placeholder - User should provide a real one)
API_KEY = "bd5e378503939ddaee76f12ad7a97608" 

def get_realtime_weather(city="Nagpur"):
    """
    Fetches real-time weather data for a city (default Nagpur for Vidarbha region).
    """
    # Clean city name for URL
    city_encoded = requests.utils.quote(city)
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_encoded}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=10) 
        if response.status_code == 200:
            data = response.json()
            return {
                "temp": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data["wind"]["speed"],
                "clouds": data["clouds"]["all"],
                "description": data["weather"][0]["description"].capitalize(),
                "city": data["name"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        elif response.status_code == 401:
            print(f"API Key Error: {response.json().get('message')}. Falling back to mock data for demonstration.")
            return get_mock_weather(city)
        else:
            print(f"Error fetching weather for {city}: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching weather for {city}: {e}. Falling back to mock data.")
        return get_mock_weather(city)
    except Exception as e:
        print(f"Unexpected error fetching weather for {city}: {e}")
        return None

def get_mock_weather(city):
    """
    Provides realistic mock data if the API key is invalid or network is down.
    This ensures the 'Nowcast' feature is always visible and demonstrable.
    """
    import random
    # Realistic defaults for Indian cities in April/May
    return {
        "temp": random.uniform(32.0, 42.0),
        "humidity": random.randint(30, 85),
        "pressure": random.randint(1000, 1015),
        "wind_speed": random.uniform(2.0, 8.0),
        "clouds": random.randint(10, 100),
        "description": random.choice(["Partly cloudy", "Broken clouds", "Haze", "Thunderstorm", "Light rain"]),
        "city": city + " (Demo Data)",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def nowcast_rainfall(weather_data):
    """
    Heuristic-based nowcasting for the next 3-4 hours.
    Returns probability and intensity based on humidity, clouds, and pressure.
    """
    humidity = weather_data.get("humidity", 0)
    clouds = weather_data.get("clouds", 0)
    pressure = weather_data.get("pressure", 1013)
    
    score = 0
    if humidity > 85: score += 40
    elif humidity > 70: score += 20
    
    if clouds > 90: score += 30
    elif clouds > 70: score += 15
    
    if pressure < 1005: score += 20
    elif pressure < 1010: score += 10
    
    # Very high humidity + high clouds is a strong indicator
    if humidity > 90 and clouds > 90:
        score += 10
        
    probability = min(score, 95)
    
    intensity = "None"
    if probability > 80:
        intensity = "Heavy Rain"
    elif probability > 50:
        intensity = "Moderate Rain"
    elif probability > 20:
        intensity = "Light Drizzle"
    else:
        intensity = "Rain"
        
    return {
        "probability": f"{probability}%",
        "intensity": intensity,
        "message": f"Based on current {weather_data['description']} in {weather_data['city']}, there is a {probability}% chance of {intensity.lower()} in the next 3-4 hours.",
        "parameters": weather_data
    }
