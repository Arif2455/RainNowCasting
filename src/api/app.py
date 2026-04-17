import sys
import os
import json
from flask import render_template, Flask, request, redirect, url_for, jsonify

# Add the project root to sys.path to handle absolute imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import redesigned services
from location_service import get_states, get_cities_by_state, search_city, validate_city
from weather_service import get_weather_data, map_weather_to_features

from src.utils.nowcast_engine import nowcast_rainfall, generate_explanation
from src.utils.geocoding import get_location_features
from src.models.predictor import RainfallPredictor
from src.data.data_loader import load_and_merge_data, get_recent_context
from src.data.feature_engineering import get_season
from src.utils.logger import setup_logger
from src.config import (
    TEMPLATES_DIR, STATIC_DIR, HISTORICAL_DATA_PATH, EXTENDED_DATA_PATH,
    MODEL_PATH, METRICS_PATH, DEFAULT_CITY
)

# Initialize Logger
logger = setup_logger("API")

# Configure Flask
app = Flask(__name__, 
            template_folder=TEMPLATES_DIR,
            static_folder=STATIC_DIR)

# Initialize Predictor
logger.info(f"Loading model from {MODEL_PATH}")
predictor = RainfallPredictor(model_path=MODEL_PATH)

# Load data for context features
logger.info("Loading context datasets for real-time features")
HISTORICAL_DATA, EXTENDED_DATA = load_and_merge_data(
    HISTORICAL_DATA_PATH,
    EXTENDED_DATA_PATH
)

# Global metrics cache
SUBDIVISION_METRICS = {}

def load_metrics():
    global SUBDIVISION_METRICS
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, 'r') as f:
            SUBDIVISION_METRICS = json.load(f)
        logger.info(f"Historical metrics loaded from {METRICS_PATH}")
    else:
        logger.warning(f"Metrics file not found at {METRICS_PATH}")

# Load metrics once at startup
load_metrics()

# List of subdivisions for the dropdown
subdivisions = [
    "ANDAMAN & NICOBAR ISLANDS", "ASSAM & MEGHALAYA", "BIHAR",
    "COASTAL ANDHRA PRADESH", "COASTAL KARNATAKA", "EAST MADHYA PRADESH",
    "EAST RAJASTHAN", "EAST UTTAR PRADESH", "GANGETIC WEST BENGAL",
    "GETYOURWEATHER", "GUJARAT REGION", "HARYANA DELHI & CHANDIGARH",
    "HIMACHAL PRADESH", "JAMMU & KASHMIR", "JHARKHAND", "KERALA",
    "KONKAN & GOA", "LAKSHADWEEP", "MADHYA MAHARASHTRA", "MARATHWADA",
    "NAGA MANI MIZO TRIPURA", "NORTH INTERIOR KARNATAKA", "ODISHA",
    "PUNJAB", "RAYALASEEMA", "SAURASHTRA & KUTCH", "SOUTH INTERIOR KARNATAKA",
    "SUB HIMALAYAN WEST BENGAL & SIKKIM", "TAMIL NADU", "TELANGANA",
    "UTTARAKHAND", "VIDARBHA", "WEST MADHYA PRADESH", "WEST RAJASTHAN",
    "WEST UTTAR PRADESH"
]

CITY_MAPPING = {
    "VIDARBHA": "Nagpur",
    "MADHYA MAHARASHTRA": "Pune",
    "MARATHWADA": "Aurangabad",
    "KONKAN & GOA": "Mumbai",
    "GANGETIC WEST BENGAL": "Kolkata",
    "SUB HIMALAYAN WEST BENGAL & SIKKIM": "Gangtok",
    "ORISSA": "Bhubaneswar",
    "ODISHA": "Bhubaneswar",
    "JHARKHAND": "Ranchi",
    "BIHAR": "Patna",
    "EAST UTTAR PRADESH": "Lucknow",
    "WEST UTTAR PRADESH": "Agra",
    "UTTARAKHAND": "Dehradun",
    "HARYANA DELHI & CHANDIGARH": "Delhi",
    "PUNJAB": "Amritsar",
    "HIMACHAL PRADESH": "Shimla",
    "JAMMU & KASHMIR": "Srinagar",
    "WEST RAJASTHAN": "Jodhpur",
    "EAST RAJASTHAN": "Jaipur",
    "WEST MADHYA PRADESH": "Indore",
    "EAST MADHYA PRADESH": "Jabalpur",
    "GUJARAT REGION": "Ahmedabad",
    "SAURASHTRA & KUTCH": "Rajkot",
    "COASTAL ANDHRA PRADESH": "Visakhapatnam",
    "TELANGANA": "Hyderabad",
    "RAYALASEEMA": "Tirupati",
    "TAMIL NADU": "Chennai",
    "COASTAL KARNATAKA": "Mangalore",
    "NORTH INTERIOR KARNATAKA": "Hubballi",
    "SOUTH INTERIOR KARNATAKA": "Bengaluru",
    "KERALA": "Thiruvananthapuram",
    "LAKSHADWEEP": "Kavaratti",
    "ANDAMAN & NICOBAR ISLANDS": "Port Blair",
    "ASSAM & MEGHALAYA": "Guwahati",
    "NAGA MANI MIZO TRIPURA": "Agartala",
    "GETYOURWEATHER": "Nagpur"
}

def process_nowcast(subdivision):
    """Core logic to process nowcast for a subdivision."""
    if not subdivision:
        return None, "Subdivision is required", 400
        
    sub_upper = subdivision.upper()
    if sub_upper not in CITY_MAPPING:
        return None, f"Invalid subdivision: {subdivision}", 400
        
    city = CITY_MAPPING[sub_upper]
    try:
        weather = get_weather_data(city)
        if not weather:
            logger.error(f"Weather API fetch failed for city: {city}")
            return None, "Weather API is currently unreachable", 503
        
        result = nowcast_rainfall(weather)
        return result, None, 200
    except Exception as e:
        logger.exception(f"Unexpected error in process_nowcast: {e}")
        return None, "An unexpected error occurred", 500

@app.route("/", methods=["GET"])
def home():
    return render_template('index.html', subdivisions=sorted(subdivisions))

# --- Location API Endpoints ---

@app.route("/api/states", methods=["GET"])
def api_get_states():
    """Returns list of all Indian states."""
    states = get_states()
    return jsonify(states)

@app.route("/api/cities", methods=["GET"])
def api_get_cities():
    """Returns list of cities for a given state."""
    state = request.args.get("state")
    if not state:
        return jsonify({"error": "State name is required"}), 400
    cities = get_cities_by_state(state)
    return jsonify(cities)

@app.route("/api/search-city", methods=["GET"])
def api_search_city():
    """Returns list of cities matching the search query."""
    query = request.args.get("q")
    if not query:
        return jsonify([])
    results = search_city(query)
    return jsonify(results)

# --- Prediction Pipeline ---

@app.route("/api/predict", methods=["POST"])
def api_predict():
    """
    Main prediction endpoint for the redesigned pipeline.
    Expects JSON: { "state": "Maharashtra", "city": "Nagpur" }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON request"}), 400
        
    state = data.get("state")
    city = data.get("city")
    
    if not state or not city:
        return jsonify({"error": "State and City are required"}), 400
        
    # 1. Fetch REAL weather data
    logger.info(f"Predicting for City: {city}, State: {state}")
    weather = get_weather_data(city)
    
    if not weather:
        return jsonify({
            "status": "error",
            "message": f"Could not fetch live weather data for {city}. Please try again later."
        }), 503
        
    # 2. Heuristic Nowcast (Short-term)
    short_term = nowcast_rainfall(weather)
    
    # 3. ML Model Prediction
    # Map to subdivision for historical context (Lags)
    # This maintains backward compatibility with the model's training
    subdivision = None
    for sub, sub_city in CITY_MAPPING.items():
        if sub_city.lower() == city.lower() or sub.lower() in state.lower():
            subdivision = sub
            break
    
    if not subdivision:
        subdivision = "GETYOURWEATHER" # Default
        
    lag_1, rolling_3 = get_recent_context(HISTORICAL_DATA, EXTENDED_DATA, subdivision)
    
    # Feature mapping
    # Determine if coastal (simple mapping)
    is_coastal = 1 if subdivision in ["KONKAN & GOA", "COASTAL KARNATAKA", "KERALA", "TAMIL NADU", "ODISHA"] else 0
    
    additional_info = {
        "lag_1": lag_1 if lag_1 is not None else 0,
        "rolling_3": rolling_3 if rolling_3 is not None else 0,
        "is_coastal": is_coastal,
        "elevation": 0 # Placeholder
    }
    
    features = map_weather_to_features(weather, additional_info)
    ml_prediction = predictor.predict(features)
    
    # 4. Confidence Analysis
    # Based on both real-time data and historical model error (RMSE)
    rmse = SUBDIVISION_METRICS.get(subdivision.upper(), 500) # Default high RMSE if not found
    
    # Confidence is lower if humidity is very low (harder to predict rain) 
    # and lower if historical RMSE for the region is high.
    confidence_score = 100
    if weather['humidity'] < 30: confidence_score -= 30
    if rmse > 300: confidence_score -= 20
    if weather['clouds'] < 20: confidence_score -= 10
    
    confidence = "High" if confidence_score > 70 else "Medium" if confidence_score > 40 else "Low"
    
    # --- Prediction vs Actual Comparison ---
    predicted_val = round(float(ml_prediction), 2) if ml_prediction else 0
    actual_val = weather.get("actual_rainfall", 0)
    
    error_val = round(abs(predicted_val - actual_val), 2)
    
    if error_val <= 2:
        error_level = "Low error (green)"
        comparison_msg = "Accurate prediction"
    elif error_val <= 5:
        error_level = "Medium error (yellow)"
        comparison_msg = "Slight overestimation" if predicted_val > actual_val else "Underestimation"
    else:
        error_level = "High error (red)"
        comparison_msg = "Overestimation" if predicted_val > actual_val else "Underestimation"
        
    explanation = generate_explanation(weather)
        
    return jsonify({
        "location": city,
        "state": state,
        "prediction_mm": predicted_val,
        "actual_mm": actual_val,
        "error_mm": error_val,
        "error_level": error_level,
        "comparison_message": comparison_msg,
        "explanation": explanation,
        "confidence": confidence,
        "temperature": weather['temp'],
        "humidity": weather['humidity'],
        "pressure": weather['pressure'],
        "nowcast": short_term,
        "status": "success"
    }), 200

@app.route("/nowcast", methods=["GET"])
def nowcast():
    subdivision = request.args.get("subdivision", "VIDARBHA")
    logger.info(f"Processing UI Nowcast request for subdivision: {subdivision}")
    result, error, status = process_nowcast(subdivision)
    
    if error:
        return render_template('error.html', message=error), status
    
    rmse = SUBDIVISION_METRICS.get(subdivision.upper(), "N/A")
    return render_template('nowcast.html', result=result, subdivision=subdivision, rmse=rmse)

@app.route("/nowcast-live", methods=["GET"])
def nowcast_live():
    """Integrated real-time prediction route using both API and ML model."""
    subdivision = request.args.get("subdivision", "VIDARBHA")
    location = request.args.get("location") # Optional city/location name
    
    logger.info(f"Processing Integrated Live Prediction for: {subdivision} (Location: {location})")
    
    # 1. Geocoding and Feature Extraction
    search_name = location if location else subdivision
    lat, lon, coastal, elev = get_location_features(search_name)
    
    # Backward compatibility: use subdivision's city if geocoding failed or not provided
    if lat is None:
        city = CITY_MAPPING.get(subdivision.upper(), DEFAULT_CITY)
        lat, lon, coastal, elev = get_location_features(subdivision)
    else:
        city = location
        
    weather = get_weather_data(city)
    
    if not weather:
        logger.error(f"Live data fetch failed for {city}")
        return render_template('error.html', message=f"Live weather data unavailable for {city}"), 503
        
    short_term = nowcast_rainfall(weather)
    
    from datetime import datetime
    now = datetime.now()
    year, month = now.year, now.month
    season = get_season(month)
    
    # Use subdivision for historical context (lags/rolling avg)
    lag_1, rolling_3 = get_recent_context(HISTORICAL_DATA, EXTENDED_DATA, subdivision)
    
    if lag_1 is None:
        logger.warning(f"No historical context found for {subdivision}, using defaults.")
        lag_1 = 0
        rolling_3 = 0
        
    # Updated feature vector: [Year, Month, Season, Lag_1, Rolling_Avg_3, Lat, Lon, Is_Coastal, Elevation]
    features = [year, month, season, lag_1, rolling_3, lat, lon, coastal, elev]
    ml_prediction = predictor.predict(features)
    
    logger.info(f"ML Prediction for {search_name}: {ml_prediction} mm")
    
    rmse = SUBDIVISION_METRICS.get(subdivision.upper(), "N/A")
    
    # --- Prediction vs Actual Comparison ---
    predicted_val = round(float(ml_prediction), 2) if ml_prediction else 0
    actual_val = weather.get("actual_rainfall", 0)
    
    error_val = round(abs(predicted_val - actual_val), 2)
    
    if error_val <= 2:
        error_level = "Low error (green)"
        comparison_msg = "Accurate prediction"
        badge_class = "success"
    elif error_val <= 5:
        error_level = "Medium error (yellow)"
        comparison_msg = "Slight overestimation" if predicted_val > actual_val else "Underestimation"
        badge_class = "warning"
    else:
        error_level = "High error (red)"
        comparison_msg = "Overestimation" if predicted_val > actual_val else "Underestimation"
        badge_class = "danger"
    
    explanation = generate_explanation(weather)
    
    return render_template('nowcast_live.html', 
                           subdivision=subdivision,
                           location=search_name,
                           weather=weather,
                           short_term=short_term,
                           ml_prediction=predicted_val,
                           actual_mm=actual_val,
                           error_mm=error_val,
                           error_level=error_level,
                           comparison_message=comparison_msg,
                           badge_class=badge_class,
                           explanation=explanation,
                           rmse=rmse,
                           lat=lat,
                           lon=lon)

@app.route("/api/nowcast", methods=["POST"])
def api_nowcast():
    """API endpoint for nowcasting. Accepts JSON input."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON or empty request body"}), 400
        
    subdivision = data.get("subdivision")
    logger.info(f"Processing API Nowcast request for subdivision: {subdivision}")
    result, error, status = process_nowcast(subdivision)
    
    if error:
        return jsonify({"error": error}), status
        
    rmse = SUBDIVISION_METRICS.get(subdivision.upper(), "N/A")
    return jsonify({
        "subdivision": subdivision,
        "nowcast": {
            "probability": result["probability"],
            "intensity": result["intensity"],
            "message": result["message"]
        },
        "metrics": {
            "historical_rmse": rmse
        },
        "parameters": result["parameters"]
    }), 200

if __name__ == "__main__":
    # Get port from environment variable for deployment (default to 5000)
    port = int(os.environ.get("PORT", 5000))
    # No debug=True in production
    app.run(host="0.0.0.0", port=port, debug=False)
