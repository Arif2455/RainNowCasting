# Deployment Guide for AtmoCast

This project is prepared for deployment on platforms like **Render**, **Heroku**, or **Railway**.

## Deployment Steps (Example: Render)

1. **Create a Web Service**:
   - Connect your GitHub repository: `https://github.com/Arif2455/RainNowCasting`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`

2. **Environment Variables**:
   Add the following secret in the platform's dashboard:
   - `OPENWEATHER_API_KEY`: Your real API key from OpenWeatherMap.

3. **Disk/Storage (Optional)**:
   The project includes a `model.pkl` and CSV data files. These are part of the repository and will be available automatically.

## Project Structure for Deployment

- `run.py`: Root-level entry point for Gunicorn.
- `Procfile`: Process file for web server configuration.
- `requirements.txt`: All Python dependencies.
- `src/`: Core application logic and assets.
  - `api/`: Flask routes, templates, and static files.
  - `models/`: ML prediction logic.
  - `data/`: Data loading and processing.
  - `utils/`: Helper services (weather, geocoding).
- `model.pkl`: The trained ML model artifact.
- `*.csv`: Historical datasets used for context.

## Local Production Test

To test the production setup locally:
```bash
# Set your API key
$env:OPENWEATHER_API_KEY="your_key_here"

# Install production server
pip install gunicorn

# Run using the production entry point
python run.py
```
