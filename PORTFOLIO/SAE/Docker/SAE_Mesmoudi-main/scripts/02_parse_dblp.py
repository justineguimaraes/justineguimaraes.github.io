import xml.etree.ElementTree as ET
import pandas as pd
import os

def parse_dblp():
    data = []
    membres_df = pd.read_csv("data/membres.csv")
    
    # Création d'une map (PID_sécurisé -> index_chercheur)
    # On force en string et on ignore les NaN
    pid_to_index = {}
    for idx, row in membres_df.iterrows():
        if pd.notna(row['pid_dblp']):
            safe_key = str(row['pid_dblp']).replace('/', '-')
            pid_to_index[safe_key] = idx

    cache_dir = "data/cache/dblp"
    if not os.path.exists(cache_dir): return

    for file in os.listdir(cache_dir):
        if not file.endswith(".xml"): continue
        
        file_key = file.replace(".xml", "")
        member_idx = pid_to_index.get(file_key)
        
        if member_idx is None: continue

        tree = ET.parse(os.path.join(cache_dir, file))
        root = tree.getroot()

        for r in root.findall(".//r"):
            pub = r[0]
            
            # 1. Filtre type : Exclure les éditoriaux et CoRR [cite: 442]
            if pub.tag == "proceedings": continue
            journal_node = pub.find("journal")
            if journal_node is not None and journal_node.text == "CoRR": continue

            year_node = pub.find("year")
            # 2. Filtre période : 2021-2025 [cite: 410]
            if year_node is not None and 2021 <= int(year_node.text) <= 2025:
                title = pub.find("title").text if pub.find("title") is not None else "Sans titre"
                
                if pub.tag == "article":
                    venue = journal_node.text if journal_node is not None else "Inconnu"
                    p_type = "journal"
                elif pub.tag == "inproceedings":
                    venue_node = pub.find("booktitle")
                    venue = venue_node.text if venue_node is not None else "Inconnu"
                    p_type = "conference"
                else:
                    continue
                    
                # 3. Extraction des co-auteurs
                authors = pub.findall("author")
                author_names = [a.text for a in authors if a.text is not None]
                authors_str = " | ".join(author_names)

                data.append({
                    "author_id": member_idx, # Index numérique stable
                    "type": p_type,
                    "titre": title,
                    "annee": int(year_node.text),
                    "venue_raw": venue,
                    "auteurs": authors_str
                })
    
    df_result = pd.DataFrame(data)
    os.makedirs("data/cache", exist_ok=True)
    df_result.to_csv("data/cache/all_publications_parsed.csv", index=False)
    print(f"✅ {len(df_result)} publications extraites.")

if __name__ == "__main__":
    parse_dblp()