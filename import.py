from model import LoadData
import asyncio
import datetime

#variable globale 
URL = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations?format=json"
URL_TR = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques_tr?format=json"

#création de la Base de données
if __name__ == "__main__" : 
    
    db = LoadData(URL, URL_TR, 'SAE204.db','schema.sql')
    db.init_db()
    lst = (db.load_departements())
    db.load_stations(lst)
    asyncio.run(db.load_stations_tr())
    db.lastupdate = datetime.datetime.now()
