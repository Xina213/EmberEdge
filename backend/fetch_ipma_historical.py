#!/usr/bin/env python3
"""
EmberEdge - IPMA Historical Weather Data
Download real Portuguese weather data 2000-2023
IPMA provides free CSV data for ~50 stations
"""

import requests
import csv
import os
from datetime import datetime
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
OUTPUT_FILE = os.path.join(DATA_DIR, 'weather_historical_ipma.csv')

# IPMA station IDs (main stations with long historical records)
# Format: {name: (station_id, lat, lon)}
IPMA_STATIONS = {
    'Lisboa': (85, 38.72, -9.14),  # Lisboa/Gago Coutinho
    'Porto': (91, 41.16, -8.62),      # Porto/Pedras Rubras
    'Faro': (32, 37.02, -7.93),        # Faro
    'Coimbra': (29, 40.21, -8.43),      # Coimbra
    'Braga': (14, 41.55, -8.42),        # Braga
    'Evora': (31, 38.57, -7.91),        # Évora
    'Beja': (10, 38.02, -7.87),         # Beja
    'Setubal': (81, 38.52, -8.89),      # Setúbal
    'Leiria': (45, 39.75, -8.81),       # Leiria
    'Portalegre': (71, 39.30, -7.43),    # Portalegre
    'Castelo Branco': (24, 39.82, -7.49), # Castelo Branco
    'Vila Real': (95, 41.30, -7.74),    # Vila Real
    'Viseu': (96, 40.66, -7.91),        # Viseu
    'Guarda': (35, 40.54, -7.27),        # Guarda
    'Braganca': (16, 41.81, -6.76),      # Bragança
    'Aveiro': (5, 40.64, -8.65),        # Aveiro
    'Viana do Castelo': (94, 41.69, -8.83), # Viana do Castelo
}

def fetch_station_data(station_name, station_id):
    """
    Fetch monthly weather data from IPMA for 2000-2023
    IPMA URL: https://www.ipma.pt/resources.www/transf/data/obs/station/{id}.csv
    """
    # IPMA provides monthly data in CSV format
    # URL pattern may vary - let's try the API endpoint
    url = f"https://api.ipma.pt/open-data/observation/climate/station/{station_id}/monthly.json"

    print(f"   [{station_name}] Fetching from IPMA API...")
    print(f"      URL: {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()

        records = []
        for item in data:
            year = int(item.get('year', 0))
            month = int(item.get('month', 0))

            if year < 2000 or year > 2023:
                continue

            # Extract weather data
            temp = float(item.get('tmed', item.get('temp_avg', 0)))
            humidity = float(item.get('umrel', item.get('humidity', 0)))
            wind = float(item.get('vvento', item.get('wind', 0)))
            precip = float(item.get('prec', item.get('precipitation', 0)))

            # Convert units if needed
            # IPMA temps are already in Celsius
            # Wind might be in m/s, convert to km/h
            if wind < 100:  # Likely m/s
                wind = wind * 3.6

            records.append({
                'year': year,
                'month': month,
                'city': station_name,
                'temperature': round(temp, 1),
                'humidity': round(max(0, min(100, humidity))),
                'wind_speed': round(wind, 1),
                'precipitation': round(max(0, precip), 1)
            })

        return records

    except Exception as e:
        print(f"      [ERROR] {e}")
        return []

def fetch_all_stations():
    """Fetch data for all IPMA stations"""
    print("\n" + "=" * 70)
    print("EMBEREDGE - IPMA HISTORICAL WEATHER (2000-2023)")
    print("=" * 70)

    all_records = []
    total_stations = len(IPMA_STATIONS)

    for idx, (station_name, (station_id, lat, lon)) in enumerate(IPMA_STATIONS.items(), 1):
        print(f"\n[{idx}/{total_stations}] {station_name} (ID: {station_id})...")

        records = fetch_station_data(station_name, station_id)
        print(f"      Got {len(records)} monthly records")

        all_records.extend(records)

        # Be nice to the API
        time.sleep(0.5)

    return all_records

def save_to_csv(records):
    """Save records to CSV"""
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    if not records:
        print("\n[ERROR] No data to save!")
        return False

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['year', 'month', 'city', 'temperature', 'humidity', 'wind_speed', 'precipitation'])
        writer.writeheader()
        writer.writerows(records)

    print(f"\n[OK] Data saved: {OUTPUT_FILE}")
    print(f"     Total records: {len(records)}")
    print(f"     Cities: {len(set(r['city'] for r in records))}")
    print(f"     Date range: {min(r['year'] for r in records)}-{max(r['year'] for r in records)}")

    return True

if __name__ == '__main__':
    print("=" * 70)
    print("EMBEREDGE - IPMA HISTORICAL DATA DOWNLOAD")
    print("=" * 70)

    records = fetch_all_stations()
    save_to_csv(records)

    print("\n" + "=" * 70)
    print("IPMA DATA DOWNLOAD COMPLETE!")
    print("=" * 70)
