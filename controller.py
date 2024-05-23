from flask import Flask, request, jsonify, render_template
from model import DataBase, Recherche
import geopy.distance


app = Flask(__name__)

db = DataBase()
recherche = Recherche(db)
# Configuration pour servir les fichiers statiques
app.static_folder = 'static'

#la route vers la page d'accueil
@app.route('/')
def index():
    return render_template('index.html')

#Route pour retourner les données des stations
@app.route('/stations')
def stations():
    with db.conn:
        cursor = db.conn.cursor()
        cursor.execute("SELECT code_bss, x, y FROM stations")
        stations = cursor.fetchall()
    return jsonify(stations)

#Route pour autocompléter les communes selon la recherche de l'utilisateur
@app.route('/recherche_communes')
def recherche_communes():
    #On récupèrele paramètre query de l'URL. Si aucun paramètre n'est fourni, une chaîne vide est utilisée par défaut
    query = request.args.get('query', '')
    communes = recherche.recherche_communes(query)
    return jsonify([commune[0] for commune in communes])


#Route pour rechercher les stations par commune
@app.route('/stations_par_commune')
def stations_par_commune():
    commune = request.args.get('commune')
    stations = recherche.recherche_stations_par_commune(commune)
    return jsonify(stations)

#Route pour rechercher les stations par commune avec un rayon spécifié
@app.route('/stations_par_commune_with_radius')
def stations_par_commune_with_radius():
    #On récupère le nom de la commune depuis la requête
    commune = request.args.get('commune')
    #On récupère le rayon depuis la requête, avec une valeur par défaut de 5km
    radius_str = request.args.get('radius', '5')  
    #On convertit le rayon en flottant
    radius = float(radius_str)
    result = recherche.recherche_stations_par_commune_et_rayon(commune, radius)
    return jsonify(result)

#Fonction pour récupérer les informations sur chaque station
@app.route('/get_station_details')
def get_station_details():
    code_bss = request.args.get('code_bss')
    station_details = recherche.get_stations_details(code_bss)
    return jsonify(station_details)
   

