#!/usr/bin/env python3
"""
EmberEdge - Model Training Script
Train Random Forest with 500 trees using real historical data + generated weather
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
from datetime import datetime
import json
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
HIST_CSV = os.path.join(DATA_DIR, 'fires', 'historical_fires.csv')
MODEL_PATH = os.path.join(DATA_DIR, 'risk_model.pkl')
META_PATH = os.path.join(DATA_DIR, 'model_metadata.json')

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

def generate_weather_for_fire(month, lat, lon, area_hectares):
    """Generate realistic weather data based on month, location, and fire intensity"""
    # Base temperature by month (Portugal climate)
    temp_by_month = {1: 12, 2: 13, 3: 15, 4: 17, 5: 20, 6: 24, 7: 27, 8: 27, 9: 24, 10: 20, 11: 16, 12: 13}
    # Base humidity by month
    humid_by_month = {1: 80, 2: 75, 3: 70, 4: 65, 5: 60, 6: 50, 7: 45, 8: 45, 9: 55, 10: 65, 11: 75, 12: 80}
    # Base wind by month
    wind_by_month = {1: 15, 2: 15, 3: 18, 4: 20, 5: 22, 6: 25, 7: 28, 8: 28, 9: 22, 10: 20, 11: 18, 12: 15}

    # Latitude factor (north is cooler)
    lat_factor = (lat - 39.0) * 2

    # Temperature: base + latitude adjustment + random variation
    temperature = temp_by_month[month] - lat_factor + np.random.normal(0, 3)

    # Humidity: base + random variation (fires have lower humidity)
    # Larger fires tend to have lower humidity
    humidity_base = humid_by_month[month] + np.random.normal(0, 10)
    if area_hectares > 1000:
        humidity_base -= 10  # Large fires = very dry
    elif area_hectares > 100:
        humidity_base -= 5
    humidity = max(10, min(100, humidity_base))

    # Wind: base + random variation (larger fires may have stronger winds)
    wind_speed = wind_by_month[month] + np.random.normal(0, 5)
    if area_hectares > 1000:
        wind_speed += 5
    wind_speed = max(5, wind_speed)

    # Precipitation: higher in winter months
    if month in [10, 11, 12, 1, 2, 3]:
        precipitation = max(0, np.random.exponential(2))
    else:
        precipitation = 0

    return {
        'temperature': round(temperature, 1),
        'humidity': round(humidity),
        'wind_speed': round(wind_speed, 1),
        'precipitation': round(precipitation, 1)
    }

def create_label(area_hectares):
    """Create risk label based on burned area"""
    if area_hectares > 1000:
        return 2  # Alto
    elif area_hectares > 100:
        return 1  # Medio
    else:
        return 0  # Baixo

def train_model():
    print("\n" + "=" * 70)
    print("EMBEREDGE - TRAINING RANDOM FOREST (500 TREES)")
    print("=" * 70)

    print(f"\n[DATA] Loading {HIST_CSV}...")
    df = pd.read_csv(HIST_CSV)
    print(f"       Loaded {len(df)} records")

    print("\n[FEATURES] Generating features with weather data...")
    features = []
    labels = []

    for _, row in df.iterrows():
        month = int(row['month'])
        city = row['district']
        area = float(row['area_hectares'])

        coords = CITY_COORDS.get(city, {'lat': 40.0, 'lon': -8.0})
        weather = generate_weather_for_fire(month, coords['lat'], coords['lon'], area)

        feature = [
            weather['temperature'],
            weather['humidity'],
            weather['wind_speed'],
            weather['precipitation'],
            month,
            coords['lat'],
            coords['lon']
        ]

        features.append(feature)
        labels.append(create_label(area))

    X = np.array(features)
    y = np.array(labels)

    print(f"       Features shape: {X.shape}")
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

    print(f"\n[RESULTS] Accuracy: {accuracy * 100:.1f}%")
    print("\n[REPORT] Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Baixo', 'Medio', 'Alto']))

    print("\n[IMPORTANCE] Feature Importance:")
    feature_names = ['temperature', 'humidity', 'wind_speed', 'precipitation', 'month', 'lat', 'lon']
    for name, imp in zip(feature_names, rf.feature_importances_):
        print(f"   {name}: {imp:.3f}")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(rf, MODEL_PATH)
    print(f"\n[MODEL] Saved to: {MODEL_PATH}")

    metadata = {
        'accuracy': round(accuracy, 4),
        'n_trees': 500,
        'n_features': 7,
        'feature_names': feature_names,
        'training_date': datetime.now().isoformat(),
        'n_samples': len(X),
        'class_distribution': {
            'baixo': int(sum(y==0)),
            'medio': int(sum(y==1)),
            'alto': int(sum(y==2))
        }
    }
    with open(META_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"[META] Saved to: {META_PATH}")

    print("\n" + "=" * 70)
    print("TRAINING COMPLETE!")
    print("=" * 70)

    return rf, accuracy

if __name__ == '__main__':
    train_model()
