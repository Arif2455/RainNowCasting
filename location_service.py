import requests
import logging

# Configure local logger for this service
logger = logging.getLogger("LocationService")
logging.basicConfig(level=logging.INFO)

# API Endpoints (CountriesNow API)
BASE_URL = "https://countriesnow.space/api/v0.1/countries"
COUNTRY_NAME = "India"

# In-memory cache
_CITY_CACHE = []
_STATE_CACHE = []

def load_data():
    """Dynamically loads states and all cities for India into the cache."""
    global _CITY_CACHE, _STATE_CACHE
    
    if _CITY_CACHE and _STATE_CACHE:
        return True
        
    try:
        logger.info(f"Fetching states for {COUNTRY_NAME}...")
        state_response = requests.post(f"{BASE_URL}/states", json={"country": COUNTRY_NAME}, timeout=10)
        state_data = state_response.json()
        
        if not state_data.get("error", True):
            _STATE_CACHE = [s["name"] for s in state_data["data"]["states"]]
            logger.info(f"Loaded {len(_STATE_CACHE)} states.")
        else:
            logger.error(f"Failed to load states: {state_data.get('msg')}")
            return False

        logger.info(f"Fetching all cities for {COUNTRY_NAME}...")
        city_response = requests.post(f"{BASE_URL}/cities", json={"country": COUNTRY_NAME}, timeout=15)
        city_data = city_response.json()
        
        if not city_data.get("error", True):
            _CITY_CACHE = city_data["data"]
            logger.info(f"Loaded {len(_CITY_CACHE)} cities.")
            return True
        else:
            logger.error(f"Failed to load cities: {city_data.get('msg')}")
            return False
            
    except Exception as e:
        logger.error(f"Error loading location data: {e}")
        return False

def get_states():
    """Returns a list of all Indian states from the cache."""
    if not _STATE_CACHE:
        load_data()
    return sorted(_STATE_CACHE)

def get_cities_by_state(state_name):
    """
    Returns a list of cities for a specific state.
    Note: CountriesNow API's /state/cities endpoint requires the state name.
    """
    if not state_name:
        return []
        
    try:
        logger.info(f"Fetching cities for state: {state_name}...")
        response = requests.post(f"{BASE_URL}/state/cities", json={
            "country": COUNTRY_NAME,
            "state": state_name
        }, timeout=10)
        data = response.json()
        
        if not data.get("error", True):
            return sorted(data["data"])
        else:
            logger.warning(f"No cities found for state {state_name}: {data.get('msg')}")
            return []
    except Exception as e:
        logger.error(f"Error fetching cities for state {state_name}: {e}")
        return []

def get_all_cities():
    """Returns the full list of all Indian cities from the cache."""
    if not _CITY_CACHE:
        load_data()
    return sorted(_CITY_CACHE)

def search_city(query):
    """
    Performs an efficient search/filter for cities matching the query.
    Used for autocomplete functionality.
    """
    if not query:
        return []
        
    all_cities = get_all_cities()
    query = query.lower().strip()
    
    # Simple prefix-based and containment-based filtering
    matches = [city for city in all_cities if city.lower().startswith(query)]
    
    # If not enough prefix matches, add containment matches
    if len(matches) < 10:
        more_matches = [city for city in all_cities if query in city.lower() and city not in matches]
        matches.extend(more_matches)
        
    return matches[:20] # Return top 20 results

def validate_city(city_name):
    """Validates if a city exists in our known city list."""
    if not city_name:
        return False
    
    all_cities = get_all_cities()
    return city_name in all_cities

# Initial load on import if needed, but better to call explicitly or on first request
# load_data()
