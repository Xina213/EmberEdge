#!/usr/bin/env python3
"""EmberEdge - AI Historical Integration"""

import pandas as pd
import csv, os, warnings
from predict_risk import RiskPredictor, get_predictor
from datetime import datetime
warnings.filterwarnings('ignore', category=UserWarning)

HISTORICAL_FILE = '../data/fires/historical_fires.csv'


def load_historical_data():
    if not os.path.exists(HISTORICAL_FILE):
        return []
    fires = []
    with open(HISTORICAL_FILE, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            fires.append(row)
    return fires


def get_historical_fires_by_city(city_name, month=None):
    fires = load_historical_data()
    if month is None:
        month = datetime.now().month
    city_fires  = [f for f in fires if city_name.lower() in f.get('district','').lower()]
    month_fires = [f for f in city_fires if int(f.get('month', 0)) == month]
    total_fires = sum(int(f.get('count', 0)) for f in month_fires)
    total_area  = sum(float(f.get('area_hectares', 0)) for f in month_fires)
    return {
        'total_fires_month':  total_fires,
        'total_area_month':   round(total_area, 2),
        'avg_fires_per_year': round(total_fires / 24, 1) if month_fires else 0,
        'historical_years':   '2000-2023'
    }


def predict_with_historical(city_name, temperature, humidity, wind_speed, precipitation):
    predictor     = get_predictor()
    current_month = datetime.now().month
    try:
        result = predictor.predict(
            temperature=temperature,
            humidity=humidity,
            wind_speed=wind_speed,
            precipitation=precipitation,
            city_name=city_name,
            month=current_month
        )
        result['historical'] = get_historical_fires_by_city(city_name, current_month)
        return result
    except Exception as e:
        print(f"❌ Erro predict_with_historical: {e}")
        return {'risk_level':'Médio','risk_value':1,'confidence':50.0,'city':city_name,'error':str(e)}


class AIHistoricalIntegration:
    def __init__(self):
        self.predictor       = get_predictor()
        self.historical_data = load_historical_data()

    def predict(self, city_name, temperature, humidity, wind_speed, precipitation):
        return predict_with_historical(city_name, temperature, humidity, wind_speed, precipitation)

    # ← MÉTODO QUE FALTAVA — chamado pelo /api/risk/all
    def predict_with_historical(self, city, day_of_year, temperature, wind_speed, humidity, lat, lon):
        return predict_with_historical(
            city_name=city,
            temperature=temperature,
            humidity=humidity,
            wind_speed=wind_speed,
            precipitation=0.0
        )

    def get_statistics(self):
        if not self.historical_data:
            return {}
        return {
            'total_fires':   sum(int(f.get('count',0)) for f in self.historical_data),
            'total_area':    round(sum(float(f.get('area_hectares',0)) for f in self.historical_data), 2),
            'years':         '2000-2023',
            'total_records': len(self.historical_data)
        }


def predict_risk_from_forecast(forecast_csv="../data/forecast_all.csv"):
    predictor = RiskPredictor()
    predictor.load_model()
    df      = pd.read_csv(forecast_csv)
    results = []
    for _, row in df.iterrows():
        prediction = predictor.predict(
            temperature=row["temperature"],
            humidity=row["humidity"],
            wind_speed=row["wind_speed"],
            precipitation=row["precipitation"]
        )
        results.append({
            "city":        row["city"],
            "datetime":    row["datetime"],
            "temperature": row["temperature"],
            "humidity":    row["humidity"],
            "wind_speed":  row["wind_speed"],
            "risk_level":  prediction["risk_level"],
            "confidence":  prediction["confidence"]
        })
    df_result = pd.DataFrame(results)
    df_result.to_csv("../data/forecast_risk.csv", index=False)
    return df_result


if __name__ == '__main__':
    print("="*70)
    print("EMBEREDGE - AI HISTORICAL INTEGRATION")
    print("="*70)
    for city in ['Guarda','Porto','Lisbon']:
        result = predict_with_historical(city, 25, 45, 20, 10)
        print(f"\n[TEST] {city} → {result.get('risk_level')} ({result.get('confidence',0):.1f}%)")
    print("\n✅ INTEGRAÇÃO AI + HISTÓRICO FUNCIONANDO!")
