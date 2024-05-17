import sqlite3
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
    
