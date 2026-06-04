import csv
import os

def load_membres(csv_path):
    membres = []
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            membres.append(row)
    return membres

def load_all_publications():
    pubs = []
    # On utilise la variable d'environnement ou le chemin par défaut
    data_dir = os.getenv("DATA_PATH", "data")
    path = os.path.join(data_dir, "cache", "pubs_final.csv")
    
    if not os.path.exists(path):
        # Fallback sur le parsed si l'enrichi n'est pas encore là
        path = os.path.join(data_dir, "cache", "all_publications_parsed.csv")
        if not os.path.exists(path):
            return []
            
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pubs.append(row)
    return pubs

def load_enriched_publications(author_idx: int):
    # Réutilisation de load_all_publications pour éviter la duplication
    all_pubs = load_all_publications()
    return [p for p in all_pubs if int(p['author_id']) == author_idx]