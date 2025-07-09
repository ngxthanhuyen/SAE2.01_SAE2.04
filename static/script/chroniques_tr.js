// Initialisation de la carte
const map = L.map('map').setView([46.603354, 1.888334], 6);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

//On déclare les variables globales qui permettent de stocker les données
let selectedDepartment = null;
let markersLayer = L.layerGroup().addTo(map);
let clickedLayer = null;
let pieChart = null;
let barChart = null;
let stationData = null;

const info = L.control();

info.onAdd = function () {
    this._div = L.DomUtil.create('div', 'info');
    this.update();
    return this._div;
};

info.update = function () {
    this._div.innerHTML;
};

info.addTo(map);

//Charger les données GeoJson
fetch('https://france-geojson.gregoiredavid.fr/repo/departements.geojson')
    .then(response => response.json())
    .then(data => {
        geojson = L.geoJson(data, {
            style: style,
            onEachFeature: onEachFeature
        }).addTo(map);
    });

function style() {
    return {
        color: '#000000',
        weight: 1,
        opacity: 0.25,
        fillColor: '#86aae0',
        fillOpacity: 1
    };
}

function highlightFeature(e) {
    const layer = e.target;
    if (layer !== clickedLayer && !selectedDepartment) {
        layer.setStyle({
            weight: 5,
            color: '#666',
            fillColor: '#86cce0',
            fillOpacity: 0.7
        });
    }
    info.update(layer.feature.properties);
}

function resetHighlight(e) {
    const layer = e.target;
    if (layer !== clickedLayer && !selectedDepartment) {
        geojson.resetStyle(layer);
    }
    info.update();
}

function onEachFeature(feature, layer) {
    layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight,
        click: stationsParDepartement
    });
    layer.bindTooltip(`${feature.properties.nom} (${feature.properties.code})`);
}

//Afficher le préchargeur et la superposition lorsque le formulaire est soumis
function showPreloader() {
    document.getElementById('preloader').style.display = 'block';
    document.getElementById('overlay').style.display = 'block';
}

//Masquer le préchargeur et la superposition lorsque la page a fini de se charger
function hidePreloader() {
    document.getElementById('preloader').style.display = 'none';
    document.getElementById('overlay').style.display = 'none';
}

function stationsParDepartement(e) {
    if (clickedLayer) {
        geojson.resetStyle(clickedLayer);
    }
    clickedLayer = e.target;
    const bounds = e.target.getBounds();
    map.fitBounds(bounds);
    selectedDepartment = e.target.feature.properties.nom;

    markersLayer.clearLayers();

    showPreloader();

    fetch(`/stations_temps_reel?departement=${selectedDepartment}`)
        .then(response => response.json())
        .then(stations => {
            stationData = stations
            if (stations.length > 0) {
                stations.forEach(station => {
                    const marker = L.marker([station.y, station.x], {
                        icon: createCustomIcon(station.color)
                    });
                    marker.on('click', () => {
                        updateSidebar(station);
                    });
                    markersLayer.addLayer(marker);
                });
                markersLayer.addTo(map);
                hidePreloader();

                //On vérifie l'état de la case à cocher et afficher les graphiques si elle est cochée
                if (document.getElementById('toggle-charts').checked) {
                    const chartContainer = document.querySelector('.chart-container');
                    chartContainer.style.display = 'flex';
                    chartContainer.scrollIntoView({ behavior: 'smooth' });
                    createPieChart(stationData);
                    createBarChart(stationData);
                }
            }
        });

    geojson.eachLayer(function (layer) {
        if (layer.feature.properties.nom === selectedDepartment) {
            layer.setStyle({
                fillColor: 'lightblue',
                weight: 5,
                color: '#666',
                fillOpacity: 0.7
            });
        } else {
            layer.setStyle({
                fillColor: '#808080',
                weight: 1,
                color: 'black',
                fillOpacity: 0.8
            });
        }
    });
}

//Fonction pour créer une icône de marqueur personnalisée
function createCustomIcon(color) {
    const markerHtmlStyles = `
        background-color: ${color || '#CCCCCC'};
        width: 30px;
        height: 30px;
        display: block;
        left: -15px;
        top: -15px;
        position: relative;
        border-radius: 30px 30px 0;
        transform: rotate(45deg);
        border: 1px solid #FFFFFF;
        opacity: 1;
        background-image: url('static/images/vague.png');
        background-size: cover;
        `;
    return L.divIcon({
        className: "my-custom-pin",
        iconAnchor: [10, 20],
        labelAnchor: [-6, 0],
        popupAnchor: [0, -30],
        html: `<span style="${markerHtmlStyles}" />`
    });
}

//Fontion pour mettre à jour les valeurs dans sidebar lorsque l'utilisateur choisit une station 
function updateSidebar(station) {
    const ngfValue = document.getElementById('ngf-value');
    const pfnValue = document.getElementById('pfn-value');
    const stationId = document.getElementById('station-id');
    const dateMesure = document.getElementById('date-de-mesure');
    
    ngfValue.textContent = station.niveau_eau_ngf.toFixed(2);
    pfnValue.textContent = station.profondeur_nappe.toFixed(2);
    stationId.textContent = station.code_bss;
    dateMesure.textContent = station.date_mesure;
}

document.addEventListener('DOMContentLoaded', function() {
    const chartContainer = document.querySelector('.chart-container');
    chartContainer.style.display = 'none';
    document.getElementById('toggle-charts').checked = false;
});

document.getElementById('toggle-charts').addEventListener('change', function() {
    const chartContainer = document.querySelector('.chart-container');
    if (this.checked) {
        chartContainer.style.display = 'flex';
        chartContainer.scrollIntoView({ behavior: 'smooth' });
         if (stationData) {
            createPieChart(stationData);
            createBarChart(stationData);
        }
        this.checked = false;
    } else {
        chartContainer.style.display = 'none';
    }
});


document.addEventListener('DOMContentLoaded', function() {
    const chartContainer = document.querySelector('.chart-container');
    chartContainer.style.display = 'none';
    document.getElementById('toggle-charts').checked = false; 
});


//Fonction pour créer le diagramme circulaire
function createPieChart(stations) {
    const categories = {
        'Niveau très bas': 0,
        'Niveau bas': 0,
        'Niveau modérément bas': 0,
        'Niveau proche de la moyenne': 0,
        'Niveau modérément haut': 0,
        'Niveau haut': 0,
        'Niveau très haut': 0,
    };

    stations.forEach(station => {
        const z = calculateZScore(station);
        if (z !== null) {
            if (z > 1.28) {
                categories['Niveau très haut']++;
            } else if (z > 0.84) {
                categories['Niveau haut']++;
            } else if (z > 0.25) {
                categories['Niveau modérément haut']++;
            } else if (z > -0.25) {
                categories['Niveau proche de la moyenne']++;
            } else if (z > -0.84) {
                categories['Niveau modérément bas']++;
            } else if (z > -1.28) {
                categories['Niveau bas']++;
            } else if (z <= -1.28) {
                categories['Niveau très bas']++;
            }
        }
    });

    if (pieChart) {
        pieChart.destroy();
    }

    const pieCanvas = document.getElementById('piechart').getContext('2d');
    pieChart = new Chart(pieCanvas, {
        type: 'pie',
        data: {
            labels: Object.keys(categories),
            datasets: [{
                label: 'Niveaux des nappes piezométriques dans ce département',
                data: Object.values(categories),
                backgroundColor: [
                    '#DB442C', '#F18E00', '#FFDD57', '#6DC55A',
                    '#32A9DD', '#1B75BB', '#286273', '#CCCCCC'
                ],
                borderColor: '#ffffff',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let label = context.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.raw;
                            return label;
                        }
                    }
                }
            }
        }
    });
}

function calculateZScore(station) {
    if (station.moyenne_niveaux !== undefined && station.ecart_type_niveaux !== undefined && station.ecart_type_niveaux !== 0) {
        return (station.niveau_eau_ngf - station.moyenne_niveaux) / station.ecart_type_niveaux;
    }
    return null;
}

//Fonction pour créer le diagramme en batons
function createBarChart(stations) {
    const categories = {
        'Niveau très bas': 0,
        'Niveau bas': 0,
        'Niveau modérément bas': 0,
        'Niveau proche de la moyenne': 0,
        'Niveau modérément haut': 0,
        'Niveau haut': 0,
        'Niveau très haut': 0,
    };

    stations.forEach(station => {
        const z = calculateZScore(station);
        if (z !== null) {
            if (z > 1.28) {
                categories['Niveau très haut']++;
            } else if (z > 0.84) {
                categories['Niveau haut']++;
            } else if (z > 0.25) {
                categories['Niveau modérément haut']++;
            } else if (z > -0.25) {
                categories['Niveau proche de la moyenne']++;
            } else if (z > -0.84) {
                categories['Niveau modérément bas']++;
            } else if (z > -1.28) {
                categories['Niveau bas']++;
            } else if (z <= -1.28) {
                categories['Niveau très bas']++;
            } else {
                categories['Indéfini']++;
            }
        }
    });

    if (barChart) {
        barChart.destroy();
    }

    const barCanvas = document.getElementById('barchart').getContext('2d');
    barChart = new Chart(barCanvas, {
        type: 'bar',
        data: {
            labels: Object.keys(categories),
            datasets: [{
                label: 'Niveaux des nappes',
                data: Object.values(categories),
                backgroundColor: [
                    '#DB442C', '#F18E00', '#FFDD57', '#6DC55A',
                    '#32A9DD', '#1B75BB', '#286273', '#CCCCCC'
                ],
                borderColor: '#ffffff',
                borderWidth: 1,
                barThickness: 50
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 0,
                        font: {
                            size: 18
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let label = context.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.raw;
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        autoSkip: false
                    },
                    categoryPercentage: 0.5,
                    barPercentage: 0.8
                },
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}
