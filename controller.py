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

@app.route('/recherche_communes')
def recherche_communes():
    db = DataBase()
    query = request.args.get('query', '')
    with db.conn:  # Context manager for automatic connection close
        cursor = db.conn.cursor()
        cursor.execute("SELECT DISTINCT nom_commune FROM communes WHERE nom_commune LIKE ?", ('%' + query + '%',))
        communes = cursor.fetchall()
    return jsonify([commune[0] for commune in communes])

if __name__ == "__main__":
    app.run(debug=True)