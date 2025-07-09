from flask import Flask, request, jsonify, render_template
import requests
from model import LoadData, Recherche, Chroniques, Chroniques_TR, calculate_statistics
import plotly.express as px
import pandas as pd
from flask_caching import Cache 
import aiohttp
import asyncio
import datetime
from datetime import timedelta
import logging

# Configurer le logging
logging.basicConfig(level=logging.INFO)

URL = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations?format=json"
URL_TR = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques_tr?format=json"

app = Flask(__name__)
# permet de mettre en cache les réponses des routes pour éviter de recalculer les mêmes données à chaque requête
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

db = LoadData(URL, URL_TR, 'SAE204.db', 'schema.sql')
recherche = Recherche(db)
ch = Chroniques(db)
tr = Chroniques_TR(db)

# Configuration pour servir les fichiers statiques
app.static_folder = 'static'

# la route vers la page d'accueil
@app.route('/')
def index():
    return render_template('index.html')

# la route vers la page des stations
@app.route('/stations')
def stations():
    return render_template('stations.html')

# Route pour retourner les données des stations
@app.route('/stations_data')
def stations_data():
    stations = recherche.recherche_stations()
    return jsonify(stations)

# Route pour autocompléter les communes selon la recherche de l'utilisateur
@app.route('/recherche_communes')
def recherche_communes():
    # On récupère le paramètre query de l'URL. Si aucun paramètre n'est fourni, une chaîne vide est utilisée par défaut
    query = request.args.get('query', '')
    communes = recherche.recherche_communes(query)
    return jsonify([commune[0] for commune in communes])

# Route pour rechercher les stations par commune
@app.route('/stations_par_commune')
def stations_par_commune():
    commune = request.args.get('commune')
    stations = recherche.recherche_stations_par_commune(commune)
    return jsonify(stations)

# permet de mettre en cache les réponses des routes pour éviter de recalculer les mêmes données à chaque requête
@cache.memoize(300)
# Route pour rechercher les stations par commune avec un rayon spécifié
@app.route('/stations_par_commune_with_radius')
def stations_par_commune_with_radius():
    # On récupère le nom de la commune depuis la requête
    commune = request.args.get('commune')
    # On récupère le rayon depuis la requête, avec une valeur par défaut de 5km
    radius_str = request.args.get('radius', '5')  
    # On convertit le rayon en flottant
    radius = float(radius_str)
    result = recherche.recherche_stations_par_commune_et_rayon(commune, radius)
    return jsonify(result)

# Fonction pour récupérer les informations sur chaque station
@app.route('/get_station_details')
def get_station_details():
    code_bss = request.args.get('code_bss')
    station_details = recherche.get_stations_details(code_bss)
    return jsonify(station_details)

#################################################
## Route pour la page des chroniques historiques
#################################################

@app.route('/get_code_bss')
def get_code_bss():
    # On récupère le paramètre query de l'URL. Si aucun paramètre n'est fourni, une chaîne vide est utilisée par défaut
    query = request.args.get('query', '')
    code_bss = ch.get_code_bss(query)
    return jsonify([code_bss[0] for code_bss in code_bss])

# Route pour récupérer les données d'un chronique à partir de son code_bss
@app.route('/niveaux_nappes/<code_bss>')
def niveaux_nappes(code_bss):
    URL = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques"
    params = {
        'code_bss': code_bss,
    }
    response = requests.get(URL, params=params)
    data = response.json()['data'] if response.status_code in [200, 206] else []

    # Conversion des dates et niveaux pour la visualisation
    dates = [point['date_mesure'] for point in data]
    niveaux = [point['niveau_nappe_eau'] for point in data]

    return render_template('chroniques.html', dates=dates, niveaux=niveaux, code_bss=code_bss)

# Fonction pour créer le graphique pour visualiser le changement de chroniques dans le temps
def time_series_plot(data):
    # Collecte des dates et des niveaux
    dates = [item['date_mesure'] for item in data if 'date_mesure' in item]
    niveaux = [float(item['niveau_nappe_eau']) for item in data if 'niveau_nappe_eau' in item]

    # On tronque les listes pour être sûrs que les listes 'dates' et 'niveaux' ont toujours la même longueur avant de convertir en DataFrame
    min_length = min(len(dates), len(niveaux))
    dates = dates[:min_length]
    niveaux = niveaux[:min_length]

    # Création du DataFrame
    df = pd.DataFrame({
        'Date': pd.to_datetime(dates),
        'Niveau': niveaux
    })

    # Création du graphique
    fig = px.line(df, x='Date', y='Niveau', title="Niveau des nappes d'eau souterraine",
                  labels={'Niveau': 'Niveau de la nappe (m NGF)'})
    fig.update_traces(
        marker=dict(size=8, color='#4682B4', opacity=1),
        hovertemplate="<b>Date:</b> %{x|%d %b %Y}<br><b>Niveau:</b> %{y:.2f} m NGF<extra></extra>"
    )  
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=1, label="1a", step="year", stepmode="backward"),
                dict(count=10, label="10a", step="year", stepmode="backward"),
                dict(step="all", label="Tout")
            ])
        ),
        rangeslider=dict(
            visible=True,
            thickness=0.1
        ),
        type='date',
    )
    fig.update_layout(
        title={
            'text': "Niveau des nappes d'eau souterraine",
            'y': 0.96,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(
                size=26 
            )
        },
        xaxis_title='Date',
        yaxis_title='Niveau de la nappe (m NGF)',
        plot_bgcolor='#F0F8FF',
        paper_bgcolor='#e5ecf6',
        height=737,
    )
    return fig.to_html(full_html=False)

# Route pour récupérer les données d'un chronique à partir de son code_bss
@app.route('/chroniques')
def chroniques():
    code_bss = request.args.get('code_bss')
    if code_bss:
        async def fetch_data():
            async with aiohttp.ClientSession() as session:
                data = await ch.get_data_chroniques(session, code_bss)
                return data

        data = asyncio.run(fetch_data())
        dates = [item['date_mesure'] for item in data if 'date_mesure' in item]
        formatted_dates = [pd.to_datetime(date).strftime('%Y-%m-%d') for date in dates]  

        time_series_html = time_series_plot(data)
        niveaux = [item['niveau_nappe_eau'] for item in data if 'niveau_nappe_eau' in item and item['niveau_nappe_eau'] is not None]
        niveaux = [float(niveau) for niveau in niveaux]  
        boxplot_html = boxplot(niveaux)
        max, min, moyenne_niveaux, ecart_type_niveau = calculate_statistics(niveaux)
        stats_present = None not in [max, min, moyenne_niveaux, ecart_type_niveau]

        return render_template('chroniques.html', time_series_html=time_series_html, boxplot_html=boxplot_html,
                               stats_present=stats_present, max=max, min=min, moyenne_niveaux=moyenne_niveaux, 
                               ecart_type_niveau=ecart_type_niveau, code_bss=code_bss, dates=formatted_dates, data_length=len(data))
    return render_template('chroniques.html')

# Route pour créer le graphique de time series pour visualiser les mesures historiques des stations
@app.route('/plot')
def plot():
    code_bss = request.args.get('code_bss')
    if (code_bss):
        async def fetch_data():
            async with aiohttp.ClientSession() as session:
                data = await ch.get_data_chroniques(session, code_bss)
                return data

        data = asyncio.run(fetch_data())
        time_series_html = time_series_plot(data)
        return time_series_html  
    return "Pas de données disponibles", 404

# Fonction pour créer la boîte à moustache afin de visualiser les différents statistiques
def boxplot(niveaux):
    df = pd.DataFrame({'Niveaux': niveaux})
    fig = px.box(df, y='Niveaux')
    fig.update_layout(
         title={
            'text': 'Boîte à moustache du niveau de la nappe',
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20)  
        },
        plot_bgcolor='#F0F8FF', paper_bgcolor='#e5ecf6', height=600,
        width=800, margin=dict(l=40, r=40, t=40, b=40))
    return fig.to_html(full_html=False)

###############################################
## Route pour la page temps réel
###############################################
@app.route('/chroniques_tr')
def real_time():
    stations = tr.get_stations_tr()
    return render_template('chroniques_tr.html', stations=stations)

def calculate_z_score(niveau_actuel, moyenne_historique, ecart_type):
    if ecart_type == 0:
        return 0  # éviter division par 0
    z = (niveau_actuel - moyenne_historique) / ecart_type
    return z

def get_color_for_z_score(z):
    if z > 1.28:
        return '#286273'  # Bleu foncé
    elif z > 0.84 and z <= 1.28:
        return '#1B75BB'  # Bleu
    elif z > 0.25 and z <= 0.84:
        return '#32A9DD'  # Bleu clair
    elif z > -0.25 and z <= 0.25:
        return '#6DC55A'  # Vert
    elif z > -0.84 and z <= -0.25:
        return '#FFDD57'  # Jaune
    elif z > -1.28 and z <= -0.84:
        return '#F18E00'  # Orange
    elif z <= -1.28:
        return '#DB442C'  # Rouge

@cache.memoize(1000)
# Route pour retourner les données des stations en temps réel
@app.route('/stations_temps_reel')
async def stations_temps_reel():
    departement = request.args.get('departement')
    stations = tr.get_stations_tr_par_departement(departement)
    
    async def fetch_data(session, station):
        code_bss, x, y = station
        data_tr, niveaux = await asyncio.gather(
            tr.get_data_tr(session, code_bss),
            ch.get_data_chroniques(session, code_bss)
        )        
        if data_tr:
            niveaux = [float(niveau['niveau_nappe_eau']) for niveau in niveaux if niveau['niveau_nappe_eau'] is not None]

            if niveaux:
                max_niveau, min_niveau, moyenne_niveaux, ecart_type_niveaux = calculate_statistics(niveaux)
                if moyenne_niveaux is not None and ecart_type_niveaux is not None:
                    z_score = calculate_z_score(float(data_tr['niveau_eau_ngf']), moyenne_niveaux, ecart_type_niveaux)
                    color = get_color_for_z_score(z_score)
                    data_tr['color'] = color
                    data_tr['moyenne_niveaux'] = moyenne_niveaux
                    data_tr['ecart_type_niveaux'] = ecart_type_niveaux

            data_tr.update({
                'x': x,
                'y': y,
                'date_mesure': tr.convert_utc_to_local(data_tr['date_mesure'])
            })
            return data_tr
        return None
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_data(session, station) for station in stations]
        stations_tr_data = await asyncio.gather(*tasks)

    stations_tr_data = [station for station in stations_tr_data if station]
    return jsonify(stations_tr_data)

def get_data_for_code_bss(code_bss):
    url = f"https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques?code_bss={code_bss}&size=100"
    response = requests.get(url)
    data = response.json()

    if 'data' in data:
        time_series_html = generate_time_series_html(data['data'])
        stats_present = True
        data_length = len(data['data'])
        dates = [item['date_mesure'] for item in data['data']]
        niveaux = [item['niveau_nappe_eau'] for item in data['data']]
        min_niveau = min(niveaux)
        max_niveau = max(niveaux)
        moyenne_niveaux = sum(niveaux) / len(niveaux)
        ecart_type_niveau = (sum((x - moyenne_niveaux) ** 2 for x in niveaux) / len(niveaux)) ** 0.5
        boxplot_html = generate_boxplot_html(niveaux)

        return time_series_html, stats_present, data_length, dates, min_niveau, max_niveau, moyenne_niveaux, ecart_type_niveau, boxplot_html
    else:
        return '', False, 0, [], 0, 0, 0, 0, ''

def generate_time_series_html(data):
    return '<div>Graphique des séries temporelles</div>'

def generate_boxplot_html(niveaux):
    return '<div>Graphique boxplot</div>'

#################################################
## Route pour les alertes
#################################################

@app.route('/alertes')
def alertes():
    return render_template('alertes.html')

@app.route('/alertes_data')
def alertes_data():
    period = request.args.get('period', default='7', type=int)
    unit = request.args.get('unit', default='0', type=int)
    # Utilisez les valeurs de `period` et `unit` pour ajuster la logique de votre fonction
    app.logger.info(f'Period: {period}, Unit: {unit}')
    # Obtenir la date actuelle
    current_date_t = datetime.datetime.now().date() - timedelta(days=7)
    # Obtenir la date d'il y a un an
    previous_date_t = current_date_t - timedelta(days=period + 7)
    # Convertir les dates en chaînes de caractères si nécessaire
    current_date = current_date_t.strftime('%Y-%m-%d')
    previous_date = previous_date_t.strftime('%Y-%m-%d')
    url = f"https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations?format=json&date_recherche={current_date}"
    response = requests.get(url)

    if response.status_code != 200:
        return jsonify({"error": "Unable to fetch stations data"}), 500

    stations_data = response.json().get('data', [])

    alertes_data = []

    for station in stations_data:
        code_bss = station.get('code_bss')

        # app.logger.debug(f'code_bss: {code_bss}')

        code_departement = station.get('code_departement')
        code_commune_insee = station.get('code_commune_insee')
        nom_commune = station.get('nom_commune')
        date_debut_mesure = station.get('date_debut_mesure')

        if not code_bss:
            continue
        # app.logger.debug(f'date_debut_mesure:{date_debut_mesure} > previous_date:{previous_date}')
        if date_debut_mesure > previous_date:
            app.logger.info(f'date_debut_mesure:{date_debut_mesure} > previous_date:{previous_date}')
            continue

        current_historical_url = f"https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques_tr?code_bss={code_bss}&size=1&sort=desc"
        current_historical_response = requests.get(current_historical_url)
        if current_historical_response.status_code not in [200, 206]:
            app.logger.info(f'current_historical_response.status_code not in [200, 206] msg={current_historical_response.status_code}')
            continue
        current_historical_data = current_historical_response.json()
        if 'data' not in current_historical_data:
            continue
        if len(current_historical_data['data']) < 1:
            continue

        previous_historical_url = f"https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques_tr?code_bss={code_bss}&size=1&date_debut_mesure={previous_date}&sort=asc"
        previous_historical_response = requests.get(previous_historical_url)
        if previous_historical_response.status_code not in [200, 206]:
            app.logger.info(f'previous_historical_response.status_code not in [200, 206] msg={previous_historical_response.status_code}')
            continue
        previous_historical_data = previous_historical_response.json()
        if 'data' not in previous_historical_data:
            continue
        if len(previous_historical_data['data']) < 1:
            continue

        try:
            # app.logger.debug(f'get level of code_bss: {code_bss}')
            level_current = float(current_historical_data['data'][0].get('niveau_eau_ngf', 0))
            current_date_mesure = (current_historical_data['data'][0].get('date_mesure', 0))
            level_previous_year = float(previous_historical_data['data'][0].get('niveau_eau_ngf', 0))
            previous_date_mesure = (previous_historical_data['data'][0].get('date_mesure', 0))
            difference_m = level_current - level_previous_year
            difference_p = ((level_current / level_previous_year) - 1) * 100
            alertes_data.append((code_bss, difference_m, difference_p, level_current, level_previous_year, nom_commune, code_commune_insee, code_departement))
        except (KeyError, ValueError, TypeError) as e:
            print(f"Error processing data for station {code_bss}: {e}")
            continue

    if unit == 0:
        alertes_data = sorted(alertes_data, key=lambda x: x[1], reverse=False)
    else:
        alertes_data = sorted(alertes_data, key=lambda x: x[2], reverse=False)

    return jsonify(alertes_data)

if __name__ == '__main__':
    app.run(debug=True)
