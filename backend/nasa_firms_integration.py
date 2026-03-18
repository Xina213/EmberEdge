#!/usr/bin/env python3
"""
EmberEdge - NASA FIRMS Integration
Busca hotspots MODIS/VIIRS em tempo real
"""

import requests
import csv
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

NASA_FIRMS_KEY = os.getenv('NASA_FIRMS_KEY', 'your_key_here')
FIRES_OUTPUT = '../data/fires/fires_latest.csv'

# Bounding box Portugal + Espanha
BBOX = '-10,36,-5,43'  # lon_min,lat_min,lon_max,lat_max

def fetch_firms_fires(days=1, source='VIIRS_SNPP_NRT'):
    """
    Buscar fogos NASA FIRMS
    
    Args:
        days: últimos N dias (1-10)
        source: MODIS_NRT, VIIRS_SNPP_NRT, VIIRS_NOAA20_NRT
    
    Returns:
        list: fogos detectados
    """
    
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{NASA_FIRMS_KEY}/{source}/{BBOX}/{days}"
    
    print(f"🛰️ Buscando NASA FIRMS ({source})...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Parse CSV response
        lines = response.text.strip().split('\n')
        
        if len(lines) < 2:
            print("⚠️ Sem fogos detectados")
            return []
        
        # Header + data
        header = lines[0].split(',')
        fires = []
        
        for line in lines[1:]:
            values = line.split(',')
            fire_dict = dict(zip(header, values))
            fires.append(fire_dict)
        
        print(f"✅ {len(fires)} hotspots FIRMS detectados")
        return fires
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro NASA FIRMS: {e}")
        return []


def save_fires_to_csv(fires):
    """Salvar fogos em CSV EmberEdge format"""
    
    if not fires:
        # Criar CSV vazio se sem fogos
        with open(FIRES_OUTPUT, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['fire_id', 'city', 'latitude', 'longitude', 
                           'area_hectares', 'active_hours', 'confidence', 
                           'temperature', 'timestamp'])
        print(f"💾 CSV vazio criado: {FIRES_OUTPUT}")
        return
    
    with open(FIRES_OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['fire_id', 'city', 'latitude', 'longitude', 
                       'area_hectares', 'active_hours', 'confidence', 
                       'temperature', 'timestamp'])
        
        for idx, fire in enumerate(fires):
            # FIRMS fields: latitude, longitude, brightness, confidence, acq_date, acq_time, etc
            fire_id = f"FIRMS_{fire.get('acq_date', '').replace('-', '')}_{idx:03d}"
            lat = float(fire.get('latitude', 0))
            lon = float(fire.get('longitude', 0))
            confidence = float(fire.get('confidence', 0))
            brightness = float(fire.get('brightness', 300))  # Kelvin
            
            # Estimar área (1 pixel VIIRS ≈ 375m = ~14 ha)
            area_ha = 14
            
            # Cidade mais próxima (simplificado - usa reverse geocoding depois)
            city = get_nearest_city(lat, lon)
            
            writer.writerow([
                fire_id,
                city,
                lat,
                lon,
                area_ha,
                0,  # active_hours (desconhecido)
                confidence,
                brightness,
                datetime.now().isoformat()
            ])
    
    print(f"💾 {len(fires)} fogos salvos: {FIRES_OUTPUT}")


def get_nearest_city(lat, lon):
    """Encontrar cidade mais próxima (simplificado)"""
    
    # Cidades principais Portugal
    cities = {
        'Lisboa': (38.72, -9.14),
        'Porto': (41.16, -8.63),
        'Coimbra': (40.20, -8.43),
        'Faro': (37.02, -7.93),
        'Évora': (38.57, -7.91),
        'Covilhã': (40.28, -7.50),
        'Guarda': (40.54, -7.27),
        'Viseu': (40.66, -7.91),
        'Braga': (41.55, -8.43),
        'Bragança': (41.81, -6.76)
    }
    
    min_dist = float('inf')
    nearest = 'Desconhecido'
    
    for city, (city_lat, city_lon) in cities.items():
        # Distância euclidiana simples
        dist = ((lat - city_lat)**2 + (lon - city_lon)**2)**0.5
        if dist < min_dist:
            min_dist = dist
            nearest = city
    
    return nearest


# ===== MAIN =====
if __name__ == '__main__':
    print("=" * 60)
    print("NASA FIRMS - INTEGRAÇÃO EMBEREDGE")
    print("=" * 60)
    
    # Verificar API key
    if NASA_FIRMS_KEY == 'your_key_here':
        print("❌ NASA_FIRMS_KEY não configurada no .env")
        print("   1. Obtém key em: https://firms.modaps.eosdis.nasa.gov/api/")
        print("   2. Adiciona ao .env: NASA_FIRMS_KEY=your_key")
        exit(1)
    
    # Buscar VIIRS (melhor resolução)
    fires_viirs = fetch_firms_fires(days=1, source='VIIRS_SNPP_NRT')
    
    # Buscar MODIS (backup)
    fires_modis = fetch_firms_fires(days=1, source='MODIS_NRT')
    
    # Combinar (VIIRS priority)
    all_fires = fires_viirs + fires_modis
    
    print(f"\n📊 Total: {len(all_fires)} hotspots")
    
    # Salvar
    save_fires_to_csv(all_fires)
    
    print("\n" + "=" * 60)
    print("✅ INTEGRAÇÃO NASA FIRMS COMPLETA!")
    print(f"📂 Dados salvos: {FIRES_OUTPUT}")
