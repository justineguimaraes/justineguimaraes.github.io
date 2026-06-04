import csv
import json
import os
import requests
import time

# Chemins des fichiers
MEMBRES_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'membres.csv')
OUTPUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'all_theses.csv')

def get_theses_reporting(person_id):
    url = f"https://theses.fr/api/v1/personnes/personne/{person_id}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Erreur API pour {person_id} : {response.status_code}")
            return []

        data = response.json()
        all_roles = data.get('theses', {})
        results = []

        # Parcourir chaque catégorie de rôle
        for role_name, theses in all_roles.items():
            for t in theses:
                # 1. ID Thèse
                id_these = t.get('id')

                # 2. Statut
                status_raw = t.get('status')
                status = "Fini" if status_raw == "soutenue" else "En cours"

                # 3. Dates
                date_debut = t.get('date_inscription') or ""
                date_fin = t.get('date_soutenance') or ""

                # 4. Extraction Auteur (pour id_personne, nom, prenom)
                auteurs = t.get('auteurs', [])
                if auteurs:
                    auteur = auteurs[0]
                    id_pers = auteur.get('id', '')
                    nom_pers = auteur.get('nom', '')
                    prenom_pers = auteur.get('prenom', '')
                else:
                    id_pers, nom_pers, prenom_pers = "", "", ""

                # 5. Colonne Directeur(s)
                directeurs = [f"{d.get('prenom', '')} {d.get('nom', '')}".strip() for d in t.get('directeurs', [])]
                directeur_str = ", ".join(filter(None, directeurs))

                # 6. Colonne Collaborateur(s)
                collabs = []
                for d in t.get('directeurs', []):
                    collabs.append(f"{d.get('nom', '')} ({d.get('id', '')})")
                for a in t.get('auteurs', []):
                    if a.get('id') != id_pers:
                        collabs.append(f"{a.get('nom', '')} ({a.get('id', '')})")
                
                colaborateur_str = str(collabs)

                results.append({
                    "id_these": id_these,
                    "id_personne": id_pers,
                    "nom": nom_pers,
                    "prenom": prenom_pers,
                    "status": status,
                    "directeur": directeur_str,
                    "colaborateur": colaborateur_str,
                    "date_debut": date_debut,
                    "date_fin": date_fin
                })

        return results

    except Exception as e:
        print(f"Erreur pour {person_id}: {e}")
        return []

def main():
    print(f"Lecture des membres depuis : {MEMBRES_CSV}")
    unique_theses = {}
    
    with open(MEMBRES_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            theses_id = row.get('theses_id', '').strip()
            # Ignorer si pas d'ID thesed.fr (certains n'en ont pas ou c'est un PID dblp comme 2000POIT2261)
            # D'après le fichier, tous semblent avoir un format de type 123456789 ou 2000POIT2261
            if not theses_id:
                continue
            
            print(f"Collecte pour {row['prenom']} {row['nom']} (ID: {theses_id})...")
            
            theses_data = get_theses_reporting(theses_id)
            for t in theses_data:
                # Utiliser l'id_these comme clé pour éviter les doublons
                # car plusieurs membres peuvent participer à la même thèse
                if t['id_these']:
                    unique_theses[t['id_these']] = t

            time.sleep(0.5) # Pause entre les appels API
            
    print(f"\nÉcriture de {len(unique_theses)} thèses uniques dans : {OUTPUT_CSV}")
    
    # Colonnes attendues
    fieldnames = [
        "id_these", "id_personne", "nom", "prenom", "status", 
        "directeur", "colaborateur", "date_debut", "date_fin"
    ]
    
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        # Trier par date_debut pour que ce soit plus joli (optionnel)
        sorted_theses = sorted(unique_theses.values(), key=lambda x: str(x.get('date_debut', '')), reverse=True)
        for t_data in sorted_theses:
            writer.writerow(t_data)
            
    print("Terminé avec succès !")

if __name__ == '__main__':
    main()
