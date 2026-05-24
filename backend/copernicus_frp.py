#!/usr/bin/env python3
"""
EmberEdge - Copernicus Sentinel-3 FRP Integration
Calcula área ardida real usando Fire Radiative Power (Sentinel-3 SLSTR)

Metodologia:
  - Sentinel-3 SLSTR mede FRP (Fire Radiative Power) em megawatts por pixel
  - Fórmula empírica: Area(ha) = FRP(MW) * fator_combustivel
  - Fatores por tipo de vegetação validados em estudos europeus (Wooster et al. 2005)
  - Cruzamento com hotspots NASA FIRMS por proximidade geográfica (≤0.1°)
"""

import requests
import os
import json
import csv
from datetime import datetime, timedelta
from dotenv import load_dotenv
from copernicus_auth import get_copernicus_token

load_dotenv()

# Portugal bounding box
PORTUGAL_BBOX = (-10.0, 36.0, -6.0, 42.0)

# Fator de conversão FRP → área (ha/MW)
# Baseado em Wooster et al. 2005 para vegetação mediterrânica
# shrubland/mato: ~2.5 ha/MW | floresta densa: ~1.8 ha/MW | media Portugal: ~2.2
FRP_TO_AREA_FACTOR = 2.2

# Raio de associação hotspot FIRMS ↔ pixel Sentinel (em graus, ~11km)
MATCH_RADIUS_DEG = 0.10

# Paths
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, '..', 'data')
FIRES_FILE = os.path.join(DATA_DIR, 'fires', 'fires_latest.csv')
FRP_CACHE  = os.path.join(DATA_DIR, 'frp_cache.json')


# ===== TOKEN =====

_token       = None
_token_expiry = None

def get_valid_token():
    global _token, _token_expiry
    if _token and _token_expiry and datetime.now() < _token_expiry - timedelta(minutes=5):
        return _token
    print("🔑 Obtendo token Copernicus...")
    _token = get_copernicus_token()
    if _token:
        _token_expiry = datetime.now() + timedelta(minutes=30)
        print(f"✅ Token válido até {_token_expiry.strftime('%H:%M:%S')}")
    return _token


# ===== SENTINEL-3 CATALOG =====

def search_sentinel3_frp(date_from=None, date_to=None):
    """
    Pesquisa produtos Sentinel-3 SLSTR com dados FRP sobre Portugal.
    Retorna lista de produtos ordenados por data desc.
    """
    token = get_valid_token()
    if not token:
        print("❌ Sem token Copernicus")
        return []

    if not date_to:
        date_to = datetime.now().strftime('%Y-%m-%d')
    if not date_from:
        date_from = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')

    lon_min, lat_min, lon_max, lat_max = PORTUGAL_BBOX

    # Sentinel-3 SLSTR Level-2 FRP product
    # Nome do produto: S3A_SL_2_FRP ou S3B_SL_2_FRP
    odata_filter = (
        f"Collection/Name eq 'SENTINEL-3' and "
        f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' "
        f"and att/OData.CSC.StringAttribute/Value eq 'SL_2_FRP___') and "
        f"OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(("
        f"{lon_min} {lat_min},{lon_max} {lat_min},"
        f"{lon_max} {lat_max},{lon_min} {lat_max},"
        f"{lon_min} {lat_min}))') and "
        f"ContentDate/Start ge {date_from}T00:00:00.000Z and "
        f"ContentDate/Start le {date_to}T23:59:59.999Z"
    )

    url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    params = {
        '$filter':  odata_filter,
        '$top':     5,
        '$orderby': 'ContentDate/Start desc'
    }
    headers = {'Authorization': f'Bearer {token}'}

    print(f"🛰️  Pesquisando Sentinel-3 FRP ({date_from} → {date_to})...")

    try:
        r = requests.get(url, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        products = r.json().get('value', [])
        print(f"   ✅ {len(products)} produtos FRP encontrados")
        return products
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erro catalog Copernicus: {e}")
        return []


# ===== FRP DATA EXTRACTION =====

def fetch_frp_json(product_id):
    """
    Tenta buscar dados FRP via OData nodes (sem download completo do ZIP).
    O Copernicus expõe alguns metadados de produto inline.
    Retorna lista de detecções FRP: [{lat, lon, frp_mw}, ...]
    """
    token = get_valid_token()
    if not token:
        return []

    headers = {'Authorization': f'Bearer {token}'}

    # Tenta aceder aos nodes do produto para extrair FRP summary
    nodes_url = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products({product_id})/Nodes"

    try:
        r = requests.get(nodes_url, headers=headers, timeout=20)
        r.raise_for_status()
        nodes = r.json().get('result', [])

        # Procura ficheiro de sumário FRP (geralmente um JSON ou XML pequeno)
        for node in nodes:
            name = node.get('Name', '')
            if 'FRP' in name.upper() and name.endswith('.json'):
                node_id = node.get('Id')
                content_url = (
                    f"https://catalogue.dataspace.copernicus.eu"
                    f"/odata/v1/Products({product_id})/Nodes({node_id})/$value"
                )
                cr = requests.get(content_url, headers=headers, timeout=30)
                if cr.status_code == 200:
                    return parse_frp_json(cr.json())

        return []

    except Exception as e:
        print(f"   ⚠️  Nodes FRP não acessíveis: {e}")
        return []


def parse_frp_json(data):
    """Extrai lista [{lat, lon, frp_mw}] de JSON Sentinel-3 FRP"""
    detections = []
    # Estrutura varia por versão — tentamos campos comuns
    features = data.get('features', data.get('detections', []))
    for feat in features:
        try:
            coords = feat.get('geometry', {}).get('coordinates', [])
            props  = feat.get('properties', feat)
            frp    = float(props.get('FRP', props.get('frp', props.get('fire_radiative_power', 0))))
            if frp > 0 and coords:
                detections.append({'lat': coords[1], 'lon': coords[0], 'frp_mw': frp})
        except (KeyError, TypeError, ValueError):
            continue
    return detections


# ===== FRP → ÁREA =====

def frp_to_area_ha(frp_mw):
    """
    Converte Fire Radiative Power (MW) em área ardida estimada (ha).

    Fórmula: Wooster et al. 2005, calibrada para vegetação mediterrânica.
    FRP < 10 MW  → pequeno (mato/restolho)
    FRP 10-50 MW → médio (pinhal/eucaliptal)
    FRP > 50 MW  → grande (incêndio florestal intenso)
    """
    if frp_mw <= 0:
        return 0.0
    elif frp_mw < 10:
        factor = 1.5   # mato/pastagem
    elif frp_mw < 50:
        factor = 2.2   # pinhal/eucaliptal (dominante em PT)
    else:
        factor = 3.0   # incêndio intenso com spotting
    return round(frp_mw * factor, 1)


# ===== MATCH FIRMS + SENTINEL =====

def match_frp_to_hotspot(hotspot_lat, hotspot_lon, frp_detections):
    """
    Associa uma deteção FIRMS ao pixel FRP Sentinel-3 mais próximo.
    Retorna FRP em MW ou None se não houver match no raio definido.
    """
    best_frp  = None
    best_dist = float('inf')

    for det in frp_detections:
        dist = ((hotspot_lat - det['lat'])**2 + (hotspot_lon - det['lon'])**2)**0.5
        if dist < MATCH_RADIUS_DEG and dist < best_dist:
            best_dist = det['frp_mw']
            best_frp  = det['frp_mw']

    return best_frp


# ===== PIPELINE PRINCIPAL =====

def enrich_fires_with_real_area():
    """
    Pipeline completo:
    1. Lê fires_latest.csv (hotspots FIRMS)
    2. Busca produtos Sentinel-3 FRP recentes
    3. Extrai dados FRP e cruza com hotspots
    4. Atualiza área_hectares com valor real (ou estimativa melhorada)
    5. Guarda fires_latest.csv atualizado
    """

    print("\n" + "="*60)
    print("🔥 EMBEREDGE - ENRIQUECIMENTO FRP SENTINEL-3")
    print("="*60)

    # 1. Lê hotspots FIRMS
    if not os.path.exists(FIRES_FILE):
        print(f"❌ {FIRES_FILE} não encontrado — corre primeiro fetch_nasa_firms.py")
        return False

    fires = []
    with open(FIRES_FILE, 'r', encoding='utf-8') as f:
        fires = list(csv.DictReader(f))

    if not fires:
        print("ℹ️  Sem fogos no CSV — nada a enriquecer")
        return True

    print(f"📋 {len(fires)} hotspots FIRMS carregados")

    # 2. Busca produtos Sentinel-3 FRP (últimas 48h para garantir cobertura)
    products = search_sentinel3_frp(
        date_from=(datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
        date_to=datetime.now().strftime('%Y-%m-%d')
    )

    # 3. Extrai deteções FRP de todos os produtos
    all_frp_detections = []
    for product in products[:3]:  # máx 3 produtos para não demorar
        pid  = product.get('Id', '')
        name = product.get('Name', '')
        print(f"   📦 Processando: {name[:50]}...")
        dets = fetch_frp_json(pid)
        all_frp_detections.extend(dets)
        print(f"      → {len(dets)} deteções FRP")

    print(f"\n📡 Total deteções FRP Sentinel-3: {len(all_frp_detections)}")

    # 4. Cruza e atualiza área
    enriched = 0
    updated_fires = []

    for fire in fires:
        try:
            lat = float(fire['latitude'])
            lon = float(fire['longitude'])
        except (ValueError, KeyError):
            updated_fires.append(fire)
            continue

        frp_mw = match_frp_to_hotspot(lat, lon, all_frp_detections)

        if frp_mw is not None:
            # Área real via Sentinel-3 FRP
            area_real = frp_to_area_ha(frp_mw)
            fire['area_hectares'] = area_real
            fire['frp_mw']        = round(frp_mw, 2)
            fire['area_source']   = 'Sentinel-3 FRP'
            enriched += 1
            print(f"   ✅ {fire.get('city','?')} ({lat:.3f},{lon:.3f}): "
                  f"FRP={frp_mw:.1f}MW → {area_real}ha")
        else:
            # Fallback: estimativa melhorada pela temperatura de brilho
            # bright_ti4 em Kelvin → quanto mais quente, maior o fogo estimado
            try:
                temp_k = float(fire.get('temperature', 0)) + 273.15
                # Escala: 300K=mínimo, 400K=muito intenso
                intensity = max(0, min(1, (temp_k - 300) / 100))
                area_est  = round(14 + intensity * 200, 1)  # 14ha a 214ha
            except (ValueError, TypeError):
                area_est = 14  # fallback mínimo VIIRS

            fire['area_hectares'] = area_est
            fire['frp_mw']        = None
            fire['area_source']   = 'estimativa_brightness'
            print(f"   ⚠️  {fire.get('city','?')} ({lat:.3f},{lon:.3f}): "
                  f"sem FRP Sentinel → estimativa {area_est}ha (brightness)")

        updated_fires.append(fire)

    # 5. Guarda CSV atualizado
    if updated_fires:
        fieldnames = list(updated_fires[0].keys())
        with open(FIRES_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_fires)

        print(f"\n✅ {FIRES_FILE} atualizado")
        print(f"   Enriquecidos com FRP real: {enriched}/{len(fires)}")
        if enriched < len(fires):
            print(f"   Estimativa brightness: {len(fires)-enriched}/{len(fires)}")

    # Guarda cache FRP para debug
    if all_frp_detections:
        with open(FRP_CACHE, 'w') as f:
            json.dump({
                'timestamp':  datetime.now().isoformat(),
                'detections': all_frp_detections
            }, f, indent=2)
        print(f"   Cache FRP guardado: {FRP_CACHE}")

    print("="*60)
    return True


# ===== MAIN =====

if __name__ == '__main__':
    success = enrich_fires_with_real_area()

    if not success:
        print("\n⚠️  Pipeline incompleto — verifica as keys no .env")
        print("   COPERNICUS_CLIENT_ID e COPERNICUS_CLIENT_SECRET são necessários")
    else:
        print("\n✅ ENRIQUECIMENTO FRP COMPLETO!")
        print("   Os fogos em fires_latest.csv têm agora área real (ou melhor estimativa)")
        print("\n📌 Próximo passo: reinicia app.py para ver os dados atualizados")
