from flask import Flask, request, jsonify, render_template
from model import DataBase
import sqlite3

app = Flask(__name__)

db = DataBase()
# Configuration pour servir les fichiers statiques
app.static_folder = 'static'

#la route vers la page d'accueil
@app.route('/')
def index():
    return render_template('index.html')

#Route pour autocompléter les communes selon la recherche de l'utilisateur
@app.route('/recherche_communes')
def recherche_communes():
    #On récupèrele paramètre query de l'URL. Si aucun paramètre n'est fourni, une chaîne vide est utilisée par défaut
    query = request.args.get('query', '')
    with db.conn:  
        cursor = db.conn.cursor()
        #On exécute une requête SQL pour sélectionner les noms distincts de commnunes qui contiennent la requête 
        cursor.execute("SELECT DISTINCT nom_commune FROM communes WHERE nom_commune LIKE ?", (query + '%',))
        communes = cursor.fetchall()
    return jsonify([commune[0] for commune in communes])

#Route pour retourner les données des stations
@app.route('/stations')
def stations():
    with db.conn:
        cursor = db.conn.cursor()
        cursor.execute("SELECT code_bss, x, y FROM stations")
        stations = cursor.fetchall()
    return jsonify(stations)

@app.route('/stations_par_commune')
def stations_par_commune():
    commune = request.args.get('commune', '')
    with db.conn:  
        cursor = db.conn.cursor()
        cursor.execute("SELECT code_bss, x, y FROM stations S INNER JOIN communes C ON s.id_commune = c.id_commune WHERE C.nom_commune LIKE ?", 
                       ('%' + commune + '%',))
        stations = cursor.fetchall()
        print(stations)  # Debug pour voir les données extraites
    return jsonify(stations)

if __name__ == "__main__":
    app.run(debug=True)
    print(stations_par_commune())