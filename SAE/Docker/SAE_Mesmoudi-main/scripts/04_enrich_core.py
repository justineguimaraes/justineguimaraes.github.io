import pandas as pd
import os

def enrich_core():
    input_path = "data/cache/all_publications_parsed.csv"
    if not os.path.exists(input_path):
        print("❌ Fichier de publications non trouvé. Lancez le script 02 d'abord.")
        return

    pubs = pd.read_csv(input_path)
    
    # chargement de CORE (Conférences)
    core_path = "data/core_ranks.csv"
    if os.path.exists(core_path):
        core = pd.read_csv(core_path)
        # Nettoyage pour la jointure
        core['acronym_clean'] = core['acronym'].str.upper().str.strip()
        pubs['venue_clean'] = pubs['venue_raw'].str.upper().str.strip()
        
        # Jointure
        pubs = pubs.merge(core[['acronym_clean', 'rank']], 
                         left_on='venue_clean', right_on='acronym_clean', how='left')
        pubs.drop(columns=['acronym_clean', 'venue_clean'], inplace=True)
    else:
        print("⚠️ Fichier core_ranks.csv absent. Rangs mis à 'NC'.")
        pubs['rank'] = None

    # Nettoyage final pour CORE
    pubs['rank'] = pubs['rank'].fillna("NC")
    
    output_path = "data/cache/pubs_core.csv"
    pubs.to_csv(output_path, index=False)
    print(f"✅ Enrichissement CORE terminé. {len(pubs)} lignes traitées.")

if __name__ == "__main__":
    enrich_core()