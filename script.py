#####################################################################
# IMPORTATION DES MODULES
#####################################################################
from model import DataBase
import requests

#On initialise l'instance de la base de données
db = DataBase()
#####################################################################
# RÉCUPÉRATION DE L'ID DE STATIONS POUR LA TABLE 'MASSE_EAU'
#####################################################################

def get_id_station(code_bss):
   query = "SELECT id_station FROM stations WHERE code_bss = ?"
   db.cursor.execute(query, (code_bss,))
   result = db.cursor.fetchone()
   return result[0] if result else 0

#####################################################################
# CHARGEMENT ET TRAITEMENT DES DONNÉES
#####################################################################
def load_data():
    URL = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations?format=json"
    response = requests.get(URL)
    #On vérifie si la requête a réussi (avec code de statut 200), ou partiellement réussi (avec code de statut = 206)
    if response.status_code == 200 or response.status_code == 206:
        data = response.json() 
        if 'data' in data:
            #On insère les données dans la base de données
            for entry in data['data']:
              #Insertion des informations des départements dans la base de données
              db.insert_dept(entry['code_departement'], entry['nom_departement'])
              #Insertion des informations des communes dans la base de données
              db.insert_commune(entry['code_commune_insee'], entry['nom_commune'], entry['code_departement'])

              #On s'assure que les champs sont des listes avant d'essayer d'accéder à leurs éléments
              code_masse_eau = entry.get('codes_masse_eau_edl')
              nom_masse_eau = entry.get('noms_masse_eau_edl')
              urn_masse_eau = entry.get('urns_masse_eau_edl')

              #On récupère le premier élément de chaque liste s'il existe et 'None' si la liste est vide
              code_masse_eau = code_masse_eau[0] if code_masse_eau else None
              nom_masse_eau = nom_masse_eau[0] if nom_masse_eau else None
              urn_masse_eau = urn_masse_eau[0] if urn_masse_eau else None
              id_station = get_id_station(entry['code_bss'])
              #On vérifie si toutes les informations nécessaires sont présentes avant d'insérer
              if id_station and code_masse_eau and nom_masse_eau and urn_masse_eau:
                db.insert_masse_eau(id_station, code_masse_eau, nom_masse_eau, urn_masse_eau) 
                
              db.insert_station(entry['code_bss'], entry['bss_id'], entry['urn_bss'], entry['code_commune_insee'],entry['profondeur_investigation'], entry['x'], entry['y'], entry['altitude_station'], entry['nb_mesures_piezo'])           
            return "Données chargées avec succès"
        else: 
            return "Il y a aucune donnée disponible"
    else:
        raise Exception(f"Erreur HTTP {response.status_code}")
  


if __name__ == "__main__":
    print(load_data())
