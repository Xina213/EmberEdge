#!/usr/bin/env python3
"""
EmberEdge - ERA5 Historical Weather Downloade
Download real historical weather data from Copernicus CDS
Uses cdsapi library (classic)
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
OUTPUT_FILE = os.path.join(DATA_DIR, 'weather_historical_era5.csv')

# City coordinates (will be mapped to nearest ERA5 grid point)
CITY_COORDS = {
    'Aveiro': (40.64, -8.65),
    'Beja': (38.02, -7.87),
    'Braga': (41.55, -8.42),
    'Braganca': (41.81, -6.76),
    'Castelo Branco': (39.82, -7.49),
    'Coimbra': (40.21, -8.43),
    'Evora': (38.57, -7.91),
    'Faro': (37.02, -7.93),
    'Guarda': (40.54, -7.27),
    'Leiria': (39.75, -8.81),
    'Lisboa': (38.72, -9.14),
    'Portalegre': (39.30, -7.43),
    'Porto': (41.16, -8.62),
    'Santarem': (39.24, -8.69),
    'Setubal': (38.52, -8.89),
    'Viana do Castelo': (41.69, -8.83),
    'Vila Real': (41.30, -7.74),
    'Viseu': (40.66, -7.91),
}

def download_era5_data():
    """
    Download ERA5 monthly averaged data for Portugal cities
    Years: 2000-2023 (matching historical_fires.csv)
    """

    try:
        import cdsapi
    except ImportError:
        print("[ERROR] cdsapi not installed. Run: pip install cdsapi")
        return False

    # Check if .cdsapirc exists with correct format
    rc_file = os.path.expanduser('~/.cdsapirc')
    if not os.path.exists(rc_file):
        print("\n[ERROR] Copernicus API key not configured!")
        print("\n=== HOW TO CONFIGURE ===")
        print("1. Go to: https://cds.climate.copernicus.eu/api-how-to")
        print("2. Copy your UID:API key")
        print(f"3. Create file: {rc_file}")
        print("4. File content:")
        print("   url: https://cds.climate.copernicus.eu/api/v2")
        print("   key: <your_uid>:<your_api_key>")
        return False

    print("\n" + "=" * 70)
    print("EMBEREDGE - DOWNLOADING ERA5 HISTORICAL DATA")
    print("=" * 70)

    c = cdsapi.Client()

    # Define area: Portugal continental
    area = [42, -10, 36.5, -6]

    years = [str(y) for y in range(2000, 2024)]
    months = [f"{m:02d}" for m in range(1, 13)]

    print(f"\n[ERA5] Requesting data for {len(years)} years x {len(months)} months...")
    print(f"       Area: Portugal Continental")
    print(f"       Variables: temperature, humidity, wind, precipitation")
    print(f"       (This may take 5-10 minutes)")

    try:
        # ERA5 API call for monthly averaged data
        # Returns a ZIP file containing the NetCDF
        zip_file = 'era5_portugal.zip'
        c.retrieve(
            'reanalysis-era5-single-levels-monthly-means',
            {
                'product_type': 'monthly_averaged_reanalysis',
                'variable': [
                    '2m_temperature',
                    '2m_dewpoint_temperature',
                    '10m_u_component_of_wind',
                    '10m_v_component_of_wind',
                    'total_precipitation',
                ],
                'year': years,
                'month': months,
                'time': '00:00',
                'area': area,
                'format': 'netcdf',
            },
            zip_file
        )

        print(f"[OK] ERA5 data downloaded: {zip_file}")

        # Unzip to get the .nc file
        import zipfile
        with zipfile.ZipFile(zip_file, 'r') as zf:
            zf.extractall('.')
            nc_files = [f for f in zf.namelist() if f.endswith('.nc')]
            if nc_files:
                import shutil
                shutil.move(nc_files[0], 'era5_portugal.nc')
                print(f"[OK] Extracted: {nc_files[0]} -> era5_portugal.nc")

        return True

    except Exception as e:
        print(f"[ERROR] ERA5 download failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def process_era5_to_csv():
    """
    Process ERA5 NetCDF file to CSV with city-level monthly weather
    """
    try:
        import xarray as xr
    except ImportError:
        print("[ERROR] xarray not installed. Run: pip install xarray netcdf4")
        return False

    nc_file = 'era5_portugal.nc'
    if not os.path.exists(nc_file):
        print(f"[ERROR] {nc_file} not found. Run download_era5_data() first.")
        return False

    print("\n[PROCESS] Processing ERA5 NetCDF to CSV...")

    ds = xr.open_dataset(nc_file)

    rows = []

    for city, (lat, lon) in CITY_COORDS.items():
        print(f"   Processing {city}...")

        # Select nearest grid point to city coordinates
        city_data = ds.sel(latitude=lat, longitude=lon, method='nearest')

        for year in range(2000, 2024):
            for month in range(1, 13):
                try:
                    # Temperature (Kelvin to Celsius)
                    temp_k = float(city_data['t2m'].sel(time=datetime(year, month, 1)).values)
                    temp_c = temp_k - 273.15

                    # Dewpoint (for humidity calculation)
                    dew_k = float(city_data['d2m'].sel(time=datetime(year, month, 1)).values)
                    dew_c = dew_k - 273.15

                    # Calculate relative humidity from temp and dewpoint
                    def rh_from_dewpoint(temp_c, dew_c):
                        a, b = 17.27, 237.7
                        rh = 100 * np.exp((a * dew_c) / (b + dew_c)) / np.exp((a * temp_c) / (b + temp_c))
                        return np.clip(rh, 0, 100)

                    humidity = rh_from_dewpoint(temp_c, dew_c)

                    # Wind speed (u and v components to magnitude)
                    u = float(city_data['u10'].sel(time=datetime(year, month, 1)).values)
                    v = float(city_data['v10'].sel(time=datetime(year, month, 1)).values)
                    wind_speed = np.sqrt(u**2 + v**2) * 3.6  # m/s to km/h

                    # Precipitation (m to mm)
                    precip_m = float(city_data['tp'].sel(time=datetime(year, month, 1)).values)
                    precip_mm = precip_m * 1000

                    rows.append({
                        'year': year,
                        'month': month,
                        'city': city,
                        'temperature': round(temp_c, 1),
                        'humidity': round(humidity, 1),
                        'wind_speed': round(wind_speed, 1),
                        'precipitation': round(precip_mm, 1)
                    })

                except Exception as e:
                    print(f"      [WARN] {city} {year}-{month:02d}: {e}")
                    continue

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\n[OK] ERA5 data saved: {OUTPUT_FILE}")
    print(f"     Total records: {len(df)}")
    print(f"     Cities: {len(df['city'].unique())}")
    print(f"     Date range: {df['year'].min()}-{df['month'].min()} to {df['year'].max()}-{df['month'].max()}")

    return True

if __name__ == '__main__':
    print("=" * 70)
    print("EMBEREDGE - ERA5 HISTORICAL WEATHER")
    print("=" * 70)

    # Step 1: Download
    if not os.path.exists('era5_portugal.nc'):
        success = download_era5_data()
        if not success:
            exit(1)

    # Step 2: Process
    success = process_era5_to_csv()

    if success:
        print("\n" + "=" * 70)
        print("ERA5 DATA READY!")
        print("=" * 70)
    else:
        print("\n[X] ERA5 processing failed")
        exit(1)
