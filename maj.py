from model import LoadData
URL = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations?format=json"
URL_TR = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques_tr?format=json"


if __name__ == "__main__" : 
   db = LoadData(URL, URL_TR, 'SAE204.db','schema.sql')
   lst = (db.load_departements())
   db.update_bd(lst)
