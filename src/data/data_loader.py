import os
import pandas as pd
import numpy as np

def load_and_merge_data(historical_path, extended_path=None):
    """Loads historical rainfall data and optionally merges with extended data."""
    df_full = pd.read_csv(historical_path)
    df_full = df_full.fillna(df_full.mean(numeric_only=True))
    
    if extended_path and os.path.exists(extended_path):
        df_extended = pd.read_csv(extended_path)
        # Merge logic will be subdivision-specific during training
        return df_full, df_extended
    return df_full, None

def get_subdivision_data(df_full, subdivision, df_extended=None):
    """Filters data for a specific subdivision and merges extended data if available."""
    df_sub = df_full[df_full['SUBDIVISION'] == subdivision].copy()
    
    if df_extended is not None:
        sub_ext = df_extended[df_extended['SUBDIVISION'] == subdivision]
        if not sub_ext.empty:
            df_sub = pd.concat([df_sub, sub_ext], ignore_index=True)
            
    # Reshape (Melt)
    df_sub = df_sub.drop(columns=['SUBDIVISION'])
    df_melted = df_sub.melt(['YEAR']).reset_index()
    df_melted = df_melted[['YEAR','variable','value']].reset_index().sort_values(by=['YEAR','index'])
    df_melted.columns = ['Index','Year','Month_Name','Avg_Rainfall']
    
    Month_map = {'JAN':1,'FEB':2,'MAR':3,'APR':4,'MAY':5,'JUN':6,'JUL':7,'AUG':8,'SEP':9,'OCT':10,'NOV':11,'DEC':12}
    df_melted['Month'] = df_melted['Month_Name'].map(Month_map)
    df_melted.drop(columns=["Index", "Month_Name"], inplace=True)
    
    return df_melted.dropna(subset=['Avg_Rainfall'])

def get_recent_context(df_full, df_extended, subdivision):
    """Gets the last 3 months of rainfall for a subdivision to calculate features."""
    df_sub = get_subdivision_data(df_full, subdivision, df_extended)
    if df_sub.empty:
        return None, None
        
    # Get last 3 rows
    last_3 = df_sub.tail(3)
    lag_1 = last_3.iloc[-1]['Avg_Rainfall']
    rolling_3 = last_3['Avg_Rainfall'].mean()
    
    return lag_1, rolling_3
