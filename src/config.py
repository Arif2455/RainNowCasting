import os

# Base directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Data Paths
DATA_DIR = os.path.join(BASE_DIR, '.')
HISTORICAL_DATA_PATH = os.path.join(DATA_DIR, "rainfall in india 1901-2015.csv")
EXTENDED_DATA_PATH = os.path.join(DATA_DIR, "getyourweather_rainfall_2015_2025.csv")

# Model Paths
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

# Static and Templates (relative to src/api/app.py)
API_DIR = os.path.join(BASE_DIR, 'src', 'api')
STATIC_DIR = os.path.join(API_DIR, 'static')
TEMPLATES_DIR = os.path.join(API_DIR, 'templates')
PLOTS_DIR = os.path.join(STATIC_DIR, 'plots')
METRICS_PATH = os.path.join(STATIC_DIR, 'metrics.json')

# API Settings
def get_api_key():
    # 1. Try environment variable
    key = os.getenv("OPENWEATHER_API_KEY")
    if key and key != "your_api_key_here":
        return key
    
    # 2. Try .env file manually (if python-dotenv is not installed)
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                for line in f:
                    if line.startswith("OPENWEATHER_API_KEY="):
                        return line.split("=")[1].strip()
        except Exception:
            pass
            
    return "your_api_key_here"

OPENWEATHER_API_KEY = get_api_key()
DEFAULT_CITY = "Nagpur"

# Logging Settings
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"
