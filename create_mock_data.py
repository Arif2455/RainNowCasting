import pandas as pd
import numpy as np

# Create dummy data for 2015-2025
years = range(2015, 2026)
data = []

for year in years:
    row = {
        'SUBDIVISION': 'GETYOURWEATHER',
        'YEAR': year,
        'JAN': np.random.uniform(0, 50),
        'FEB': np.random.uniform(0, 50),
        'MAR': np.random.uniform(0, 50),
        'APR': np.random.uniform(0, 50),
        'MAY': np.random.uniform(0, 100),
        'JUN': np.random.uniform(100, 300),
        'JUL': np.random.uniform(200, 400),
        'AUG': np.random.uniform(200, 400),
        'SEP': np.random.uniform(100, 300),
        'OCT': np.random.uniform(50, 150),
        'NOV': np.random.uniform(0, 50),
        'DEC': np.random.uniform(0, 50)
    }
    data.append(row)

df = pd.DataFrame(data)

# Calculate annual
df['ANNUAL'] = df[['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']].sum(axis=1)

output_file = "getyourweather_rainfall_2015_2025.csv"
df.to_csv(output_file, index=False)
print(f"Mock data created at {output_file}")
print(df.head())
