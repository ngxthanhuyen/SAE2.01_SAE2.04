//On récupère les éléments nécessaires du DOM dès que le script est chargé
const input = document.getElementById('search');
const dropdown = document.getElementById('autocomplete');
//Index pour suivre l'élément actuellement en focus dans les suggestions
let currentFocus = -1;
//On déclare map au niveau global
let map;

//écouteur pour les saisies dans le champ de recherche
input.addEventListener("input", getCommuneData);

//écouteur pour la gestion des touches du clavier (flèche haut/bas et entrée)
input.addEventListener("keydown", function(e) {
    //On collecte toutes les suggestions actuellement affichées
    let items = dropdown.querySelectorAll(".autocomplete-items");
    switch (e.keyCode) {
        case 40: //Flèche bas
            currentFocus++;
            if (currentFocus >= items.length) currentFocus = 0; 
            addActive(items);
            break;
        case 38: //Flèche haut
            currentFocus--;
            if (currentFocus < 0) currentFocus = items.length - 1; 
            addActive(items);
            break;
        case 13: //Entrée
            e.preventDefault(); //On empêche le formulaire de s'envoyer
            if (currentFocus > -1 && items.length) {
                items[currentFocus].click();
            }
            break;
    }
});
///////////////////////////////////////////////////////////////////////////////////////
//Fonction pour récupérer les données des communes basées sur la saisie de l'utilisateur
///////////////////////////////////////////////////////////////////////////////////////
function getCommuneData() {
    let val = this.value;
    if (!val) {
        val = input.value; 
    }
    //On efface les suggestions après la sélection ou lorsque l'utilisateur modifie sa recherche
    dropdown.innerHTML = '';
    //On réinitialise 'currentFocus' à -1 chaque fois que les données de l'input changent
    currentFocus = -1;
    //Si l'input de la recherche contient un élément
    if (val.length > 0) {
        //On envoie une requête au serveur pour obtenir les données des communes basées sur le texte saisi
        fetch(`/recherche_communes?query=${encodeURIComponent(val)}`)
            .then(response => response.json())
            .then(data => {
                //Pour chaque commune reçue du serveur, on crée un nouvel élément div dans la liste déroulante
                data.forEach(commune => {
                    const item = document.createElement('div');
                    item.innerHTML = commune.replace(new RegExp(val, 'gi'), (match) => `<strong>${match}</strong>`); //On remplace les correspondances par des versions en gras
                    item.classList.add('autocomplete-items');
                    item.addEventListener("click", function() {
                        //On met à jour le champ de recherche avec la valeur sélectionnée
                        input.value = commune;
                        dropdown.innerHTML = '';
                    });
                    //On ajoute l'élément de suggestion au DOM
                    dropdown.appendChild(item);
                });
            })
            .catch(error => console.error('Error: ', error));
    }
}
////////////////////////////////////////////////////////////////////////////////////////////////////////
//Fonction pour ajouter la classe 'active' à un élément (pour le menu déroulant de recherche de communes)
////////////////////////////////////////////////////////////////////////////////////////////////////////
function addActive(items) {
    if (!items) return;
    removeActive(items);
    items[currentFocus].classList.add("autocomplete-active");
    //On fait défiler les éléments dans la vue visible
    items[currentFocus].scrollIntoView( {
        behavior: 'smooth',
        block: 'nearest',
        inline: 'start'
    });
    //On met à jour l'input de recherche avec le texte de l'élément actif
    input.value = items[currentFocus].textContent;
}

////////////////////////////////////////////////////////////////////////////////////////////////////////
//Fonction pour ajouter la classe 'remove' à un élément (pour le menu déroulant de recherche de communes)
////////////////////////////////////////////////////////////////////////////////////////////////////////
function removeActive(items) {
    for (let i = 0; i < items.length; i++) {
        items[i].classList.remove("autocomplete-active");
    }
}


/////////////////////////////////////////////////////////////////////////////////////////////////////
// Fonction pour initialiser la carte Leaflet au chargement de la fenêtre
//////////////////////////////////////////////////////////////////////////////////////////////////////
function init() {
    const centerLoc = [48.8588548, 2.347035];
    map = L.map('map').setView(centerLoc, 4.8);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    loadStationsList();
}

window.onload = init;

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//Fonction pour charger toutes les stations et appelle la fonction 'populateStationList' pour afficher une liste de toutes les stations initialement 
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
function loadStationsList() {
    fetch('/stations_data')
        .then(response => response.json())
        .then(stations => {
            populateStationList(stations);
    });
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//Fonction pour ajouter les marqueurs de stations sur la carte lorsque l'utilisateur clique sur une station dans la liste 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
function addMarkerForStation(station) {
    const { x, y, code_bss } = station;
    if (x && y) {
        const marker = L.marker([y, x]).addTo(map);
        marker.bindPopup(`Code BSS: ${code_bss}`).openPopup();
        mapMarkers.push(marker);

        //On ajoute un événement pour rechercher et afficher les détails de la station
        marker.on('click', () => {
            searchStationInList(code_bss); //Recherche et affiche les détails de la station dans la liste
        });

        map.setView([y, x], 14);
    }
}

////////////////////////////////////////////////////////////
//Fonction pour afficher la liste de toutes les stations 
///////////////////////////////////////////////////////////
function populateStationList(stations) {
    const list = document.getElementById('stationList');
    list.innerHTML ='';
    stations.forEach(station => {
        let code_bss, x, y;

        //On vérifie si les requêtes renvoient les résultats sous forme de tuple ou de dictionnaire et les extrait ensuite selon en fonction de leur format
        if (Array.isArray(station)) {
            [code_bss, x, y] = station;
        } else if (station && typeof station === 'object') {
            ({ code_bss, x, y } = station);
        } else {
            console.error('Format de données de station inconnu:', station);
            return; 
        }
        //On vérifie que les stations ont des coordonnées valides
        if (x !== null && y !== null) {  
            const li = document.createElement('li');
            const img = document.createElement('img');
            img.src ='static/images/location.png';
            img.alt ='location icon';
            img.style.width='26px';
            img.style.height='26px';
            img.style.marginRight = '8px'; 
            const textSpan = document.createElement('span');
            
            const code_bss = station[0] ? station[0] : station.code_bss; 
            textSpan.textContent = `Station: ${code_bss}`;
            li.appendChild(img); 
            li.appendChild(textSpan);
            li.onclick = () => {
                //Appelle cette fonction pour afficher toutes les informations pour la station choisie
                showStationDetails(code_bss);
                //Appelle cette fonction pour afficher les marqueurs sur la carte en fonction des stations sélectionnées dans la liste
                addMarkerForStation({ code_bss, x, y }); 
            };
            list.appendChild(li);
        }
    });
}

//////////////////////////////////////////////////////////////////////////////////////
//Fonction pour afficher toutes les informations pour la station choisie dans la liste
//////////////////////////////////////////////////////////////////////////////////////
function showStationDetails(code_bss) {
    fetch(`/get_station_details?code_bss=${encodeURIComponent(code_bss)}`)
        .then(response => response.json())
        .then(station => {
            const detailsDiv = document.getElementById('stationDetails');
            detailsDiv.style.display = 'block';  
            const detailsContent = `
                <h3>Station ${station.code_bss}</h3>
                <p><strong>ID BSS:</strong> ${station.bss_id}</p>
                <p><strong>Commune:</strong> ${station.code_commune_insee} - ${station.nom_commune}</p>
                <p><strong>Département:</strong> ${station.code_departement} - ${station.nom_departement}</p>
                <p><strong>Profondeur d'investigation:</strong> ${station.profondeur_investigation}</p>
                <p><strong>Altitude de la station:</strong> ${station.altitude_station}</p>
                <p><strong>Nombre minimal de mesures piézométriques requis:</strong> ${station.nb_mesures_piezo}</p>
                <p><strong>Accéder au chronique: </strong> <a href = "/chroniques?code_bss=${encodeURIComponent(station.code_bss)}" targer="_blank">Voir le graphique</a><p>
        `;
        detailsDiv.querySelector('.details-content').innerHTML = detailsContent;  
    })
}
    

document.addEventListener('DOMContentLoaded', function() {
    const closeButton = document.querySelector('.close-btn');
    if (closeButton) {
        closeButton.addEventListener('click', function() {
            document.getElementById('stationDetails').style.display = 'none';
        });
    }
});

//Fonction pour rechercher la station dans la liste et afficher les détails
function searchStationInList(code_bss) {
    const list = document.getElementById('stationList');
    const items = list.getElementsByTagName('li');

    for (let item of items) {
        const textSpan = item.querySelector('span');
        if (textSpan.textContent.includes(code_bss)) {
            item.click(); //On simule un clic sur l'élément pour afficher les détails
            break;
        }
    }
}

//On déclare globalement les marqueurs et le cercle de la commune
var mapMarkers = [];
var communeCircle = null;

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//Fonction pour nettoyer tous les marqueurs et le cercle de la carte(pour mettre à jour la recherche de l'utilisateur)
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
function clearMarkers() {
    mapMarkers.forEach(marker => marker.remove());
    mapMarkers = [];
    if (communeCircle) {
        communeCircle.remove();
        communeCircle = null;
    }
}
function showPreloader() {
    document.getElementById('preloader').style.display = 'block';
    document.getElementById('overlay').style.display = 'block';
}

function hidePreloader() {
    document.getElementById('preloader').style.display = 'none';
    document.getElementById('overlay').style.display = 'none';
}
///////////////////////////////////////////////////////////////////////////////////////////////
//Fonction pour charger les stations dans un rayon spécifique autour d'une commune sélectionnée
///////////////////////////////////////////////////////////////////////////////////////////////
function loadStationsForCommuneWithinRadius(commune, radius, map) {
    clearMarkers(); 
    showPreloader(); 
    fetch(`/stations_par_commune_with_radius?commune=${encodeURIComponent(commune)}&radius=${encodeURIComponent(radius)}`)
        .then(response => response.json())
        .then(data => {
            const { latitude, longitude, stations } = data;
            populateStationList(stations);  //On met à jour la liste des stations

            //Dessin du cercle de recherche
            communeCircle = L.circle([latitude, longitude], {
                color: 'lightblue',
                fillColor: '#87CEFA',
                fillOpacity: 0.5,
                radius: radius * 1000  
            }).addTo(map);

            stations.forEach(station => {
                const marker = L.marker([station.y, station.x]).addTo(map).bindPopup(`Code BSS: ${station.code_bss}`);
                mapMarkers.push(marker);

                //On ajoute un événement pour rechercher et afficher les détails de la station
                marker.on('click', () => {
                    searchStationInList(station.code_bss); //Recherche et affiche les détails de la station dans la liste
                });
            });

            map.fitBounds(communeCircle.getBounds(), { padding: [50, 50] });
        })
        .finally(() => hidePreloader()); //Masquer le préchargeur après la réponse ou en cas d'erreur
    }

/////////////////////////////////////////////////////////////////////////////////////////////////////
//Fonction pour charger les stations seulement autour d'une commune sélectionnée (sans rayon spécifié)
//////////////////////////////////////////////////////////////////////////////////////////////////////
function loadStationsInCommuneOnly(commune, map) {
    clearMarkers(); 
    fetch(`/stations_par_commune?commune=${encodeURIComponent(commune)}`)
        .then(response => response.json())
        .then(stations => {
            populateStationList(stations);  //On met à jour la liste des stations
            let group = new L.featureGroup();  //On crée un groupe de fonctionnalités pour contenir les marqueurs

            stations.forEach(station => {
                const [code_bss, x, y] = station;
                if (x && y) { 
                    const marker = L.marker([y, x]).addTo(map).bindPopup(`Code BSS: ${code_bss}`);
                    group.addLayer(marker);  //On ajoute chaque marqueur au groupe
                    window.mapMarkers.push(marker);  //On stocke les marqueurs pour une gestion future

                    //On ajoute un événement pour rechercher et afficher les détails de la station
                    marker.on('click', () => {
                        searchStationInList(code_bss); //Recherche et affiche les détails de la station dans la liste
                    });
                }
            });

            if (group.getLayers().length > 0) {
                map.fitBounds(group.getBounds(), { padding: [50, 50] });  
            }
        })
        .catch(error => console.error('Erreur lors de la récupération des stations:', error));
}
////////////////////////////////////////////////////////////////////////////////////
// Fonction appelée pour activer le bouton de recherche
////////////////////////////////////////////////////////////////////////////////////
function searchStations() {
    clearMarkers();  
    const commune = input.value.trim();
    const radiusElement = document.getElementById('radius');
    const radius = parseFloat(radiusElement.value);
    if (commune &&  (radius === 0)) {
        loadStationsInCommuneOnly(commune, map);
    } else if (commune) {
        loadStationsForCommuneWithinRadius(commune, radius, map);
    } else {
        loadStationsList(); 
    }
}



