#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EmberEdge - NASA FIRMS Data Fetcher
Busca fogos ativos VIIRS/MODIS e salva em CSV
"""

import requests
import csv
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

NASA_KEY = os.getenv('NASA_FIRMS_KEY', 'your_key_here')
OUTPUT_FILE = '../data/fires/fires_latest.csv'

# Bounding Box Portugal + Espanha
BBOX = '-10,36,-5,43'

# Cidades principais
CITIES = {
    'Lisboa': (38.72, -9.14),
    'Porto': (41.16, -8.63),
    'Coimbra': (40.20, -8.43),
    'Faro': (37.02, -7.93),
    'Évora': (38.57, -7.91),
    'Covilhã': (40.28, -7.50),
    'Guarda': (40.54, -7.27),
    'Viseu': (40.66, -7.91),
    'Braga': (41.55, -8.43),
    'Bragança': (41.81, -6.76),
    'Castelo Branco': (39.82, -7.49),
    'Leiria': (39.75, -8.80),
    'Santarém': (39.24, -8.69),
    'Portalegre': (39.30, -7.43),
    'Beja': (38.02, -7.86),
    'Madrid': (40.42, -3.70),
    'Toledo': (39.86, -4.03),
    'Cáceres': (39.48, -6.37),
    'Badajoz': (38.88, -6.97)
}


def fetch_firms(source='VIIRS_SNPP_NRT', days=1):
    """Buscar dados NASA FIRMS"""
    
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{NASA_KEY}/{source}/{BBOX}/{days}"
    
    print(f"[FIRMS] Fetching {source}...")
    print(f"   Days: {days} | BBox: Portugal+Espanha")
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        lines = response.text.strip().split('\n')
        
        if len(lines) < 2:
            print("[FIRMS] No fires detected")
            return []
        
        import csv
        from io import StringIO
        
        reader = csv.DictReader(StringIO(response.text))
        fires = list(reader)
        
        print(f"[OK] {len(fires)} hotspots detected")
        return fires
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] NASA FIRMS: {e}")
        return []


def get_nearest_city(lat, lon):
    """Encontrar cidade mais próxima"""
    
    min_dist = float('inf')
    nearest = 'Unknown'
    
    for city, (city_lat, city_lon) in CITIES.items():
        dist = ((lat - city_lat)**2 + (lon - city_lon)**2)**0.5
        if dist < min_dist:
            min_dist = dist
            nearest = city
    
    return nearest


def save_to_csv(fires):
    """Salvar fogos em formato EmberEdge"""
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'fire_id', 'city', 'latitude', 'longitude', 
            'area_hectares', 'active_hours', 'confidence', 
            'temperature', 'timestamp'
        ])
        
        if not fires:
            print(f"[SAVED] Empty CSV: {OUTPUT_FILE}")
            return
        
        for idx, fire in enumerate(fires):
            fire_id = f"FIRMS_{fire['acq_date'].replace('-', '')}_{idx:03d}"
            lat = float(fire['latitude'])
            lon = float(fire['longitude'])
            confidence = float(fire.get('confidence', 80))
            brightness = float(fire.get('brightness', 300))
            
            temp_celsius = brightness - 273.15
            area_ha = 14 if 'VIIRS' in fire.get('satellite', '') else 100
            
            acq_time = fire.get('acq_time', '0000')
            hours_active = int(acq_time[:2]) if acq_time.isdigit() else 0
            
            city = get_nearest_city(lat, lon)
            
            writer.writerow([
                fire_id, city, lat, lon, area_ha, hours_active,
                confidence, round(temp_celsius, 1),
                datetime.now().isoformat()
            ])
    
    print(f"[SAVED] {len(fires)} fires: {OUTPUT_FILE}")


# ===== MAIN =====
if __name__ == '__main__':
    print("=" * 70)
    print("NASA FIRMS - FETCHING REAL FIRE DATA")
    print("=" * 70)
    
    if NASA_KEY == 'your_key_here':
        print("\n[ERROR] NASA_FIRMS_KEY not configured!")
        print("   1. Get key: https://firms.modaps.eosdis.nasa.gov/api/")
        print("   2. Add to .env: NASA_FIRMS_KEY=your_key")
        exit(1)
    
    print(f"\n[KEY] {NASA_KEY[:20]}...{NASA_KEY[-10:]}")
    
    fires_viirs = fetch_firms('VIIRS_SNPP_NRT', days=1)
    fires_modis = fetch_firms('MODIS_NRT', days=1)
    
    all_fires = fires_viirs + fires_modis
    
    print(f"\n[TOTAL] {len(all_fires)} hotspots")
    
    save_to_csv(all_fires)
    
    print("\n" + "=" * 70)
    print("[SUCCESS] NASA FIRMS DATA FETCHED!")
    print(f"[FILE] {OUTPUT_FILE}")
    print("=" * 70)
