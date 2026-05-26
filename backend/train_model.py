#!/usr/bin/env python3
"""
EmberEdge - Model Training Script
Train Random Forest with 500 trees using REAL data.

Data sources:
  - Historical fires: ICNF (Portugal, 2000-2023) — real
  - Weather: ERA5 (ECMWF reanalysis) — real
  - NDVI: Copernicus Sentinel-2 cache when available, seasonal estimation otherwise

IMPORTANT: NDVI is estimated based on seasonal patterns and latitude when
real satellite data is unavailable. There is NO data leakage — NDVI is
computed independently of fire area.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os
from datetime import datetime
import json
import unicodedata

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
HIST_CSV = os.path.join(DATA_DIR, 'fires', 'historical_fires.csv')
ERA5_CSV = os.path.join(DATA_DIR, 'weather_historical_era5.csv')
MODEL_PATH = os.path.join(DATA_DIR, 'risk_model.pkl')
META_PATH = os.path.join(DATA_DIR, 'model_metadata.json')
NDVI_CACHE = os.path.join(DATA_DIR, 'ndvi_cache.csv')

# City coordinates
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

NDVI_CACHE_CITIES = {}


def normalize_text(text):
    """Remove accents and convert to standard form"""
    if not text:
        return text
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    return text.strip().title()


def load_ndvi_cache():
    """Load cached real NDVI values from Copernicus Sentinel-2."""
    global NDVI_CACHE_CITIES
    if NDVI_CACHE_CITIES:
        return NDVI_CACHE_CITIES

    if not os.path.exists(NDVI_CACHE):
        print("[NDVI] No cache file found. Will use seasonal estimates.")
        NDVI_CACHE_CITIES = {}
        return NDVI_CACHE_CITIES

    try:
        import csv
        now = datetime.now()
        cache_ttl = 72 * 3600  # 72 hours for training

        with open(NDVI_CACHE, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                try:
                    cached_time = datetime.fromisoformat(row['timestamp'])
                    age = (now - cached_time).total_seconds()
                    if age < cache_ttl:
                        NDVI_CACHE_CITIES[row['city']] = float(row['ndvi'])
                except (ValueError, KeyError):
                    continue

        print(f"[NDVI] Loaded {len(NDVI_CACHE_CITIES)} cached NDVI values")
    except Exception as e:
        print(f"[NDVI] Warning: cache read error: {e}")
        NDVI_CACHE_CITIES = {}

    return NDVI_CACHE_CITIES


def estimate_ndvi(month, lat):
    """
    Generate realistic NDVI based on seasonal patterns and latitude (Portugal).
    NO dependency on fire area — this is purely seasonal/geographic.

    NDVI ranges: -1 to 1
    - High: 0.6-0.9 = dense green vegetation (winter/spring)
    - Medium: 0.3-0.6 = moderate vegetation (spring/autumn)
    - Low: 0.1-0.3 = sparse/dry vegetation (summer) - HIGH FIRE RISK
    """
    ndvi_by_month = {
        1: 0.65, 2: 0.60, 3: 0.55, 4: 0.50, 5: 0.45,
        6: 0.35, 7: 0.25, 8: 0.22, 9: 0.30, 10: 0.45,
        11: 0.55, 12: 0.62
    }

    lat_factor = (lat - 37.0) * 0.05
    ndvi = ndvi_by_month.get(month, 0.45) - lat_factor

    # Small random variation to reflect real NDVI variability
    # (actual NDVI varies due to soil type, land use, etc.)
    ndvi += np.random.normal(0, 0.05)

    return round(max(-0.1, min(1.0, ndvi)), 3)


def generate_ndvi(month, lat, city_name):
    """
    Generate NDVI for training, checking real cache first.
    """
    ndvi_cache = load_ndvi_cache()

    # Try real NDVI from cache
    city_norm = normalize_text(city_name)
    if city_norm in ndvi_cache:
        return ndvi_cache[city_norm]

    # Try matching city names
    for cached_city, cached_ndvi in ndvi_cache.items():
        if normalize_text(cached_city) == city_norm:
            return cached_ndvi

    # Fallback to seasonal estimate (NO area-based adjustment)
    return estimate_ndvi(month, lat)


def load_era5_data():
    """Load ERA5 historical weather data"""
    if not os.path.exists(ERA5_CSV):
        print(f"[WARN] ERA5 data not found: {ERA5_CSV}")
        return None

    print(f"[ERA5] Loading {ERA5_CSV}...")
    df = pd.read_csv(ERA5_CSV)
    df['city_normalized'] = df['city'].apply(normalize_text)

    print(f"       Loaded {len(df)} records")
    print(f"       Cities: {df['city'].nunique()}")
    return df


def create_label(area_hectares):
    """
    Create risk label based on burned area.

    Thresholds defined based on ICNF historical analysis:
    - < 100 ha: small fire → Baixo (0)
    - 100-1000 ha: medium fire → Medio (1)
    - > 1000 ha: large fire → Alto (2)

    Reference: https://fogos.icnf.pt/ - annual statistical reports
    """
    if area_hectares > 1000:
        return 2  # Alto
    elif area_hectares > 100:
        return 1  # Medio
    else:
        return 0  # Baixo


def train_model():
    print("\n" + "=" * 70)
    print("EMBEREDGE - TRAINING RANDOM FOREST (500 TREES)")
    print("Data sources: ERA5 (real) + ICNF (real) + NDVI (Copernicus/seasonal)")
    print("=" * 70)

    # Load historical fire data (real ICNF data)
    print(f"\n[DATA] Loading {HIST_CSV}...")
    df_fires = pd.read_csv(HIST_CSV)
    print(f"       Loaded {len(df_fires)} fire records (ICNF 2000-2023)")

    df_fires['district_normalized'] = df_fires['district'].apply(normalize_text)

    # Load ERA5 weather data (real climate data)
    df_weather = load_era5_data()

    if df_weather is None:
        print("\n[ERROR] Cannot proceed without ERA5 data!")
        print("        Run: python fetch_era5.py first")
        return None, 0

    print(f"\n[FEATURES] Merging fire data with REAL ERA5 weather...")

    # Load NDVI cache
    load_ndvi_cache()

    features = []
    labels = []

    # Group ERA5 data by normalized city for faster lookup
    weather_groups = df_weather.groupby(['city_normalized', 'year', 'month'])

    matched = 0
    skipped = 0

    for _, row in df_fires.iterrows():
        year = int(row['year'])
        month = int(row['month'])
        city = row['district']
        city_norm = normalize_text(city)
        area = float(row['area_hectares'])

        coords = CITY_COORDS.get(city_norm, {'lat': 40.0, 'lon': -8.0})

        # Get REAL weather from ERA5
        try:
            weather = weather_groups.get_group((city_norm, year, month))
            temperature = float(weather.iloc[0]['temperature'])
            humidity = float(weather.iloc[0]['humidity'])
            wind_speed = float(weather.iloc[0]['wind_speed'])
            precipitation = float(weather.iloc[0]['precipitation'])
        except KeyError:
            try:
                weather = df_weather[
                    (df_weather['city'] == city) &
                    (df_weather['year'] == year) &
                    (df_weather['month'] == month)
                ]
                if len(weather) > 0:
                    temperature = float(weather.iloc[0]['temperature'])
                    humidity = float(weather.iloc[0]['humidity'])
                    wind_speed = float(weather.iloc[0]['wind_speed'])
                    precipitation = float(weather.iloc[0]['precipitation'])
                else:
                    skipped += 1
                    continue
            except Exception:
                skipped += 1
                continue

        # NDVI: try real cache first, fall back to seasonal estimate
        # NO area-based adjustment = no data leakage
        ndvi = generate_ndvi(month, coords['lat'], city_norm)

        feature = [
            temperature,
            humidity,
            wind_speed,
            precipitation,
            month,
            coords['lat'],
            coords['lon'],
            ndvi
        ]

        features.append(feature)
        labels.append(create_label(area))
        matched += 1

    X = np.array(features)
    y = np.array(labels)

    print(f"\n[DATA] Matched: {matched}, Skipped: {skipped}")
    print(f"       Final dataset: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"       Class distribution: Baixo={sum(y==0)}, Medio={sum(y==1)}, Alto={sum(y==2)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("\n[TRAINING] Training RandomForest with 500 trees...")
    rf = RandomForestClassifier(
        n_estimators=500,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    rf.fit(X_train, y_train)

    y_pred = rf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\n[RESULTS] Overall Accuracy: {accuracy * 100:.1f}%")
    print("\n[CLASSIFICATION REPORT]:")
    print(classification_report(y_test, y_pred, target_names=['Baixo', 'Medio', 'Alto']))

    print("\n[CONFUSION MATRIX]:")
    cm = confusion_matrix(y_test, y_pred)
    print("              Previsto:")
    print("              Baixo  Medio  Alto")
    for i, row_name in enumerate(['Baixo', 'Medio', 'Alto']):
        print(f"   Real {row_name:6s}", end="")
        for val in cm[i]:
            print(f" {val:5d}", end="")
        print()

    print("\n[IMPORTANCE] Feature Importance:")
    feature_names = ['temperature', 'humidity', 'wind_speed', 'precipitation', 'month', 'lat', 'lon', 'ndvi']
    for name, imp in zip(feature_names, rf.feature_importances_):
        marker = " <<<" if imp == max(rf.feature_importances_) else ""
        print(f"   {name}: {imp:.3f}{marker}")

    # ===== BASELINE COMPARISON =====
    # Simple rule-based model to prove ML adds value
    def rule_baseline_predict(t, h, w):
        if t > 30 and h < 30:
            return 2
        elif t > 25 and h < 50:
            return 1
        return 0

    y_baseline = np.array([rule_baseline_predict(X_test[i,0], X_test[i,1], X_test[i,2]) for i in range(len(X_test))])
    baseline_acc = accuracy_score(y_test, y_baseline)
    print(f"\n[BASELINE] Rule-based accuracy: {baseline_acc * 100:.1f}%")
    print(f"[BASELINE] ML improvement: {(accuracy - baseline_acc) * 100:.1f}%")

    # Per-class metrics
    from sklearn.metrics import precision_recall_fscore_support
    per_class = precision_recall_fscore_support(y_test, y_pred, labels=[0, 1, 2])
    baseline_per_class = precision_recall_fscore_support(y_test, y_baseline, labels=[0, 1, 2])
    class_metrics = {}
    for i, class_name in enumerate(['baixo', 'medio', 'alto']):
        class_metrics[class_name] = {
            'precision': round(per_class[0][i], 4),
            'recall': round(per_class[1][i], 4),
            'f1_score': round(per_class[2][i], 4),
            'support': int(per_class[3][i])
        }

    # Confusion matrix as percentages for visual display
    cm = confusion_matrix(y_test, y_pred)
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    class_names_list = ['baixo', 'medio', 'alto']
    confusion_data = {}
    for i, true_class in enumerate(class_names_list):
        confusion_data[true_class] = {}
        for j, pred_class in enumerate(class_names_list):
            confusion_data[true_class][pred_class] = {
                'count': int(cm[i][j]),
                'pct': round(float(cm_normalized[i][j]) * 100, 1)
            }

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(rf, MODEL_PATH)
    print(f"\n[MODEL] Saved to: {MODEL_PATH}")

    # Count real NDVI usage
    ndvi_cache = load_ndvi_cache()
    ndvi_real_count = len(ndvi_cache)
    ndvi_estimated_cities = len(CITY_COORDS) - ndvi_real_count

    metadata = {
        'accuracy': round(accuracy, 4),
        'n_trees': 500,
        'n_features': 8,
        'feature_names': feature_names,
        'feature_importance': {
            name: round(float(imp), 4)
            for name, imp in zip(feature_names, rf.feature_importances_)
        },
        'training_date': datetime.now().isoformat(),
        'n_samples': len(X),
        'class_distribution': {
            'baixo': int(sum(y==0)),
            'medio': int(sum(y==1)),
            'alto': int(sum(y==2))
        },
        'class_metrics': class_metrics,
        'confusion_matrix': confusion_data,
        'baseline': {
            'description': 'Rule-based: if temp>30 and hum<30 → Alto, elif temp>25 and hum<50 → Medio',
            'accuracy': round(float(baseline_acc), 4),
            'ml_improvement': round(float(accuracy - baseline_acc), 4)
        },
        'weather_source': 'ERA5 (ECMWF reanalysis) - 100% real',
        'fire_source': 'ICNF (Portugal 2000-2023) - 100% real',
        'ndvi_source': {
            'description': 'Copernicus Sentinel-2 (cached) when available, seasonal estimation otherwise',
            'cached_real_cities': ndvi_real_count,
            'estimated_cities': ndvi_estimated_cities,
            'no_data_leakage': True
        },
        'thresholds': {
            'baixo': 'area < 100 ha',
            'medio': '100 ha <= area <= 1000 ha',
            'alto': 'area > 1000 ha'
        }
    }
    with open(META_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"[META] Saved to: {META_PATH}")

    print("\n" + "=" * 70)
    print("TRAINING COMPLETE!")
    print("=" * 70)
    print(f"Data: ERA5 (real) + ICNF (real) + NDVI (Copernicus/seasonal)")
    print(f"Overall Accuracy: {accuracy * 100:.1f}%")
    print("=" * 70)

    return rf, accuracy


if __name__ == '__main__':
    train_model()