#!/usr/bin/env python3
"""
EmberEdge - Risk Predictor
Random Forest model with 8 features: temperature, humidity, wind_speed,
precipitation, month, latitude, longitude, NDVI.

NDVI (Normalized Difference Vegetation Index):
  - Real values from Copernicus Sentinel-2 when available (cached)
  - Seasonal estimation as fallback (based on Portuguese vegetation cycles)
"""

import joblib
import numpy as np
from datetime import datetime

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, '..', 'data', 'risk_model.pkl')

# Mapping of city names to coordinates
CITY_ALIASES = {
    'Lisbon': 'Lisboa', 'Porto': 'Porto', 'Coimbra': 'Coimbra',
    'Braga': 'Braga', 'Faro': 'Faro', 'Evora': 'Evora',
    'Guarda': 'Guarda', 'Beja': 'Beja', 'Viseu': 'Viseu',
    'Aveiro': 'Aveiro', 'Setubal': 'Setubal', 'Leiria': 'Leiria',
    'Santarem': 'Santarem', 'Castelo Branco': 'Castelo Branco',
    'Vila Real': 'Vila Real', 'Braganca': 'Braganca', 'Bragança': 'Braganca',
    'Viana do Castelo': 'Viana do Castelo', 'Portalegre': 'Portalegre',
    'Funchal': 'Funchal', 'Ponta Delgada': 'Ponta Delgada',
    'Cascais': 'Cascais', 'Sintra': 'Sintra',
    'Almada': 'Almada', 'Matosinhos': 'Matosinhos',
    'Vila Nova de Gaia': 'Vila Nova de Gaia', 'Loures': 'Loures',
    'Odivelas': 'Odivelas', 'Gondomar': 'Gondomar',
    'Amadora': 'Amadora', 'Barreiro': 'Barreiro',
    'Tomar': 'Tomar', 'Caldas da Rainha': 'Caldas da Rainha',
    'Figueira da Foz': 'Figueira da Foz', 'Covilha': 'Covilha'
}

def normalize_city(name):
    """Normalize city name (remove accents, English to Portuguese, lowercase to title case)"""
    if not name:
        return name
    import unicodedata
    name = name.strip().title()
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
    return CITY_ALIASES.get(name, name)

# City coordinates
CITY_COORDS = {
    'Aveiro': {'lat': 40.64, 'lon': -8.65},
    'Beja': {'lat': 38.02, 'lon': -7.87},
    'Braga': {'lat': 41.55, 'lon': -8.42},
    'Braganca': {'lat': 41.81, 'lon': -6.76},
    'Caldas da Rainha': {'lat': 39.40, 'lon': -9.14},
    'Castelo Branco': {'lat': 39.82, 'lon': -7.49},
    'Coimbra': {'lat': 40.21, 'lon': -8.43},
    'Covilha': {'lat': 40.28, 'lon': -7.50},
    'Evora': {'lat': 38.57, 'lon': -7.91},
    'Faro': {'lat': 37.02, 'lon': -7.93},
    'Figueira da Foz': {'lat': 40.14, 'lon': -8.86},
    'Funchal': {'lat': 32.67, 'lon': -16.92},
    'Guarda': {'lat': 40.54, 'lon': -7.27},
    'Leiria': {'lat': 39.75, 'lon': -8.81},
    'Lisboa': {'lat': 38.72, 'lon': -9.14},
    'Portalegre': {'lat': 39.30, 'lon': -7.43},
    'Ponta Delgada': {'lat': 37.74, 'lon': -25.68},
    'Porto': {'lat': 41.16, 'lon': -8.62},
    'Santarem': {'lat': 39.24, 'lon': -8.69},
    'Setubal': {'lat': 38.52, 'lon': -8.89},
    'Tomar': {'lat': 39.60, 'lon': -8.41},
    'Viana do Castelo': {'lat': 41.69, 'lon': -8.83},
    'Vila Real': {'lat': 41.30, 'lon': -7.74},
    'Viseu': {'lat': 40.66, 'lon': -7.91},
    'Cascais': {'lat': 38.70, 'lon': -9.42},
    'Sintra': {'lat': 38.80, 'lon': -9.38},
    'Almada': {'lat': 38.68, 'lon': -9.16},
    'Matosinhos': {'lat': 41.18, 'lon': -8.69},
    'Vila Nova de Gaia': {'lat': 41.13, 'lon': -8.62},
    'Loures': {'lat': 38.83, 'lon': -9.17},
    'Odivelas': {'lat': 38.79, 'lon': -9.18},
    'Gondomar': {'lat': 41.14, 'lon': -8.53},
    'Amadora': {'lat': 38.75, 'lon': -9.23},
    'Barreiro': {'lat': 38.66, 'lon': -9.07},
}

# Load NDVI cache on import (lazy, for fallback only)
_ndvi_cache = None
_ndvi_cache_loaded = False


def _load_ndvi_cache():
    """Load the NDVI cache CSV into memory."""
    global _ndvi_cache, _ndvi_cache_loaded
    if _ndvi_cache_loaded:
        return _ndvi_cache

    _ndvi_cache_loaded = True
    cache_path = os.path.join(BASE_DIR, '..', 'data', 'ndvi_cache.csv')

    if not os.path.exists(cache_path):
        _ndvi_cache = {}
        return _ndvi_cache

    try:
        import csv
        _ndvi_cache = {}
        cache_ttl = 24 * 3600  # 24 hours
        now = datetime.now()

        with open(cache_path, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                try:
                    cached_time = datetime.fromisoformat(row['timestamp'])
                    age = (now - cached_time).total_seconds()
                    if age < cache_ttl:
                        _ndvi_cache[row['city']] = float(row['ndvi'])
                except (ValueError, KeyError):
                    continue
    except Exception:
        _ndvi_cache = {}

    return _ndvi_cache


def estimate_ndvi(month, lat):
    """
    Estimate NDVI based on seasonal patterns (Portugal vegetation cycle).
    Used when real Copernicus NDVI is unavailable.

    Summer (6-9): low NDVI = dry vegetation = higher fire risk
    Winter/Spring (11-4): higher NDVI = green vegetation = lower risk
    """
    ndvi_by_month = {
        1: 0.65, 2: 0.60, 3: 0.55, 4: 0.50, 5: 0.45,
        6: 0.35, 7: 0.25, 8: 0.22, 9: 0.30, 10: 0.45,
        11: 0.55, 12: 0.62
    }

    # Latitude factor: south is drier (lower NDVI)
    lat_factor = (lat - 37.0) * 0.05
    ndvi = ndvi_by_month.get(month, 0.45) - lat_factor

    return round(max(-0.1, min(1.0, ndvi)), 3)


def get_ndvi_for_city(city_name, month=None, lat=None):
    """
    Get NDVI for a city using the cache chain:
    1. Check Copernicus real NDVI cache (24h TTL)
    2. Fall back to seasonal estimation

    Returns (ndvi_value, is_real) where is_real is True for cached Copernicus data.
    """
    if month is None:
        month = datetime.now().month

    # Step 1: Try real NDVI cache
    cache = _load_ndvi_cache()
    import unicodedata
    city_norm = unicodedata.normalize('NFKD', city_name).encode('ASCII', 'ignore').decode('utf-8')

    for cached_city, cached_ndvi in cache.items():
        cached_norm = unicodedata.normalize('NFKD', cached_city).encode('ASCII', 'ignore').decode('utf-8')
        if cached_norm.lower() == city_norm.lower():
            return cached_ndvi, True

    # Step 2: Fallback to seasonal estimation
    if lat is None:
        coords = CITY_COORDS.get(normalize_city(city_name), {'lat': 40.0})
        lat = coords['lat']

    ndvi = estimate_ndvi(month, lat)
    return ndvi, False


class RiskPredictor:
    def __init__(self):
        self.model = None
        self.risk_labels = ['Baixo', 'Medio', 'Alto']
        self.load_model()

    def load_model(self):
        """Load trained model (8 features with NDVI)"""
        try:
            self.model = joblib.load(MODEL_PATH)
            print(f"[OK] Model loaded (8 features with NDVI): {MODEL_PATH}")
        except FileNotFoundError:
            print(f"[WARN] Model not found: {MODEL_PATH}")
            self.model = None

    def predict(self, temperature, humidity, wind_speed, precipitation, city_name, month=None, ndvi=None):
        """
        Predict fire risk with 8 features (including NDVI).

        NDVI is sourced from:
          - Copernicus Sentinel-2 cache (real satellite data) if available
          - Seasonal estimation otherwise

        Args:
            temperature: Temperature in C
            humidity: Humidity in %
            wind_speed: Wind speed in km/h
            precipitation: Precipitation in mm
            city_name: City name (for lat/lon)
            month: Month (1-12), if None uses current month
            ndvi: NDVI value (-1 to 1), if None auto-detects from cache or estimates
        """
        if self.model is None:
            return self._fallback_prediction(temperature, humidity)

        try:
            # Normalize city name
            city_name = normalize_city(city_name)

            # Get city coordinates
            coords = CITY_COORDS.get(city_name, {'lat': 40.0, 'lon': -8.0})
            lat = coords['lat']
            lon = coords['lon']

            # Get current month if not provided
            if month is None:
                month = datetime.now().month

            # Get NDVI: use provided value, or auto-detect from cache/fallback
            ndvi_source = "provided"
            if ndvi is None:
                ndvi, is_real = get_ndvi_for_city(city_name, month, lat)
                ndvi_source = "real (Copernicus)" if is_real else "estimated (seasonal)"

            # Create feature array in correct order (8 features)
            features = np.array([[
                temperature,
                humidity,
                wind_speed,
                precipitation,
                month,
                lat,
                lon,
                ndvi
            ]])

            # Prediction
            prediction = self.model.predict(features)[0]
            probabilities = self.model.predict_proba(features)[0]

            result = {
                'risk_level': self.risk_labels[prediction],
                'risk_value': int(prediction),
                'confidence': float(probabilities[prediction] * 100),
                'probabilities': {
                    'baixo': float(probabilities[0] * 100),
                    'medio': float(probabilities[1] * 100),
                    'alto': float(probabilities[2] * 100)
                },
                'city': city_name,
                'coordinates': {'lat': lat, 'lon': lon},
                'month': month,
                'ndvi': ndvi,
                'ndvi_source': ndvi_source  # New field: transparency about data origin
            }

            return result

        except Exception as e:
            print(f"[ERROR] Prediction error: {e}")
            return self._fallback_prediction(temperature, humidity)

    def _fallback_prediction(self, temperature, humidity):
        """Simple rule-based prediction if model fails"""
        if temperature > 30 and humidity < 30:
            risk = 'Alto'
            risk_value = 2
        elif temperature > 25 and humidity < 50:
            risk = 'Medio'
            risk_value = 1
        else:
            risk = 'Baixo'
            risk_value = 0

        return {
            'risk_level': risk,
            'risk_value': risk_value,
            'confidence': 70.0,
            'probabilities': {
                'baixo': 33.3,
                'medio': 33.3,
                'alto': 33.3
            },
            'city': 'Unknown',
            'coordinates': {'lat': 40.0, 'lon': -8.0},
            'month': datetime.now().month,
            'ndvi': 0.5,
            'ndvi_source': 'fallback (no model)'
        }


# Singleton instance
_predictor = None

def get_predictor():
    """Return singleton predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = RiskPredictor()
    return _predictor