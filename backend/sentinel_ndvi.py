#!/usr/bin/env python3
"""
EmberEdge - Real NDVI from Copernicus Sentinel-2
Queries the Copernicus Data Space Process API for real NDVI values.

NDVI (Normalized Difference Vegetation Index) is computed from
Sentinel-2 L2A bands: B04 (Red, 665nm) and B08 (NIR, 842nm).
    NDVI = (NIR - Red) / (NIR + Red)

Range: -1 (water) to 1 (dense vegetation).
Low values (0.1-0.3) = dry/sparse vegetation = HIGH fire risk.
High values (0.6-0.9) = green vegetation = LOW fire risk.
"""

import requests
import csv
import os
import json
import time
import io
from datetime import datetime, timedelta
from dotenv import load_dotenv
from copernicus_auth import get_copernicus_token
import numpy as np
import tifffile

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
NDVI_CACHE = os.path.join(DATA_DIR, 'ndvi_cache.csv')

# City coordinates (same as predict_risk.py)
CITY_COORDS = {
    'Aveiro': {'lat': 40.64, 'lon': -8.65},
    'Beja': {'lat': 38.02, 'lon': -7.87},
    'Braga': {'lat': 41.55, 'lon': -8.42},
    'Braganca': {'lat': 41.81, 'lon': -6.76},
    'Castelo Branco': {'lat': 39.82, 'lon': -7.49},
    'Coimbra': {'lat': 40.21, 'lon': -8.43},
    'Evora': {'lat': 38.57, 'lon': -7.91},
    'Faro': {'lat': 37.02, 'lon': -7.93},
    'Guarda': {'lat': 40.54, 'lon': -7.27},
    'Leiria': {'lat': 39.75, 'lon': -8.81},
    'Lisboa': {'lat': 38.72, 'lon': -9.14},
    'Portalegre': {'lat': 39.30, 'lon': -7.43},
    'Porto': {'lat': 41.16, 'lon': -8.62},
    'Santarem': {'lat': 39.24, 'lon': -8.69},
    'Setubal': {'lat': 38.52, 'lon': -8.89},
    'Viana do Castelo': {'lat': 41.69, 'lon': -8.83},
    'Vila Real': {'lat': 41.30, 'lon': -7.74},
    'Viseu': {'lat': 40.66, 'lon': -7.91},
}

# Cache validity: 24 hours (Sentinel-2 revisits every 5 days)
CACHE_TTL_HOURS = 24

# Small buffer around city center (~2km) to avoid water bodies
BUFFER_DEG = 0.02

# Sentinel Hub Process API endpoint
PROCESS_API = "https://sh.dataspace.copernicus.eu/api/v1/process"

# Evalscript for NDVI computation (Sentinel Hub format)
NDVI_EVALSCRIPT = """
//VERSION=3
function setup() {
  return {
    input: ["B04", "B08"],
    output: { bands: 1, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(sample) {
  let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04 + 1e-10);
  return [ndvi];
}
"""


def query_ndvi_for_city(lat, lon, token, days_back=30):
    """
    Query the Copernicus Process API for mean NDVI around a coordinate.
    Returns (mean_ndvi, source_description) or (None, error_reason).
    """
    buffer = BUFFER_DEG
    geometry = {
        "type": "Polygon",
        "coordinates": [[
            [lon - buffer, lat - buffer],
            [lon + buffer, lat - buffer],
            [lon + buffer, lat + buffer],
            [lon - buffer, lat + buffer],
            [lon - buffer, lat - buffer]
        ]]
    }

    date_to = datetime.now()
    date_from = date_to - timedelta(days=days_back)

    payload = {
        "input": {
            "bounds": {
                "geometry": geometry,
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
            },
            "data": [{
                "type": "S2L2A",
                "dataFilter": {
                    "timeRange": {
                        "from": date_from.strftime("%Y-%m-%dT00:00:00Z"),
                        "to": date_to.strftime("%Y-%m-%dT23:59:59Z")
                    },
                    "maxCloudCoverage": 30
                }
            }]
        },
        "evalscript": NDVI_EVALSCRIPT,
        "output": {
            "width": 50,
            "height": 50,
            "responses": [
                {"identifier": "default", "format": {"type": "image/tiff"}}
            ]
        }
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(PROCESS_API, json=payload, headers=headers, timeout=120)
        response.raise_for_status()

        # Parse TIFF response
        with tifffile.TiffFile(io.BytesIO(response.content)) as tif:
            img = tif.asarray()

        # Extract NDVI band
        if img.ndim > 2:
            ndvi_band = img[..., 0]
        else:
            ndvi_band = img

        # Filter out NaN values
        valid_mask = ~np.isnan(ndvi_band)
        valid_pixels = valid_mask.sum()

        if valid_pixels > 0:
            mean_ndvi = float(ndvi_band[valid_mask].mean())
            ndvi = round(mean_ndvi, 3)
            return ndvi, f"Sentinel-2 L2A ({date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')})"

        return None, "no_valid_ndvi_found"

    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            return None, "auth_failed"
        elif response.status_code == 429:
            return None, "rate_limited"
        else:
            return None, f"http_{response.status_code}"
    except requests.exceptions.Timeout:
        return None, "timeout"
    except requests.exceptions.RequestException as e:
        return None, f"request_error: {str(e)[:50]}"
    except (ValueError, IndexError) as e:
        return None, f"parse_error: {str(e)[:50]}"


def load_ndvi_cache():
    """Load cached NDVI values from CSV."""
    cache = {}
    if not os.path.exists(NDVI_CACHE):
        return cache

    try:
        with open(NDVI_CACHE, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                cache[row['city']] = {
                    'ndvi': float(row['ndvi']),
                    'timestamp': row['timestamp'],
                    'source': row.get('source', 'unknown')
                }
    except Exception as e:
        print(f"[NDVI] Warning: cache read error: {e}")

    return cache


def save_ndvi_cache(ndvi_data):
    """Save NDVI values to CSV cache."""
    os.makedirs(DATA_DIR, exist_ok=True)

    fieldnames = ['city', 'ndvi', 'timestamp', 'source']
    with open(NDVI_CACHE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for city, data in ndvi_data.items():
            writer.writerow({
                'city': city,
                'ndvi': data['ndvi'],
                'timestamp': data['timestamp'],
                'source': data.get('source', 'unknown')
            })

    print(f"[NDVI] Cache saved: {len(ndvi_data)} cities -> {NDVI_CACHE}")


def is_cache_fresh(cache_entry):
    """Check if a cache entry is still fresh (< CACHE_TTL_HOURS old)."""
    try:
        cached_time = datetime.fromisoformat(cache_entry['timestamp'])
        age = datetime.now() - cached_time
        return age.total_seconds() < CACHE_TTL_HOURS * 3600
    except (ValueError, KeyError):
        return False


def get_ndvi(city_name, force_refresh=False):
    """
    Get NDVI for a city.
    Returns cached value if fresh, otherwise queries Copernicus API.

    Args:
        city_name: City name (with or without accents)
        force_refresh: If True, bypasses cache

    Returns:
        (ndvi_value, source) where ndvi_value is a float or None
        source describes the origin (real/estimated)
    """
    import unicodedata
    city_norm = unicodedata.normalize('NFKD', city_name).encode('ASCII', 'ignore').decode('utf-8')

    city_map = {unicodedata.normalize('NFKD', k).encode('ASCII', 'ignore').decode('utf-8').lower(): k
                for k in CITY_COORDS}
    actual_city = city_map.get(city_norm.lower(), city_norm)
    if actual_city not in CITY_COORDS:
        return None, "city_not_found"

    coords = CITY_COORDS[actual_city]
    cache = load_ndvi_cache()

    if not force_refresh and actual_city in cache:
        entry = cache[actual_city]
        if is_cache_fresh(entry):
            return entry['ndvi'], f"cache ({entry['source']})"

    token = get_copernicus_token()
    if not token:
        return None, "no_auth_token"

    ndvi, source = query_ndvi_for_city(coords['lat'], coords['lon'], token)

    if ndvi is not None:
        existing = load_ndvi_cache()
        existing[actual_city] = {
            'ndvi': ndvi,
            'timestamp': datetime.now().isoformat(),
            'source': source
        }
        save_ndvi_cache(existing)

    return ndvi, source


def estimate_ndvi_seasonal(month, lat):
    """
    Seasonal NDVI estimation (fallback when real data unavailable).
    Based on typical Portuguese vegetation cycles.

    NDVI ranges:
        Winter (11-4): high NDVI (0.50-0.65) = green vegetation
        Summer (6-9): low NDVI (0.22-0.35) = dry vegetation
        Spring/Autumn (5, 10): transition (0.30-0.50)
    """
    ndvi_by_month = {
        1: 0.65, 2: 0.60, 3: 0.55, 4: 0.50, 5: 0.45,
        6: 0.35, 7: 0.25, 8: 0.22, 9: 0.30, 10: 0.45,
        11: 0.55, 12: 0.62
    }

    lat_factor = (lat - 37.0) * 0.05

    base_ndvi = ndvi_by_month.get(month, 0.45)
    ndvi = base_ndvi - lat_factor

    return round(max(-0.1, min(1.0, ndvi)), 3)


def get_ndvi_with_fallback(city_name, month=None, lat=None):
    """
    Get NDVI with automatic fallback chain:
    1. Try Copernicus real NDVI
    2. Fall back to seasonal estimation

    Returns (ndvi_value, source_tag):
        ('real', <ndvi>) when Copernicus provides data
        ('estimated', <ndvi>) when using seasonal fallback
    """
    if month is None:
        month = datetime.now().month

    ndvi, source = get_ndvi(city_name)

    if ndvi is not None:
        return ndvi, "real"

    if lat is None:
        import unicodedata
        city_norm = unicodedata.normalize('NFKD', city_name).encode('ASCII', 'ignore').decode('utf-8')
        city_map = {unicodedata.normalize('NFKD', k).encode('ASCII', 'ignore').decode('utf-8').lower(): k
                    for k in CITY_COORDS}
        actual_city = city_map.get(city_norm.lower(), city_norm)
        coords = CITY_COORDS.get(actual_city, {'lat': 40.0})
        lat = coords['lat']

    est_ndvi = estimate_ndvi_seasonal(month, lat)
    return est_ndvi, "estimated"


_ndvi_cache_memory = None
_ndvi_cache_time = None


def fetch_all_ndvi(force_refresh=False):
    """
    Fetch NDVI for ALL Portuguese cities from Copernicus Sentinel-2.
    Results are cached to CSV.

    Returns dict: {city_name: {ndvi: float, source: str}}
                 source = 'real' (Copernicus) or 'estimated' (seasonal)
    """
    global _ndvi_cache_memory, _ndvi_cache_time

    if not force_refresh and _ndvi_cache_memory and _ndvi_cache_time:
        if (datetime.now() - _ndvi_cache_time).total_seconds() < CACHE_TTL_HOURS * 3600:
            return _ndvi_cache_memory

    results = {}
    token = get_copernicus_token()

    if not token:
        print("[NDVI] No Copernicus token available. Using seasonal estimates.")
        month = datetime.now().month
        for city, coords in CITY_COORDS.items():
            ndvi = estimate_ndvi_seasonal(month, coords['lat'])
            results[city] = {'ndvi': ndvi, 'source': 'estimated'}
        return results

    print(f"[NDVI] Fetching NDVI for {len(CITY_COORDS)} cities from Copernicus Sentinel-2...")
    success_count = 0
    fallback_count = 0

    for i, (city, coords) in enumerate(CITY_COORDS.items()):
        ndvi, source = query_ndvi_for_city(coords['lat'], coords['lon'], token)

        if ndvi is not None:
            results[city] = {'ndvi': ndvi, 'source': 'real'}
            success_count += 1
            print(f"  [{i+1}/{len(CITY_COORDS)}] {city}: NDVI={ndvi:.3f} (real)")
        else:
            month = datetime.now().month
            est = estimate_ndvi_seasonal(month, coords['lat'])
            results[city] = {'ndvi': est, 'source': 'estimated'}
            fallback_count += 1
            print(f"  [{i+1}/{len(CITY_COORDS)}] {city}: Copernicus unavailable ({source}), using seasonal ({est:.3f})")

        if i < len(CITY_COORDS) - 1:
            time.sleep(0.5)

    # Save to CSV cache
    cache_data = {}
    for city, data in results.items():
        cache_data[city] = {
            'ndvi': data['ndvi'],
            'timestamp': datetime.now().isoformat(),
            'source': data['source']
        }
    save_ndvi_cache(cache_data)

    _ndvi_cache_memory = results
    _ndvi_cache_time = datetime.now()

    print(f"[NDVI] Done: {success_count} real, {fallback_count} estimated")
    return results


def get_ndvi_for_all_cities():
    """
    Get NDVI for all cities using cache (fast, no API calls).
    Returns dict: {city_name: ndvi_value}
    """
    cache = load_ndvi_cache()
    month = datetime.now().month
    results = {}

    for city, coords in CITY_COORDS.items():
        if city in cache and is_cache_fresh(cache[city]):
            results[city] = cache[city]['ndvi']
        else:
            results[city] = estimate_ndvi_seasonal(month, coords['lat'])

    return results


if __name__ == '__main__':
    print("=" * 70)
    print("EMBEREDGE - REAL NDVI FROM COPERNICUS SENTINEL-2")
    print("=" * 70)

    results = fetch_all_ndvi(force_refresh=True)

    print("\nNDVI RESULTS:")
    print(f"{'City':20s} {'NDVI':6s} {'Source':10s}")
    print("-" * 40)
    for city in sorted(results, key=lambda c: results[c]['ndvi']):
        data = results[city]
        src_icon = "REAL" if data['source'] == 'real' else "EST"
        print(f"  {city:20s} {data['ndvi']:.3f}  {src_icon}")

    print("\n" + "=" * 70)
    print("NDVI UPDATE COMPLETE!")
    print("=" * 70)