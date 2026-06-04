"""
03a_collect_core.py
Scraping des rangs CORE pour les conférences à partir du portail CORE.
[Source: https://portal.core.edu.au/conf-ranks/]
"""
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os


def scrap_core_ranks():
    pubs_path = "data/cache/all_publications_parsed.csv"
    if not os.path.exists(pubs_path):
        print("❌ Fichier de publications absent. Lance le script 02 d'abord.")
        return

    pubs = pd.read_csv(pubs_path)
    # On ne cherche que les conférences
    acronyms = pubs[pubs['type'] == 'conference']['venue_raw'].unique()

    results = []
    print(f"🔎 {len(acronyms)} conférences à vérifier sur le portail CORE...")

    for acronym in acronyms:
        if pd.isna(acronym) or acronym == "Inconnu":
            continue

        # Nettoyage de l'acronyme pour la recherche
        search_term = re.sub(r'\(.*?\)', '', acronym).strip()
        if search_term.startswith("IEEE "):
            search_term = search_term.replace("IEEE ", "").strip()
        # On ne garde que le premier mot si composé (sauf noms connus)
        known_multi_word = ["Big Data", "VTC Fall", "VTC Spring"]
        if " " in search_term and not any(k in search_term for k in known_multi_word):
            search_term = search_term.split(' ')[0]

        print(f"  Recherche de : {search_term} (original: {acronym})...")
        url = f"https://portal.core.edu.au/conf-ranks/?search={search_term}&by=all&source=CORE2023"

        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            table = soup.find('table')
            if table:
                rows = table.find_all('tr')[1:]  # On ignore l'entête
                found = False
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) > 3:
                        res_acronym = cols[1].text.strip().upper()
                        if search_term.upper() == res_acronym:
                            rank = cols[3].text.strip()
                            if "note" in rank.lower():
                                rank = "TBR"
                            results.append({"acronym": acronym, "rank": rank})
                            print(f"    ✅ Trouvé : {rank}")
                            found = True
                            break

                if not found:
                    if rows:
                        cols = rows[0].find_all('td')
                        if len(cols) > 3:
                            rank = cols[3].text.strip()
                            if "note" in rank.lower():
                                rank = "TBR"
                            results.append({"acronym": acronym, "rank": rank})
                            print(f"    ✅ Trouvé (proximité) : {rank}")
                        else:
                            results.append({"acronym": acronym, "rank": "none"})
                    else:
                        results.append({"acronym": acronym, "rank": "none"})
            else:
                results.append({"acronym": acronym, "rank": "none"})

            time.sleep(1.2)

        except Exception as e:
            print(f"    ❌ Erreur pour {acronym}: {e}")
            results.append({"acronym": acronym, "rank": "none"})

    df_core = pd.DataFrame(results)
    os.makedirs("data", exist_ok=True)
    df_core.to_csv("data/core_ranks.csv", index=False)
    print(f"✨ {len(results)} rangs enregistrés dans data/core_ranks.csv")


if __name__ == "__main__":
    scrap_core_ranks()