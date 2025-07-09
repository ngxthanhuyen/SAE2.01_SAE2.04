document.addEventListener('DOMContentLoaded', () => {
    console.log('alerte.js : Document loaded');

    const periodSelect = document.getElementById('period');
    const unitSelect = document.getElementById('unit');
    const tableBody = document.querySelector('table tbody');

    periodSelect.addEventListener('change', updatePeriodDates);

    periodSelect.addEventListener('click', () => {
        tableBody.innerHTML = '';
    });
    unitSelect.addEventListener('click', () => {
        tableBody.innerHTML = '';
    });

    function updatePeriodDates() {
        const period = parseInt(periodSelect.value);
        const today = new Date();
        const dateFin = new Date(today.setDate(today.getDate() - 7));
        const dateDebut = new Date(dateFin);
        dateDebut.setDate(dateFin.getDate() - period);

        const options = { year: 'numeric', month: 'numeric', day: 'numeric' };
        const dateFinStr = dateFin.toLocaleDateString('fr-FR', options);
        const dateDebutStr = dateDebut.toLocaleDateString('fr-FR', options);

        const periodDatesLabel = document.getElementById('period_dates');
        periodDatesLabel.textContent = `Période: ${dateDebutStr} à ${dateFinStr}`;
    }

    // Appel initial pour mettre à jour les dates lors du chargement de la page
    updatePeriodDates();
});

function searchAlertes() {
    const loadingElement = document.getElementById('loading');
    const waterFillElement = document.getElementById('water-fill');
    const backgroundVideo = document.getElementById('background-video');

    //Affiche la vidéo en arrière-plan
    backgroundVideo.style.display = 'block';

    //Démarrer l'animation de remplissage d'eau
    waterFillElement.classList.add('fill-animate');

    loadingElement.style.display = 'block';  //Affiche l'animation de chargement

    const period = document.getElementById('period').value;
    const unit = document.getElementById('unit').value;
    const tableBody = document.querySelector('table tbody');
    tableBody.innerHTML = ''; //Efface les données précédentes

    fetch(`/alertes_data?period=${period}&unit=${unit}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            console.log('alerte.js : Fetching alertes data');
            return response.json();
        })
        .then(data => {
            console.log('alerte.js : Data received:', data);

            data.forEach(row => {
                const tr = document.createElement('tr');
                tr.classList.add('table-row'); // Ajout de la classe pour la gestion des clics
                tr.dataset.stationId = row[0];  // Ajouter un ID de station pour la redirection

                const stationCell = document.createElement('td');
                const differenceCell1 = document.createElement('td');
                const differenceCell2 = document.createElement('td');
                const actualCell = document.createElement('td');
                const previousCell = document.createElement('td');
                const cityCell = document.createElement('td');
                const CPCell = document.createElement('td');
                const depCell = document.createElement('td');

                stationCell.textContent = row[0];
                differenceCell1.textContent = row[1].toFixed(2);
                differenceCell2.textContent = row[2].toFixed(2);
                actualCell.textContent = row[3].toFixed(2);
                previousCell.textContent = row[4].toFixed(2);
                cityCell.textContent = row[5];
                CPCell.textContent = row[6];
                depCell.textContent = row[7];

                tr.appendChild(stationCell);
                tr.appendChild(differenceCell1);
                tr.appendChild(differenceCell2);
                tr.appendChild(actualCell);
                tr.appendChild(previousCell);
                tr.appendChild(cityCell);
                tr.appendChild(CPCell);
                tr.appendChild(depCell);
                tableBody.appendChild(tr);
            });

            // Ajouter des gestionnaires d'événements aux lignes de la table
            document.querySelectorAll('.table-row').forEach(row => {
                row.addEventListener('click', () => {
                    const stationId = row.dataset.stationId;
                    window.open(`/chroniques?code_bss=${stationId}`, '_blank');  //Ouvrir dans un nouvel onglet
                });
            });
        })
        .catch(error => {
            console.error('Error fetching alertes data:', error);
        })
        .finally(() => {
            loadingElement.style.display = 'none';  // Cache l'animation de chargement
            backgroundVideo.style.display = 'none'; // Masquer la vidéo en arrière-plan
            //Arrêter l'animation de remplissage d'eau après la fin du chargement
            setTimeout(() => {
                waterFillElement.classList.remove('fill-animate');
            }, 2000); // Correspond à la durée de l'animation de remplissage d'eau
        });
}
