/* ============================================================
   EMBEREDGE - DASHBOARD INCENDIOS
   JavaScript COMPLETO - Leaflet + Chart.js + API Integration
   ============================================================ */

// ===== CONFIGURAÇÃO =====
const API_BASE = window.location.origin + '/api';
let map = null;
let markers = [];
let historyChart = null;
let districtLayer = null;
let simSelectedCity = null;

// ===== ICONES SVG =====
const ICONS = {
    fire: '<svg width="16" height="16" viewBox="0 0 24 24" fill="#EF4444" style="vertical-align: middle; margin-right: 8px;"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>',
    area: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2" style="vertical-align: middle; margin-right: 8px;"><circle cx="12" cy="12" r="10"/></svg>',
    temp: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2" style="vertical-align: middle; margin-right: 8px;"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>',
    wind: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#60A5FA" stroke-width="2" style="vertical-align: middle; margin-right: 8px;"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/></svg>',
    humidity: '<svg width="16" height="16" viewBox="0 0 24 24" fill="#3B82F6" style="vertical-align: middle; margin-right: 8px;"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" transform="rotate(180 12 12)"/></svg>',
    alert: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2" style="vertical-align: middle; margin-right: 8px;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    ai: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" style="vertical-align: middle; margin-right: 8px;"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/><circle cx="12" cy="12" r="3" fill="#10B981"/></svg>',
    clock: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    location: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
    target: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    check: '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>',
    satellite: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><path d="M2 12A10 10 0 0 1 12 2"/><path d="M10 14l-6 6"/><path d="M14 10l6-6"/><circle cx="12" cy="12" r="2"/></svg>'
};

// ===== TRADUCOES EN/PT =====
const TRANSLATIONS = {
    pt: {
        'header-subtitle': 'Inteligência Artificial para Previsão de Incêndios',
        'status-connected': 'Conectado',
        'updated': 'Atualizado',
        'fullscreen': 'Fullscreen',
        'stats-title': 'Estatísticas',
        'stats-subtitle': 'Tempo real',
        'fires-title': 'Fogos Ativos',
        'fires-subtitle': 'NASA FIRMS',
        'risk-title': 'Áreas de Risco',
        'risk-subtitle': 'AI Prediction',
        'model-title': 'Modelo AI',
        'model-subtitle': '91.4% Precisão',
        'sim-title': 'Simulação Interativa',
        'sim-subtitle': 'Teste Cenários',
        'sim-desc': 'Ajuste os sliders e clique num distrito no mapa para simular condições meteorológicas e ver como o risco de incêndio se altera em tempo real.',
        'sim-placeholder': 'Clique num distrito do mapa para simular',
        'how-title': 'Como Funciona',
        'how-subtitle': 'Pipeline de IA',
        'step1-title': 'Recolha de Dados',
        'step1-desc': 'NASA FIRMS (fogos em tempo real), OpenWeatherMap (meteo), ERA5 + ICNF (histórico 2000-2023), Copernicus Sentinel-2 (NDVI real por satélite).',
        'step2-title': 'NDVI por Satélite',
        'step2-desc': 'O NDVI real é calculado a partir das bandas B04 (vermelho) e B08 (infravermelho próximo) do Sentinel-2, processadas pela API do Copernicus Data Space.',
        'step3-title': 'Treino do Modelo',
        'step3-desc': 'Random Forest com 500 árvores, 8 features (NDVI, temperatura, humidade, vento, precipitação, mês, latitude, longitude), treinado com 5184 registos reais.',
        'step4-title': 'Previsão em Tempo Real',
        'step4-desc': 'IA prediz risco para 16+ cidades portuguesas com 91.4% de precisão.',
        'step5-title': 'Visualização',
        'step5-desc': 'Dashboard interativo com mapa, gráficos, alertas visuais e modo de simulação para testar cenários meteorológicos.',
        'history-title': 'Histórico 7 Dias',
        'history-subtitle': 'Evolução do risco Portugal',
        'science-title': 'Ciência do Modelo',
        'science-subtitle': 'Random Forest · Precisão: --',
        'footer-desc': 'IA para Previsão de Incêndios Florestais',
        'refresh-title': 'Atualizar Dados',
        'theme-title': 'Alternar Tema',
        'lang-title': 'English/Português',
        'loading-text': 'A carregar dados...',
        'status-updating': 'Atualizando dados...',
        'status-updated': 'Dados atualizados',
        'status-error': 'Erro ao carregar',
        'no-fires': 'Nenhum fogo ativo no momento',
        'last-check': 'Última verificação',
        'calculating': 'A calcular...',
        'sim-error': 'Erro ao simular. Tente novamente.',
        'toggle-science': 'Expandir ciência do modelo',
        'cm-baixo': 'Baixo',
        'cm-medio': 'Médio',
        'cm-alto': 'Alto',
        'pred-baixo': 'Previsto Baixo',
        'pred-medio': 'Previsto Médio',
        'pred-alto': 'Previsto Alto',
        'real-baixo': 'Real Baixo',
        'real-medio': 'Real Médio',
        'real-alto': 'Real Alto',
        'team': 'Equipa',
        'tech': 'Dados & Tech',
        'data-tech': 'Dados: NASA FIRMS, ERA5, ICNF, OpenWeatherMap | Tech: Random Forest, Flask, Leaflet.js, Chart.js',
        'school': 'Escola Secundária D. Maria II • Braga, Portugal',
        'project-academic': 'Projeto Académico • Mostra Nacional de Ciência 2026',
        'github': 'GitHub'
    },
    en: {
        'header-subtitle': 'Artificial Intelligence for Wildfire Prediction',
        'status-connected': 'Connected',
        'updated': 'Updated',
        'fullscreen': 'Fullscreen',
        'stats-title': 'Statistics',
        'stats-subtitle': 'Real time',
        'fires-title': 'Active Fires',
        'fires-subtitle': 'NASA FIRMS',
        'risk-title': 'Risk Areas',
        'risk-subtitle': 'AI Prediction',
        'model-title': 'AI Model',
        'model-subtitle': '91.4% Accuracy',
        'sim-title': 'Interactive Simulation',
        'sim-subtitle': 'Test Scenarios',
        'sim-desc': 'Adjust the sliders and click a district on the map to simulate weather conditions and see how fire risk changes in real time.',
        'sim-placeholder': 'Click a district on the map to simulate',
        'how-title': 'How It Works',
        'how-subtitle': 'AI Pipeline',
        'step1-title': 'Data Collection',
        'step1-desc': 'NASA FIRMS (real-time fires), OpenWeatherMap (weather), ERA5 + ICNF (historical 2000-2023), Copernicus Sentinel-2 (real NDVI by satellite).',
        'step2-title': 'NDVI by Satellite',
        'step2-desc': 'Real NDVI is calculated from Sentinel-2 bands B04 (red) and B08 (near infrared), processed through the Copernicus Data Space API.',
        'step3-title': 'Model Training',
        'step3-desc': 'Random Forest with 500 trees, 8 features (NDVI, temperature, humidity, wind, precipitation, month, latitude, longitude), trained on 5184 real records.',
        'step4-title': 'Real-Time Prediction',
        'step4-desc': 'AI predicts risk for 16+ Portuguese cities with 91.4% accuracy.',
        'step5-title': 'Visualization',
        'step5-desc': 'Interactive dashboard with map, charts, visual alerts and simulation mode to test weather scenarios.',
        'history-title': '7-Day History',
        'history-subtitle': 'Risk evolution Portugal',
        'science-title': 'Model Science',
        'science-subtitle': 'Random Forest · Accuracy: --',
        'footer-desc': 'AI for Wildfire Prediction',
        'refresh-title': 'Refresh Data',
        'theme-title': 'Toggle Theme',
        'lang-title': 'English/Português',
        'loading-text': 'Loading data...',
        'status-updating': 'Updating data...',
        'status-updated': 'Data updated',
        'status-error': 'Error loading data',
        'no-fires': 'No active fires at the moment',
        'last-check': 'Last check',
        'calculating': 'Calculating...',
        'sim-error': 'Simulation error. Try again.',
        'toggle-science': 'Expand model science',
        'cm-baixo': 'Low',
        'cm-medio': 'Medium',
        'cm-alto': 'High',
        'pred-baixo': 'Predicted Low',
        'pred-medio': 'Predicted Medium',
        'pred-alto': 'Predicted High',
        'real-baixo': 'Actual Low',
        'real-medio': 'Actual Medium',
        'real-alto': 'Actual High',
        'team': 'Team',
        'tech': 'Data & Tech',
        'data-tech': 'Data: NASA FIRMS, ERA5, ICNF, OpenWeatherMap | Tech: Random Forest, Flask, Leaflet.js, Chart.js',
        'school': 'Escola Secundária D. Maria II • Braga, Portugal',
        'project-academic': 'Academic Project • National Science Fair 2026',
        'github': 'GitHub'
    }
};

let currentLang = localStorage.getItem('emberedge-lang') || 'pt';

function applyLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('emberedge-lang', lang);

    // Update data-i18n elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const text = TRANSLATIONS[lang] && TRANSLATIONS[lang][key];
        if (text) {
            el.textContent = text;
        }
    });

    // Update lang toggle label
    const langLabel = document.getElementById('lang-label');
    if (langLabel) langLabel.textContent = lang === 'pt' ? 'PT' : 'EN';

    // Update title attributes
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) refreshBtn.title = TRANSLATIONS[lang]['refresh-title'];
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) themeToggle.title = TRANSLATIONS[lang]['theme-title'];
    const langToggle = document.getElementById('lang-toggle');
    if (langToggle) langToggle.title = TRANSLATIONS[lang]['lang-title'];
    const scienceToggle = document.getElementById('science-toggle');
    if (scienceToggle) scienceToggle.title = TRANSLATIONS[lang]['toggle-science'];

    // Update footer school/academic text
    const schoolEl = document.querySelector('.school-name');
    if (schoolEl) schoolEl.textContent = TRANSLATIONS[lang]['school'];
    const academicEl = document.querySelector('.footer-copy');
    if (academicEl) academicEl.textContent = '© 2026 • ' + TRANSLATIONS[lang]['project-academic'];
    const githubEl = document.querySelector('.footer-link');
    if (githubEl) githubEl.childNodes[githubEl.childNodes.length - 1].textContent = ' ' + TRANSLATIONS[lang]['github'];
    const teamHeader = document.querySelectorAll('.footer-section h4')[1];
    if (teamHeader) {
        const svgClone = teamHeader.querySelector('svg');
        teamHeader.innerHTML = svgClone ? svgClone.outerHTML : '';
        teamHeader.innerHTML += ' ' + TRANSLATIONS[lang]['team'];
    }
    const techHeader = document.querySelectorAll('.footer-section h4')[2];
    if (techHeader) {
        const svgClone = techHeader.querySelector('svg');
        techHeader.innerHTML = svgClone ? svgClone.outerHTML : '';
        techHeader.innerHTML += ' ' + TRANSLATIONS[lang]['tech'];
    }
}

function toggleLanguage() {
    const newLang = currentLang === 'pt' ? 'en' : 'pt';
    applyLanguage(newLang);
}

// ===== ANIMACOES SCROLL =====
function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    // Observe all animate-in elements
    document.querySelectorAll('.animate-in').forEach(el => observer.observe(el));

    // Observe chart container
    const chartContainer = document.querySelector('.chart-container');
    if (chartContainer) observer.observe(chartContainer);

    // Observe footer
    const footer = document.querySelector('.dashboard-footer');
    if (footer) observer.observe(footer);
}

// ===== MAPEAMENTO DE NOMES (GeoJSON -> Cidades) =====
const CITY_NAME_MAP = {
    'Santarem': 'Santarem',
    'Castelo Branco': 'Castelo Branco',
    'Vila Real': 'Vila Real',
    'Viana do Castelo': 'Viana do Castelo',
    'Braganca': 'Braganca',
    'Evora': 'Evora',
    'Leiria': 'Leiria',
    'Setubal': 'Setubal',
    'Portalegre': 'Portalegre'
};

// ===== INICIALIZAÇÃO =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔥 EmberEdge Dashboard iniciando...');

    initMap();
    loadAllData();
    setupEventListeners();
    initScrollAnimations();

    // Auto-refresh a cada 5 minutos
    setInterval(loadAllData, 5 * 60 * 1000);

    console.log('✅ Dashboard pronto!');
});

// ===== MAPA LEAFLET =====
function initMap() {
    console.log('🗺️ Inicializando mapa Leaflet...');

    map = L.map('map').setView([39.5, -8.0], 7);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18,
        minZoom: 6
    }).addTo(map);

    // Map Legend
    const legend = L.control({ position: 'bottomright' });
    legend.onAdd = function() {
        const div = L.DomUtil.create('div', 'map-legend');
        div.innerHTML = `
            <h4>Legenda do Mapa</h4>
            <div class="legend-item">
                <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#FF0000;margin-right:8px;"></span>
                <span>Fogo Ativo (>800K)</span>
            </div>
            <div class="legend-item">
                <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#FF6600;margin-right:8px;"></span>
                <span>Fogo Ativo (600-800K)</span>
            </div>
            <div class="legend-item">
                <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#FFA500;margin-right:8px;"></span>
                <span>Fogo Ativo (<600K)</span>
            </div>
            <div class="legend-item">
                <span style="display:inline-block;width:100px;height:10px;background:linear-gradient(to right,#0000ff,#00ff00,#ffff00,#ff0000);margin-right:8px;"></span>
                <span>Mapa de Calor</span>
            </div>
            <div class="legend-item">
                <span style="color:#EF4444;margin-right:4px;">■</span><span style="color:#F59E0B;margin-right:4px;">■</span><span style="color:#10B981;">■</span>
                <span style="margin-left:8px;">Alto/Medio/Baixo</span>
            </div>
        `;
        return div;
    };
    legend.addTo(map);

    console.log('✅ Mapa criado!');
}

// ===== CARREGAR TODOS OS DADOS (UMA CHAMADA) =====
async function loadAllData() {
    console.log('📡 Carregando dados...');
    updateStatus('Atualizando dados...', false);

    // Fallback: hide loading screen after 12s even if data fails (Render cold start)
    const fallbackTimer = setTimeout(() => {
        hideLoadingScreen();
    }, 12000);

    try {
        console.log('📡 Fetching all APIs...');

    // Fetch each API individually so one failure doesn't break the whole dashboard
    const [stats, fires, weather, history, riskAll, modelInfo] = await Promise.all([
        fetchAPI('/stats').then(d => { console.log('✅ /stats loaded'); return d; }).catch(e => { console.error('❌ /stats failed:', e); return null; }),
        fetchAPI('/fires').then(d => { console.log('✅ /fires loaded'); return d; }).catch(e => { console.error('❌ /fires failed:', e); return null; }),
        fetchAPI('/weather').then(d => { console.log('✅ /weather loaded'); return d; }).catch(e => { console.error('❌ /weather failed:', e); return null; }),
        fetchAPI('/history').then(d => { console.log('✅ /history loaded'); return d; }).catch(e => { console.error('❌ /history failed:', e); return null; }),
        fetchWithRetry('/risk/all', 2, 4000, 20000).then(d => { console.log('✅ /risk/all loaded'); return d; }).catch(e => { console.error('❌ /risk/all failed:', e); return null; }),
        fetchWithRetry('/model/info', 2, 4000, 15000).then(d => { console.log('✅ /model/info loaded'); return d; }).catch(e => { console.error('❌ /model/info failed:', e); return null; })
    ]);

    // Graceful degradation: only update sections that loaded successfully
    let loadedCount = 0;
    let timestamps = {};

    if (stats && stats.status === 'success') {
        updateStats(stats);
        timestamps.stats = stats.timestamp || stats.data?.last_update;
        document.getElementById('stats-content').closest('.card').classList.remove('card-offline');
        loadedCount++;
    } else {
        document.getElementById('stats-content').closest('.card').classList.add('card-offline');
    }
    if (fires && fires.status === 'success') {
        displayFires(fires);
        displayFiresOnMap(fires);
        timestamps.fires = fires.timestamp;
        document.getElementById('fires-content').closest('.card').classList.remove('card-offline');
        loadedCount++;
    } else {
        document.getElementById('fires-content').closest('.card').classList.add('card-offline');
    }
    if (weather && weather.status === 'success') {
        await addDistrictLayer(weather);
        timestamps.weather = weather.timestamp;
        loadedCount++;
    }
    if (riskAll && riskAll.status === 'success') {
        displayRiskCities(riskAll, weather || { data: {} });
        checkAlerts(riskAll);
        displayHeatmap(riskAll);
        timestamps.risk = riskAll.timestamp;
        document.getElementById('risk-cities-content').closest('.card').classList.remove('card-offline');
        loadedCount++;
    } else {
        // Show loading state instead of aggressive offline overlay
        const riskContent = document.getElementById('risk-cities-content');
        if (!riskContent.querySelector('.risk-retry-msg')) {
            riskContent.innerHTML = `
                <div class="risk-retry-msg" style="text-align:center;padding:1.5rem;color:var(--color-text-secondary);">
                    <div style="margin-bottom:8px;font-size:0.9rem;">A carregar dados de risco...</div>
                    <div style="width:24px;height:24px;border:3px solid var(--color-border);border-top-color:var(--color-accent);border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto;"></div>
                </div>`;
        }
        // Background retry: try again after a delay (Render wake-up takes time)
        const weatherForRetry = weather || { data: {} };
        (async function retryRisk() {
            const retryResult = await fetchWithRetry('/risk/all', 2, 5000, 20000);
            if (retryResult && retryResult.status === 'success') {
                displayRiskCities(retryResult, weatherForRetry);
                checkAlerts(retryResult);
                displayHeatmap(retryResult);
                document.getElementById('risk-cities-content').closest('.card').classList.remove('card-offline');
            } else {
                const riskContent = document.getElementById('risk-cities-content');
                riskContent.innerHTML = '<p style="text-align:center;color:var(--color-text-secondary);padding:1rem;">Dados de risco temporariamente indisponiveis</p>';
            }
        })();
    }
    if (history && Object.keys(history).length > 0) {
        plotHistory(history);
        loadedCount++;
    }
    if (modelInfo && modelInfo.status === 'success' && modelInfo.data?.confusion_matrix) {
        renderModelScience(modelInfo.data);
        loadedCount++;
    } else {
        // Science section remains hidden until build completes with real data
        if (modelInfo && modelInfo.status === 'success') {
            console.log('⏳ Model metadata loading (no confusion matrix yet)');
        }
        // Retry model info in background — build may still be deploying
        (async function retryModelInfo() {
            const retryResult = await fetchWithRetry('/model/info', 4, 5000, 15000);
            if (retryResult && retryResult.status === 'success' && retryResult.data?.confusion_matrix) {
                renderModelScience(retryResult.data);
            }
        })();
    }

    // Show per-source timestamps
    renderSourceTimestamps(timestamps);

    if (loadedCount > 0) {
        updateStatus('Dados atualizados', true);
        updateLastUpdate();
        clearTimeout(fallbackTimer);
        hideLoadingScreen();
    } else {
        updateStatus('Erro ao carregar', false);
        // Also hide loading screen on complete failure (user sees partial data)
        hideLoadingScreen();
    }
    } catch (e) {
        console.error('[FATAL] loadAllData error:', e);
        clearTimeout(fallbackTimer);
        hideLoadingScreen();
        updateStatus('Erro de conexao', false);
    }
}

function hideLoadingScreen() {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen && !loadingScreen.classList.contains('hidden')) {
        loadingScreen.classList.add('hidden');
        setTimeout(() => {
            loadingScreen.style.display = 'none';
        }, 600);
    }
}

// ===== VERIFICAR E MOSTRAR ALERTAS =====
function checkAlerts(riskAll) {
    if (!riskAll || !riskAll.data) return;

    const risks = riskAll.data;
    const highRiskCities = [];

    for (const [city, data] of Object.entries(risks)) {
        if (data.risk_level === 'Alto' || data.risk_value === 2) {
            highRiskCities.push(city);
        }
    }

    const alertBanner = document.getElementById('risk-alert');
    const alertTitle = document.getElementById('alert-title');
    const alertDesc = document.getElementById('alert-desc');

    if (highRiskCities.length > 0) {
        alertTitle.textContent = `ALERTA: ${highRiskCities.length} cidade(s) com Risco Alto!`;
        alertDesc.textContent = `Cidades em risco elevado: ${highRiskCities.slice(0, 3).join(', ')}${highRiskCities.length > 3 ? '...' : ''}`;
        alertBanner.classList.remove('hidden');
    } else {
        alertBanner.classList.add('hidden');
    }
}

// ===== HEATMAP DE RISCO =====
let heatLayer = null;

function displayHeatmap(riskAll) {
    if (!riskAll || !riskAll.data || !map) return;

    if (heatLayer) {
        map.removeLayer(heatLayer);
    }

    const heatPoints = [];

    for (const [city, data] of Object.entries(riskAll.data)) {
        if (data.coordinates && data.risk_value !== undefined) {
            const lat = data.coordinates.lat;
            const lon = data.coordinates.lon;
            const risk = data.risk_value;

            const intensity = risk === 0 ? 0.3 : (risk === 1 ? 0.6 : 1.0);
            heatPoints.push([lat, lon, intensity]);
        }
    }

    if (heatPoints.length > 0) {
        heatLayer = L.heatLayer(heatPoints, {
            radius: 35,
            blur: 20,
            maxZoom: 10,
            gradient: {
                0.3: '#10B981',
                0.6: '#F59E0B',
                1.0: '#EF4444'
            }
        }).addTo(map);
        console.log(`🔥 Heatmap adicionado: ${heatPoints.length} pontos`);
    }
}

// ===== CAMADA DE DISTRITOS PORTUGAL (HOVER) =====
const GEOJSON_URLS = [
    '/api/districts.geojson',
    'https://raw.githubusercontent.com/codeforgermany/click_that_hood/master/public/data/portugal.geojson',
    'https://raw.githubusercontent.com/datasets/geo-portugal/master/data/districts.geojson',
    'https://raw.githubusercontent.com/centraldedados/portugal-geojson/master/portugal.geojson'
];

async function fetchGeoJSON() {
    for (const url of GEOJSON_URLS) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 8000);
            const resp = await fetch(url, { signal: controller.signal });
            clearTimeout(timeoutId);
            if (resp.ok) {
                const data = await resp.json();
                if (data && data.features && data.features.length > 0) {
                    console.log('GeoJSON loaded from: ' + url.substring(0, 60) + '...');
                    return data;
                }
            }
        } catch (e) {
            console.log('GeoJSON fallback: ' + url.substring(0, 50) + '... (' + (e.message || 'error') + ')');
        }
    }
    return null;
}

async function addDistrictLayer(weatherData) {
    console.log('Carregando camada de distritos...');

    try {
        const geoData = await fetchGeoJSON();
        if (!geoData) {
            throw new Error('All GeoJSON sources failed');
        }

        const cities = weatherData.data;

        districtLayer = L.geoJSON(geoData, {
            style: {
                fillColor: 'transparent',
                fillOpacity: 0,
                color: '#475569',
                weight: 0.8,
                opacity: 0.5
            },
            onEachFeature: function(feature, layer) {
                const districtName = feature.properties.NAME_1 || feature.properties.name;

                let cityData = null;
                let cityWeather = null;

                for (let city of Object.keys(cities)) {
                    const mappedName = CITY_NAME_MAP[districtName] || districtName;
                    const normMapped = mappedName.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
                    const normCity = city.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
                    if (normMapped === normCity) {
                        cityData = city;
                        cityWeather = cities[city];
                        break;
                    }
                }

                                if (cityData && cityWeather) {
                    layer._hoverReqId = 0;

                    layer.on('mouseover', function(e) {
                        const reqId = ++this._hoverReqId;

                        this._hoverTimer = setTimeout(async () => {
                            if (this._hoverReqId !== reqId) return;

                            map.closePopup();

                            try {
                                const risk = await fetchAPI('/risk/' + encodeURIComponent(cityData));
                                if (this._hoverReqId !== reqId) return;

                                const color = getRiskColor(risk.risk_value);

                                this.setStyle({
                                    fillColor: color,
                                    fillOpacity: 0.35,
                                    color: color,
                                    weight: 2
                                });

                                const isRealNdvi = risk.ndvi_source && risk.ndvi_source.includes('real');
                                const ndviBadgeClass = isRealNdvi ? 'ndvi-real-badge' : 'ndvi-est-badge';
                                const ndviBadgeText = isRealNdvi ? 'SATÉLITE' : 'ESTIMADO';

                                const ndviSection = risk.ndvi !== undefined
                                    ? `<div style="margin: 8px 0; font-size: 0.82rem; color: #6b7280;">
                                            ${ICONS.satellite}<strong>NDVI: ${risk.ndvi.toFixed(3)}</strong>
                                            <span class="${ndviBadgeClass}">${ndviBadgeText}</span>
                                            <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 2px;">
                                                ${isRealNdvi
                                                    ? 'Dados reais do satélite Copernicus Sentinel-2'
                                                    : 'Estimativa sazonal (satélite indisponível)'}
                                            </div>
                                            ${risk.ndvi_comparison ? `
                                            <div style="margin-top: 4px; padding: 4px 8px; background: rgba(16,185,129,0.08); border-radius: 4px; font-size: 0.75rem;">
                                                <span style="color:#10B981;">Impacto do NDVI real:</span>
                                                Risco estimado sem satélite: <strong>${risk.ndvi_comparison.estimated_risk_level}</strong>
                                                (NDVI estimado: ${risk.ndvi_comparison.estimated_ndvi.toFixed(3)})
                                            </div>` : ''}
                                        </div>`
                                    : '';

                                const popup = L.popup()
                                    .setLatLng(e.latlng)
                                    .setContent(`
                                        <div style="font-family: Inter, sans-serif; min-width: 240px;">
                                            <strong style="font-size: 1.2rem; color: ${color};">${cityData}</strong>
                                            <hr style="margin: 8px 0; border: none; border-top: 1px solid #e5e7eb;">
                                            <div style="margin: 10px 0;">
                                                <strong>Risco:</strong><br>
                                                <span style="background: ${color}; color: white; padding: 4px 12px; border-radius: 6px; font-weight: bold; display: inline-block; margin-top: 4px;">
                                                    ${risk.risk_level}
                                                </span>
                                            </div>
                                            <div style="margin: 10px 0; font-size: 0.85rem; color: #6b7280;">
                                                ${ICONS.target}<strong>Confiança: ${risk.confidence.toFixed(1)}%</strong>
                                            </div>
                                            ${ndviSection}
                                            <hr style="margin: 8px 0; border: none; border-top: 1px solid #e5e7eb;">
                                            <div style="font-size: 0.85rem; color: #6b7280;">
                                                ${ICONS.temp}${cityWeather.temperature.toFixed(1)}C |
                                                ${ICONS.wind}${cityWeather.wind_speed.toFixed(1)} km/h<br>
                                                ${ICONS.humidity}${cityWeather.humidity.toFixed(0)}% |
                                                ${ICONS.area}${cityWeather.precipitation.toFixed(1)} mm
                                            </div>
                                        </div>
                                    `)
                                    .openOn(map);
                            } catch (error) {
                                console.error('Erro ao buscar risco:', error);
                            }
                        }, 150);
                    });

                    layer.on('mouseout', function() {
                        this._hoverReqId++;
                        clearTimeout(this._hoverTimer);

                        this.setStyle({
                            fillColor: 'transparent',
                            fillOpacity: 0,
                            color: '#475569',
                            weight: 0.8,
                            opacity: 0.5
                        });
                        map.closePopup();
                    });

                    layer.on('click', function() {
                        runSimulation(cityData);
                    });

                    layer.on('mouseover', function() {
                        if (this._path) this._path.style.cursor = 'pointer';
                    });
                }
            }
        }).addTo(map);

        console.log('✅ Camada de distritos adicionada');

    } catch (error) {
        console.error('❌ Erro ao carregar GeoJSON:', error);
        console.log('⚠️ Fallback: Usando marcadores invisiveis...');
        await displayInvisibleMarkers(weatherData);
    }
}

// ===== FALLBACK - MARCADORES INVISIVEIS =====
async function displayInvisibleMarkers(weatherData) {
    const cities = weatherData.data;
    const cityNames = Object.keys(cities);

    for (const cityName of cityNames) {
        const cityWeather = cities[cityName];

        try {
            const risk = await fetchAPI('/risk/' + encodeURIComponent(cityName));
            if (!risk || risk.risk_value === undefined) continue;

            const lat = cityWeather.latitude;
            const lon = cityWeather.longitude;
            const color = getRiskColor(risk.risk_value);

            const marker = L.circleMarker([lat, lon], {
                radius: 15,
                fillColor: 'transparent',
                color: 'transparent',
                weight: 0,
                opacity: 0,
                fillOpacity: 0
            }).addTo(map);

            marker.on('mouseover', function() {
                this.setStyle({
                    fillColor: color,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8,
                    radius: 12
                });
            });

            marker.on('mouseout', function() {
                this.setStyle({
                    fillColor: 'transparent',
                    color: 'transparent',
                    weight: 0,
                    opacity: 0,
                    fillOpacity: 0
                });
            });

            marker.bindPopup(`
                <div style="font-family: Inter, sans-serif; min-width: 220px;">
                    <strong style="font-size: 1.2rem; color: ${color};">${cityName}</strong>
                    <hr style="margin: 8px 0; border: none; border-top: 1px solid #e5e7eb;">
                    <div style="margin: 10px 0;">
                        <strong>Risco:</strong><br>
                        <span style="background: ${color}; color: white; padding: 4px 12px; border-radius: 6px; font-weight: bold; display: inline-block; margin-top: 4px;">
                            ${risk.risk_level}
                        </span>
                    </div>
                    <div style="font-size: 0.85rem; color: #6b7280;">
                        ${ICONS.temp}${cityWeather.temperature.toFixed(1)}°C |
                        ${ICONS.wind}${cityWeather.wind_speed.toFixed(1)} km/h<br>
                        ${ICONS.humidity}${cityWeather.humidity.toFixed(0)}% |
                        ${ICONS.area}${cityWeather.precipitation.toFixed(1)} mm
                    </div>
                </div>
            `);

            markers.push(marker);

        } catch (error) {
            console.error('❌ Erro em ' + cityName + ':', error);
        }
    }

    console.log('✅ ' + markers.length + ' marcadores invisiveis criados');
}

// ===== DEBOUNCE =====
function debounce(fn, ms) {
    let timer = null;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), ms);
    };
}

// ===== FETCH API =====
async function fetchWithRetry(endpoint, retries = 3, delay = 4000, timeoutMs = 20000) {
    for (let i = 0; i < retries; i++) {
        const result = await fetchAPI(endpoint, timeoutMs).catch(e => null);
        if (result && result.status === 'success') return result;
        if (i < retries - 1) {
            await new Promise(r => setTimeout(r, delay));
        }
    }
    return null;
}

async function fetchAPI(endpoint, timeoutMs = 15000) {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

        const response = await fetch(`${API_BASE}${endpoint}`, {
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (!response.ok) {
            console.error(`API Error: ${response.status} at ${endpoint}`);
            throw new Error(`HTTP ${response.status}: ${endpoint}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        if (error.name === 'AbortError') {
            console.error(`Timeout ${endpoint} (>${timeoutMs}ms)`);
        } else {
            console.error(`Fetch failed for ${endpoint}:`, error);
        }
        throw error;
    }
}

// ===== ATUALIZAR STATUS =====
function updateStatus(text, isSuccess) {
    const statusEl = document.getElementById('status-text');
    statusEl.textContent = text;

    if (isSuccess) {
        statusEl.style.color = '#10B981';
    } else {
        statusEl.style.color = '#F59E0B';
    }
}

function formatActiveHours(value) {
    if (!value || value === '0') return 'Tempo desconhecido';
    if (typeof value === 'string' && value.includes('UTC')) {
        const time = value.replace(' UTC', '');
        return `Detetado as ${time}`;
    }
    return `${value}h ativo`;
}

function updateLastUpdate() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('pt-PT', {
        hour: '2-digit',
        minute: '2-digit'
    });
    const el = document.getElementById('last-update-time');
    if (el) el.textContent = timeStr;
}

function timeAgo(isoString) {
    if (!isoString) return null;
    const now = new Date();
    const then = new Date(isoString);
    const diffSec = Math.floor((now - then) / 1000);
    if (diffSec < 60) return 'agora';
    if (diffSec < 3600) return `ha ${Math.floor(diffSec / 60)}min`;
    if (diffSec < 86400) return `ha ${Math.floor(diffSec / 3600)}h`;
    const days = Math.floor(diffSec / 86400);
    return `ha ${days}d`;
}

function renderSourceTimestamps(timestamps) {
    const container = document.getElementById('source-timestamps');
    if (!container) return;

    const sources = [
        { key: 'fires', label: 'Fogos', dot: 'red' },
        { key: 'weather', label: 'Meteo', dot: 'yellow' },
        { key: 'stats', label: 'Estatísticas', dot: 'green' },
        { key: 'risk', label: 'Risco', dot: 'yellow' }
    ];

    let html = '';
    for (const src of sources) {
        const ago = timeAgo(timestamps[src.key]);
        if (ago) {
            html += `<span class="source-timestamp"><span class="ts-dot ${src.dot}"></span>${src.label}: ${ago}</span>`;
        }
    }
    container.innerHTML = html;
}

// ===== ESTATISTICAS COM ICONES SVG =====
function updateStats(stats) {
    const data = stats.data;

    const html = `
        <div class="stat-row">
            <span>${ICONS.fire}Fogos Ativos</span>
            <strong>${data.active_fires}</strong>
        </div>
        <div class="stat-row">
            <span>${ICONS.area}Area Queimada</span>
            <strong>${data.total_area_ha} ha</strong>
        </div>
        <div class="stat-row">
            <span>${ICONS.temp}Temperatura Media</span>
            <strong>${data.avg_temperature}°C</strong>
        </div>
        <div class="stat-row">
            <span>${ICONS.wind}Vento Medio</span>
            <strong>${data.avg_wind} km/h</strong>
        </div>
        <div class="stat-row">
            <span>${ICONS.humidity}Humidade Media</span>
            <strong>${data.avg_humidity}%</strong>
        </div>
        <div class="stat-row">
            <span>${ICONS.alert}Cidades em Risco</span>
            <strong style="color: #EF4444;">${data.cities_at_risk}</strong>
        </div>
    `;

    document.getElementById('stats-content').innerHTML = html;

    // Update model accuracy display from API data
    if (data.model_accuracy) {
        const accDisplay = document.getElementById('model-accuracy-display');
        if (accDisplay) {
            accDisplay.textContent = data.model_accuracy.toFixed(1) + '%';
        }
        // Also update card subtitle
        const accSubtitle = document.querySelector('.card-header .card-subtitle');
        if (accSubtitle && accSubtitle.textContent.includes('%')) {
            accSubtitle.textContent = data.model_accuracy.toFixed(1) + '% Precisão';
        }
    }
}

// ===== FOGOS ATIVOS COM ICONES SVG =====
function displayFires(firesData) {
    const fires = firesData.data;

    if (fires.length === 0) {
        document.getElementById('fires-content').innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--color-text-secondary);">
                <div style="margin-bottom: 1rem;">${ICONS.check}</div>
                <p style="margin-top: 1rem; font-weight: 600;">Nenhum fogo ativo no momento</p>
                <p style="font-size: 0.85rem; margin-top: 0.5rem; opacity: 0.7;">Ultima verificacao: ${new Date().toLocaleTimeString('pt-PT')}</p>
            </div>
        `;
        return;
    }

    let html = '<div style="max-height: 400px; overflow-y: auto;">';

    fires.forEach((fire, idx) => {
        html += `
            <div class="fire-item">
                <div class="fire-header">
                    <strong>${ICONS.fire}${fire.city || 'Desconhecido'}</strong>
                    <span class="fire-badge">${fire.area_hectares || 0} ha</span>
                </div>
                <div class="fire-details">
                    <small>
                        ${ICONS.clock}${formatActiveHours(fire.active_hours)} |
                        ${ICONS.temp}${fire.temperature || 600}°C |
                        ${ICONS.location}${parseFloat(fire.latitude).toFixed(3)}, ${parseFloat(fire.longitude).toFixed(3)}
                    </small>
                </div>
            </div>
        `;
    });

    html += '</div>';
    document.getElementById('fires-content').innerHTML = html;
}

// ===== CIDADES RISCO COM ICONES SVG (OTIMIZADO: usa /api/risk/all) =====
function displayRiskCities(riskAllData, weatherData) {
    const cities = weatherData.data;

    if (!riskAllData || !riskAllData.data || Object.keys(cities).length === 0) {
        document.getElementById('risk-cities-content').innerHTML =
            '<p style="text-align:center;color:var(--color-text-secondary);">Sem dados</p>';
        return;
    }

    const riskData = riskAllData.data;

    // Build array with city + weather + risk data combined
    const citiesWithRisk = [];
    for (const [city, data] of Object.entries(riskData)) {
        const weather = cities[city];
        if (weather) {
            citiesWithRisk.push({
                name: city,
                risk_level: data.risk_level,
                risk_value: data.risk_value,
                confidence: data.confidence,
                ndvi: data.ndvi,
                ndvi_source: data.ndvi_source,
                temperature: weather.temperature,
                humidity: weather.humidity
            });
        }
    }

    citiesWithRisk.sort((a, b) => b.risk_value - a.risk_value);
    const topCities = citiesWithRisk.slice(0, 5);

    if (topCities.length === 0) {
        document.getElementById('risk-cities-content').innerHTML =
            '<p style="text-align:center;color:var(--color-text-secondary);padding:1rem;">Sem dados de risco disponiveis</p>';
        return;
    }

    let html = '<ul class="risk-list">';

    topCities.forEach((city, idx) => {
        const colors = { 0: '#10B981', 1: '#F59E0B', 2: '#EF4444' };
        const riskColor = colors[city.risk_value] || '#94A3B8';

        const ndviColor = city.ndvi > 0.4 ? '#10B981' : (city.ndvi > 0.2 ? '#F59E0B' : '#EF4444');
        const ndviIcon = city.ndvi_source?.includes('real') ? ICONS.satellite : '';

        html += `
            <li class="risk-item" style="border-left: 4px solid ${riskColor};">
                <div class="risk-header">
                    <strong>${idx + 1}. ${city.name}</strong>
                    <span class="risk-badge" style="background-color: ${riskColor};">
                        ${city.risk_level}
                    </span>
                </div>
                <div class="risk-details">
                    <small>
                        ${ICONS.temp}${city.temperature.toFixed(1)}°C |
                        ${ICONS.humidity}${city.humidity.toFixed(0)}% humidade |
                        ${ICONS.target}${city.confidence?.toFixed(0)}% confianca
                        ${city.ndvi !== undefined
                            ? `| NDVI: <span style="color:${ndviColor};">${city.ndvi.toFixed(3)}</span> ${ndviIcon}`
                            : ''}
                    </small>
                </div>
            </li>
        `;
    });

    html += '</ul>';
    document.getElementById('risk-cities-content').innerHTML = html;
}

// ===== FOGOS ATIVOS NO MAPA =====
function displayFiresOnMap(firesData) {
    const fires = firesData.data;

    markers.forEach(m => map.removeLayer(m));
    markers = [];

    if (fires.length === 0) {
        console.log('ℹ️ Sem fogos ativos para mostrar no mapa');
        return;
    }

    console.log(`🗺️ A adicionar ${fires.length} marcadores ao mapa...`);

    fires.forEach(fire => {
        const area = parseFloat(fire.area_hectares) || 10;
        const radius = Math.min(25, Math.max(8, Math.sqrt(area) * 2));

        const temp = parseFloat(fire.temperature) || 600;
        const color = temp > 800 ? '#FF0000' : (temp > 600 ? '#FF4400' : '#FF6600');

        const marker = L.circleMarker(
            [parseFloat(fire.latitude), parseFloat(fire.longitude)],
            {
                radius: radius,
                fillColor: color,
                color: '#FFA500',
                weight: 3,
                opacity: 1,
                fillOpacity: 0.8
            }
        ).addTo(map);

        marker.bindPopup(`
            <div style="font-family: Inter, sans-serif;">
                <strong style="color: #EF4444; font-size: 1.2rem;">${ICONS.fire} FOGO ATIVO</strong><br>
                <hr style="margin: 8px 0;">
                <strong>${fire.city || 'Desconhecido'}</strong><br>
                ${ICONS.area}${fire.area_hectares || 0} ha queimados<br>
                ${ICONS.clock}${formatActiveHours(fire.active_hours)}<br>
                ${ICONS.temp}${fire.temperature || 600}°C
            </div>
        `);

        markers.push(marker);
    });

    if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }

    console.log(`✅ ${fires.length} fogos ativos no mapa`);
}

function getRiskColor(riskValue) {
    const colors = {
        0: '#10B981',
        1: '#F59E0B',
        2: '#EF4444'
    };
    return colors[riskValue] || '#94A3B8';
}

// ===== GRAFICO HISTORICO =====
function plotHistory(historyData) {
    if (!document.getElementById('history-chart')) {
        console.error('Canvas #history-chart not found!');
        return;
    }
    const dates = Object.keys(historyData).sort();
    const riskData = dates.map(date => historyData[date].risk_avg * 100);
    const firesData = dates.map(date => historyData[date].fires_count);

    const labels = dates.map(date => {
        const d = new Date(date);
        return `${d.getDate()}/${d.getMonth() + 1}`;
    });

    const ctx = document.getElementById('history-chart');
    if (!ctx) return;

    if (historyChart) {
        historyChart.destroy();
    }

    historyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Risco Medio (%)',
                    data: riskData,
                    borderColor: '#EF4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    pointBackgroundColor: '#EF4444',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    yAxisID: 'y'
                },
                {
                    label: 'Fogos Ativos',
                    data: firesData,
                    borderColor: '#F59E0B',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.3,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#F59E0B',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#F1F5F9',
                        font: { size: 13, weight: '600' },
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#F1F5F9',
                    bodyColor: '#94A3B8',
                    borderColor: '#FF6B35',
                    borderWidth: 1,
                    padding: 12,
                    titleFont: { size: 14, weight: 'bold' },
                    bodyFont: { size: 13 }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#94A3B8',
                        font: { size: 12 }
                    },
                    grid: {
                        color: 'rgba(51, 65, 85, 0.3)',
                        drawBorder: false
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    min: 0,
                    max: 100,
                    ticks: {
                        color: '#10B981',
                        font: { size: 12, weight: '600' },
                        callback: value => value + '%'
                    },
                    grid: {
                        color: 'rgba(16, 185, 129, 0.1)',
                        drawBorder: false
                    },
                    title: {
                        display: true,
                        text: 'Risco (%)',
                        color: '#10B981',
                        font: { size: 13, weight: 'bold' }
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    min: 0,
                    ticks: {
                        color: '#F59E0B',
                        font: { size: 12, weight: '600' }
                    },
                    grid: {
                        drawOnChartArea: false,
                        drawBorder: false
                    },
                    title: {
                        display: true,
                        text: 'Fogos',
                        color: '#F59E0B',
                        font: { size: 13, weight: 'bold' }
                    }
                }
            }
        }
    });

    console.log('Grafico historico criado');
}

// ===== CIENCIA DO MODELO =====
let scienceExpanded = false;

window.toggleScience = function() {
    scienceExpanded = !scienceExpanded;
    const body = document.getElementById('science-body');
    const toggle = document.getElementById('science-toggle');
    if (body) body.style.display = scienceExpanded ? 'block' : 'none';
    if (toggle) toggle.classList.toggle('open', scienceExpanded);
};

function renderModelScience(data) {
    console.log('🔬 Model science data loaded:', data.accuracy_pct + '%');

    const section = document.getElementById('science-section');
    if (section) section.style.display = 'block';

    // Update subtitle
    const sub = document.getElementById('model-science-subtitle');
    if (sub) sub.textContent = 'Random Forest · Precisao: ' + data.accuracy_pct + '%';

    // Metrics row
    document.getElementById('sci-accuracy').textContent = data.accuracy_pct + '%';
    document.getElementById('sci-trees').textContent = data.n_trees || '--';
    document.getElementById('sci-features').textContent = data.n_features || '--';
    document.getElementById('sci-samples').textContent = data.n_samples ? data.n_samples.toLocaleString() : '--';

    renderConfusionMatrix(data.confusion_matrix);
    renderFeatureImportance(data.feature_importance, data.feature_names);
    renderClassMetrics(data.class_metrics);
    renderBaselineComparison(data.baseline);
}

function renderConfusionMatrix(cm) {
    if (!cm) return;
    const classes = ['baixo', 'medio', 'alto'];
    for (let i = 0; i < 3; i++) {
        for (let j = 0; j < 3; j++) {
            const cell = document.getElementById('cm-' + classes[i] + '-' + classes[j]);
            if (!cell) continue;
            const val = cm[classes[i]] && cm[classes[i]][classes[j]];
            if (val) {
                const isDiagonal = i === j;
                cell.innerHTML = val.pct + '%<span class="cm-count">(' + val.count + ')</span>';
                if (isDiagonal) {
                    cell.className = 'cm-cell ' + (i === 0 ? 'cm-baixo' : i === 1 ? 'cm-medio' : 'cm-alto');
                }
            }
        }
    }
}

function renderFeatureImportance(featureImportance, featureNames) {
    const container = document.getElementById('feature-importance-bars');
    if (!container || !featureImportance) return;

    const barColors = ['bar-green', 'bar-blue', 'bar-purple', 'bar-orange', 'bar-red', 'bar-teal', 'bar-indigo', 'bar-pink'];

    // Sort features by importance descending
    const sorted = featureNames
        ? featureNames.map((name, i) => ({ name: name, importance: featureImportance[name] || 0 }))
            .sort((a, b) => b.importance - a.importance)
        : Object.entries(featureImportance)
            .map(([name, imp]) => ({ name, importance: imp }))
            .sort((a, b) => b.importance - a.importance);

    const maxImp = sorted[0] ? sorted[0].importance : 1;

    let html = '';
    sorted.forEach((item, idx) => {
        const pct = (item.importance * 100).toFixed(1);
        const widthPct = (item.importance / maxImp * 100).toFixed(1);
        const colorClass = barColors[idx % barColors.length];
        const nameLabel = item.name.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
        html += '<div class="fi-bar-group">'
            + '<span class="fi-bar-name">' + nameLabel + '</span>'
            + '<div class="fi-bar-track">'
            + '<div class="fi-bar-fill ' + colorClass + '" style="width:' + widthPct + '%">' + pct + '%</div>'
            + '</div>'
            + '</div>';
    });

    container.innerHTML = html;
}

function renderClassMetrics(metrics) {
    if (!metrics) return;
    const classes = ['alto', 'medio', 'baixo'];
    classes.forEach(cls => {
        const m = metrics[cls];
        if (!m) return;
        const set = function(id, val) {
            const el = document.getElementById(id);
            if (el) el.textContent = val !== undefined ? (val * 100).toFixed(1) + '%' : '--';
        };
        set('cm-' + cls + '-prec', m.precision);
        set('cm-' + cls + '-recall', m.recall);
        set('cm-' + cls + '-f1', m.f1_score);
    });
}

function renderBaselineComparison(baseline) {
    if (!baseline) return;
    const baseAcc = baseline.accuracy || 0;
    const mlAcc = parseFloat(document.getElementById('sci-accuracy')?.textContent || '0');
    const mlAccNum = parseFloat(mlAcc) / 100;
    const improvement = baseline.ml_improvement !== undefined ? baseline.ml_improvement : (mlAccNum - baseAcc);

    // Animate bars after a short delay
    setTimeout(() => {
        const baseBar = document.getElementById('baseline-base-bar');
        const mlBar = document.getElementById('baseline-ml-bar');
        const improvementEl = document.getElementById('baseline-improvement');

        if (baseBar) {
            const basePct = (baseAcc * 100).toFixed(1);
            baseBar.style.width = basePct + '%';
            baseBar.textContent = basePct + '%';
        }
        if (mlBar) {
            const mlPct = mlAcc;
            mlBar.style.width = mlPct + '%';
            mlBar.textContent = mlPct + '%';
        }
        if (improvementEl) {
            const impPct = (improvement * 100).toFixed(1);
            improvementEl.textContent = 'Ganho: +' + impPct + '% com Machine Learning';
        }
    }, 300);
}

// ===== SIMULACAO INTERATIVA =====
async function runSimulation(cityName) {
    const simResult = document.getElementById('sim-result');
    if (!cityName) {
        simResult.innerHTML = `<div class="sim-result-placeholder">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="1.5">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            </svg>
            <p>Clique num distrito do mapa para simular</p>
        </div>`;
        return;
    }

    const temp = document.getElementById('sim-temp').value;
    const humidity = document.getElementById('sim-humidity').value;
    const wind = document.getElementById('sim-wind').value;

    simResult.innerHTML = '<div style="color: var(--color-text-muted);">A calcular...</div>';

    try {
        const risk = await fetchAPI(`/risk/${encodeURIComponent(cityName)}?temperature=${temp}&humidity=${humidity}&wind_speed=${wind}`, 10000);
        const color = getRiskColor(risk.risk_value);

        let ndviImpactHtml = '';
        if (risk.ndvi_comparison) {
            ndviImpactHtml = `<div class="sim-result-ndvi-impact">
                ${ICONS.satellite} Impacto do NDVI real: risco sem satélite seria <strong>${risk.ndvi_comparison.estimated_risk_level}</strong>
                (NDVI real ${risk.ndvi.toFixed(3)} vs estimado ${risk.ndvi_comparison.estimated_ndvi.toFixed(3)})
            </div>`;
        }

        simResult.innerHTML = `<div class="sim-result-active">
            <div class="sim-result-city">${cityName}</div>
            <div class="sim-result-risk" style="background: ${color};">${risk.risk_level}</div>
            <div class="sim-result-details">
                <span>Confiança: ${risk.confidence.toFixed(1)}%</span>
                <span>NDVI: ${risk.ndvi.toFixed(3)} (${risk.ndvi_source || 'N/A'})</span>
            </div>
            <div class="sim-result-details">
                <span>${risk.temperature.toFixed(1)}C / ${risk.humidity.toFixed(0)}% / ${wind} km/h</span>
            </div>
            ${ndviImpactHtml}
        </div>`;
    } catch (error) {
        simResult.innerHTML = '<div style="color: #EF4444; font-size: 0.85rem;">Erro ao simular. Tente novamente.</div>';
    }
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            console.log('Refresh manual');
            loadAllData();
        });
    }

    const fullscreenBtn = document.getElementById('fullscreen-btn');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', () => {
            const mapContainer = document.querySelector('.map-container');
            if (!mapContainer) return;

            const isFullscreen = mapContainer.classList.toggle('fullscreen');

            if (isFullscreen) {
                fullscreenBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;"><path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/></svg> Sair do Ecra Completo';
            } else {
                fullscreenBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg> Ecra Completo';
            }

            setTimeout(() => {
                if (map) map.invalidateSize();
            }, 300);
        });
    }

    // Simulation slider listeners (debounced 300ms to avoid API spam)
    const debouncedSim = debounce((city) => runSimulation(city), 300);
    const simSliders = ['sim-temp', 'sim-humidity', 'sim-wind'];
    simSliders.forEach(id => {
        const slider = document.getElementById(id);
        const display = document.getElementById(id + '-value');
        if (slider && display) {
            slider.addEventListener('input', () => {
                display.textContent = slider.value;
                if (simSelectedCity) {
                    debouncedSim(simSelectedCity);
                }
            });
        }
    });

    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('light-mode');
        });
    }

    // Language toggle
    const langToggle = document.getElementById('lang-toggle');
    if (langToggle) {
        langToggle.addEventListener('click', toggleLanguage);
    }

    // Apply saved language on page load
    applyLanguage(currentLang);
}

console.log('📊 EmberEdge Dashboard carregado');
console.log('🔗 API Base:', API_BASE);