function updateSuggestions() {
    var input = document.getElementById('search');
    var dropdown = document.getElementById('suggestions');
    if (input.value.length > 0) {
        fetch(`/recherche_communes?query=${input.value}`)
            .then(response => response.json())
            .then(data => {
                dropdown.innerHTML = '';
                data.forEach(commune => {
                    let div = document.createElement('div');
                    div.textContent = commune;
                    div.style.padding = '10px';
                    div.style.cursor = 'pointer';
                    div.onclick = function () {
                        input.value = commune;
                        dropdown.innerHTML = '';
                    };
                    dropdown.appendChild(div);
                });
            });
    } else {
        dropdown.innerHTML = '';
    }
}



const init = () => {
    // On déclare une variable 'centerLoc' pour stocker le centre de location
    const centerLoc = ([48.8588548, 2.347035]);
    const map = L.map('map').setView(centerLoc, 12);
    // Les attributs de l'OpenStreetMap
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    L.marker(centerLoc).addTo(map)
        .bindPopup('Station')
        .openPopup();
};



window.onload = init;