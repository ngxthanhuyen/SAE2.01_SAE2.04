import sqlite3
import requests
import geopy.distance

class DataBase:
    def __init__(self):
        self.conn = sqlite3.connect('SAE204.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        try:
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS DEPARTEMENTS (
              code_departement TEXT PRIMARY KEY NOT NULL,
              nom_departement TEXT
            );''')
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS COMMUNES (
              code_commune_insee TEXT PRIMARY KEY,
              nom_commune TEXT, 
              code_departement TEXT,
              FOREIGN KEY (code_departement) REFERENCES departements(code_departement)
            );''')
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS STATIONS (
              id_station INTEGER PRIMARY KEY AUTOINCREMENT,
              code_bss TEXT UNIQUE,
              bss_id TEXT,
              urn_bss TEXT,
              code_commune_insee TEXT,
              profondeur_investigation REAL,
              x REAL,
              y REAL,
              altitude_station REAL,
              nb_mesures_piezo INTEGER,
              FOREIGN KEY (code_commune_insee) REFERENCES COMMUNES(code_commune_insee)
            );''')
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS MASSE_EAU (
              id_masse_eau INTEGER PRIMARY KEY AUTOINCREMENT,
              id_station INTEGER,
              code_masse_eau_edl TEXT UNIQUE NOT NULL,
              nom_masse_eau_edl TEXT,
              urn_masse_eau_edl TEXT,
              FOREIGN KEY (id_station) REFERENCES stations(id_station)                  
            );''')
            self.conn.commit()
        except Exception as e:
            print(f"Il y a une erreur{e}")

    def insert_dept(self, code_departement, nom_departement):
        self.cursor.execute('INSERT OR IGNORE INTO DEPARTEMENTS (code_departement, nom_departement) VALUES (?,?)',
                            (code_departement, nom_departement))
        self.conn.commit()
    def insert_commune(self, code_commune_insee, nom_commune, code_departement):
        self.cursor.execute('INSERT OR IGNORE INTO COMMUNES (code_commune_insee, nom_commune, code_departement) VALUES (?,?, ?)',
                            (code_commune_insee, nom_commune, code_departement))
        self.conn.commit()
    def insert_station(self, code_bss, bss_id, urn_bss, code_commune_insee, profondeur_investigation, x, y, altitude_station, nb_mesures_piezo):
        self.cursor.execute('INSERT OR IGNORE INTO STATIONS (code_bss, bss_id, urn_bss, code_commune_insee, profondeur_investigation, x, y, altitude_station, nb_mesures_piezo) VALUES (?,?,?,?,?,?,?,?,?)',
                            (code_bss, bss_id, urn_bss, code_commune_insee, profondeur_investigation, x, y, altitude_station, nb_mesures_piezo))
        self.conn.commit()
    def insert_masse_eau(self, id_station, code_masse_eau, nom_masse_eau, urn_masse_eau):
        self.cursor.execute('INSERT OR IGNORE INTO MASSE_EAU(id_station, code_masse_eau_edl, nom_masse_eau_edl, urn_masse_eau_edl) VALUES (?,?,?,?)',
                            (id_station, code_masse_eau, nom_masse_eau, urn_masse_eau))
        self.conn.commit()    
    def close(self):
        self.conn.close()

class Recherche:
    def __init__(self,db):
        self.db = db

    def recherche_communes(self, query):
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT DISTINCT nom_commune FROM communes WHERE nom_commune LIKE ?", (query + '%',))
            return cursor.fetchall()

    def recherche_stations_par_commune(self, commune):
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT code_bss, x, y FROM stations S
                INNER JOIN communes C ON S.code_commune_insee = C.code_commune_insee
                WHERE nom_commune LIKE ?
            """, ('%' + commune + '%',))
            return cursor.fetchall()

    def recherche_stations_par_commune_et_rayon(self, commune, radius):
        with self.db.conn:
          cursor = self.db.conn.cursor()
          #Requête SQL pour obtenir les coordonnées moyennes de la commune basées sur les stations
          cursor.execute("""
            SELECT AVG(x) as avg_lon, AVG(y) as avg_lat
            FROM stations S
            JOIN communes C ON S.code_commune_insee = C.code_commune_insee
            WHERE C.nom_commune LIKE ?
          """, ('%' + commune + '%',))
          avg_coords = cursor.fetchone()
          avg_lon, avg_lat = avg_coords
          #On sélectionne les stations dans le rayon spécifié
          cursor.execute("SELECT code_bss, x, y FROM stations")
          stations = cursor.fetchall()
          filtered_stations = [
            {"code_bss": s[0], "x": s[1], "y": s[2]}
            for s in stations
            if geopy.distance.geodesic((avg_lat, avg_lon), (s[2], s[1])).km <= radius
          ]
          return {"latitude": avg_lat, "longitude": avg_lon, "stations": filtered_stations}
    
    def get_stations_details(self, code_bss):
      with self.db.conn:
        cursor = self.db.conn.cursor()
        cursor.execute('''
          SELECT S.code_bss, S.bss_id, S.code_commune_insee, C.nom_commune, C.code_departement, D.nom_departement, M.code_masse_eau_edl, M.nom_masse_eau_edl, S.profondeur_investigation, S.altitude_station, S.nb_mesures_piezo
          FROM stations S
          LEFT JOIN communes C ON S.code_commune_insee = C.code_commune_insee
          LEFT JOIN departements D ON C.code_departement = D.code_departement
          LEFT JOIN masse_eau M ON S.id_station = M.id_station
          WHERE S.code_bss = ?
        ''', (code_bss,))
        result = cursor.fetchone()
        #On transforme les résultats bruts de la requête en un dictionnaire ou chaque clé est le nom d'une colonne
        return dict(zip([column[0] for column in cursor.description], result))
        

    
        
        


