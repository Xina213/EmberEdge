#!/usr/bin/env python3
"""
EmberEdge - Risk Predictor (UPDATED for 7-feature model)
Compatible with retrained model using real historical data
"""

import joblib
import numpy as np
from datetime import datetime

MODEL_PATH = '../data/risk_model.pkl'

# Mapeamento de cidades para coordenadas
CITY_COORDS = {
    'Aveiro': {'lat': 40.64, 'lon': -8.65},
    'Beja': {'lat': 38.02, 'lon': -7.87},
    'Braga': {'lat': 41.55, 'lon': -8.42},
    'Bragança': {'lat': 41.81, 'lon': -6.76},
    'Caldas da Rainha': {'lat': 39.40, 'lon': -9.14},
    'Castelo Branco': {'lat': 39.82, 'lon': -7.49},
    'Coimbra': {'lat': 40.21, 'lon': -8.43},
    'Covilhã': {'lat': 40.28, 'lon': -7.50},
    'Évora': {'lat': 38.57, 'lon': -7.91},
    'Faro': {'lat': 37.02, 'lon': -7.93},
    'Guarda': {'lat': 40.54, 'lon': -7.27},
    'Leiria': {'lat': 39.75, 'lon': -8.81},
    'Lisboa': {'lat': 38.72, 'lon': -9.14},
    'Portalegre': {'lat': 39.30, 'lon': -7.43},
    'Porto': {'lat': 41.16, 'lon': -8.62},
    'Santarém': {'lat': 39.24, 'lon': -8.69},
    'Setúbal': {'lat': 38.52, 'lon': -8.89},
    'Viana do Castelo': {'lat': 41.69, 'lon': -8.83},
    'Vila Real': {'lat': 41.30, 'lon': -7.74},
    'Viseu': {'lat': 40.66, 'lon': -7.91},
    # Espanha
    'Madrid': {'lat': 40.42, 'lon': -3.70},
    'Badajoz': {'lat': 38.88, 'lon': -6.97},
    'Cáceres': {'lat': 39.48, 'lon': -6.37}
}

class RiskPredictor:
    def __init__(self):
        self.model = None
        self.risk_labels = ['Baixo', 'Médio', 'Alto']
        self.load_model()
    
    def load_model(self):
        """Carrega modelo treinado"""
        try:
            self.model = joblib.load(MODEL_PATH)
            print(f"✅ Modelo carregado: {MODEL_PATH}")
        except FileNotFoundError:
            print(f"⚠️ Modelo não encontrado: {MODEL_PATH}")
            self.model = None
    
    def predict(self, temperature, humidity, wind_speed, precipitation, city_name, month=None):
        """
        Prediz risco de incêndio com 7 features
        
        Args:
            temperature: Temperatura em °C
            humidity: Humidade em %
            wind_speed: Velocidade do vento em km/h
            precipitation: Precipitação em mm
            city_name: Nome da cidade (para lat/lon)
            month: Mês (1-12), se None usa mês atual
        """
        if self.model is None:
            return self._fallback_prediction(temperature, humidity)
        
        try:
            # Obtem coordenadas da cidade
            coords = CITY_COORDS.get(city_name, {'lat': 40.0, 'lon': -8.0})
            lat = coords['lat']
            lon = coords['lon']
            
            # Obtem mês atual se não fornecido
            if month is None:
                month = datetime.now().month
            
            # Cria array de features na ordem correta (7 features)
            # Order: temperature, humidity, wind_speed, precipitation, month, lat, lon
            features = np.array([[
                temperature,
                humidity,
                wind_speed,
                precipitation,
                month,
                lat,
                lon
            ]])
            
            # Predição
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
                'month': month
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Erro na predição: {e}")
            return self._fallback_prediction(temperature, humidity)
    
    def _fallback_prediction(self, temperature, humidity):
        """
        Predição simples caso modelo falhe
        """
        # Lógica simples baseada em regras
        if temperature > 30 and humidity < 30:
            risk = 'Alto'
            risk_value = 2
        elif temperature > 25 and humidity < 50:
            risk = 'Médio'
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
            'month': datetime.now().month
        }

# Singleton instance
_predictor = None

def get_predictor():
    """Retorna instância singleton do predictor"""
    global _predictor
    if _predictor is None:
        _predictor = RiskPredictor()
    return _predictor
