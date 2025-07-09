CREATE TABLE IF NOT EXISTS DEPARTEMENTS (
    code_departement TEXT PRIMARY KEY NOT NULL,
    nom_departement TEXT
);

CREATE TABLE IF NOT EXISTS COMMUNES (
    code_commune_insee TEXT PRIMARY KEY,
    nom_commune TEXT, 
    code_departement TEXT,
    FOREIGN KEY (code_departement) REFERENCES departements(code_departement)
);

CREATE TABLE IF NOT EXISTS STATIONS (
    code_bss TEXT PRIMARY KEY,
    bss_id TEXT UNIQUE,
    urn_bss TEXT,
    code_commune_insee TEXT,
    profondeur_investigation REAL,
    x REAL,
    y REAL,
    altitude_station TEXT,
    nb_mesures_piezo INTEGER,
    date_debut_mesure TEXT,
    date_fin_mesure TEXT, 
    code_departement TEXT,               
    FOREIGN KEY (code_commune_insee) REFERENCES COMMUNES(code_commune_insee),
    FOREIGN KEY (code_departement) REFERENCES DEPARTEMENTS(code_departement)
);

CREATE TABLE IF NOT EXISTS STATIONS_TR (
    code_bss TEXT PRIMARY KEY,
    FOREIGN KEY (code_bss) REFERENCES STATIONS(code_bss)
);