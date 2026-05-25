#!/bin/bash
# EmberEdge - Build script for Render deployment
# This runs during build phase to generate model and initial data

echo "=========================================="
echo "EMBEREDGE - BUILD PHASE"
echo "=========================================="

# Download Portugal districts GeoJSON for local serving
echo ""
echo "[BUILD] Downloading Portugal GeoJSON..."
mkdir -p ../data
curl -sL -o ../data/portugal_districts.geojson \
  https://raw.githubusercontent.com/codeforgermany/click_that_hood/master/public/data/portugal.geojson
echo "[BUILD] GeoJSON downloaded"

# Train the Random Forest model
echo ""
echo "[BUILD] Training Random Forest model (500 trees)..."
cd backend
python train_model.py
echo "[BUILD] Model training complete!"

# Fetch initial NASA FIRMS data (if API key available)
echo ""
echo "[BUILD] Fetching initial fire data..."
python fetch_nasa_firms.py || echo "[WARN] NASA FIRMS fetch failed - will retry on startup"

# Fetch initial weather data
echo ""
echo "[BUILD] Fetching initial weather data..."
python fetch_weather.py || echo "[WARN] Weather fetch failed - will retry on startup"

# Fetch NDVI from Copernicus (if available)
echo ""
echo "[BUILD] Fetching NDVI data..."
python fetch_ndvi.py || echo "[WARN] NDVI fetch failed - will retry on startup"

echo ""
echo "=========================================="
echo "BUILD COMPLETE!"
echo "=========================================="