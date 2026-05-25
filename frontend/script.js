/* ============================================================
   EMBEREDGE - DASHBOARD INCÊNDIOS
   JavaScript COMPLETO - Leaflet + Chart.js + API Integration
   ============================================================ */

// ===== CONFIGURAÇÃO =====
const API_BASE = window.location.origin + '/api';
let map = null;
let markers = [];
let historyChart = null;
let districtLayer = null;

// ===== ÍCONES SVG =====
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
    check: '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>'
};

// ===== MAPEAMENTO DE NOMES (GeoJSON -> Cidades) =====
const CITY_NAME_MAP = {
    'Santarem': 'Santarem',
    'Castelo Branco': 'Castelo Branco',
    'Vila Real': 'Vila Real',
    'Viana do Castelo': 'Viana do Castelo',
    'Bragança': 'Braganca',
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
            <h4>Lenda do Mapa</h4>
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
                <span>Heatmap</span>
            </div>
            <div class="legend-item">
                <span style="color:#EF4444;margin-right:4px;">■</span><span style="color:#F59E0B;margin-right:4px;">■</span><span style="color:#10B981;">■</span>
                <span style="margin-left:8px;">Alto/Médio/Baixo</span>
            </div>
        `;
        return div;
    };
    legend.addTo(map);
    
    console.log('✅ Mapa criado!');
}

// ===== CARREGAR TODOS OS DADOS =====
async function loadAllData() {
    console.log('📡 Carregando dados...');
    updateStatus('Atualizando dados...', false);

    try {
        const [stats, fires, weather, history, riskAll] = await Promise.all([
            fetchAPI('/stats'),
            fetchAPI('/fires'),
            fetchAPI('/weather'),
            fetchAPI('/history'),
            fetchAPI('/risk/all')
        ]);

        updateStats(stats);
        displayFires(fires);
        await displayRiskCities(weather);
        plotHistory(history);
        displayFiresOnMap(fires);
        await addDistrictLayer(weather);

        // Verificar alertas de risco alto
        checkAlerts(riskAll);

        // Mostrar heatmap de risco
        displayHeatmap(riskAll);

        updateStatus('Dados atualizados', true);
        updateLastUpdate();

    } catch (error) {
        console.error('❌ Erro carregar dados:', error);
        updateStatus('Erro ao carregar', false);
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

    // Remover heatmap anterior se existir
    if (heatLayer) {
        map.removeLayer(heatLayer);
    }

    const heatPoints = [];

    for (const [city, data] of Object.entries(riskAll.data)) {
        if (data.coordinates && data.risk_value !== undefined) {
            const lat = data.coordinates.lat;
            const lon = data.coordinates.lon;
            const risk = data.risk_value; // 0, 1, or 2

            // Normalizar: Baixo=0.3, Médio=0.6, Alto=1.0
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
                0.3: '#10B981',  // Verde (Baixo)
                0.6: '#F59E0B',  // Amarelo (Médio)
                1.0: '#EF4444'   // Vermelho (Alto)
            }
        }).addTo(map);
        console.log(`🔥 Heatmap adicionado: ${heatPoints.length} pontos`);
    }
}

// ===== CAMADA DE DISTRITOS PORTUGAL (HOVER) =====
async function addDistrictLayer(weatherData) {
    console.log('🗺️ Adicionando camada de distritos...');
    
    try {
        const response = await fetch('https://raw.githubusercontent.com/codeforgermany/click_that_hood/master/public/data/portugal.geojson');
        const geoData = await response.json();
        
        const cities = weatherData.data;
        
        districtLayer = L.geoJSON(geoData, {
            style: {
                fillColor: 'transparent',
                fillOpacity: 0,
                color: 'transparent',
                weight: 0
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
                    layer.on('mouseover', async function(e) {
                        try {
                            const risk = await fetchAPI('/risk/' + encodeURIComponent(cityData));
                            const color = getRiskColor(risk.risk_value);
                            
                            this.setStyle({
                                fillColor: color,
                                fillOpacity: 0.35,
                                color: color,
                                weight: 2
                            });
                            
                            const popup = L.popup()
                                .setLatLng(e.latlng)
                                .setContent(`
                                    <div style="font-family: Inter, sans-serif; min-width: 220px;">
                                        <strong style="font-size: 1.2rem; color: ${color};">${cityData}</strong>
                                        <hr style="margin: 8px 0; border: none; border-top: 1px solid #e5e7eb;">
                                        <div style="margin: 10px 0;">
                                            <strong>Risco:</strong><br>
                                            <span style="background: ${color}; color: white; padding: 4px 12px; border-radius: 6px; font-weight: bold; display: inline-block; margin-top: 4px;">
                                                ${risk.risk_level}
                                            </span>
                                        </div>
                                        <div style="margin: 10px 0; font-size: 0.85rem; color: #6b7280;">
                                            ${ICONS.target}Confiança: <strong>${risk.confidence.toFixed(1)}%</strong>
                                        </div>
                                        <hr style="margin: 8px 0; border: none; border-top: 1px solid #e5e7eb;">
                                        <div style="font-size: 0.85rem; color: #6b7280;">
                                            ${ICONS.temp}${cityWeather.temperature.toFixed(1)}°C | 
                                            ${ICONS.wind}${cityWeather.wind_speed.toFixed(1)} km/h<br>
                                            ${ICONS.humidity}${cityWeather.humidity.toFixed(0)}% | 
                                            ${ICONS.area}${cityWeather.precipitation.toFixed(1)} mm
                                        </div>
                                    </div>
                                `)
                                .openOn(map);
                        } catch (error) {
                            console.error('❌ Erro ao buscar risco:', error);
                        }
                    });
                    
                    layer.on('mouseout', function() {
                        this.setStyle({
                            fillColor: 'transparent',
                            fillOpacity: 0,
                            color: 'transparent',
                            weight: 0
                        });
                        map.closePopup();
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
        console.log('⚠️ Fallback: Usando marcadores invisíveis...');
        await displayInvisibleMarkers(weatherData);
    }
}

// ===== FALLBACK - MARCADORES INVISÍVEIS =====
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
    
    console.log('✅ ' + markers.length + ' marcadores invisíveis criados');
}

// ===== FETCH API =====
async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        
        if (!response.ok) {
            console.error(`❌ API Error: ${response.status} at ${endpoint}`);
            throw new Error(`HTTP ${response.status}: ${endpoint}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error(`❌ Fetch failed for ${endpoint}:`, error);
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

function updateLastUpdate() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('pt-PT', {
        hour: '2-digit',
        minute: '2-digit'
    });
    document.getElementById('last-update-time').textContent = timeStr;
}

// ===== ESTATÍSTICAS COM ÍCONES SVG =====
function updateStats(stats) {
    const data = stats.data;
    
    const html = `
        <div class="stat-row">
            <span>${ICONS.fire}Fogos Ativos</span>
            <strong>${data.active_fires}</strong>
        </div>
        <div class="stat-row">
            <span>${ICONS.area}Área Queimada</span>
            <strong>${data.total_area_ha} ha</strong>
        </div>
        <div class="stat-row">
            <span>${ICONS.temp}Temperatura Média</span>
            <strong>${data.avg_temperature}°C</strong>
        </div>
        <div class="stat-row">
            <span>${ICONS.wind}Vento Médio</span>
            <strong>${data.avg_wind} km/h</strong>
        </div>
        <div class="stat-row">
            <span>${ICONS.humidity}Humidade Média</span>
            <strong>${data.avg_humidity}%</strong>
        </div>
        <div class="stat-row">
            <span>${ICONS.alert}Cidades em Risco</span>
            <strong style="color: #EF4444;">${data.cities_at_risk}</strong>
        </div>
    `;
    
    document.getElementById('stats-content').innerHTML = html;
}

// ===== FOGOS ATIVOS COM ÍCONES SVG =====
function displayFires(firesData) {
    const fires = firesData.data;
    
    if (fires.length === 0) {
        document.getElementById('fires-content').innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--color-text-secondary);">
                <div style="margin-bottom: 1rem;">${ICONS.check}</div>
                <p style="margin-top: 1rem; font-weight: 600;">Nenhum fogo ativo no momento</p>
                <p style="font-size: 0.85rem; margin-top: 0.5rem; opacity: 0.7;">Última verificação: ${new Date().toLocaleTimeString('pt-PT')}</p>
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
                        ${ICONS.clock}${fire.active_hours || 0}h ativo | 
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

// ===== CIDADES RISCO COM ÍCONES SVG =====
async function displayRiskCities(weatherData) {
    const cities = weatherData.data;
    const cityNames = Object.keys(cities);
    
    if (cityNames.length === 0) {
        document.getElementById('risk-cities-content').innerHTML = 
            '<p style="text-align:center;color:var(--color-text-secondary);">Sem dados</p>';
        return;
    }
    
    const citiesWithRisk = [];
    
    for (const city of cityNames.slice(0, 15)) {
        try {
            const riskData = await fetchAPI(`/risk/${encodeURIComponent(city)}`);

            if (riskData.status === 'success') {
                citiesWithRisk.push({
                    name: city,
                    ...riskData.data
                });
            }
        } catch (error) {
            console.error(`Erro risco ${city}:`, error);
        }
    }

    citiesWithRisk.sort((a, b) => b.risk_value - a.risk_value);

    const topCities = citiesWithRisk.slice(0, 5);

    if (topCities.length === 0) {
        document.getElementById('risk-cities-content').innerHTML =
            '<p style="text-align:center;color:var(--color-text-secondary);padding:1rem;">Sem dados de risco disponíveis</p>';
        return;
    }

    let html = '<ul class="risk-list">';
    
    topCities.forEach((city, idx) => {
        const colors = {
            0: '#10B981',
            1: '#F59E0B',
            2: '#EF4444'
        };
        const riskColor = colors[city.risk_value];
        
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
                        ${ICONS.temp}${city.temperature}°C |
                        ${ICONS.humidity}${city.humidity}% humidade |
                        ${ICONS.target}${city.confidence?.toFixed(0)}% confiança
                        ${city.ndvi ? `| NDVI: <span style="color:${city.ndvi > 0.6 ? '#10B981' : (city.ndvi > 0.3 ? '#F59E0B' : '#EF4444')}">${city.ndvi.toFixed(2)}</span>` : ''}
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

    // Limpar marcadores anteriores
    markers.forEach(m => map.removeLayer(m));
    markers = [];

    if (fires.length === 0) {
        console.log('ℹ️ Sem fogos ativos para mostrar no mapa');
        return;
    }

    console.log(`🗺️ A adicionar ${fires.length} marcadores ao mapa...`);

    fires.forEach(fire => {
        // Dynamic radius based on burned area
        const area = parseFloat(fire.area_hectares) || 10;
        const radius = Math.min(25, Math.max(8, Math.sqrt(area) * 2));

        // Color based on temperature (hotter = brighter red)
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
                ${ICONS.clock}${fire.active_hours || 0}h ativo<br>
                ${ICONS.temp}${fire.temperature || 600}°C
            </div>
        `);
        
        markers.push(marker);
    });

    // Ajustar o mapa para mostrar todos os fogos
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

// ===== GRÁFICO HISTÓRICO =====
function plotHistory(historyData) {
    // No script.js, adiciona isto logo no início da plotHistory:
console.log('plotHistory called with:', historyData);
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
                    label: 'Risco Médio (%)',
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
    
    console.log('✅ Gráfico histórico criado');
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            console.log('🔄 Refresh manual');
            loadAllData();
        });
    }
    
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', () => {
            const mapContainer = document.querySelector('.map-container');

            if (!mapContainer) return;

            if (mapContainer.classList.contains('fullscreen')) {
                mapContainer.classList.remove('fullscreen');
                fullscreenBtn.innerHTML = `
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;">
                        <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
                    </svg>
                    Fullscreen
                `;
            } else {
                mapContainer.classList.add('fullscreen');
                fullscreenBtn.innerHTML = `
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;">
                        <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/>
                    </svg>
                    Exit Fullscreen
                `;
            }

            setTimeout(() => {
                if (map) map.invalidateSize();
            }, 300);
        });
    }
    
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('light-mode');
        });
    }
}

console.log('📊 EmberEdge Dashboard carregado');
console.log('🔗 API Base:', API_BASE);
