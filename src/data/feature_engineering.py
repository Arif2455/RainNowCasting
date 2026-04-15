import pandas as pd
import numpy as np
from src.utils.geocoding import get_location_features

def get_season(month):
    """Classifies month into Indian seasons."""
    if month in [1, 2]: return 1  # Winter
    if month in [3, 4, 5]: return 2  # Summer
    if month in [6, 7, 8, 9]: return 3  # Monsoon
    return 4  # Post-Monsoon

def apply_feature_engineering(df, subdivision=None):
    """Adds season, lag, rolling average, and location-based features to the dataframe."""
    df = df.copy()
    
    # 1. Season Classification
    df['Season'] = df['Month'].apply(get_season)
    
    # 2. Lag Features (Previous month's rainfall)
    df['Lag_1'] = df['Avg_Rainfall'].shift(1)
    
    # 3. Rolling Average (3-month window)
    df['Rolling_Avg_3'] = df['Avg_Rainfall'].rolling(window=3).mean()
    
    # 4. Location-based Features
    if subdivision:
        lat, lon, coastal, elev = get_location_features(subdivision)
        df['Lat'] = lat if lat is not None else 0
        df['Lon'] = lon if lon is not None else 0
        df['Is_Coastal'] = coastal if coastal is not None else 0
        df['Elevation'] = elev if elev is not None else 0
    
    # Fill NaN values created by shift/rolling with subdivision mean
    df = df.fillna(df.mean(numeric_only=True))
    
    return df
