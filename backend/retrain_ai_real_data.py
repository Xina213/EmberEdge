#!/usr/bin/env python3
"""
EmberEdge - AI Model Retraining with Real Historical Data
Retreina Random Forest com dados históricos reais 2000-2023
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os
from datetime import datetime

# Paths
HISTORICAL_FILE = '../data/fires/historical_fires.csv'
MODEL_OUTPUT = '../data/risk_model.pkl'
METADATA_OUTPUT = '../data/model_metadata.json'

# Mapeamento de distritos para coordenadas aproximadas
DISTRICT_COORDS = {
    'Aveiro': {'lat': 40.64, 'lon': -8.65, 'zone': 'litoral'},
    'Beja': {'lat': 38.02, 'lon': -7.87, 'zone': 'interior'},
    'Braga': {'lat': 41.55, 'lon': -8.42, 'zone': 'litoral'},
    'Bragança': {'lat': 41.81, 'lon': -6.76, 'zone': 'interior'},
    'Castelo Branco': {'lat': 39.82, 'lon': -7.49, 'zone': 'interior'},
    'Coimbra': {'lat': 40.21, 'lon': -8.43, 'zone': 'litoral'},
    'Évora': {'lat': 38.57, 'lon': -7.91, 'zone': 'interior'},
    'Faro': {'lat': 37.02, 'lon': -7.93, 'zone': 'litoral'},
    'Guarda': {'lat': 40.54, 'lon': -7.27, 'zone': 'interior'},
    'Leiria': {'lat': 39.75, 'lon': -8.81, 'zone': 'litoral'},
    'Lisboa': {'lat': 38.72, 'lon': -9.14, 'zone': 'litoral'},
    'Portalegre': {'lat': 39.30, 'lon': -7.43, 'zone': 'interior'},
    'Porto': {'lat': 41.16, 'lon': -8.62, 'zone': 'litoral'},
    'Santarém': {'lat': 39.24, 'lon': -8.69, 'zone': 'interior'},
    'Setúbal': {'lat': 38.52, 'lon': -8.89, 'zone': 'litoral'},
    'Viana do Castelo': {'lat': 41.69, 'lon': -8.83, 'zone': 'litoral'},
    'Vila Real': {'lat': 41.30, 'lon': -7.74, 'zone': 'interior'},
    'Viseu': {'lat': 40.66, 'lon': -7.91, 'zone': 'interior'}
}

def load_historical_data():
    """
    Carrega dados históricos
    """
    print("\n[LOAD] Carregando dados históricos...")
    
    if not os.path.exists(HISTORICAL_FILE):
        print(f"   [ERROR] Ficheiro não encontrado: {HISTORICAL_FILE}")
        return None
    
    df = pd.read_csv(HISTORICAL_FILE)
    print(f"   [SUCCESS] {len(df)} registos carregados")
    
    return df

def create_weather_features(df):
    """
    Cria features meteorológicas baseadas em padrões sazonais reais de Portugal
    """
    print("\n[FEATURES] Gerando features meteorológicas realistas...")
    
    # Temperatura média mensal em Portugal (baseado em dados IPMA)
    temp_by_month = {
        1: 12, 2: 13, 3: 15, 4: 17, 5: 20, 6: 24,
        7: 27, 8: 28, 9: 25, 10: 20, 11: 16, 12: 13
    }
    
    # Humidade média mensal
    humidity_by_month = {
        1: 78, 2: 75, 3: 72, 4: 70, 5: 65, 6: 60,
        7: 55, 8: 54, 9: 60, 10: 68, 11: 75, 12: 78
    }
    
    # Velocidade do vento média
    wind_by_month = {
        1: 15, 2: 16, 3: 17, 4: 16, 5: 14, 6: 13,
        7: 12, 8: 12, 9: 13, 10: 14, 11: 15, 12: 16
    }
    
    # Precipitação mensal (mm)
    precip_by_month = {
        1: 120, 2: 100, 3: 80, 4: 90, 5: 60, 6: 30,
        7: 10, 8: 5, 9: 40, 10: 100, 11: 120, 12: 130
    }
    
    # Aplica temperatura base + variação aleatória
    df['temperature'] = df['month'].map(temp_by_month) + np.random.normal(0, 3, len(df))
    
    # Ajuste interior/litoral (interior +2°C verão, -1°C inverno)
    for district, info in DISTRICT_COORDS.items():
        mask = df['district'] == district
        if info['zone'] == 'interior':
            summer_mask = df['month'].isin([6,7,8,9])
            df.loc[mask & summer_mask, 'temperature'] += 2
            winter_mask = df['month'].isin([12,1,2])
            df.loc[mask & winter_mask, 'temperature'] -= 1
    
    # Outras features
    df['humidity'] = df['month'].map(humidity_by_month) + np.random.normal(0, 5, len(df))
    df['wind_speed'] = df['month'].map(wind_by_month) + np.random.normal(0, 3, len(df))
    df['precipitation'] = df['month'].map(precip_by_month) + np.random.normal(0, 20, len(df))
    
    # Adiciona coordenadas
    df['lat'] = df['district'].map(lambda x: DISTRICT_COORDS.get(x, {}).get('lat', 40.0))
    df['lon'] = df['district'].map(lambda x: DISTRICT_COORDS.get(x, {}).get('lon', -8.0))
    df['zone'] = df['district'].map(lambda x: DISTRICT_COORDS.get(x, {}).get('zone', 'interior'))
    
    # Limita valores
    df['temperature'] = df['temperature'].clip(0, 45)
    df['humidity'] = df['humidity'].clip(20, 100)
    df['wind_speed'] = df['wind_speed'].clip(0, 50)
    df['precipitation'] = df['precipitation'].clip(0, 300)
    
    print(f"   [SUCCESS] Features criadas: temp, humidity, wind_speed, precipitation")
    
    return df

def create_risk_labels(df):
    """
    Cria labels de risco baseado em ocorrências reais
    """
    print("\n[LABELS] Criando labels de risco...")
    
    # Define thresholds baseados em dados reais
    # Percentis: 33% baixo, 33% médio, 33% alto
    low_threshold = df['count'].quantile(0.33)
    high_threshold = df['count'].quantile(0.67)
    
    print(f"   Thresholds: Baixo<{low_threshold:.0f}, Médio<{high_threshold:.0f}, Alto>={high_threshold:.0f}")
    
    def classify_risk(count):
        if count < low_threshold:
            return 0  # Baixo
        elif count < high_threshold:
            return 1  # Médio
        else:
            return 2  # Alto
    
    df['risk_level'] = df['count'].apply(classify_risk)
    
    # Conta distribuição
    risk_counts = df['risk_level'].value_counts().sort_index()
    print(f"   Distribuição:")
    print(f"      Baixo (0): {risk_counts.get(0, 0)}")
    print(f"      Médio (1): {risk_counts.get(1, 0)}")
    print(f"      Alto (2): {risk_counts.get(2, 0)}")
    
    return df

def train_model(df):
    """
    Treina Random Forest com dados reais
    """
    print("\n[TRAIN] Treinando modelo Random Forest...")
    
    # Features para treino
    feature_columns = ['temperature', 'humidity', 'wind_speed', 'precipitation', 
                       'month', 'lat', 'lon']
    
    X = df[feature_columns]
    y = df['risk_level']
    
    # Split treino/teste (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"   Treino: {len(X_train)} samples")
    print(f"   Teste: {len(X_test)} samples")
    
    # Treina Random Forest
    print("\n   [TRAINING] Random Forest (n_estimators=200)...")
    
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Avalia
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n   [ACCURACY] {accuracy*100:.2f}%")
    
    # Feature importance
    print("\n   [FEATURE IMPORTANCE]")
    feature_importance = sorted(
        zip(feature_columns, model.feature_importances_),
        key=lambda x: x[1],
        reverse=True
    )
    
    for feat, importance in feature_importance:
        print(f"      {feat}: {importance*100:.1f}%")
    
    # Classification report
    print("\n   [CLASSIFICATION REPORT]")
    print(classification_report(y_test, y_pred, 
                                target_names=['Baixo', 'Médio', 'Alto'],
                                zero_division=0))
    
    # Confusion matrix
    print("\n   [CONFUSION MATRIX]")
    cm = confusion_matrix(y_test, y_pred)
    print("              Previsto:")
    print("              Baixo  Médio  Alto")
    for i, row_name in enumerate(['Baixo', 'Médio', 'Alto']):
        print(f"   Real {row_name:6s}", end="")
        for val in cm[i]:
            print(f" {val:5d}", end="")
        print()
    
    return model, accuracy, feature_importance

def save_model(model, accuracy, feature_importance):
    """
    Salva modelo treinado
    """
    print(f"\n[SAVE] Salvando modelo...")
    
    # Salva modelo
    os.makedirs(os.path.dirname(MODEL_OUTPUT), exist_ok=True)
    joblib.dump(model, MODEL_OUTPUT)
    print(f"   [SUCCESS] Modelo salvo: {MODEL_OUTPUT}")
    
    # Salva metadata
    metadata = {
        'trained_date': datetime.now().isoformat(),
        'accuracy': float(accuracy),
        'model_type': 'RandomForestClassifier',
        'n_estimators': 200,
        'features': ['temperature', 'humidity', 'wind_speed', 'precipitation', 
                     'month', 'lat', 'lon'],
        'feature_importance': {feat: float(imp) for feat, imp in feature_importance},
        'data_source': 'ICNF Historical Data 2000-2023',
        'risk_levels': {
            0: 'Baixo',
            1: 'Médio',
            2: 'Alto'
        }
    }
    
    import json
    with open(METADATA_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"   [SUCCESS] Metadata salvo: {METADATA_OUTPUT}")

def test_predictions(model):
    """
    Testa predições com cenários reais
    """
    print("\n" + "="*70)
    print("TESTES DE PREDIÇÃO")
    print("="*70)
    
    test_cases = [
        {
            'name': 'Verão Seco - Guarda (Interior)',
            'features': [32, 30, 25, 5, 8, 40.54, -7.27],  # Temp, Hum, Wind, Precip, Month, Lat, Lon
            'expected': 'Alto'
        },
        {
            'name': 'Inverno Húmido - Porto (Litoral)',
            'features': [12, 80, 18, 120, 1, 41.16, -8.62],
            'expected': 'Baixo'
        },
        {
            'name': 'Primavera Moderada - Coimbra',
            'features': [20, 65, 15, 60, 5, 40.21, -8.43],
            'expected': 'Médio'
        },
        {
            'name': 'Pedrogão 2017 (Simulação)',
            'features': [40, 20, 35, 0, 6, 40.0, -8.0],
            'expected': 'Alto'
        }
    ]
    
    risk_names = ['Baixo', 'Médio', 'Alto']
    
    for i, test in enumerate(test_cases, 1):
        features = np.array([test['features']])
        prediction = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0]
        
        print(f"\n[TESTE {i}] {test['name']}")
        print(f"   Features: T={test['features'][0]}°C, H={test['features'][1]}%, " +
              f"W={test['features'][2]}km/h, P={test['features'][3]}mm, Mês={test['features'][4]}")
        print(f"   Predição: {risk_names[prediction]} ({probabilities[prediction]*100:.1f}% confiança)")
        print(f"   Probabilidades: Baixo={probabilities[0]*100:.1f}%, " +
              f"Médio={probabilities[1]*100:.1f}%, Alto={probabilities[2]*100:.1f}%")
        print(f"   Esperado: {test['expected']} {'✅' if risk_names[prediction] == test['expected'] else '⚠️'}")

def main():
    print("="*70)
    print("EMBEREDGE - AI MODEL RETRAINING")
    print("="*70)
    print("Dataset: Dados Históricos ICNF 2000-2023")
    print("Modelo: Random Forest Classifier")
    print("="*70)
    
    # 1. Carrega dados
    df = load_historical_data()
    if df is None:
        return
    
    # 2. Cria features meteorológicas
    df = create_weather_features(df)
    
    # 3. Cria labels de risco
    df = create_risk_labels(df)
    
    # 4. Treina modelo
    model, accuracy, feature_importance = train_model(df)
    
    # 5. Salva modelo
    save_model(model, accuracy, feature_importance)
    
    # 6. Testa predições
    test_predictions(model)
    
    print("\n" + "="*70)
    print("TREINO COMPLETO!")
    print("="*70)
    print(f"Accuracy: {accuracy*100:.2f}%")
    print(f"Modelo: {MODEL_OUTPUT}")
    print(f"Metadata: {METADATA_OUTPUT}")
    print("="*70)
    print("\n[NEXT] Reinicia app.py para usar novo modelo!")
    print("       python app.py")
    print("="*70)

if __name__ == '__main__':
    main()
