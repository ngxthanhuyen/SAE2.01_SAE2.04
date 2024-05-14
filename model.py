import sqlite3
class DataBase:
    def __init__(self):
        self.conn = sqlite3.connect('SAE204.db')
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        try:
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS DEPARTEMENTS (
              id_departement INTEGER PRIMARY KEY AUTOINCREMENT,
              code_departement TEXT UNIQUE NOT NULL,
              nom_departement TEXT
            );''')
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS COMMUNES (
              id_commune INTEGER PRIMARY KEY AUTOINCREMENT,
              code_commune_insee TEXT UNIQUE NOT NULL,
              nom_commune TEXT
            );''')
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS MASSE_EAU (
              id_masse_eau INTEGER PRIMARY KEY AUTOINCREMENT,
              code_masse_eau_edl TEXT UNIQUE NOT NULL,
              nom_masse_eau_edl TEXT,
              urn_masse_eau_edl TEXT
            );''')
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS STATIONS (
              id_station INTEGER PRIMARY KEY AUTOINCREMENT,
              id_commune INTEGER NOT NULL,
              id_departement INTEGER NOT NULL,
              id_masse_eau INTEGER NOT NULL,
              code_bss TEXT UNIQUE,
              bss_id TEXT,
              urn_bss TEXT,
              profondeur_investigation REAL,
              x REAL,
              y REAL,
              altitude_station REAL,
              nb_mesures_piezo INTEGER,
              FOREIGN KEY (id_commune) REFERENCES COMMUNES(id_commune),
              FOREIGN KEY (id_departement) REFERENCES DEPARTEMENTS(id_departement),
              FOREIGN KEY (id_masse_eau) REFERENCES MASSE_EAU(id_masse_eau)
            );''')
            self.conn.commit()
        except Exception as e:
            print(f"Il y a une erreur{e}")

    def insert_dept(self, code_departement, nom_departement):
        self.cursor.execute('INSERT OR IGNORE INTO DEPARTEMENTS (code_departement, nom_departement) VALUES (?,?)',
                            (code_departement, nom_departement))
        self.conn.commit()
    def insert_commune(self, code_commune_insee, nom_commune):
        self.cursor.execute('INSERT OR IGNORE INTO COMMUNES (code_commune_insee, nom_commune) VALUES (?,?)',
                            (code_commune_insee, nom_commune))
        self.conn.commit()
    def insert_masse_eau(self, code_masse_eau, nom_masse_eau, urn_masse_eau):
        self.cursor.execute('INSERT OR IGNORE INTO MASSE_EAU(code_masse_eau_edl, nom_masse_eau_edl, urn_masse_eau_edl) VALUES (?,?,?)',
                            (code_masse_eau, nom_masse_eau, urn_masse_eau))
        self.conn.commit()
    def insert_station(self, id_commune, id_departement, id_masse_eau, code_bss, bss_id, urn_bss, profondeur_investigation, x, y, altitude_station, nb_mesures_piezo):
        self.cursor.execute('INSERT OR IGNORE INTO STATIONS (id_commune, id_departement, id_masse_eau, code_bss, bss_id, urn_bss, profondeur_investigation, x, y, altitude_station, nb_mesures_piezo) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                            (id_commune, id_departement, id_masse_eau, code_bss, bss_id, urn_bss, profondeur_investigation, x, y, altitude_station, nb_mesures_piezo))
        self.conn.commit()
    def close(self):
        self.conn.close()
    
