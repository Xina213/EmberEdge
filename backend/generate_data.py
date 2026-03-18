#!/usr/bin/env python3
"""
EmberEdge - Gerador de Dados Simulados
Gera weather_latest.csv e fires_latest.csv com dados realistas
"""

import csv
import os
import random
from datetime import datetime, timedelta

# ===== CONFIGURAÇÃO =====
DATA_DIR = "../data"
FIRES_DIR = os.path.join(DATA_DIR, "fires")
WEATHER_FILE = os.path.join(DATA_DIR, "weather_latest.csv")
FIRES_FILE = os.path.join(FIRES_DIR, "fires_latest.csv")

# ===== CIDADES PORTUGAL + ESPANHA =====
CITIES = {
    'Lisboa': (38.7223, -9.1393),
    'Porto': (41.1579, -8.6291),
    'Covilhã': (40.2829, -7.4998),
    'Guarda': (40.5353, -7.2695),
    'Castelo Branco': (39.8198, -7.4917),
    'Viseu': (40.6599, -7.9139),
    'Aveiro': (40.6406, -8.6535),
    'Figueira da Foz': (40.1403, -8.8596),
    'Leiria': (39.7553, -8.8046),
    'Caldas da Rainha': (39.4034, -9.1371),
    'Tomar': (39.6013, -8.4093),
    'Santarém': (39.2369, -8.6867),
    'Portalegre': (39.2972, -7.4285),
    'Évora': (38.5714, -7.9093),
    'Beja': (38.0151, -7.8629),
    'Faro': (37.0194, -7.9322),
    'Braga': (41.5454, -8.4265),
    'Viana do Castelo': (41.6938, -8.8344),
    'Vila Real': (41.3006, -7.7445),
    'Bragança': (41.8065, -6.7570),
    'Madrid': (40.4168, -3.7038),
    'Toledo': (39.8628, -4.0273),
    'Cuenca': (40.0703, -2.1374),
    'Ávila': (40.6564, -4.6813),
    'Segovia': (40.9429, -4.1088),
    'Salamanca': (40.9701, -5.6635),
    'Cáceres': (39.4753, -6.3724),
    'Badajoz': (38.8794, -6.9706),
    'Ciudad Real': (38.9848, -3.9276),
    'Valladolid': (41.6523, -4.7245)
}

# ===== FUNÇÕES =====

def create_directories():
    """Cria pastas necessárias"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(FIRES_DIR, exist_ok=True)
    print(f"✅ Pastas criadas: {DATA_DIR}, {FIRES_DIR}")


def generate_weather_data():
    """Gera dados meteorológicos realistas para 30 cidades"""
    print("\n📊 Gerando weather_latest.csv...")
    
    with open(WEATHER_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['city', 'latitude', 'longitude', 'temperature', 
                        'wind_speed', 'humidity', 'precipitation', 'timestamp'])
        
        for city, (lat, lon) in CITIES.items():
            # Dados realistas baseados em padrões IPMA Portugal (Fevereiro)
            temp = round(random.uniform(8, 18), 1)  # Inverno PT
            wind = round(random.uniform(5, 25), 1)  # Vento moderado
            humidity = random.randint(55, 90)  # Humidade alta inverno
            precip = round(random.uniform(0, 8), 1)  # Chuva ocasional
            
            writer.writerow([
                city, lat, lon, temp, wind, humidity, precip,
                datetime.now().isoformat()
            ])
    
    print(f"✅ {len(CITIES)} cidades geradas em {WEATHER_FILE}")


def generate_fires_data():
    """Gera fogos ativos realistas (poucos em Fevereiro)"""
    print("\n🔥 Gerando fires_latest.csv...")
    
    num_fires = random.randint(0, 3)  # Inverno = poucos fogos
    
    with open(FIRES_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['fire_id', 'city', 'latitude', 'longitude', 
                        'area_hectares', 'active_hours', 'confidence', 
                        'temperature', 'timestamp'])
        
        for i in range(num_fires):
            city = random.choice(list(CITIES.keys()))
            lat, lon = CITIES[city]
            
            # Variação pequena nas coordenadas
            fire_lat = round(lat + random.uniform(-0.05, 0.05), 4)
            fire_lon = round(lon + random.uniform(-0.05, 0.05), 4)
            
            writer.writerow([
                f"FIRE_{datetime.now().strftime('%Y%m%d')}_{i:03d}",
                city,
                fire_lat,
                fire_lon,
                random.randint(5, 150),  # Área pequena inverno
                random.randint(1, 48),  # Horas ativo
                random.randint(75, 99),  # Confiança detecção
                round(random.uniform(600, 900), 1),  # Temperatura fogo
                datetime.now().isoformat()
            ])
    
    print(f"✅ {num_fires} fogos gerados em {FIRES_FILE}")


def verify_data():
    """Verifica se ficheiros foram criados corretamente"""
    print("\n🔍 Verificando ficheiros...")
    
    if os.path.exists(WEATHER_FILE):
        with open(WEATHER_FILE, 'r', encoding='utf-8') as f:
            lines = len(f.readlines()) - 1  # -1 header
            print(f"✅ {WEATHER_FILE} → {lines} registos")
    else:
        print(f"❌ {WEATHER_FILE} NÃO EXISTE")
    
    if os.path.exists(FIRES_FILE):
        with open(FIRES_FILE, 'r', encoding='utf-8') as f:
            lines = len(f.readlines()) - 1
            print(f"✅ {FIRES_FILE} → {lines} registos")
    else:
        print(f"❌ {FIRES_FILE} NÃO EXISTE")


# ===== MAIN =====
if __name__ == '__main__':
    print("🔥 EMBEREDGE - GERADOR DE DADOS SIMULADOS")
    print("=" * 50)
    
    create_directories()
    generate_weather_data()
    generate_fires_data()
    verify_data()
    
    print("\n" + "=" * 50)
    print("✅ DADOS GERADOS COM SUCESSO!")
    print("📂 Ficheiros criados:")
    print(f"   - {WEATHER_FILE}")
    print(f"   - {FIRES_FILE}")
    print("\n🚀 Pronto para executar app.py!")
