import requests
import time
import os
import pandas as pd

MEMBRES_CSV = "data/membres.csv"
CACHE_DIR = "data/cache/dblp"
os.makedirs(CACHE_DIR, exist_ok=True)

def load_overrides():
    overrides_path = "data/overrides.csv"
    if os.path.exists(overrides_path):
        # On lit le fichier en ignorant les lignes de commentaires (#)
        df_ov = pd.read_csv(overrides_path, comment='#')
        # On ne garde que les overrides de PID
        return df_ov[df_ov['champ'] == 'pid_dblp'].set_index('nom')['valeur_corrigee'].to_dict()
    return {}

def collect_dblp():
    df = pd.read_csv(MEMBRES_CSV)
    overrides = load_overrides()
    
    for index, row in df.iterrows():
        fullname = f"{row['nom']} {row['prenom']}"
        pid = row['pid_dblp']
        
        # Application de l'override si présent
        if row['nom'] in overrides:
             pid = overrides[row['nom']]
             print(f"🔧 Override PID pour {row['nom']} : {pid}")
        elif fullname in overrides:
             pid = overrides[fullname]
             print(f"🔧 Override PID pour {fullname} : {pid}")

        # Vérifie si le PID est valide
        if pd.isna(pid) or str(pid).strip() == "":
            print(f"⏩ Saut de {row['nom']} {row['prenom']} (pas de PID DBLP)")
            continue

        name = row['nom']
        # On remplace le slash pour le nom du fichier local
        safe_pid = str(pid).replace('/', '-')
        output_file = os.path.join(CACHE_DIR, f"{safe_pid}.xml")
        
        if not os.path.exists(output_file):
            print(f"Téléchargement pour {name} (PID: {pid})...")
            url = f"https://dblp.org/pid/{pid}.xml"
            try:
                r = requests.get(url)
                r.raise_for_status()
                with open(output_file, 'wb') as f:
                    f.write(r.content)
                time.sleep(2.5) # Rate limiting requis [cite: 485, 722]
            except Exception as e:
                print(f"❌ Erreur pour {name}: {e}")
        else:
            print(f"✅ {name} est déjà en cache.")

if __name__ == "__main__":
    collect_dblp()