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

# Bounding Box Portugal Continental apenas (exclui Espanha)
BBOX = '-9.8,36.9,-6.2,42.2'

# Cidades principais Portugal
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
    'Viana do Castelo': (41.69, -8.83),
    'Vila Real': (41.30, -7.74),
    'Aveiro': (40.64, -8.65),
    'Setúbal': (38.52, -8.89)
}


def fetch_firms(source='VIIRS_SNPP_NRT', days=1):
    """Buscar dados NASA FIRMS"""

    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{NASA_KEY}/{source}/{BBOX}/{days}"

    print(f"[FIRMS] Fetching {source}...")
    print(f"   Days: {days} | BBox: Portugal+Espanha")

    try:
        response = requests.get(url, timeout=60)

        # NASA FIRMS devolve 200 mesmo com key inválida — verificar body
        if "Invalid" in response.text or "Error" in response.text or "error" in response.text:
            print(f"[ERROR] NASA FIRMS rejeitou key. Resposta: {response.text[:200]}")
            return None  # None = erro, não lista vazia

        response.raise_for_status()

        lines = response.text.strip().split('\n')

        if len(lines) < 2:
            print("[FIRMS] API ok — sem fogos no período")
            return []  # Lista vazia = ok, sem fogos

        import csv
        from io import StringIO

        reader = csv.DictReader(StringIO(response.text))
        fires = list(reader)

        print(f"[OK] {len(fires)} hotspots detected")
        return fires

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] NASA FIRMS: {e}")
        return None  # None = erro de rede


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

    if fires is None:
        # Erro de API — não sobrescrever CSV existente
        print(f"[WARN] Erro de API — CSV existente mantido: {OUTPUT_FILE}")
        return

    saved_count = 0
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

            # VIIRS devolve 'l' (low), 'n' (nominal), 'h' (high) em vez de numero
            confidence_raw = fire.get('confidence', '80')
            confidence_map = {'l': 40, 'n': 75, 'h': 95}
            if confidence_raw in confidence_map:
                confidence = confidence_map[confidence_raw]
            else:
                try:
                    confidence = float(confidence_raw)
                except (ValueError, TypeError):
                    confidence = 75  # default nominal

            # Filter out low-confidence detections (false positives: agricultural burns, industrial heat, etc.)
            if confidence < 50:
                continue

            # brightness pode estar em 'bright_ti4' (VIIRS) ou 'brightness' (MODIS)
            brightness_raw = fire.get('bright_ti4') or fire.get('brightness', '300')
            try:
                brightness = float(brightness_raw)
            except (ValueError, TypeError):
                brightness = 300.0

            temp_celsius = brightness - 273.15

            # VIIRS: satellite='N' (NOAA) ou 'S' (Suomi), instrumento='VIIRS'
            # MODIS: satellite='T' (Terra) ou 'A' (Aqua), instrumento='MODIS'
            # Calculate area based on brightness temperature (FRP proxy)
            # Higher brightness = hotter fire = larger area
            instrument = fire.get('instrument', '').upper()
            satellite  = fire.get('satellite', '').upper()
            is_viirs   = 'VIIRS' in instrument or satellite in ('N', 'S', '1')

            # Dynamic area calculation based on brightness temperature
            # Brightness 300K (~27C) = small fire, 600K+ (~327C) = large fire
            if brightness > 600:
                area_ha = 500 + (brightness - 600) * 5  # Large fire: 500-1000+ ha
            elif brightness > 500:
                area_ha = 100 + (brightness - 500) * 4  # Medium fire: 100-500 ha
            elif brightness > 400:
                area_ha = 20 + (brightness - 400) * 0.8  # Small fire: 20-100 ha
            else:
                area_ha = 5 + (brightness - 300) * 0.15  # Very small: 5-20 ha

            area_ha = round(max(1, min(area_ha, 5000)), 1)

            # acq_time é a hora UTC de passagem do satélite (ex: '1230' = 12h30)
            # Não sabemos há quantas horas está ativo — deixamos 0 (desconhecido)
            # O frontend deve mostrar "Detetado às HH:MM UTC" em vez de "X horas ativo"
            acq_time = fire.get('acq_time', '0000')
            try:
                acq_hour   = int(str(acq_time).zfill(4)[:2])
                acq_minute = int(str(acq_time).zfill(4)[2:])
                detection_time = f"{acq_hour:02d}:{acq_minute:02d} UTC"
            except (ValueError, TypeError):
                detection_time = "desconhecido"
            hours_active = detection_time  # campo reutilizado com significado correto
            
            city = get_nearest_city(lat, lon)
            
            writer.writerow([
                fire_id, city, lat, lon, area_ha, hours_active,
                confidence, round(temp_celsius, 1),
                datetime.now().isoformat()
            ])
            saved_count += 1

    filtered = len(fires) - saved_count
    print(f"[SAVED] {saved_count} fires (filtered {filtered} low-confidence): {OUTPUT_FILE}")


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
    
    all_fires = (fires_viirs or []) + (fires_modis or [])
    
    print(f"\n[TOTAL] {len(all_fires)} hotspots")
    
    save_to_csv(all_fires)
    
    print("\n" + "=" * 70)
    print("[SUCCESS] NASA FIRMS DATA FETCHED!")
    print(f"[FILE] {OUTPUT_FILE}")
    print("=" * 70)
