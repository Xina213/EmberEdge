#!/usr/bin/env python3
"""
EmberEdge - ICNF Historical Fire Data Fetcher
Busca dados históricos de incêndios 2001-2026 do WebService ICNF oficial
"""

import requests
import csv
import json
from datetime import datetime, timedelta
import os
import time

OUTPUT_FILE = '../data/fires/historical_fires.csv'
ICNF_API = 'https://fogos.icnf.pt/localizador/webserviceocorrencias.asp'

def fetch_fires_by_year(year):
    """
    Busca fogos de um ano específico do ICNF
    """
    print(f"\n[{year}] Buscando dados do ICNF...")
    
    # ICNF API aceita queries por data
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    params = {
        'fromDate': start_date,
        'toDate': end_date,
        'format': 'json'  # Tenta JSON primeiro
    }
    
    try:
        response = requests.get(ICNF_API, params=params, timeout=30)
        
        if response.status_code == 200:
            # Tenta parsear JSON
            try:
                data = response.json()
                print(f"   [SUCCESS] {len(data)} ocorrências encontradas")
                return data
            except json.JSONDecodeError:
                # Se não for JSON, tenta XML ou outro formato
                print(f"   [WARNING] Resposta não é JSON, tentando outro formato...")
                return parse_alternative_format(response.text)
        else:
            print(f"   [ERROR] Status {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"   [ERROR] Request failed: {e}")
        return []

def parse_alternative_format(text):
    """
    Parser alternativo caso API retorne XML ou outro formato
    """
    # Placeholder - ajustaremos baseado na resposta real
    return []

def process_fire_data(raw_data):
    """
    Processa dados brutos e converte para formato EmberEdge
    """
    processed = []
    
    for fire in raw_data:
        try:
            processed_fire = {
                'date': fire.get('dateTime', fire.get('data', '')),
                'lat': float(fire.get('lat', fire.get('latitude', 0))),
                'lon': float(fire.get('lon', fire.get('longitude', 0))),
                'concelho': fire.get('concelho', fire.get('municipality', 'Desconhecido')),
                'distrito': fire.get('distrito', fire.get('district', 'Desconhecido')),
                'freguesia': fire.get('freguesia', fire.get('parish', '')),
                'area_hectares': float(fire.get('areaBurned', fire.get('area', 0))),
                'state': fire.get('state', fire.get('status', 'unknown')),
                'natureza': fire.get('natureza', fire.get('nature', 'florestal'))
            }
            processed.append(processed_fire)
        except (ValueError, KeyError) as e:
            # Skip registos inválidos
            continue
    
    return processed

def save_to_csv(data, filename):
    """
    Guarda dados em CSV
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    fieldnames = ['date', 'lat', 'lon', 'concelho', 'distrito', 'freguesia', 
                  'area_hectares', 'state', 'natureza']
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"\n[SAVED] {len(data)} registos salvos em: {filename}")

def main():
    print("="*70)
    print("ICNF HISTORICAL FIRE DATA FETCHER")
    print("="*70)
    print("Fonte: ICNF WebService Oficial")
    print("Período: 2001-2026")
    print("="*70)
    
    # Primeiro testa conectividade com ano recente
    print("\n[TEST] Testando API com dados de 2023...")
    test_data = fetch_fires_by_year(2023)
    
    if not test_data:
        print("\n[ERROR] API não respondeu. Vamos tentar abordagem alternativa...")
        print("\nOPÇÕES:")
        print("1. Usar dataset pré-processado (GitHub)")
        print("2. Tentar outro endpoint ICNF")
        print("3. Debug manual da API")
        return
    
    # Se funcionou, busca todos os anos
    print("\n[INFO] API funciona! Buscando histórico completo...")
    all_fires = []
    
    # Anos de interesse (2001-2026)
    years = range(2001, 2027)
    
    for year in years:
        fires = fetch_fires_by_year(year)
        processed = process_fire_data(fires)
        all_fires.extend(processed)
        
        # Delay entre requests para não sobrecarregar API
        time.sleep(1)
    
    # Salva tudo
    save_to_csv(all_fires, OUTPUT_FILE)
    
    # Estatísticas
    print("\n" + "="*70)
    print("RESUMO")
    print("="*70)
    print(f"Total de ocorrências: {len(all_fires)}")
    print(f"Período: {years[0]}-{years[-1]}")
    print(f"Arquivo: {OUTPUT_FILE}")
    print("="*70)
    print("\n[NEXT] Execute: python process_historical_data.py")

if __name__ == '__main__':
    main()
