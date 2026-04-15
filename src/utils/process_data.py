import xarray as xr
import pandas as pd
import numpy as np
import os

input_file = "getyourweather_era5_2015_2025.nc"
output_csv = "getyourweather_rainfall_2015_2025.csv"
full_features_csv = "getyourweather_all_features_2015_2025.csv"

def process_data():
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found. Please run fetch_data.py first.")
        return

    print(f"Opening {input_file}...")
    ds = xr.open_dataset(input_file)

    # Calculate monthly aggregation
    # Precipitation should be summed
    # Temperature, Pressure, Wind etc should be averaged
    
    # Resample to monthly frequency
    # tp is total precipitation in meters. 
    # We want total monthly precipitation in mm.
    # First sum hourly values to get monthly accumulation in meters, then * 1000.
    
    print("Resampling and calculating monthly values...")
    
    # Create a dictionary for aggregation methods
    agg_dict = {}
    if 'tp' in ds.variables:
        agg_dict['tp'] = 'sum'
    if 't2m' in ds.variables:
        agg_dict['t2m'] = 'mean'
    if 'sp' in ds.variables:
        agg_dict['sp'] = 'mean'
    if 'u10' in ds.variables:
        agg_dict['u10'] = 'mean'
    if 'v10' in ds.variables:
        agg_dict['v10'] = 'mean'
    if 'tcwv' in ds.variables:
        agg_dict['tcwv'] = 'mean'
        
    # Resample
    ds_monthly = ds.resample(time='1ME').apply(lambda x: x.sum() if x.name == 'tp' else x.mean())
    # Note: 1ME is month end frequency.
    
    # Convert tp to mm
    if 'tp' in ds_monthly.variables:
        ds_monthly['tp'] = ds_monthly['tp'] * 1000
        
    # Convert t2m to Celsius (optional, but standard is Kelvin in ERA5)
    if 't2m' in ds_monthly.variables:
        ds_monthly['t2m'] = ds_monthly['t2m'] - 273.15

    # Convert to DataFrame
    df = ds_monthly.to_dataframe().reset_index()
    
    # Extract Year and Month
    df['YEAR'] = df['time'].dt.year
    df['MONTH'] = df['time'].dt.month
    
    # Filter out incomplete years/months if necessary (e.g. future dates)
    current_date = pd.Timestamp.now()
    df = df[df['time'] <= current_date]

    # Create the Rainfall DataFrame structure matching the existing CSV
    # SUBDIVISION,YEAR,JAN,FEB,MAR,APR,MAY,JUN,JUL,AUG,SEP,OCT,NOV,DEC,ANNUAL,...
    
    # Pivot to wide format for Rainfall
    if 'tp' in df.columns:
        rainfall_df = df.pivot_table(index='YEAR', columns='MONTH', values='tp')
        rainfall_df.columns = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
        rainfall_df.reset_index(inplace=True)
        rainfall_df['SUBDIVISION'] = 'GETYOURWEATHER' # User specified region name
        
        # Calculate Annual and seasonal
        rainfall_df['ANNUAL'] = rainfall_df[['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']].sum(axis=1)
        rainfall_df['Jan-Feb'] = rainfall_df[['JAN','FEB']].sum(axis=1)
        rainfall_df['Mar-May'] = rainfall_df[['MAR','APR','MAY']].sum(axis=1)
        rainfall_df['Jun-Sep'] = rainfall_df[['JUN','JUL','AUG','SEP']].sum(axis=1)
        rainfall_df['Oct-Dec'] = rainfall_df[['OCT','NOV','DEC']].sum(axis=1)
        
        # Reorder columns
        cols = ['SUBDIVISION','YEAR','JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC','ANNUAL','Jan-Feb','Mar-May','Jun-Sep','Oct-Dec']
        rainfall_df = rainfall_df[cols]
        
        print(f"Saving rainfall data to {output_csv}...")
        rainfall_df.to_csv(output_csv, index=False)
        print(rainfall_df.head())
    
    # Save all features to a separate CSV
    print(f"Saving all features to {full_features_csv}...")
    df.to_csv(full_features_csv, index=False)
    print("Done.")

if __name__ == "__main__":
    process_data()
