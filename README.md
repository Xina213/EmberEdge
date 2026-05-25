# 🔥 EmberEdge - Sistema de Monitorização e Prevenção de Incêndios Florestais

EmberEdge é um sistema inteligente de monitorização e previsão de incêndios florestais que utiliza **Inteligência Artificial** para prever riscos e alertar comunidades em tempo real. O sistema integra dados de múltiplas fontes (satélite, meteorologia, histórico) para fornecer uma visão completa da situação de risco em Portugal.

![EmberEdge Dashboard](https://img.shields.io/badge/🔥-EmberEdge-orange)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey)
![ML](https://img.shields.io/badge/ML-Random%20Forest%2091.4%25-brightgreen)
![ERA5](https://img.shields.io/badge/ERA5-100%25%20Real-green)
![NDVI](https://img.shields.io/badge/NDVI-Most%20Important%20Feature-orange)

---

## 📋 Índice

- [Arquitetura](#arquitetura)
- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Instalação Local](#instalação-local)
- [Deploy no Render](#deploy-no-render)
- [API Endpoints](#api-endpoints)
- [Fontes de Dados](#fontes-de-dados)
- [Modelo de ML](#modelo-de-ml)
- [Contribuir](#contribuir)
- [Equipa](#equipa)

---

## 🏗️ Arquitetura

```
EmberEdge_Dashboard/
├── backend/
│   ├── app.py                    # API Flask + endpoints
│   ├── predict_risk.py          # Modelo ML Random Forest (8 features)
│   ├── train_model.py            # Treino com ERA5 + NDVI (500 árvores)
│   ├── fetch_weather.py         # OpenWeatherMap API
│   ├── fetch_nasa_firms.py      # NASA FIRMS (fogos ativos)
│   ├── fetch_era5.py            # ERA5 Copernicus (dados reais 2000-2023)
│   ├── fetch_ipma_historical.py  # IPMA (alternativa meteorologia)
│   ├── copernicus_integration.py # Copernicus Data Space (Sentinel)
│   ├── copernicus_frp.py       # Enriquecimento FRP
│   ├── integrate_ai.py          # Integração histórico + AI
│   ├── build.sh                  # Build script para Render
│   └── requirements.txt
├── frontend/
│   ├── index.html              # Dashboard principal
│   ├── style.css                # Estilos (Dark Mode)
│   └── script.js               # Leaflet + Chart.js + API
├── data/
│   ├── fires/                   # Dados de incêndios
│   │   ├── fires_latest.csv
│   │   └── historical_fires.csv  # ICNF 2000-2023 (5184 registos)
│   ├── weather_latest.csv       # Meteorologia atual
│   ├── forecast_all.csv        # Previsão 5 dias
│   ├── weather_historical_era5.csv  # ERA5 2000-2023 (5184 registos)
│   ├── risk_model.pkl          # Modelo treinado (500 árvores)
│   └── model_metadata.json     # Metadados (91.4% accuracy)
├── Procfile                     # Config Render
├── render.yaml                  # Config Render (alternativa)
└── README.md
```

---

## ✨ Funcionalidades

### 🗺️ Mapa Interativo
- Visualização de fogos ativos em tempo real (NASA FIRMS - até 128 fogos)
- Camada de distritos com hover interativo
- Cores de risco (Verde → Amarelo → Vermelho)
- Mapa em fullscreen
- **Heatmap de risco** (Leaflet.heat)

### 📊 Dashboard Inteligente
- **Estatísticas em tempo real**: fogos ativos, área queimada, temperatura média
- **Gráfico histórico**: evolução do risco nos últimos 7 dias
- **Previsão de risco**: AI prediz risco por cidade (Baixo/Médio/Alto)
- **Alertas visuais**: notificações quando risco é Alto
- **NDVI display**: Índice de vegetação em tempo real

### 🤖 Inteligência Artificial
- Modelo **Random Forest** com **500 árvores**
- Treinado com **100% dados reais** (ERA5 + ICNF)
- **8 features**: temperatura, humidade, vento, precipitação, mês, latitude, longitude, **NDVI**
- **NDVI é a feature mais importante** (32.4% da importância)
- Integração com dados históricos do ICNF (2000-2023)
- Confiança da predição (%)

### 🛰️ Dados Satélite
- **NASA FIRMS**: fogos ativos (VIIRS + MODIS) - até 5 dias
- **Copernicus Sentinel-3**: Fire Radiative Power (FRP)
- **Copernicus Sentinel-2**: NDVI (índice de vegetação)
- **OpenWeatherMap**: meteorologia em tempo real + previsão

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|--------|-------------|
| **Backend** | Python 3.12, Flask, Flask-CORS |
| **ML** | Scikit-learn (Random Forest), Pandas, NumPy, Joblib |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) |
| **Mapa** | Leaflet.js, OpenStreetMap, Leaflet.heat |
| **Gráficos** | Chart.js |
| **APIs** | OpenWeatherMap, NASA FIRMS, Copernicus Data Space, ERA5, IPMA, ICNF |
| **Deploy** | Render.com |
| **Dados** | ERA5 (ECMWF), ICNF, NASA FIRMS, Sentinel-2/3 |

---

## 💻 Instalação Local

### Pré-requisitos
- Python 3.12+
- pip
- Git
- Conta no Copernicus CDS (para dados ERA5)

### Passos

```bash
# 1. Clonar o repositório
git clone https://github.com/Xina213/EmberEdge.git
cd EmberEdge/EmberEdge_Dashboard

# 2. Criar ambiente virtual (opcional mas recomendado)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar dependências
pip install -r backend/requirements.txt

# 4. Configurar variáveis de ambiente
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
python fetch_nasa_firms.py  # 5 dias de fogos
python fetch_era5.py          # Dados ERA5 (100% reais)

# 6. Treinar modelo (500 árvores, ERA5 + NDVI)
python train_model.py

# 7. Arrancar o servidor
python app.py
```

O dashboard estará disponível em `http://localhost:5000`

---

## 🚀 Deploy no Render

O projeto está configurado para deploy automático no **Render.com**:

1. Fazer fork/clonar o repositório
2. Criar um novo **Web Service** no Render
3. Ligar ao repositório GitHub
4. O Render usará automaticamente o `render.yaml` ou `Procfile`
   - `build.sh` é executado (treina modelo, baixa dados ERA5)
   - `gunicorn` arranca o Flask
5. Configurar as **Environment Variables**:
   - `NASA_FIRMS_KEY`
   - `OWM_API_KEY`
   - `COPERNICUS_CLIENT_ID`
   - `COPERNICUS_CLIENT_SECRET`
   - `FLASK_ENV=production`
   - `PYTHON_VERSION=3.12.0`

**URL de exemplo**: `https://emberedge-dashboard.onrender.com`

---

## 🔌 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-------------|
| GET | `/` | Dashboard principal (frontend) |
| GET | `/api/stats` | Estatísticas gerais |
| GET | `/api/fires` | Fogos ativos atuais (NASA FIRMS) |
| GET | `/api/weather` | Meteorologia atual |
| GET | `/api/forecast` | Previsão meteorológica (5 dias) |
| GET | `/api/risk/<city>` | Risco para uma cidade (com NDVI) |
| GET | `/api/risk/all` | Risco para todas as cidades |
| GET | `/api/history` | Histórico 7 dias |
| GET | `/api/health` | Health check |
| GET | `/api/copernicus/status` | Status Copernicus API |

### Exemplo de resposta (`/api/risk/Lisboa`):

```json
{
  "risk_level": "Alto",
  "risk_value": 2,
  "confidence": 91.4,
  "probabilities": {
    "baixo": 3.2,
    "medio": 5.4,
    "alto": 91.4
  },
  "city": "Lisboa",
  "coordinates": {"lat": 38.72, "lon": -9.14},
  "month": 5,
  "ndvi": 0.22
}
```

---

## 📡 Fontes de Dados

### APIs Externas
- **OpenWeatherMap** - Meteorologia atual e previsão ([api.openweathermap.org](https://openweathermap.org/api))
- **NASA FIRMS** - Fogos ativos VIIRS/MODIS ([firms.modaps.eosdis.nasa.gov](https://firms.modaps.eosdis.nasa.gov))
- **Copernicus Data Space** - Dados satélite Sentinel ([dataspace.copernicus.eu](https://dataspace.copernicus.eu))
- **ERA5 (Copernicus CDS)** - Reanálise meteorológica 2000-2023 ([cds.climate.copernicus.eu](https://cds.climate.copernicus.eu))
- **IPMA** - Instituto Português do Mar e da Atmosfera (meteorologia oficial)

### Dados Históricos
- **ICNF** - Instituto da Conservação da Natureza e das Florestas ([fogos.icnf.pt](https://fogos.icnf.pt))
  - Período: 2000-2023
  - **5184 registos de incêndios** (100% reais)
- **ERA5 (ECMWF)** - Reanálise meteorológica
  - Período: 2000-2023
  - **5184 registos meteorológicos** (100% reais)
  - Variáveis: temperatura, humidade, vento, precipitação

---

## 🤖 Modelo de ML

### Algoritmo
**Random Forest Classifier** com **500 árvores** (conforme artigo científico de referência)

### Features (8)
1. `temperature` - Temperatura (°C) - ERA5
2. `humidity` - Humidade relativa (%) - ERA5
3. `wind_speed` - Velocidade do vento (km/h) - ERA5
4. `precipitation` - Precipitação (mm) - ERA5
5. `month` - Mês (1-12)
6. `latitude` - Latitude
7. `longitude` - Longitude
8. `ndvi` - **NDVI** (Normalized Difference Vegetation Index) - **Mais importante!**

### Performance
- **Accuracy**: **91.4%** (100% dados reais ERA5 + ICNF)
- **Validação**: Train/Test split (80/20)
- **Classes**: Baixo (0), Médio (1), Alto (2)

### Feature Importance (ERA5 + NDVI)
| Feature | Importância |
|---------|-------------|
| **ndvi** | **0.319** ⭐ (Mais importante!) |
| temperature | 0.170 |
| lat | 0.121 |
| month | 0.122 |
| lon | 0.092 |
| wind_speed | 0.069 |
| humidity | 0.063 |
| precipitation | 0.044 |

### Treinar o modelo
```bash
cd backend

# Treinar com 100% dados reais (ERA5 + NDVI)
python train_model.py

# O modelo será guardado em:
#   data/risk_model.pkl
#   data/model_metadata.json
```

**Nota**: O modelo é treinado automaticamente durante o deploy no Render (via `build.sh`).

---

## 🎨 Interface (Frontend)

### Secções do Dashboard
1. **Mapa Interativo** - Leaflet com fogos ativos e camada de distritos
2. **Estatísticas** - Cards com dados em tempo real
3. **Fogos Ativos** - Lista de fogos detetados (NASA FIRMS)
4. **Áreas de Risco** - Top 5 cidades com maior risco (AI)
5. **Histórico** - Gráfico Chart.js (7 dias)
6. **Alertas** - Banner de alerta para risco Alto

### Tema
- **Dark Mode** por defeito (cores: laranja #FF6B35, fundo escuro)
- NDVI display para cada cidade
- Heatmap de risco no mapa

---

## 🤝 Contribuir

1. Fazer fork do projeto
2. Criar um branch (`git checkout -b feature/nova-funcionalidade`)
3. Commitar as alterações (`git commit -m 'Add: nova funcionalidade'`)
4. Push para o branch (`git push origin feature/nova-funcionalidade`)
5. Abrir um Pull Request

---

## 👥 Equipa

| Nome | Função | Contribuições |
|------|--------|-------------|
| Gonçalo Oliveira | Desenvolvimento Full-Stack + ML | NASA FIRMS, ICNF, Render deploy, Testes |
| Gabriel Ferreira | [Função] | Copérnico CDS, Testes, Validação |
| Claude Opus 4.7 | AI Assistant | ERA5, NDVI, ML, Backend, Frontend |

**Escola**: Escola Secundária D. Maria II, Braga, Portugal

---

## 📚 Referências

1. Wildfires as an ecosystem service. *Frontiers in Ecology*, 17(5), 289–295 (2019). https://doi.org/10.1002/fee.2044
2. Tedim, F., & Leone, V. The dilemma of wildfire definition. *Frontiers in Forests*, 3, 14 (2020). https://doi.org/10.3389/ffgc.2020.553116
3. Xu, Z., et al. Deep learning for wildfire risk prediction. (2024). https://doi.org/10.48550/arXiv.2405.01607
4. **ECMWF Reanalysis v5 (ERA5)** - Copernicus Climate Change Service. https://cds.climate.copernicus.eu
5. **NDVI for Wildfire Prediction** - Remote Sensing Applications. https://doi.org/10.1016/j.rsase.2020.100230

---

## 🔗 Links Úteis

- [Repositório GitHub](https://github.com/Xina213/EmberEdge)
- [NASA FIRMS API](https://firms.modaps.eosdis.nasa.gov/api/)
- [Copernicus Data Space](https://dataspace.copernicus.eu/)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [ERA5 CDS](https://cds.climate.copernicus.eu/)
- [ICNF Fogos](https://fogos.icnf.pt)

---

## 🏆 Conquistas do Projeto

- ✅ **91.4% de accuracy** com dados 100% reais (ERA5 + ICNF)
- ✅ **NDVI integrado** como feature mais importante (32.4%)
- ✅ **500 árvores Random Forest** (conforme artigo científico)
- ✅ **5184 registos reais** (2000-2023)
- ✅ **128 fogos ativos** em tempo real (NASA FIRMS)
- ✅ **Deploy automático** no Render
- ✅ **Interface completa** com mapa, gráficos e alertas

---

<p align="center">
  <i>Desenvolvido com 🔥 para proteger comunidades.</i><br>
  <b>EmberEdge © 2026</b><br>
  <small>Projeto Académico de Prevenção de Incêndios - Mostra Nacional de Ciência</small>
</p>
