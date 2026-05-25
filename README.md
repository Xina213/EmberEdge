# 🔥 EmberEdge - Sistema de Monitorizacao e Prevencao de Incendios Florestais

EmberEdge e um sistema inteligente de monitorizacao e previsao de incendios florestais que utiliza **Inteligencia Artificial** para prever riscos e alertar comunidades em tempo real. O sistema integra dados de multiplas fontes (satelite, meteorologia, historico) para fornecer uma visao completa da situacao de risco em Portugal.

![EmberEdge Dashboard](https://img.shields.io/badge/🔥-EmberEdge-orange)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey)
![ML](https://img.shields.io/badge/ML-Random%20Forest-91.4%25-brightgreen)
![ERA5](https://img.shields.io/badge/ERA5-100%25%20Real-green)
![NDVI](https://img.shields.io/badge/NDVI-Real%20%2B%20Modelado-orange)

---

## 📋 Indice

- [Arquitetura](#arquitetura)
- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Instalacao Local](#instalacao-local)
- [Deploy no Render](#deploy-no-render)
- [API Endpoints](#api-endpoints)
- [Fontes de Dados](#fontes-de-dados)
- [Modelo de ML](#modelo-de-ml)
- [Transparencia dos Dados](#transparencia-dos-dados)
- [Contribuir](#contribuir)
- [Equipa](#equipa)

---

## 🏗️ Arquitetura

```
EmberEdge_Dashboard/
├── backend/
│   ├── app.py                    # API Flask + endpoints
│   ├── predict_risk.py          # Modelo ML Random Forest (8 features)
│   ├── train_model.py            # Treino com ERA5 + NDVI (500 arvores)
│   ├── sentinel_ndvi.py         # NDVI real via Copernicus Sentinel-2
│   ├── fetch_ndvi.py            # Script de busca NDVI
│   ├── fetch_weather.py         # OpenWeatherMap API
│   ├── fetch_nasa_firms.py      # NASA FIRMS (fogos ativos)
│   ├── fetch_era5.py            # ERA5 Copernicus (dados reais 2000-2023)
│   ├── copernicus_integration.py # Copernicus Data Space (Sentinel)
│   ├── copernicus_frp.py       # Enriquecimento FRP
│   ├── integrate_ai.py          # Integracao historico + AI
│   ├── build.sh                  # Build script para Render
│   └── requirements.txt
├── frontend/
│   ├── index.html              # Dashboard principal
│   ├── style.css                # Estilos (Dark Mode)
│   └── script.js               # Leaflet + Chart.js + API
├── data/
│   ├── fires/                   # Dados de incendios
│   │   ├── fires_latest.csv
│   │   └── historical_fires.csv  # ICNF 2000-2023 (5184 registos)
│   ├── weather_latest.csv       # Meteorologia atual
│   ├── forecast_all.csv        # Previsao 5 dias
│   ├── weather_historical_era5.csv  # ERA5 2000-2023 (5184 registos)
│   ├── risk_model.pkl          # Modelo treinado (500 arvores)
│   ├── model_metadata.json     # Metadados
│   ├── ndvi_cache.csv          # NDVI real do Copernicus (cache)
│   └── portugal_districts.geojson  # Distritos (servido localmente)
├── Procfile                     # Config Render
├── render.yaml                  # Config Render
└── README.md
```

---

## ✨ Funcionalidades

### 🗺️ Mapa Interativo
- Visualizacao de fogos ativos em tempo real (NASA FIRMS)
- Camada de distritos com hover interativo
- Cores de risco (Verde -> Amarelo -> Vermelho)
- Mapa em fullscreen
- **Heatmap de risco** (Leaflet.heat)

### 📊 Dashboard Inteligente
- **Estatisticas em tempo real**: fogos ativos, area queimada, temperatura media
- **Grafico historico**: evolucao do risco nos ultimos 7 dias
- **Previsao de risco**: AI prediz risco por cidade (Baixo/Medio/Alto)
- **Alertas visuais**: notificacoes quando risco e Alto
- **NDVI display**: Indice de vegetacao (real Copernicus Sentinel-2 ou modelado)

### 🤖 Inteligencia Artificial
- Modelo **Random Forest** com **500 arvores**
- Treinado com dados reais (ERA5 + ICNF) e NDVI (Copernicus Sentinel-2 / modelado)
- **8 features**: temperatura, humidade, vento, precipitacao, mes, latitude, longitude, **NDVI**
- Integracao com dados historicos do ICNF (2000-2023)
- Confianca da predicao (%)

### 🛰️ Dados Satelite
- **NASA FIRMS**: fogos ativos (VIIRS + MODIS)
- **Copernicus Sentinel-2**: NDVI real (indice de vegetacao)
- **Copernicus Sentinel-3**: Fire Radiative Power (FRP)
- **OpenWeatherMap**: meteorologia em tempo real + previsao

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|--------|-------------|
| **Backend** | Python 3.12, Flask, Flask-CORS |
| **ML** | Scikit-learn (Random Forest), Pandas, NumPy, Joblib |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) |
| **Mapa** | Leaflet.js, OpenStreetMap, Leaflet.heat |
| **Graficos** | Chart.js |
| **APIs** | Copernicus Data Space, OpenWeatherMap, NASA FIRMS, ERA5, IPMA, ICNF |
| **Deploy** | Render.com |
| **Dados** | ERA5 (ECMWF), ICNF, NASA FIRMS, Sentinel-2/3 |

---

## 💻 Instalacao Local

### Pre-requisitos
- Python 3.12+
- pip
- Git
- Conta no Copernicus Data Space (para NDVI real)

### Passos

```bash
# 1. Clonar o repositorio
git clone https://github.com/Xina213/EmberEdge.git
cd EmberEdge/EmberEdge_Dashboard

# 2. Criar ambiente virtual (opcional mas recomendado)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r backend/requirements.txt

# 4. Configurar variaveis de ambiente
# Criar ficheiro .env na pasta backend/ com:
# NASA_FIRMS_KEY=sua_key_aqui
# OWM_API_KEY=sua_key_openweather
# COPERNICUS_CLIENT_ID=sua_id
# COPERNICUS_CLIENT_SECRET=seu_secret
# Criar ficheiro ~/.cdsapirc para ERA5:
#   url: https://cds.climate.copernicus.eu/api/v2
#   key: seu_uid:seu_api_key

# 5. Obter dados iniciais
cd backend
python fetch_weather.py
python fetch_nasa_firms.py
python fetch_era5.py          # Dados ERA5 (100% reais)
python fetch_ndvi.py          # NDVI real do Copernicus Sentinel-2

# 6. Treinar modelo (500 arvores, ERA5 + NDVI)
python train_model.py

# 7. Arrancar o servidor
python app.py
```

O dashboard estara disponivel em `http://localhost:5000`

---

## 🚀 Deploy no Render

O projeto esta configurado para deploy automatico no **Render.com**:

1. Fazer fork/clonar o repositorio
2. Criar um novo **Web Service** no Render
3. Ligar ao repositorio GitHub
4. O Render usara automaticamente o `render.yaml` ou `Procfile`
   - `build.sh` e executado (treina modelo, baixa dados, faz download do GeoJSON)
   - `gunicorn` arranca o Flask
5. Configurar as **Environment Variables**:
   - `NASA_FIRMS_KEY`
   - `OWM_API_KEY`
   - `COPERNICUS_CLIENT_ID`
   - `COPERNICUS_CLIENT_SECRET`
   - `FLASK_ENV=production`
   - `PYTHON_VERSION=3.12.0`

---

## 🔌 API Endpoints

| Metodo | Endpoint | Descricao |
|--------|----------|-------------|
| GET | `/` | Dashboard principal (frontend) |
| GET | `/api/stats` | Estatisticas gerais |
| GET | `/api/fires` | Fogos ativos atuais (NASA FIRMS) |
| GET | `/api/weather` | Meteorologia atual |
| GET | `/api/forecast` | Previsao meteorologica (5 dias) |
| GET | `/api/risk/<city>` | Risco para uma cidade (com NDVI) |
| GET | `/api/risk/all` | Risco para todas as cidades |
| GET | `/api/ndvi` | NDVI atual para todas as cidades |
| GET | `/api/history` | Historico 7 dias |
| GET | `/api/health` | Health check |
| GET | `/api/copernicus/status` | Status Copernicus API |

---

## 📡 Fontes de Dados

### APIs Externas
- **OpenWeatherMap** - Meteorologia atual e previsao ([api.openweathermap.org](https://openweathermap.org/api))
- **NASA FIRMS** - Fogos ativos VIIRS/MODIS ([firms.modaps.eosdis.nasa.gov](https://firms.modaps.eosdis.nasa.gov))
- **Copernicus Data Space** - Dados satelite Sentinel ([dataspace.copernicus.eu](https://dataspace.copernicus.eu))
  - Sentinel-2: NDVI real (indice de vegetacao)
  - Sentinel-3: FRP (Fire Radiative Power)
- **ERA5 (Copernicus CDS)** - Reanalise meteorologica 2000-2023 ([cds.climate.copernicus.eu](https://cds.climate.copernicus.eu))

### Dados Historicos
- **ICNF** - Instituto da Conservacao da Natureza e das Florestas ([fogos.icnf.pt](https://fogos.icnf.pt))
  - Periodo: 2000-2023
  - **5184 registos de incendios** (100% reais)
- **ERA5 (ECMWF)** - Reanalise meteorologica
  - Periodo: 2000-2023
  - **5184 registos meteorologicos** (100% reais)
  - Variaveis: temperatura, humidade, vento, precipitacao

---

## 🤖 Modelo de ML

### Algoritmo
**Random Forest Classifier** com **500 arvores**

### Features (8)
1. `temperature` - Temperatura (°C) - ERA5
2. `humidity` - Humidade relativa (%) - ERA5
3. `wind_speed` - Velocidade do vento (km/h) - ERA5
4. `precipitation` - Precipitacao (mm) - ERA5
5. `month` - Mes (1-12)
6. `latitude` - Latitude
7. `longitude` - Longitude
8. `ndvi` - **NDVI** (Normalized Difference Vegetation Index)*

*\*NDVI: valores reais do Copernicus Sentinel-2 quando disponiveis (cache),
estimativa sazonal como fallback (baseada no ciclo de vegetacao portugues).*

### Performance
- **Accuracy**: **91.4%**
- **Validacao**: Train/Test split (80/20)
- **Classes**: Baixo (0), Medio (1), Alto (2)

### Metricas por Classe
| Classe | Precisao | Recall | F1-Score | Amostras |
|--------|----------|--------|----------|----------|
| Baixo  | -        | -      | -        | 1106     |
| Medio  | -        | -      | -        | 2668     |
| Alto   | -        | -      | -        | 1410     |

*(Metricas apos retreino com dados corrigidos)*

### Thresholds de Classificacao
| Classe | Area Queimada | Criterio |
|--------|---------------|----------|
| Baixo  | < 100 ha      | Pequeno incendio |
| Medio  | 100-1000 ha   | Incendio medio   |
| Alto   | > 1000 ha     | Grande incendio  |

### Treinar o modelo
```bash
cd backend

# Treinar com dados reais (ERA5 + ICNF + NDVI Copernicus)
python train_model.py

# O modelo sera guardado em:
#   data/risk_model.pkl
#   data/model_metadata.json
```

**Nota**: O modelo e treinado automaticamente durante o deploy no Render (via `build.sh`).

---

## 🔍 Transparencia dos Dados

O EmberEdge segue um principio de **transparencia total** sobre a origem dos dados:

| Feature | Origem | Fiabilidade |
|---------|--------|-------------|
| Temperatura | ERA5 (reanalise ECMWF) | 100% real |
| Humidade | ERA5 (reanalise ECMWF) | 100% real |
| Vel. Vento | ERA5 (reanalise ECMWF) | 100% real |
| Precipitacao | ERA5 (reanalise ECMWF) | 100% real |
| Mes | Calendario | 100% real |
| Coordenadas | Geograficas | 100% real |
| **NDVI** | **Copernicus Sentinel-2** quando disponivel | **Real (cached)** |
| **NDVI** | Estimativa sazonal (fallback) | **Modelado** |

**Sobre o NDVI:**
- Quando a API do Copernicus Data Space esta acessivel, o NDVI e calculado a partir de imagens reais do Sentinel-2 (bandas B04 e B08)
- Os valores sao cacheados por 24h para evitar rate limiting
- Quando a API nao esta disponivel, usamos uma estimativa sazonal baseada no ciclo natural de vegetacao portugues (mais alto no inverno, mais baixo no verao)
- O NDVI **nunca** e ajustado com base na area ardida — nao existe data leakage

---

## 🎨 Interface (Frontend)

### Secoes do Dashboard
1. **Mapa Interativo** - Leaflet com fogos ativos e camada de distritos
2. **Estatisticas** - Cards com dados em tempo real
3. **Fogos Ativos** - Lista de fogos detetados (NASA FIRMS)
4. **Areas de Risco** - Top 5 cidades com maior risco (AI)
5. **Historico** - Grafico Chart.js (7 dias)
6. **Alertas** - Banner de alerta para risco Alto

### Tema
- **Dark Mode** por defeito (cores: laranja #FF6B35, fundo escuro)
- NDVI display para cada cidade com indicador de origem (real/modelado)
- Heatmap de risco no mapa

---

## 🤝 Contribuir

1. Fazer fork do projeto
2. Criar um branch (`git checkout -b feature/nova-funcionalidade`)
3. Commitar as alteracoes (`git commit -m 'Add: nova funcionalidade'`)
4. Push para o branch (`git push origin feature/nova-funcionalidade`)
5. Abrir um Pull Request

---

## 👥 Equipa

| Nome | Funcao | Contribuicoes |
|------|--------|-------------|
| Goncalo Oliveira | Desenvolvimento Full-Stack + ML | Codigo completo, NASA FIRMS, ICNF, ERA5, NDVI, Render deploy, Testes |
| Gabriel Ferreira | Pesquisa & Alocacao de Recursos | Copernicus CDS, Pesquisa cientifica, Testes, Validacao |

**Escola**: Escola Secundaria D. Maria II, Braga, Portugal

---

## 📧 Contactos

| Nome | Email Pessoal | Email Institucional |
|------|-----------------|----------------------|
| Goncalo Oliveira | goncaloxina213@gmail.com | 41489@aedonamaria.pt |
| Gabriel Ferreira | - | 41482@aedonamaria.pt |

---

## 📚 Referencias

1. Wildfires as an ecosystem service. *Frontiers in Ecology*, 17(5), 289-295 (2019). https://doi.org/10.1002/fee.2044
2. Tedim, F., & Leone, V. The dilemma of wildfire definition. *Frontiers in Forests*, 3, 14 (2020). https://doi.org/10.3389/ffgc.2020.553116
3. Xu, Z., et al. Deep learning for wildfire risk prediction. (2024). https://doi.org/10.48550/arXiv.2405.01607
4. **ECMWF Reanalysis v5 (ERA5)** - Copernicus Climate Change Service. https://cds.climate.copernicus.eu
5. **NDVI for Wildfire Prediction** - Remote Sensing Applications. https://doi.org/10.1016/j.rsase.2020.100230
6. **Copernicus Sentinel-2 Mission** - ESA. https://sentinel.esa.int/web/sentinel/missions/sentinel-2

---

## 🔗 Links Uteis

- [Repositorio GitHub](https://github.com/Xina213/EmberEdge)
- [NASA FIRMS API](https://firms.modaps.eosdis.nasa.gov/api/)
- [Copernicus Data Space](https://dataspace.copernicus.eu/)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [ERA5 CDS](https://cds.climate.copernicus.eu/)
- [ICNF Fogos](https://fogos.icnf.pt)

---

## 🏆 Conquistas do Projeto

- ✅ **91.4% de accuracy** com dados reais (ERA5 + ICNF)
- ✅ **NDVI integrado**: real (Copernicus Sentinel-2) + modelado (fallback sazonal)
- ✅ **500 arvores Random Forest**
- ✅ **5184 registos reais** (2000-2023)
- ✅ **Fogos ativos em tempo real** (NASA FIRMS)
- ✅ **NDVI real de satelite** (Copernicus Sentinel-2)
- ✅ **GeoJSON servido localmente** (sem dependencia externa)
- ✅ **Deploy automatico** no Render
- ✅ **Interface completa** com mapa, graficos e alertas
- ✅ **Transparencia total** na origem dos dados

---

<p align="center">
  <i>Desenvolvido com 🔥 para proteger comunidades.</i><br>
  <b>EmberEdge © 2026</b><br>
  <small>Projeto Academico de Prevencao de Incendios - Mostra Nacional de Ciencia</small>
</p>