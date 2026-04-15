import requests
import os
from src.config import OPENWEATHER_API_KEY, DEFAULT_CITY

# Representative (Lat, Lon, Is_Coastal, Elevation) for each subdivision
SUBDIVISION_COORDINATES = {
    "ANDAMAN & NICOBAR ISLANDS": (11.6234, 92.7265, 1, 0),
    "ARUNACHAL PRADESH": (28.2180, 94.7278, 0, 0),
    "ASSAM & MEGHALAYA": (26.1445, 91.7362, 0, 0),
    "NAGA MANI MIZO TRIPURA": (23.8315, 91.2868, 0, 0),
    "SUB HIMALAYAN WEST BENGAL & SIKKIM": (27.3314, 88.6138, 0, 0),
    "GANGETIC WEST BENGAL": (22.5726, 88.3639, 1, 0),
    "ORISSA": (20.2961, 85.8245, 1, 0),
    "ODISHA": (20.2961, 85.8245, 1, 0),
    "JHARKHAND": (23.3441, 85.3096, 0, 0),
    "BIHAR": (25.5941, 85.1376, 0, 0),
    "EAST UTTAR PRADESH": (26.8467, 80.9462, 0, 0),
    "WEST UTTAR PRADESH": (27.1767, 78.0081, 0, 0),
    "UTTARAKHAND": (30.3165, 78.0322, 0, 0),
    "HARYANA DELHI & CHANDIGARH": (28.6139, 77.2090, 0, 0),
    "PUNJAB": (31.6340, 74.8723, 0, 0),
    "HIMACHAL PRADESH": (31.1048, 77.1734, 0, 0),
    "JAMMU & KASHMIR": (34.0837, 74.7973, 0, 0),
    "WEST RAJASTHAN": (26.2389, 73.0243, 0, 0),
    "EAST RAJASTHAN": (26.9124, 75.7873, 0, 0),
    "WEST MADHYA PRADESH": (22.7196, 75.8577, 0, 0),
    "EAST MADHYA PRADESH": (23.1815, 79.9864, 0, 0),
    "GUJARAT REGION": (23.0225, 72.5714, 0, 0),
    "SAURASHTRA & KUTCH": (22.3039, 70.8022, 1, 0),
    "KONKAN & GOA": (19.0760, 72.8777, 1, 0),
    "MADHYA MAHARASHTRA": (18.5204, 73.8567, 0, 0),
    "MATATHWADA": (19.8762, 75.3433, 0, 0),
    "MARATHWADA": (19.8762, 75.3433, 0, 0),
    "VIDARBHA": (21.1458, 79.0882, 0, 0),
    "CHHATTISGARH": (21.2514, 81.6296, 0, 0),
    "COASTAL ANDHRA PRADESH": (17.6868, 83.2185, 1, 0),
    "TELANGANA": (17.3850, 78.4867, 0, 0),
    "RAYALSEEMA": (13.6288, 79.4192, 0, 0),
    "RAYALASEEMA": (13.6288, 79.4192, 0, 0),
    "TAMIL NADU": (13.0827, 80.2707, 1, 0),
    "COASTAL KARNATAKA": (12.9141, 74.8560, 1, 0),
    "NORTH INTERIOR KARNATAKA": (15.3647, 75.1240, 0, 0),
    "SOUTH INTERIOR KARNATAKA": (12.9716, 77.5946, 0, 0),
    "KERALA": (8.5241, 76.9366, 1, 0),
    "LAKSHADWEEP": (10.5667, 72.6417, 1, 0),
    "GETYOURWEATHER": (21.1458, 79.0882, 0, 0)
}

def get_location_features(location_name):
    """
    Returns (lat, lon, is_coastal, elevation) for a location.
    Checks static map first, then tries geocoding API.
    """
    if not location_name:
        return None, None, None, None
        
    location_upper = location_name.upper()
    
    # 1. Check static map
    if location_upper in SUBDIVISION_COORDINATES:
        return SUBDIVISION_COORDINATES[location_upper]
        
    # 2. Try Geocoding API
    try:
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={location_name},IN&limit=1&appid={OPENWEATHER_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data:
            lat = data[0]['lat']
            lon = data[0]['lon']
            # Heuristic for coastal
            is_coastal = 1 if "COASTAL" in location_upper or any(c in location_upper for c in ["MUMBAI", "CHENNAI", "KOCHI", "VIZAG"]) else 0
            elevation = 0 # Placeholder
            return lat, lon, is_coastal, elevation
            
    except Exception as e:
        print(f"Geocoding error for {location_name}: {e}")
        
    return None, None, None, None
