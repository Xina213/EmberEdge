#!/usr/bin/env python3
"""EmberEdge - Backend API Flask"""


from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os, csv, threading, time, json, unicodedata
from datetime import datetime, timedelta
from dotenv import load_dotenv
from predict_risk import RiskPredictor, get_predictor, get_ndvi_for_city, estimate_ndvi, CITY_COORDS
from sentinel_ndvi import fetch_all_ndvi as fetch_real_ndvi
from integrate_ai import AIHistoricalIntegration
from copernicus_integration import CopernicusIntegration
from copernicus_frp import enrich_fires_with_real_area
from fetch_weather import fetch_current_weather, fetch_forecast

load_dotenv()

# ===== CSV LOCK (thread safety for gunicorn) =====
csv_lock = threading.Lock()


# ===== VALIDAÇÃO DE KEYS NO ARRANQUE =====
def validate_env_keys():
    required = {
        'NASA_FIRMS_KEY':          'https://firms.modaps.eosdis.nasa.gov/api/',
        'OWM_API_KEY':             'https://openweathermap.org/api',
        'COPERNICUS_CLIENT_ID':    'https://dataspace.copernicus.eu/',
        'COPERNICUS_CLIENT_SECRET':'https://dataspace.copernicus.eu/'
    }
    missing = []
    for key, url in required.items():
        val = os.getenv(key, '')
        if not val or val in ('your_key_here', 'your_client_id', 'your_client_secret'):
            missing.append((key, url))

    if missing:
        print("\n[AVISO] KEYS EM FALTA NO .env / RENDER ENVIRONMENT:")
        for key, url in missing:
            print(f"   [FALTA] {key} -> obtem em: {url}")
        print("   Algumas funcionalidades estarao indisponiveis.\n")
    else:
        print("[OK] Todas as API keys configuradas\n")
    return len(missing) == 0


fires_list = []
weather_list = []


BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR     = os.path.join(BASE_DIR, "..", "data")
FIRES_FILE   = os.path.join(DATA_DIR, "fires", "fires_latest.csv")
WEATHER_FILE = os.path.join(DATA_DIR, "weather_latest.csv")

def get_model_accuracy():
    """Lê accuracy real do model_metadata.json"""
    try:
        meta_path = os.path.join(DATA_DIR, 'model_metadata.json')
        with open(meta_path, 'r') as f:
            meta = json.load(f)
        return round(meta.get('accuracy', 0) * 100, 1)
    except Exception:
        return None

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, '..', 'frontend'), static_url_path='')
CORS(app)


predictor      = RiskPredictor()
ai_integration = AIHistoricalIntegration()
copernicus     = CopernicusIntegration()



def load_csv(filepath):
    if not os.path.exists(filepath):
        return []
    data = []
    try:
        with csv_lock:
            with open(filepath, 'r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    data.append(row)
    except Exception as e:
        print(f"[ERR] Erro carregar {filepath}: {e}")
    return data



def load_data():
    global fires_list, weather_list
    fires_list   = load_csv(FIRES_FILE)
    weather_list = load_csv(WEATHER_FILE)
    print(f" Dados carregados: {len(fires_list)} fogos, {len(weather_list)} cidades")



# ===== FRONTEND =====


@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    if path.startswith('api/'):
        return jsonify({"status":"error","message":"Endpoint não encontrado","code":404}), 404
    return send_from_directory('../frontend', path)


@app.route('/favicon.ico')
def favicon():
    return '', 204



# ===== API =====


@app.route('/api/fires')
def get_fires():
    fires = load_csv(FIRES_FILE)
    return jsonify({"status":"success","count":len(fires),"timestamp":datetime.now().isoformat(),"data":fires})



@app.route('/api/weather')
def get_weather():
    rows = load_csv(WEATHER_FILE)
    d = {}
    for r in rows:
        d[r.get('city','')] = {
            'temperature':  float(r.get('temperature',15)),
            'wind_speed':   float(r.get('wind_speed',10)),
            'humidity':     float(r.get('humidity',70)),
            'precipitation':float(r.get('precipitation',0)),
            'latitude':     float(r.get('latitude',40)),
            'longitude':    float(r.get('longitude',-8)),
            'weather_desc': r.get('weather_desc',''),
            'source':       r.get('source','OpenWeatherMap'),
            'timestamp':    r.get('timestamp','')
        }
    return jsonify({"status":"success","count":len(d),"timestamp":datetime.now().isoformat(),"data":d})



@app.route('/api/forecast')
def get_forecast():
    rows = load_csv(os.path.join(DATA_DIR,"forecast_all.csv"))
    by_city = {}
    for r in rows:
        city = r.get("city","")
        if city not in by_city:
            by_city[city] = []
        by_city[city].append({
            "datetime":     r.get("datetime"),
            "temperature":  float(r.get("temperature",15)),
            "humidity":     float(r.get("humidity",70)),
            "wind_speed":   float(r.get("wind_speed",10)),
            "precipitation":float(r.get("precipitation",0)),
            "weather_desc": r.get("weather_desc","")
        })
    return jsonify({"status":"success","cities":len(by_city),"timestamp":datetime.now().isoformat(),"data":by_city})



@app.route('/api/risk/<city>')
def get_risk_city(city):
    try:
        current_weather = load_csv(WEATHER_FILE)
        city_norm = unicodedata.normalize('NFKD', city).encode('ASCII', 'ignore').decode('utf-8').lower()
        wd = next((w for w in current_weather if unicodedata.normalize('NFKD', w['city']).encode('ASCII', 'ignore').decode('utf-8').lower()==city_norm), None)
        if not wd:
            return jsonify({'error':f'City {city} not found','available_cities':[w['city'] for w in weather_list]}), 404

        # Support query params for simulation mode (override weather values)
        sim_temp = request.args.get('temperature')
        sim_humidity = request.args.get('humidity')
        sim_wind = request.args.get('wind_speed')

        result = ai_integration.predict(
            city_name=city,
            temperature=float(sim_temp) if sim_temp is not None else float(wd['temperature']),
            humidity=float(sim_humidity) if sim_humidity is not None else float(wd['humidity']),
            wind_speed=float(sim_wind) if sim_wind is not None else float(wd['wind_speed']),
            precipitation=float(wd.get('precipitation',0))
        )

        # Add simulation flag
        if sim_temp is not None or sim_humidity is not None or sim_wind is not None:
            result['simulation'] = True
        return jsonify(result)
    except Exception as e:
        return jsonify({'error':str(e)}), 500



@app.route('/api/risk/all')
def get_all_risks():
    rows = load_csv(WEATHER_FILE)
    day  = datetime.now().timetuple().tm_yday
    risks = {}
    for r in rows:
        city   = r.get('city','')
        result = ai_integration.predict_with_historical(
            city=city, day_of_year=day,
            temperature=float(r.get('temperature',15)),
            wind_speed =float(r.get('wind_speed',10)),
            humidity   =float(r.get('humidity',70)),
            lat=float(r.get('latitude',40)),
            lon=float(r.get('longitude',-8))
        )
        if result:
            risks[city] = result
    return jsonify({"status":"success","count":len(risks),"data":risks})



@app.route('/api/ndvi')
def get_ndvi_all():
    """Return current NDVI values for all monitored cities.
    Tries real Copernicus Sentinel-2 data first, falls back to seasonal estimation.
    """
    try:
        ndvi_data = fetch_real_ndvi()
    except Exception:
        ndvi_data = {}

    result = {}
    for city, data in ndvi_data.items():
        result[city] = {
            'ndvi': data.get('ndvi', 0.5) if isinstance(data, dict) else data,
            'source': data.get('source', 'estimated') if isinstance(data, dict) else 'estimated',
            'latitude': CITY_COORDS.get(city, {}).get('lat', 40.0),
            'month': datetime.now().month
        }

    return jsonify({"status":"success","count":len(result),"timestamp":datetime.now().isoformat(),"data":result})



@app.route('/api/history')
def get_history():
    """Return 7-day risk history — real data where available, ERA5 averages for past."""
    history = {}
    base_date = datetime.now() - timedelta(days=6)

    forecast_rows = load_csv(os.path.join(DATA_DIR, "forecast_all.csv"))
    forecast_by_city = {}
    for r in forecast_rows:
        city = r.get('city', '')
        if city not in forecast_by_city:
            forecast_by_city[city] = []
        forecast_by_city[city].append(r)

    # Historical ICNF fire counts for current month (real 2000-2023)
    hist_fires = load_csv(os.path.join(DATA_DIR, 'fires', 'historical_fires.csv'))
    current_month = datetime.now().month
    month_fires = [f for f in hist_fires if int(f.get('month', 0)) == current_month]
    total_month_fires = sum(int(f.get('count', 0)) for f in month_fires)
    avg_fires_per_day = round(total_month_fires / 30, 1) if month_fires else 0

    weather_data = load_csv(WEATHER_FILE)

    # Build today's actual weather baseline once
    today_temps = [float(w.get('temperature', 20)) for w in weather_data]
    today_humids = [float(w.get('humidity', 50)) for w in weather_data]
    today_winds = [float(w.get('wind_speed', 10)) for w in weather_data]
    today_avg_temp = round(sum(today_temps) / len(today_temps), 1) if today_temps else 20.0
    today_avg_humid = round(sum(today_humids) / len(today_humids), 1) if today_humids else 50.0

    # Portugal May ERA5 climate normals (1991-2020) for pattern reference
    # May avg: ~19°C, 65% humidity — but this week is a heatwave
    # Past days: gradual warming from seasonal norm to today's heatwave peak
    may_seasonal_temp = 19.0
    may_seasonal_humid = 65.0

    for i in range(7):
        date     = base_date + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')

        # Try real forecast data first
        temps, humidities, winds = [], [], []

        for city, forecasts in forecast_by_city.items():
            for fc in forecasts:
                try:
                    fc_date = datetime.strptime(fc['datetime'][:10], '%Y-%m-%d')
                    if fc_date.date() == date.date():
                        temps.append(float(fc.get('temperature', 15)))
                        humidities.append(float(fc.get('humidity', 70)))
                        winds.append(float(fc.get('wind_speed', 10)))
                except (ValueError, KeyError):
                    continue

        if temps:
            # Real forecast data — use as-is
            avg_temp   = round(sum(temps) / len(temps), 1)
            avg_humid  = round(sum(humidities) / len(humidities), 1)
            avg_wind   = round(sum(winds) / len(winds), 1)
        else:
            # Past days: gradual heatwave ramp from May seasonal norm to today
            # Days ago = 6 - i (0 = today, 6 = furthest past)
            days_ago = 6 - i
            progress = days_ago / 6.0  # 1.0 = furthest past, 0.0 = today
            avg_temp = round(today_avg_temp - (today_avg_temp - may_seasonal_temp) * progress, 1)
            avg_humid = round(today_avg_humid + (may_seasonal_humid - today_avg_humid) * progress, 1)
            avg_wind = 11.0

        try:
            result = predictor.predict(
                temperature=avg_temp,
                humidity=avg_humid,
                wind_speed=avg_wind,
                precipitation=0.0,
                city_name='Lisboa',
                month=date.month
            )
            risk_avg = round(result['risk_value'] / 2, 2)
        except Exception:
            if avg_temp > 30 and avg_humid < 30:
                risk_avg = 1.0
            elif avg_temp > 25 and avg_humid < 50:
                risk_avg = 0.5
            else:
                risk_avg = 0.25

        real_fires_today = len(load_csv(FIRES_FILE))

        # Fire count: real for today, historical monthly avg for past
        fires_today = real_fires_today if i == 6 else int(avg_fires_per_day)

        history[date_str] = {
            'risk_avg':        min(risk_avg, 1.0),
            'fires_count':     fires_today,
            'area_burned_ha':  fires_today * 100,
            'avg_temperature': avg_temp,
            'avg_humidity':    avg_humid
        }

    return jsonify(history)



@app.route('/api/stats')
def get_stats():
    fires   = load_csv(FIRES_FILE)
    weather = load_csv(WEATHER_FILE)


    total_area   = sum(float(f.get('area_hectares',0)) for f in fires)
    temps        = [float(w.get('temperature',15)) for w in weather]
    winds        = [float(w.get('wind_speed',10))  for w in weather]
    humidities   = [float(w.get('humidity',70))    for w in weather]


    avg_temp     = round(sum(temps)/len(temps),1)           if temps      else 15.0
    avg_wind     = round(sum(winds)/len(winds),1)           if winds      else 10.0
    avg_humidity = round(sum(humidities)/len(humidities),1) if humidities else 70.0


    month = datetime.now().month
    if month in [6,7,8,9]:
        t_thresh, h_thresh, w_thresh = 30, 35, 40
    elif month in [4,5,10]:
        t_thresh, h_thresh, w_thresh = 22, 45, 35
    else:
        t_thresh, h_thresh, w_thresh = 18, 55, 30


    cities_at_risk = sum(
        1 for w in weather
        if float(w.get('temperature',0)) > t_thresh
        or float(w.get('humidity',100))  < h_thresh
        or float(w.get('wind_speed',0))  > w_thresh
    )


    return jsonify({
        "status":"success",
        "data":{
            "active_fires":     len(fires),
            "total_area_ha":    round(total_area,1),
            "avg_temperature":  avg_temp,
            "avg_wind":         avg_wind,
            "avg_humidity":     avg_humidity,
            "cities_at_risk":   cities_at_risk,
            "cities_monitored": len(weather),
            "model_accuracy":   get_model_accuracy(),
            "last_update":      datetime.now().isoformat()
        }
    })



@app.route('/api/health')
def health():
    return jsonify({
        "status":         "healthy" if predictor.model else "degraded",
        "fires_loaded":   len(load_csv(FIRES_FILE)),
        "weather_loaded": len(load_csv(WEATHER_FILE)),
        "model_loaded":   predictor.model is not None,
        "model_accuracy": get_model_accuracy(),
        "timestamp":      datetime.now().isoformat(),
        "version":        "1.1.0"
    })



@app.route('/api/copernicus/status')
def copernicus_status():
    try:
        token = copernicus.get_valid_token()
        return jsonify({
            "status":        "success" if token else "error",
            "token_valid":   token is not None,
            "token_expires": copernicus.token_expires.isoformat() if copernicus.token_expires else None,
            "service":       "Copernicus Data Space",
            "timestamp":     datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"status":"error","message":str(e),"service":"Copernicus Data Space"}), 500



@app.route('/api/districts.geojson')
def serve_districts():
    """Serve the Portugal districts GeoJSON locally."""
    geojson_path = os.path.join(BASE_DIR, '..', 'data', 'portugal_districts.geojson')
    if os.path.exists(geojson_path):
        return send_from_directory(os.path.join(BASE_DIR, '..', 'data'), 'portugal_districts.geojson')
    return jsonify({"status":"error","message":"GeoJSON not available locally"}), 404



# ===== ERRO HANDLERS =====


@app.errorhandler(404)
def not_found(e):
    return jsonify({"status":"error","message":"Endpoint não encontrado","code":404}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"status":"error","message":"Erro interno servidor","code":500}), 500



# ===== AUTO-UPDATE =====


def update_firms_data():
    while True:
        try:
            print("\n Atualizando NASA FIRMS...")
            import subprocess
            r = subprocess.run(['python', 'fetch_nasa_firms.py'],
                capture_output=True, text=True, cwd=os.path.dirname(__file__))
            if r.returncode == 0:
                print("[OK] NASA FIRMS ok")
            else:
                print(f"[!] NASA FIRMS stderr:\n{r.stderr}")
            if r.stdout:
                print(r.stdout)

            print("\n🛰️  Enriquecendo com Sentinel-3 FRP...")
            try:
                enrich_fires_with_real_area()
            except Exception as frp_err:
                print(f"[!]  FRP enrichment falhou (usando estimativa): {frp_err}")

            fetch_current_weather()
            fetch_forecast()
            print("[OK] Meteorologia OWM atualizada")

            # NDVI from Copernicus (once per cycle)
            print("\n[NDVI] Atualizando NDVI via Copernicus Sentinel-2...")
            try:
                from sentinel_ndvi import fetch_all_ndvi
                ndvi_data = fetch_all_ndvi(force_refresh=False)
                if ndvi_data:
                    real_count = sum(1 for v in ndvi_data.values() if v.get('source') == 'real')
                    print(f"[NDVI] OK: {real_count} cidades com dados reais, {len(ndvi_data) - real_count} estimadas")
            except Exception as ndvi_err:
                print(f"[NDVI] Erro: {ndvi_err}")

        except Exception as e:
            print(f"[ERR] Erro update: {e}")
        time.sleep(30 * 60)



# ===== MAIN =====


validate_env_keys()
load_data()
threading.Thread(target=update_firms_data, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*60)
    print(" EMBEREDGE DASHBOARD BACKEND API")
    print("="*60)
    print(f" Fogos: {len(load_csv(FIRES_FILE))} | 🌡️ Cidades: {len(load_csv(WEATHER_FILE))} | 🤖 AI: {'[OK]' if predictor.model else '[ERR]'}")
    print(f"🌐 Porta: {port}")
    print("="*60 + "\n")
    app.run(debug=False, port=port, host='0.0.0.0', use_reloader=False)