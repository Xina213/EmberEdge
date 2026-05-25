#!/usr/bin/env python3
"""
EmberEdge - Weather Data Fetcher
Fetches current weather and forecast from OpenWeatherMap API
"""

import requests
import csv
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEATHER_FILE = os.path.join(BASE_DIR, '..', 'data', 'weather_latest.csv')
FORECAST_FILE = os.path.join(BASE_DIR, '..', 'data', 'forecast_all.csv')

OWM_API_KEY = os.getenv('OWM_API_KEY', 'your_key_here')

# Cities with coordinates (Portugal)
CITIES = {
    'Lisboa': {'lat': 38.72, 'lon': -9.14},
    'Porto': {'lat': 41.16, 'lon': -8.62},
    'Coimbra': {'lat': 40.21, 'lon': -8.43},
    'Braga': {'lat': 41.55, 'lon': -8.42},
    'Faro': {'lat': 37.02, 'lon': -7.93},
    'Evora': {'lat': 38.57, 'lon': -7.91},
    'Guarda': {'lat': 40.54, 'lon': -7.27},
    'Viseu': {'lat': 40.66, 'lon': -7.91},
    'Leiria': {'lat': 39.75, 'lon': -8.81},
    'Setubal': {'lat': 38.52, 'lon': -8.89},
    'Castelo Branco': {'lat': 39.82, 'lon': -7.49},
    'Beja': {'lat': 38.02, 'lon': -7.87},
    'Viana do Castelo': {'lat': 41.69, 'lon': -8.83},
    'Vila Real': {'lat': 41.30, 'lon': -7.74},
    'Braganca': {'lat': 41.81, 'lon': -6.76},
    'Aveiro': {'lat': 40.64, 'lon': -8.65},
    'Portalegre': {'lat': 39.30, 'lon': -7.43},
}


def fetch_current_weather():
    """Fetch current weather for all cities and save to CSV"""
    print("\n[WEATHER] Fetching current weather...")
    use_real_api = OWM_API_KEY and OWM_API_KEY != 'your_key_here'
    weather_data = []

    for city, coords in CITIES.items():
        if use_real_api:
            try:
                url = "https://api.openweathermap.org/data/2.5/weather"
                params = {
                    'lat': coords['lat'],
                    'lon': coords['lon'],
                    'appid': OWM_API_KEY,
                    'units': 'metric',
                    'lang': 'pt'
                }
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                weather_data.append({
                    'city': city,
                    'temperature': data['main']['temp'],
                    'humidity': data['main']['humidity'],
                    'wind_speed': round(data['wind']['speed'] * 3.6, 1),
                    'precipitation': data.get('rain', {}).get('1h', 0),
                    'latitude': coords['lat'],
                    'longitude': coords['lon'],
                    'weather_desc': data['weather'][0]['description'],
                    'source': 'OpenWeatherMap',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                print(f"  [WARN] {city}: {e}, using simulated")
                weather_data.append(_simulated_weather(city, coords))
        else:
            weather_data.append(_simulated_weather(city, coords))

    os.makedirs(os.path.dirname(WEATHER_FILE), exist_ok=True)
    with open(WEATHER_FILE, 'w', newline='', encoding='utf-8') as f:
        if weather_data:
            writer = csv.DictWriter(f, fieldnames=weather_data[0].keys())
            writer.writeheader()
            writer.writerows(weather_data)

    print(f"[OK] Weather saved: {len(weather_data)} cities -> {WEATHER_FILE}")
    return weather_data


def fetch_forecast():
    """Fetch 5-day forecast for all cities and save to CSV"""
    print("\n[FORECAST] Fetching 5-day forecast...")
    use_real_api = OWM_API_KEY and OWM_API_KEY != 'your_key_here'
    forecast_data = []

    for city, coords in CITIES.items():
        if use_real_api:
            try:
                url = "https://api.openweathermap.org/data/2.5/forecast"
                params = {
                    'lat': coords['lat'],
                    'lon': coords['lon'],
                    'appid': OWM_API_KEY,
                    'units': 'metric',
                    'cnt': 40
                }
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                for item in data['list']:
                    forecast_data.append({
                        'city': city,
                        'datetime': item['dt_txt'],
                        'temperature': item['main']['temp'],
                        'humidity': item['main']['humidity'],
                        'wind_speed': round(item['wind']['speed'] * 3.6, 1),
                        'precipitation': item.get('rain', {}).get('3h', 0),
                        'weather_desc': item['weather'][0]['description']
                    })
            except Exception as e:
                print(f"  [WARN] Forecast {city}: {e}, using simulated")
                forecast_data.extend(_simulated_forecast(city, coords))
        else:
            forecast_data.extend(_simulated_forecast(city, coords))

    os.makedirs(os.path.dirname(FORECAST_FILE), exist_ok=True)
    with open(FORECAST_FILE, 'w', newline='', encoding='utf-8') as f:
        if forecast_data:
            writer = csv.DictWriter(f, fieldnames=forecast_data[0].keys())
            writer.writeheader()
            writer.writerows(forecast_data)

    print(f"[OK] Forecast saved: {len(forecast_data)} records -> {FORECAST_FILE}")
    return forecast_data


def _simulated_weather(city, coords):
    """Fallback simulated weather data"""
    import random
    random.seed(int(datetime.now().strftime('%Y%m%d%H')) + hash(city) % 1000)
    return {
        'city': city,
        'temperature': round(random.uniform(16, 34), 1),
        'humidity': random.randint(30, 85),
        'wind_speed': round(random.uniform(5, 35), 1),
        'precipitation': 0,
        'latitude': coords['lat'],
        'longitude': coords['lon'],
        'weather_desc': 'ceu limpo',
        'source': 'simulated',
        'timestamp': datetime.now().isoformat()
    }


def _simulated_forecast(city, coords):
    """Fallback simulated forecast data"""
    import random
    from datetime import timedelta
    random.seed(int(datetime.now().strftime('%Y%m%d')) + hash(city) % 1000)
    items = []
    base = datetime.now()
    for i in range(40):
        dt = base + timedelta(hours=i * 3)
        items.append({
            'city': city,
            'datetime': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': round(random.uniform(14, 36), 1),
            'humidity': random.randint(25, 90),
            'wind_speed': round(random.uniform(5, 40), 1),
            'precipitation': 0,
            'weather_desc': 'ceu limpo'
        })
    return items


if __name__ == '__main__':
    print("=" * 70)
    print("EMBEREDGE - WEATHER DATA FETCHER")
    print("=" * 70)
    fetch_current_weather()
    fetch_forecast()
    print("=" * 70)
    print("[OK] WEATHER DATA COMPLETE!")
    print("=" * 70)
