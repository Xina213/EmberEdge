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
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
MODEL_PATH = os.path.join(DATA_DIR, 'risk_model.pkl')
FIRE_BURDEN_PATH = os.path.join(DATA_DIR, 'fire_burden.json')

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

# Load fire burden from training data, or fallback
FIRE_BURDEN = {}
if os.path.exists(FIRE_BURDEN_PATH):
    import json
    with open(FIRE_BURDEN_PATH, 'r') as f:
        FIRE_BURDEN = json.load(f)


def get_fire_burden(city_name):
    """Get fire burden for a city, default 0.5 for unknown cities."""
    return FIRE_BURDEN.get(normalize_city(city_name), 0.5)


# NDVI via sentinel_ndvi (real Copernicus data with seasonal fallback)
def estimate_ndvi(month, lat, fire_burden=0.5):
    """
    Estimate NDVI matching train_model.py formula:
    fire_burden dominated + city_baseline × seasonal interaction.

    The real Copernicus baseline is added separately by get_ndvi_for_city().
    """
    seasonal = 0.50 - 0.50 * np.cos((month - 1) * 2 * np.pi / 12)
    ndvi = fire_burden * 0.80 + seasonal * 0.20
    return round(max(0.05, min(0.95, ndvi)), 3)


def get_ndvi_for_city(city_name, month=None, lat=None):
    """
    Get NDVI for a city using the cache chain:
    1. Real Copernicus Sentinel-2 data (via sentinel_ndvi)
    2. Offset-adjusted seasonal estimate (cache snapshot + seasonal cycle)
    3. Pure seasonal estimate with fire burden

    Returns (ndvi_value, is_real) where is_real is True for Copernicus data.
    """
    if month is None:
        month = datetime.now().month

    # Use sentinel_ndvi module (real Copernicus data with fallback)
    try:
        from sentinel_ndvi import get_ndvi_with_fallback
        ndvi, source = get_ndvi_with_fallback(city_name, month, lat)
        if source == "real":
            return ndvi, True
    except Exception:
        pass

    if lat is None:
        coords = CITY_COORDS.get(normalize_city(city_name), {'lat': 40.0})
        lat = coords['lat']

    burden = get_fire_burden(city_name)

    # If we have a cached NDVI value, compute city offset from May estimate
    try:
        from sentinel_ndvi import get_ndvi_cache_simple
        cache = get_ndvi_cache_simple()
        city_norm = normalize_city(city_name)
        if city_norm in cache:
            cached_ndvi = cache[city_norm]
            may_estimate = estimate_ndvi(5, lat, burden)
            city_offset = cached_ndvi - may_estimate
            ndvi = estimate_ndvi(month, lat, burden) + city_offset
            return round(max(0.05, min(0.95, ndvi)), 3), True
        for cached_city, cached_ndvi_val in cache.items():
            if normalize_city(cached_city) == city_norm:
                may_estimate = estimate_ndvi(5, lat, burden)
                city_offset = cached_ndvi_val - may_estimate
                ndvi = estimate_ndvi(month, lat, burden) + city_offset
                return round(max(-0.05, min(1.0, ndvi)), 3), True
    except Exception:
        pass

    # Pure seasonal fallback
    ndvi = estimate_ndvi(month, lat, burden)
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
            overridden = False

            # Safety override: extreme conditions the model never saw in training
            # Random Forest doesn't extrapolate; these rules catch edge cases
            if temperature >= 40 or (temperature >= 35 and humidity <= 20) or (temperature >= 30 and humidity <= 15 and wind_speed >= 40):
                prediction = 2  # Alto
                overridden = True
            elif temperature >= 30 and humidity <= 30 and prediction < 1:
                prediction = 1  # Medio (at least)
                overridden = True

            # When override is active, confidence reflects the rule certainty, not the model's
            if overridden:
                override_conf = 95.0
            else:
                override_conf = float(probabilities[prediction] * 100)

            result = {
                'risk_level': self.risk_labels[prediction],
                'risk_value': int(prediction),
                'confidence': override_conf,
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