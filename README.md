# 🔥 EmberEdge - Sistema de Monitorização e Prevenção de Incêndios Florestais

EmberEdge é um sistema inteligente de monitorização e previsão de incêndios florestais que utiliza **Inteligência Artificial** para prever riscos e alertar comunidades em tempo real. O sistema integra dados de múltiplas fontes (satélite, meteorologia, histórico) para fornecer uma visão completa da situação de risco em Portugal.

![EmberEdge Dashboard](https://img.shields.io/badge/🔥-EmberEdge-orange)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey)
![ML](https://img.shields.io/badge/ML-Random%20Forest-green)

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
│   ├── predict_risk.py          # Modelo ML Random Forest
│   ├── fetch_weather.py         # OpenWeatherMap API
│   ├── fetch_nasa_firms.py      # NASA FIRMS (fogos ativos)
│   ├── copernicus_integration.py # Copernicus Data Space (Sentinel)
│   ├── copernicus_frp.py       # Enriquecimento FRP
│   ├── integrate_ai.py          # Integração histórico + AI
│   └── requirements.txt
├── frontend/
│   ├── index.html              # Dashboard principal
│   ├── style.css                # Estilos (Dark Mode)
│   └── script.js               # Leaflet + Chart.js + API
├── data/
│   ├── fires/                   # Dados de incêndios
│   │   ├── fires_latest.csv
│   │   └── historical_fires.csv
│   ├── weather_latest.csv       # Meteorologia atual
│   ├── forecast_all.csv        # Previsão 5 dias
│   ├── risk_model.pkl          # Modelo treinado
│   └── model_metadata.json     # Metadados do modelo
├── Procfile                     # Config Render
├── render.yaml                  # Config Render (alternativa)
└── README.md
```

---

## ✨ Funcionalidades

### 🗺️ Mapa Interativo
- Visualização de fogos ativos em tempo real (NASA FIRMS)
- Camada de distritos com hover interativo
- Cores de risco (Verde → Amarelo → Vermelho)
- Mapa em fullscreen

### 📊 Dashboard Inteligente
- **Estatísticas em tempo real**: fogos ativos, área queimada, temperatura média
- **Gráfico histórico**: evolução do risco nos últimos 7 dias
- **Previsão de risco**: AI prediz risco por cidade (Baixo/Médio/Alto)
- **Alertas visuais**: notificações quando risco é Alto

### 🤖 Inteligência Artificial
- Modelo **Random Forest** treinado com dados históricos (2000-2023)
- 7 features: temperatura, humidade, vento, precipitação, mês, latitude, longitude
- Integração com dados históricos do ICNF
- Confiança da predição (%)

### 🛰️ Dados Satélite
- **NASA FIRMS**: fogos ativos (VIIRS + MODIS)
- **Copernicus Sentinel-3**: Fire Radiative Power (FRP)
- **OpenWeatherMap**: meteorologia em tempo real + previsão

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|--------|-------------|
| **Backend** | Python 3.12, Flask, Flask-CORS |
| **ML** | Scikit-learn (Random Forest), Pandas, NumPy, Joblib |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) |
| **Mapa** | Leaflet.js, OpenStreetMap |
| **Gráficos** | Chart.js |
| **APIs** | OpenWeatherMap, NASA FIRMS, Copernicus Data Space, ICNF |
| **Deploy** | Render.com |

---

## 💻 Instalação Local

### Pré-requisitos
- Python 3.12+
- pip
- Git

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

# 5. Obter dados iniciais
cd backend
python fetch_weather.py
python fetch_nasa_firms.py

# 6. Arrancar o servidor
python app.py
```

O dashboard estará disponível em `http://localhost:5000`

---

## 🚀 Deploy no Render

O projeto está configurado para deploy automático no **Render.com**:

1. Fazer fork/clonar o repositório
2. Criar um novo **Web Service** no Render
3. Ligar ao repositório GitHub
4. Configurar as **Environment Variables**:
   - `NASA_FIRMS_KEY`
   - `OWM_API_KEY`
   - `COPERNICUS_CLIENT_ID`
   - `COPERNICUS_CLIENT_SECRET`
   - `FLASK_ENV=production`
5. O Render usará automaticamente o `Procfile` ou `render.yaml`

**URL de exemplo**: `https://emberedge-dashboard.onrender.com`

---

## 🔌 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-------------|
| GET | `/` | Dashboard principal (frontend) |
| GET | `/api/stats` | Estatísticas gerais |
| GET | `/api/fires` | Fogos ativos atuais |
| GET | `/api/weather` | Meteorologia atual |
| GET | `/api/forecast` | Previsão meteorológica |
| GET | `/api/risk/<city>` | Risco para uma cidade |
| GET | `/api/risk/all` | Risco para todas as cidades |
| GET | `/api/history` | Histórico 7 dias |
| GET | `/api/health` | Health check |
| GET | `/api/copernicus/status` | Status Copernicus API |

### Exemplo de resposta (`/api/risk/Lisboa`):

```json
{
  "risk_level": "Alto",
  "risk_value": 2,
  "confidence": 87.5,
  "probabilities": {
    "baixo": 5.2,
    "medio": 7.3,
    "alto": 87.5
  },
  "city": "Lisboa",
  "coordinates": {"lat": 38.72, "lon": -9.14},
  "month": 5
}
```

---

## 📡 Fontes de Dados

### APIs Externas
- **OpenWeatherMap** - Meteorologia atual e previsão ([api.openweathermap.org](https://openweathermap.org/api))
- **NASA FIRMS** - Fogos ativos VIIRS/MODIS ([firms.modaps.eosdis.nasa.gov](https://firms.modaps.eosdis.nasa.gov))
- **Copernicus Data Space** - Dados satélite Sentinel ([dataspace.copernicus.eu](https://dataspace.copernicus.eu))
- **IPMA** - Instituto Português do Mar e da Atmosfera (meteorologia oficial)

### Dados Históricos
- **ICNF** - Instituto da Conservação da Natureza e das Florestas ([fogos.icnf.pt](https://fogos.icnf.pt))
- Período: 2000-2023
- ~5000 registos de incêndios

---

## 🤖 Modelo de ML

### Algoritmo
**Random Forest Classifier** (100 árvores)

### Features (7)
1. `temperature` - Temperatura (°C)
2. `humidity` - Humidade relativa (%)
3. `wind_speed` - Velocidade do vento (km/h)
4. `precipitation` - Precipitação (mm)
5. `month` - Mês (1-12)
6. `latitude` - Latitude
7. `longitude` - Longitude

### Performance
- **Accuracy**: ~85-92% (depende dos dados de treino)
- **Validação**: Cross-validation 5-fold
- **Classes**: Baixo (0), Médio (1), Alto (2)

### Treinar o modelo
```bash
cd backend
python train_model.py  # Se existir script de treino
# Ou via Flask:
# O modelo é carregado automaticamente de data/risk_model.pkl
```

---

## 🎨 Interface (Frontend)

### Secções do Dashboard
1. **Mapa Interativo** - Leaflet com fogos ativos e camada de distritos
2. **Estatísticas** - Cards com dados em tempo real
3. **Fogos Ativos** - Lista de fogos detetados (NASA FIRMS)
4. **Áreas de Risco** - Top 5 cidades com maior risco (AI)
5. **Histórico** - Gráfico Chart.js (7 dias)

### Tema
- **Dark Mode** por defeito (cores: laranja #FF6B35, fundo escuro)
- Suporte para Light Mode (em desenvolvimento)

---

## 🤝 Contribuir

1. Fazer fork do projeto
2. Criar um branch (`git checkout -b feature/nova-funcionalidade`)
3. Commitar as alterações (`git commit -m 'Add: nova funcionalidade'`)
4. Push para o branch (`git push origin feature/nova-funcionalidade`)
5. Abrir um Pull Request

---

## 👥 Equipa

| Nome | Função |
|------|--------|
| Gonçalo Oliveira | Desenvolvimento Full-Stack + ML |
| Gabriel Ferreira | [Função] |

**Escola**: Escola Secundária D. Maria II, Braga, Portugal

---

## 📄 Licença

Projeto académico para a **Mostra Nacional de Ciência**.  
Uso educativo e de investigação.

---

## 📚 Referências

1. Wildfires as an ecosystem service. *Frontiers in Ecology*, 17(5), 289–295 (2019). https://doi.org/10.1002/fee.2044
2. Tedim, F., & Leone, V. The dilemma of wildfire definition. *Frontiers in Forests*, 3, 14 (2020). https://doi.org/10.3389/ffgc.2020.553116
3. Xu, Z., et al. Deep learning for wildfire risk prediction. (2024). https://doi.org/10.48550/arXiv.2405.01607

---

## 🔗 Links Úteis

- [Repositório GitHub](https://github.com/Xina213/EmberEdge)
- [NASA FIRMS API](https://firms.modaps.eosdis.nasa.gov/api/)
- [Copernicus Data Space](https://dataspace.copernicus.eu/)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [ICNF Fogos](https://fogos.icnf.pt)

---

<p align="center">
  <i>Desenvolvido com 🔥 para proteger comunidades.</i><br>
  <b>EmberEdge © 2026</b>
</p>
