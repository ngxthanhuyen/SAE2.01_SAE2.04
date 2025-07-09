document.addEventListener('DOMContentLoaded', (event) => {
    const input = document.getElementById('code_bss_input');
    const dropdown = document.getElementById('autocomplete');
    const plotlyContainer = document.getElementById('plotly-container');
    //permet de naviguer dans les suggestions ('autocomplete') avec les touches fléchées
    let currentFocus = -1; 
    //On ajoute un flag pour vérifier si le graphique est déjà chargé
    let isGraphLoaded = false; 

    input.addEventListener('input', getCode_Bss);

    //Fonction pour obtenir les suggestions des code_bss en fonctionne de l'entrée de l'utilisateur
    function getCode_Bss() {
        const val = input.value; 
        dropdown.innerHTML = '';  //On réinitialise le contenu de menu déroulant
        currentFocus = -1;

        if (val.length > 0) {
            fetch(`/get_code_bss?query=${encodeURIComponent(val)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.length === 0) {
                        const noResultItem = document.createElement('div');
                        noResultItem.innerHTML = "Aucun résultat trouvé";
                        noResultItem.classList.add('autocomplete-items');
                        dropdown.appendChild(noResultItem);
                    } else {
                        data.forEach(code_bss => {
                            const item = document.createElement('div');
                            item.innerHTML = code_bss.replace(new RegExp(val, 'gi'), (match) => `<strong>${match}</strong>`); // Highlight matching text
                            item.classList.add('autocomplete-items');
                            item.addEventListener("click", function() {
                                input.value = code_bss;
                                dropdown.innerHTML = '';
                            });
                            dropdown.appendChild(item);
                        });
                    }
                })
                .catch(error => console.error('Erreur pendant la récupération des données:', error));
        }
    }
    //Gestion de la navigation dans les suggestions avec les touches du clavier
    input.addEventListener("keydown", function(e) {
        let items = dropdown.querySelectorAll(".autocomplete-items");
        switch (e.keyCode) {
            case 40: //Flèche vers le bas
                currentFocus++;
                if (currentFocus >= items.length) currentFocus = 0; 
                addActive(items);
                break;
            case 38: // Flèche vers le haut
                currentFocus--;
                if (currentFocus < 0) currentFocus = items.length - 1; 
                addActive(items);
                break;
            case 13: //Entrée
                e.preventDefault(); 
                if (currentFocus > -1 && items.length) {
                    items[currentFocus].click();
                }
                break;
        }
    });

    //On ajoute la classe CSS "autocomplete-active" à l'élément actif
    function addActive(items) {
        if (!items) return;
        removeActive(items);
        if (currentFocus >= items.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = items.length - 1;
        items[currentFocus].classList.add("autocomplete-active");
        items[currentFocus].scrollIntoView({
            behavior: 'smooth',
            block: 'nearest',
            inline: 'start'
        });
    }
    //On supprime la classe CSS "autocomplete-active" de tous les éléments
    function removeActive(items) {
        for (let i = 0; i < items.length; i++) {
            items[i].classList.remove("autocomplete-active");
        }
    }
    //Soumission du code BSS et redirection vers la page des chroniques
    window.submitCodeBss = function() {
        const code_bss = input.value;
        if (code_bss) {
            window.location.href = `/chroniques?code_bss=${encodeURIComponent(code_bss)}`;
        } else {
            alert("Veuillez entrer un code BSS");
        }
    }
    //Fonction utilitaire pour extraire les paramètres de l'URL
    function getParameterByName(name) {
        const url = new URL(window.location.href);
        return url.searchParams.get(name);
    }
    //Chargement du graphique lors du chargement de la page
    window.onload = function() {
        const code_bss = getParameterByName('code_bss');
        if (code_bss && !isGraphLoaded) {
            document.getElementById('code_bss_input').value = code_bss;
            fetch(`/plot?code_bss=${encodeURIComponent(code_bss)}`)
                .then(response => response.json())
                .then(data => {
                    plotlyContainer.innerHTML = data.html; 
                    isGraphLoaded = true; 
                })
                .catch(error => {
                    console.error('Erreur lors de la requête pour afficher le graphique :', error);
                });
        }
    }
});
