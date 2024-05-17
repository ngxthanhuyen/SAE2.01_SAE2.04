//On récupère les éléments nécessaires du DOM dès que le script est chargé
const input = document.getElementById('search');
const dropdown = document.getElementById('autocomplete');
//Index pour suivre l'élément actuellement en focus dans les suggestions
let currentFocus = -1;
let map;  // Déclarer map au niveau global

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

//Fonction pour récupérer les données des communes basées sur la saisie de l'utilisateur
function getCommuneData() {
    let val = this.value;
    if (!val) {
        val = input.value;  //Fallback au cas où 'this.value' n'est pas défini
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
                        console.log("Commune sélectionnée:", commune);  // Ajoutez ceci pour déboguer
                        //On charge les stations pour la commune sélectionnée
                        loadStationsForCommune(commune, map);
                    });
                    //On ajoute l'élément de suggestion au DOM
                    dropdown.appendChild(item);
                });
            })
            .catch(error => console.error('Error: ', error));
    }
}

//Fonction pour ajouter la classe 'active' à un élément
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

//Fonction pour supprimer la classe 'active' de tous les éléments
function removeActive(items) {
    for (let i = 0; i < items.length; i++) {
        items[i].classList.remove("autocomplete-active");
    }
}

//Initialisation de la carte Leaflet 
const init = () => {
    //On déclare une variable 'centerLoc' pour stocker le centre de location
    const centerLoc = [48.8588548, 2.347035];
    map = L.map('map').setView(centerLoc, 12);
    //Les attributs de l'OpenStreetMap
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    //On appelle la fonction pour afficher les stations
    displayStations(map);
};

window.onload = init;


//Fonction pour afficher les stations sur la carte
function displayStations(map) {
    fetch('/stations')
    .then(response => response.json())
    .then(data => {
        data.forEach(station => {
            const [code_bss, x, y] = station;
            if (x && y) {
                // 'y' est latitude et 'x' est longtitude et Leaflet attend la latitude en premier puis la longtitude
                const marker = L.marker([y,x]).addTo(map);
                marker.bindPopup(`Code BSS: ${code_bss}`);
            }
        });
    })
    .catch(error => console.error('Erreur lors de la récupération des données de stations: ',error));
}

function loadStationsForCommune(commune, map) {
    if (!map) {
        console.error("Map instance is not provided or is undefined.");
        return;
    }
    fetch(`/stations_par_commune?commune=${encodeURIComponent(commune)}`)
    .then(response => response.json())
    .then(data => {
        console.log("Stations reçues:", data);  // Ajoutez ceci pour vérifier les données
        // Nettoyer les anciens marqueurs avant d'ajouter de nouveaux
        if (window.mapMarkers) {
            window.mapMarkers.forEach(marker => map.removeLayer(marker));
        }
        window.mapMarkers = [];
        
        data.forEach(station => {
            const [code_bss, x, y] = station;
            if (x && y) { 
                const marker = L.marker([y, x]).addTo(map);
                marker.bindPopup(`Code BSS: ${code_bss}`);
                window.mapMarkers.push(marker); // Stocker le marqueur pour suppression future
            }
        });
    })
    .catch(error => console.error('Erreur lors de la récupération des stations:', error));
}


