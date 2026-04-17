import os
import sys

# Add the root directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Import the Flask app instance
from src.api.app import app

if __name__ == "__main__":
    # Get port from environment variable for deployment (default to 5000)
    port = int(os.environ.get("PORT", 5001))
    # In production, we usually use a WSGI server like Gunicorn,
    # but for local testing or simple runs:
    app.run(host="0.0.0.0", port=port)
