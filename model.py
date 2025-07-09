import sqlite3
import requests
import geopy.distance
import aiohttp
import asyncio
from datetime import datetime
import numpy as np
import pytz



########################################################################################
# Classe pour créer la base de données et manipuler les données
########################################################################################
class DataBase:
    def __init__(self, name, schema):
        self.schema = schema
        self.conn = sqlite3.connect(name, check_same_thread=False)
        self.init_db()

    def init_db(self):
        with open(self.schema, mode='r') as f:
            try:
                cursor = self.conn.cursor()
                cursor.executescript(f.read())
                self.conn.commit()
            except Exception as e:
                print(f"Il y a une erreur {e}")

    def execute(self, requete, params=()):
        cursor = self.conn.cursor()
        cursor.execute(requete, params)
        self.conn.commit()
        cursor.close()  

    def execute_many(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.executemany(query, params)
        self.conn.commit()
        cursor.close() 

    def fetchall(self, requete, params=()):
        cursor = self.conn.cursor()
        cursor.execute(requete, params)
        results = cursor.fetchall()
        cursor.close()  
        return results

    def fetchone(self, requete, params=()):
        cursor = self.conn.cursor()
        cursor.execute(requete, params)
        result = cursor.fetchone()
        cursor.close()  
        return result

    def close(self):
        self.conn.close()
        
#############################################################################################################
# Classe pour insérer les données dans la base de données et récupérer les données depuis la base de données
#############################################################################################################
class Insert(DataBase):
    def __init__(self, name, schema):
        super().__init__(name, schema)

    def insert_communes_batch(self, communes):
        if communes:
            self.execute_many(
                'INSERT OR IGNORE INTO communes (code_commune_insee, nom_commune, code_departement) VALUES (?,?,?)',
                communes
            )

    def insert_stations_batch(self, stations):
        if stations:
            self.execute_many(
                'INSERT OR IGNORE INTO stations (code_bss, bss_id, urn_bss, code_commune_insee, profondeur_investigation, x, y, altitude_station, nb_mesures_piezo, date_debut_mesure, date_fin_mesure, code_departement) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                stations
            )

    def update_communes_batch(self, communes):
        if communes:
            self.execute_many(
                'INSERT OR REPLACE INTO communes (code_commune_insee, nom_commune, code_departement) VALUES (?,?,?)',
                communes
            )

    def insert_dept(self, code_departement, nom_departement):
        self.execute('INSERT OR IGNORE INTO departements (code_departement, nom_departement) VALUES (?,?)',
                        (code_departement, nom_departement))

    def insert_commune(self, code_commune_insee, nom_commune, code_departement):
        self.execute('INSERT OR IGNORE INTO communes (code_commune_insee, nom_commune, code_departement) VALUES (?,?,?)',
                        (code_commune_insee, nom_commune, code_departement))

    def insert_station(self, code_bss, bss_id, urn_bss, code_commune_insee, profondeur_investigation, x, y, altitude_station, nb_mesures_piezo, date_debut_mesure, date_fin_mesure, code_departement):
        self.execute('INSERT OR IGNORE INTO stations (code_bss, bss_id, urn_bss, code_commune_insee, profondeur_investigation, x, y, altitude_station, nb_mesures_piezo, date_debut_mesure, date_fin_mesure, code_departement) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                        (code_bss, bss_id, urn_bss, code_commune_insee, profondeur_investigation, x, y, altitude_station, nb_mesures_piezo, date_debut_mesure, date_fin_mesure, code_departement))
        
    def insert_station_tr(self, code_bss):
        self.execute('INSERT OR IGNORE INTO STATIONS_TR (code_bss) VALUES (?)',
                        (code_bss,))

    def update_stations_batch(self, stations):
        if stations:
            self.execute_many(
                'INSERT OR REPLACE INTO stations (code_bss, bss_id, urn_bss, code_commune_insee, profondeur_investigation, x, y, altitude_station, nb_mesures_piezo, date_debut_mesure, date_fin_mesure, code_departement) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                stations
            )

    def get_commune(self, code_commune_insee):
        query = "SELECT * FROM communes WHERE code_commune_insee = ?"
        if query : 
            return self.fetchone(query, (code_commune_insee,))
        return None

    def get_station(self, code_bss):
        query = "SELECT * FROM stations WHERE code_bss = ?"
        if query : 
            return self.fetchone(query, (code_bss,))
        return None
########################################################################################
# Classe pour récupérer les données depuis L'API et pour mettre à jour les données statistiques
########################################################################################
class LoadData(Insert):
    def __init__(self, URL, URL_TR, name, schema):
        super().__init__(name, schema)
        self.URL = URL
        self.URL_TR = URL_TR

    def load_departements(self):
        size = 15000
        response = requests.get(self.URL, params={'size': size})
        data = response.json()
        if 'data' in data:
            for entry in data['data']:
                self.insert_dept(entry['code_departement'], entry['nom_departement'])
        else:
            return "Il y a aucun département disponible"
        departements = self.fetchall("SELECT code_departement FROM departements")
        print(f"{len(departements)} départements récupérés de la base de données")
        lst = [row[0] for row in departements]
        return lst

    def load_stations(self, lst):
        moitie = len(lst) // 2
        params1 = {'size': 20000, 'code_departement': lst[:moitie]}
        params2 = {'size': 20000, 'code_departement': lst[moitie:]}
        reponse1 = requests.get(self.URL, params=params1)
        reponse2 = requests.get(self.URL, params=params2)
        data1 = reponse1.json()
        data2 = reponse2.json()
        results = [data1, data2]
        communes = []
        stations = []

        for data in results:
            for entry in data['data']:
                communes.append((entry['code_commune_insee'], entry['nom_commune'], entry['code_departement']))
                stations.append((
                    entry['code_bss'], entry['bss_id'], entry['urn_bss'], entry['code_commune_insee'],
                    entry['profondeur_investigation'], entry['x'], entry['y'], entry['altitude_station'],
                    entry['nb_mesures_piezo'], entry['date_debut_mesure'], entry['date_fin_mesure'],
                    entry['code_departement']
                ))

        self.insert_communes_batch(communes)
        self.insert_stations_batch(stations)
        print("Données chargées")

    async def fetch_station_data(self, session, url, station, semaphore):
        params = {'size': 1, 'code_bss': station}
        async with semaphore:
            try:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if 'data' in data and data['data']:
                        return station
                    else:
                        return None
            except aiohttp.ClientError as e:
                print(f"Erreur lors de la requête pour code_bss {station}: {e}")
                return None

    async def load_stations_tr(self):
        bss_list = self.fetchall("SELECT code_bss FROM stations")
        tasks = []
        semaphore = asyncio.Semaphore(100)
        async with aiohttp.ClientSession() as session:
            for row in bss_list:
                station = row[0]
                task = asyncio.create_task(self.fetch_station_data(session, self.URL_TR, station, semaphore))
                tasks.append(task)

            results = await asyncio.gather(*tasks)

        for station in results:
            if station:
                self.insert_station_tr(station)

        print("Données station_tr chargées avec succès")

    def update_bd(self, lst):
            communes = []
            stations = []
            code_bss = []
            update_station = []
            update_commune = []
            update_count = 0
            insert_count = 0
            for i in lst : 
                params1 = {'size': 10000, 'code_departement': i}
                reponse1 = requests.get(self.URL, params=params1)
                data1 = [reponse1.json()]
                for data in data1:
                    for entry in data['data']:
                        new_station = (entry['code_bss'], entry['bss_id'], entry['urn_bss'], entry['code_commune_insee'],
                            entry['profondeur_investigation'], entry['x'], entry['y'], entry['altitude_station'],
                            entry['nb_mesures_piezo'], entry['date_debut_mesure'], entry['date_fin_mesure'],
                            entry['code_departement'])
                        station = entry['code_bss']
                        if not self.get_station(station) : #on ajoute la station
                            communes.append((entry['code_commune_insee'], entry['nom_commune'], entry['code_departement']))
                            stations.append(new_station)
                            insert_count +=1
                            code_bss.append(station)

                            
                        if self.get_station(station) != new_station : #on modifie la station
                            communes.append((entry['code_commune_insee'], entry['nom_commune'], entry['code_departement']))
                            stations.append(new_station)
                            update_count+=1 
                            code_bss.append(station)
            asyncio.run(self.load_stations_tr())
            self.insert_communes_batch(communes)
            self.insert_stations_batch(stations)
            self.update_stations_batch(update_station)
            self.update_communes_batch(update_commune)
            
            self.lastupdate = datetime.now()

            print(f"Mise à jour complétée. {update_count} mise à jour et {insert_count} stations ajoutées.")
            print(self.lastupdate)
    



########################################################################################
# Classe pour effectuer les recherches de stations en fonction du choix de l'utilisateur
########################################################################################
class Recherche:
    def __init__(self, db: DataBase):
        self.db = db

    def recherche_communes(self, query):
        return self.db.fetchall(
            "SELECT DISTINCT nom_commune FROM communes WHERE nom_commune LIKE ?", (query + '%',))

    def recherche_stations(self):
        return self.db.fetchall(
            "SELECT code_bss, x, y FROM stations"
        )
    def recherche_stations_par_commune(self, commune):
        return self.db.fetchall("""
            SELECT code_bss, x, y FROM stations S
            INNER JOIN communes C ON S.code_commune_insee = C.code_commune_insee
            WHERE nom_commune LIKE ?
        """, ('%' + commune + '%',))

    def recherche_stations_par_commune_et_rayon(self, commune, radius):
        avg_coords = self.db.fetchone("""
            SELECT AVG(x) as avg_lon, AVG(y) as avg_lat
            FROM stations S
            JOIN communes C ON S.code_commune_insee = C.code_commune_insee
            WHERE C.nom_commune LIKE ?
        """, ('%' + commune + '%',))
        avg_lon, avg_lat = avg_coords
        stations = self.db.fetchall("SELECT code_bss, x, y FROM stations")
        filtered_stations = [
            {"code_bss": s[0], "x": s[1], "y": s[2]}
            for s in stations
            if geopy.distance.geodesic((avg_lat, avg_lon), (s[2], s[1])).km <= radius
        ]
        return {"latitude": avg_lat, "longitude": avg_lon, "stations": filtered_stations}

    def get_stations_details(self, code_bss):
        result = self.db.fetchall('''
            SELECT S.code_bss, S.bss_id, S.code_commune_insee, C.nom_commune, C.code_departement, D.nom_departement, S.profondeur_investigation, S.altitude_station, S.nb_mesures_piezo
            FROM stations S
            LEFT JOIN communes C ON S.code_commune_insee = C.code_commune_insee
            LEFT JOIN departements D ON C.code_departement = D.code_departement
            WHERE S.code_bss = ?
        ''', (code_bss,))
        if result:
            keys = ["code_bss", "bss_id", "code_commune_insee", "nom_commune", "code_departement", 
                "nom_departement", "profondeur_investigation", "altitude_station", "nb_mesures_piezo"]
            return dict(zip(keys, result[0]))
        return {}



#Fonction pour calculer le maximum, le minimum, la moyenne et l'écart-type des niveaux piezométriques
def calculate_statistics(niveaux):
    niveaux_array = np.array(niveaux)  #on convertit la liste en un tableau numpy
    if len(niveaux_array) == 0:
        return None, None, None, None
    max = np.max(niveaux_array)
    min = np.min(niveaux_array)
    moyenne = np.mean(niveaux_array)   #on calcule la moyenne des valeurs dans le tableau
    ecart_type = np.std(niveaux_array) #on calcule l'écart-type dans le tableau
    return max, min, moyenne, ecart_type
    
#####################################################################
# Classe pour récupérer et gérer les données des chroniques historiques
#####################################################################
class Chroniques():
    def __init__(self, db: DataBase):
        self.db = db

    def get_code_bss(self, query):
        return self.db.fetchall(
            "SELECT DISTINCT code_bss FROM stations WHERE code_bss LIKE ?", (query + '%',))

    async def get_data_chroniques(self, session, code_bss):
        URL = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques"
        all_data = []
        page = 1
        while True:
            params = {'code_bss': code_bss, 'size': 1000, 'page': page}
            async with session.get(URL, params=params) as response:
                data = await response.json()
                data = data.get('data', [])
                if not data:
                    break
                all_data.extend(data)
                page += 1
        return all_data
    
    
   
    def get_chroniques_historiques(self):
        all_chroniques_data = {}
        stations = self.db.fetchall("SELECT code_bss FROM stations")
        for station in stations:
            code_bss = station[0]
            chroniques_historiques = self.get_data_chroniques(code_bss)
            if chroniques_historiques:
                niveaux = [float(point['niveau_nappe_eau']) for point in chroniques_historiques]
                if niveaux:
                    max, min, moyenne_niveaux, ecart_type_niveaux, = calculate_statistics(niveaux)
                    all_chroniques_data[code_bss] = {
                     'max':max,
                     'min':min,
                     'moyenne': moyenne_niveaux, 
                     'ecart_type': ecart_type_niveaux
                     }
        return all_chroniques_data
    
#####################################################################
# Classe pour filtrer les données en temps réel en fonction du besoin
#####################################################################
class Chroniques_TR():
    def __init__(self, db: DataBase):
        self.db = db

    def get_stations_tr(self):
        stations_tr = self.db.fetchall("""
                SELECT TR.code_bss, S.x, S.y FROM stations_tr TR
                INNER JOIN stations S ON TR.code_bss = S.code_bss
            """)
        return stations_tr

    def get_stations_tr_par_departement(self, departement):
        stations_tr = self.db.fetchall("""
                SELECT TR.code_bss, S.x, S.y 
                FROM stations_tr TR
                INNER JOIN stations S ON TR.code_bss = S.code_bss
                INNER JOIN communes C ON S.code_commune_insee = C.code_commune_insee
                INNER JOIN departements D ON C.code_departement = D.code_departement
                WHERE D.nom_departement = ?
            """, (departement,))
        return stations_tr
        
    @staticmethod #indiquer que c'est une méthode statique pour ne pas confondre avec la méthode d'instance de classe
    def convert_utc_to_local(utc_datetime_str):
        #On parse la date UTC en objet datetime
        utc_datetime = datetime.strptime(utc_datetime_str, '%Y-%m-%dT%H:%M:%SZ')
        #On associe la date à un fuseau horaire UTC
        utc_datetime = utc_datetime.replace(tzinfo=pytz.UTC)
        return utc_datetime.strftime('%d/%m/%Y - %H:%M:%S')

    async def get_data_tr(self, session, code_bss):
        URL = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques_tr"
        params = {
            'code_bss': code_bss,
            'size': 1,
            'sort': 'desc'
        }
        async with session.get(URL, params=params) as response:
            if response.status in [200, 206]:
                data = await response.json()
                data = data.get('data', [])
                if data:
                    latest_mesure = data[0]
                    return {
                        'code_bss': code_bss,
                        'niveau_eau_ngf': latest_mesure.get('niveau_eau_ngf'),
                        'profondeur_nappe': latest_mesure.get('profondeur_nappe'),
                        'date_mesure': latest_mesure.get('date_mesure')
                    }
        return None
    
