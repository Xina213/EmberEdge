#!/usr/bin/env python3
"""EmberEdge - OpenWeatherMap Real Data Fetcher"""

import requests
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
OWM_API_KEY = os.getenv("OWM_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5"

CITIES = [
    "Lisbon","Porto","Braga","Coimbra","Faro","Evora","Guarda","Beja",
    "Viseu","Aveiro","Setubal","Leiria","Santarem","Castelo Branco",
    "Vila Real","Braganca","Viana do Castelo","Portalegre","Funchal",
    "Ponta Delgada","Cascais","Sintra","Almada","Matosinhos",
    "Vila Nova de Gaia","Loures","Odivelas","Gondomar","Amadora","Barreiro"
]

def fetch_current_weather():
    if not OWM_API_KEY:
        print("❌ OWM_API_KEY não encontrada no .env!")
        return None

    print("🌤️  Buscando meteorologia real (OpenWeatherMap)...")
    records = []

    for city in CITIES:
        try:
            r = requests.get(f"{BASE_URL}/weather", params={
                "q": f"{city},PT", "appid": OWM_API_KEY,
                "units": "metric", "lang": "pt"
            }, timeout=10)
            r.raise_for_status()
            d = r.json()
            records.append({
                "city":         city,
                "latitude":     d["coord"]["lat"],
                "longitude":    d["coord"]["lon"],
                "temperature":  round(d["main"]["temp"], 1),
                "humidity":     d["main"]["humidity"],
                "wind_speed":   round(d["wind"]["speed"] * 3.6, 1),
                "precipitation":d.get("rain", {}).get("1h", 0.0),
                "weather_desc": d["weather"][0]["description"],
                "timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source":       "OpenWeatherMap"
            })
            print(f"  ✅ {city}: {d['main']['temp']}°C | {d['main']['humidity']}% hum")
        except Exception as e:
            print(f"  ⚠️  {city}: {e}")

    if records:
        df = pd.DataFrame(records)
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DATA_DIR = os.path.join(BASE_DIR, "..", "data")
        os.makedirs(DATA_DIR, exist_ok=True)
        df.to_csv(os.path.join(DATA_DIR, "weather_latest.csv"), index=False)
        print(f"✅ {len(records)} cidades guardadas em weather_latest.csv")
        return df
    return None  # ← dentro da função, alinhado com o if


def fetch_forecast():
    if not OWM_API_KEY:
        return None

    print("📅 Buscando previsões 5 dias...")
    main_cities = ["Lisbon","Porto","Braga","Faro","Coimbra",
                   "Evora","Castelo Branco","Guarda","Beja","Vila Real"]
    all_records = []

    for city in main_cities:
        try:
            r = requests.get(f"{BASE_URL}/forecast", params={
                "q": f"{city},PT", "appid": OWM_API_KEY,
                "units": "metric", "cnt": 40
            }, timeout=10)
            r.raise_for_status()
            for item in r.json()["list"]:
                all_records.append({
                    "city":         city,
                    "datetime":     item["dt_txt"],
                    "temperature":  round(item["main"]["temp"], 1),
                    "humidity":     item["main"]["humidity"],
                    "wind_speed":   round(item["wind"]["speed"] * 3.6, 1),
                    "precipitation":item.get("rain", {}).get("3h", 0.0),
                    "weather_desc": item["weather"][0]["description"]
                })
            print(f"  ✅ {city}: 40 registos")
        except Exception as e:
            print(f"  ⚠️  {city}: {e}")

    if all_records:
        df = pd.DataFrame(all_records)
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DATA_DIR = os.path.join(BASE_DIR, "..", "data")
        df.to_csv(os.path.join(DATA_DIR, "forecast_all.csv"), index=False)
        print(f"✅ Previsões guardadas em forecast_all.csv")
        return df
    return None


if __name__ == "__main__":
    fetch_current_weather()
    fetch_forecast()
