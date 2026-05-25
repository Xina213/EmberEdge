# 🔥 EmberEdge - Projeto Final 2026
## Mostra Nacional de Ciência - Relatório Completo

**Data:** 25 de maio de 2026  
**Estado:** 200% Pronto para Apresentação  
**Equipa:** Gonçalo Oliveira, Gabriel Ferreira  
**Escola:** Escola Secundária D. Maria II, Braga

---

## 👥 Equipa e Contribuições

| Nome | Função | Contribuições | Contactos |
|------|--------|-------------|----------|
| **Gonçalo Oliveira** | Desenvolvedor Full-Stack + ML | Código completo, NASA FIRMS, ICNF, ERA5, NDVI, Render deploy, Testes | 📧 goncaloxina213@gmail.com<br>📧 41489@aedonamaria.pt |
| **Gabriel Ferreira** | Pesquisa & Alocação de Recursos | Copernicus CDS, Pesquisa científica, Testes, Validação | 📧 41482@aedonamaria.pt |
| **Claude Opus 4.7** | AI Assistant | ERA5, NDVI, ML, Backend, Frontend | - |

---

## 🎯 Objetivo

Sistema inteligente de monitorização e previsão de incêndios florestais usando **Inteligência Artificial** para prever riscos e alertar comunidades em tempo real.

---

## ✅ O Que Foi Feito (Checklist Completo)

### 1. Modelo de Machine Learning
- ✅ **Random Forest** com **500 árvores** (conforme artigo científico)
- ✅ Treinado com **100% dados reais** (ERA5 + ICNF)
- ✅ **8 features:** temperature, humidity, wind_speed, precipitation, month, lat, lon, **ndvi**
- ✅ **NDVI** integrado como feature mais importante (**32.4%** de importância)
- ✅ **91.4% accuracy** (subiu de 88.2%)
- ✅ **5184 registos reais** (ICNF 2000-2023 + ERA5)
- ✅ Ficheiros: `risk_model.pkl`, `model_metadata.json`

### 2. Dados Integrados
| Fonte | Tipo | Período | Status |
|-------|------|---------|--------|
| **ERA5 (Copernicus CDS)** | Meteorologia reanalise | 2000-2023 | ✅ 100% Real |
| **ICNF** | Histórico incêndios | 2000-2023 (5184 registos) | ✅ 100% Real |
| **NASA FIRMS** | Fogos ativos (VIIRS/MODIS) | Tempo real (5 dias) | ✅ Integrado |
| **OpenWeatherMap** | Meteorologia atual + previsão | Tempo real (30 min) | ✅ Integrado |
| **Copernicus Sentinel-2** | NDVI (índice vegetação) | Tempo real | ✅ Integrado |
| **Copernicus Sentinel-3** | FRP (Fire Radiative Power) | Tempo real | ✅ Integrado |

### 3. Backend (Python/Flask)
- ✅ `app.py` - API Flask com endpoints:
  - `GET /` - Dashboard (frontend)
  - `GET /api/stats` - Estatísticas
  - `GET /api/fires` - Fogos ativos NASA FIRMS
  - `GET /api/weather` - Meteorologia OpenWeatherMap
  - `GET /api/forecast` - Previsão 5 dias
  - `GET /api/risk/<city>` - Risco para cidade (com NDVI)
  - `GET /api/risk/all` - Risco todas cidades
  - `GET /api/history` - Histórico 7 dias
  - `GET /api/health` - Health check
  - `GET /api/copernicus/status` - Status Copernicus
- ✅ `predict_risk.py` - Modelo com 8 features + NDVI
- ✅ `train_model.py` - Treino com ERA5 + ICNF
- ✅ `fetch_weather.py` - OpenWeatherMap (atualiza 30 min)
- ✅ `fetch_nasa_firms.py` - NASA FIRMS (5 dias, 128 fogos)
- ✅ `fetch_era5.py` - ERA5 Copernicus CDS
- ✅ `copernicus_integration.py` - Sentinel-2/3
- ✅ `integrate_ai.py` - Integração histórico + AI
- ✅ Correção de acentos (Bragança/Braganca) em todo o código
- ✅ Normalização com `unicodedata` em Python e `normalize('NFD')` em JS

### 4. Frontend (HTML/CSS/JS)
- ✅ **Dashboard** em Dark Mode (padrão) e Light Mode (funcional)
- ✅ **Mapa Interativo** (Leaflet.js + Leaflet.heat)
  - Fogos ativos com marcadores dinâmicos (raio por área)
  - Heatmap de risco
  - Camada de distritos com hover
  - **Fullscreen** funcional (abre e fecha)
  - **Legenda do Mapa** (fogos, heatmap, riscos)
- ✅ **Cards Informativos:**
  - Estatísticas (fogos, área, temperatura, vento, humidade)
  - Fogos Ativos (NASA FIRMS)
  - Áreas de Risco (top 5 cidades, cores verde/amarelo/vermelho)
  - **Modelo AI** (com feature importance bars)
- ✅ **Gráfico Histórico** (Chart.js - 7 dias)
- ✅ **How It Works** (5 passos: Dados → Processamento → Treino → Previsão → Visualização)
- ✅ **Alertas Visuais** (risco alto)
- ✅ **Footer Redesign:**
  - GitHub link
  - Contactos (Gonçalo: gmail + institucional, Gabriel: institucional)
  - Créditos atualizados
- ✅ **Tema Toggle** (Dark/Light) com transição suave
- ✅ **Shimmer Animation** nos skeleton loaders
- ✅ Correção de bugs:
  - `risk_code` → `risk_value` (áreas de risco agora mostram)
  - "Erro ao carregar" (404 fix no serve_static)
  - Bragança/Braga (normalize accents em todo o código)

### 5. Deploy e Git
- ✅ **Render.com** deploy automático
  - `build.sh` executa treino e download ERA5
  - `gunicorn` serve a aplicação
  - Atualizações a cada push para `main`
- ✅ **GitHub:** https://github.com/Xina213/EmberEdge
- ✅ **Live Demo:** https://emberedge-dashboard.onrender.com
- ✅ **Commits recentes:**
  ```
  3c8683f - fix: 404 error - serve_static catching API routes
  818fd7f - fix: normalize accents everywhere (Bragança/Braganca bug resolved)
  4772a18 - fix: fullscreen, credits, and error handling improvements
  503c835 - feat: visual polish and bug fixes for science fair
  724dcc1 - feat: visual improvements for science fair presentation
  ```

### 6. README.md Atualizado
- ✅ Índice completo
- ✅ Arquitetura documentada
- ✅ Funcionalidades listadas
- ✅ Tecnologias (tabela)
- ✅ Instalação local
- ✅ Deploy no Render
- ✅ API Endpoints (tabela)
- ✅ Fontes de Dados
- ✅ Modelo de ML (features, importance, performance)
- ✅ Equipa (tabela com contribuições)
- ✅ **Contactos** (secção nova com emails)
- ✅ Referências científicas

---

## 📊 Performance do Modelo

| Métrica | Valor |
|---------|-------|
| **Accuracy** | **91.4%** |
| **Número de Árvores** | 500 (Random Forest) |
| **Número de Features** | 8 (incluindo NDVI) |
| **NDVI Importance** | **32.4%** (mais importante!) |
| **Dataset Size** | 5184 registos |
| **Dataset Source** | 100% Real (ERA5 + ICNF) |
| **Train/Test Split** | 80/20 |

### Feature Importance (Top 5)
1. **ndvi** - 32.4% ⭐
2. **temperature** - 17.0%
3. **month** - 12.2%
4. **lat** - 12.1%
5. **lon** - 9.2%

---

## 🛠️ Stack Tecnológico

| Camada | Tecnologia |
|--------|-------------|
| **Backend** | Python 3.12, Flask, Flask-CORS |
| **ML** | Scikit-learn (Random Forest), Pandas, NumPy, Joblib |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) |
| **Mapa** | Leaflet.js, OpenStreetMap, Leaflet.heat |
| **Gráficos** | Chart.js |
| **APIs** | OpenWeatherMap, NASA FIRMS, Copernicus CDS, ERA5, IPMA, ICNF |
| **Deploy** | Render.com |
| **Dados** | ERA5 (ECMWF), ICNF, NASA FIRMS, Sentinel-2/3 |

---

## 🎨 Aspeto Visual (Para Apresentação)

### Cores
- **Primária:** #FF6B35 (Laranja)
- **Sucesso:** #10B981 (Verde)
- **Aviso:** #F59E0B (Amarelo)
- **Perigo:** #EF4444 (Vermelho)
- **Fundo Dark:** #0F172A
- **Cards:** #1E293B

### Secções do Dashboard
1. ✅ Header com logo, status, botões (refresh, theme, fullscreen)
2. ✅ Alerta visual (risco alto)
3. ✅ Mapa interativo (600px altura, fullscreen)
4. ✅ Cards (Estatísticas, Fogos, Risco, Modelo AI)
5. ✅ How It Works (5 passos)
6. ✅ Gráfico histórico (7 dias)
7. ✅ Footer (GitHub, equipa, dados, tech, contactos)

---

## 🚀 Deploy no Render

**URL:** https://emberedge-dashboard.onrender.com

### Environment Variables (Configuradas no Render)
- `NASA_FIRMS_KEY` ✅
- `OWM_API_KEY` ✅
- `COPERNICUS_CLIENT_ID` ✅
- `COPERNICUS_CLIENT_SECRET` ✅
- `FLASK_ENV=production` ✅
- `PYTHON_VERSION=3.12.0` ✅

### Como Fazer Push
```bash
cd C:/Users/gonca/OneDrive/Documentos/EmberEdge_Dashboard/EmberEdge_Dashboard
git add .
git commit -m "feat: mensagem"
git push origin main
# Render faz deploy automático em 2-3 minutos
```

---

## 📝 Notas para a Apresentação

### O Que Demonstrar
1. **Dashboard ao vivo** - https://emberedge-dashboard.onrender.com
2. **Mapa** - Fogos ativos, heatmap, clicar em distritos
3. **Cards** - Estatísticas atualizam a cada 30 min
4. **Modelo AI** - Feature importance bars (NDVI 32.4%)
5. **How It Works** - Explicar pipeline de 5 passos
6. **Theme Toggle** - Dark/Light mode
7. **Alertas** - Se houver risco alto, aparece banner

### Pontos Fortes (Para Mencionar)
- ✅ **91.4% accuracy** com dados 100% reais
- ✅ **NDVI** é a feature mais importante (32.4%)
- ✅ **5184 registos reais** (2000-2023)
- ✅ **500 árvores Random Forest** (conforme artigo)
- ✅ **NASA FIRMS + OpenWeatherMap** em tempo real
- ✅ **Deploy automático** no Render
- ✅ **Interface completa** (mapa, gráficos, alertas)

### Referências Científicas
1. Wildfires as an ecosystem service. *Frontiers in Ecology*, 17(5), 289–295 (2019)
2. Tedim, F., & Leone, V. The dilemma of wildfire definition. *Frontiers in Forests*, 3, 14 (2020)
3. Xu, Z., et al. Deep learning for wildfire risk prediction. (2024)
4. **ERA5 (ECMWF)** - Copernicus Climate Change Service
5. **NDVI for Wildfire Prediction** - Remote Sensing Applications

---

## 🔗 Links Importantes

- **Repositório GitHub:** https://github.com/Xina213/EmberEdge
- **Live Demo:** https://emberedge-dashboard.onrender.com
- **NASA FIRMS API:** https://firms.modaps.eosdis.nasa.gov/api/
- **Copernicus Data Space:** https://dataspace.copernicus.eu/
- **OpenWeatherMap API:** https://openweathermap.org/api
- **ERA5 CDS:** https://cds.climate.copernicus.eu/
- **ICNF Fogos:** https://fogos.icnf.pt

---

## ✅ Estado Final

**TUDO PRONTO PARA A MOSTRA NACIONAL DE CIÊNCIA 2026!** 🔥

- ✅ Modelo treinado (91.4% accuracy)
- ✅ Dados integrados (100% reais)
- ✅ Dashboard funcional (todas as secções)
- ✅ Visual polido (dark mode, animações)
- ✅ Bugs corrigidos (acentos, fullscreen, 404)
- ✅ Contactos adicionados (footer + README)
- ✅ Deploy no Render (live demo)
- ✅ README completo
- ✅ Commit history limpa

**BOA SORTE NA APRESENTAÇÃO!** 🚀🇵🇹
