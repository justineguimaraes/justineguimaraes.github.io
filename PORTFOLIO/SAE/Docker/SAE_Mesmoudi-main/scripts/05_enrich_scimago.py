"""
05_enrich_scimago.py
Enrichissement des publications avec les quartiles Scimago (SJR).
Utilise un mapping DBLP -> Scimago pour les noms abrégés + recherche exacte.
"""
import pandas as pd
import os

# ──────────────────────────────────────────────────────────────
# Mapping manuel : abréviation DBLP -> titre Scimago (EXACT)
# Ce mapping couvre les journaux du périmètre LIAS 2021-2025
# Pour ajouter un journal absent, ajouter une entrée ici.
# ──────────────────────────────────────────────────────────────
DBLP_TO_SCIMAGO = {
    "Real Time Syst.": "Real-Time Systems",
    "IEEE Geosci. Remote. Sens. Lett.": "IEEE Geoscience and Remote Sensing Letters",
    "Remote. Sens.": "Remote Sensing",
    "IEEE J. Sel. Top. Appl. Earth Obs. Remote. Sens.": "IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing",
    "World Wide Web (WWW)": "World Wide Web",
    "IEEE Trans. Neural Networks Learn. Syst.": "IEEE Transactions on Neural Networks and Learning Systems",
    "Comput. Sci. Inf. Syst.": "Computer Science and Information Systems",
    "Neural Comput. Appl.": "Neural Computing and Applications",
    "Distributed Parallel Databases": "Distributed and Parallel Databases",
    "Comput. Electron. Agric.": "Computers and Electronics in Agriculture",
    "Sensors": "Sensors",
    "Int. J. Intell. Comput. Cybern.": "International Journal of Intelligent Computing and Cybernetics",
    "IEEE Trans. Serv. Comput.": "IEEE Transactions on Services Computing",
    "Fuzzy Sets Syst.": "Fuzzy Sets and Systems",
    "Inf. Fusion": "Information Fusion",
    "Inf. Syst.": "Information Systems",
    "Inf. Syst. Frontiers": "Information Systems Frontiers",
    "J. Supercomput.": "Journal of Supercomputing",
    "VLDB J.": "VLDB Journal",
    "Data Knowl. Eng.": "Data and Knowledge Engineering",
    "Softw. Syst. Model.": "Software and Systems Modeling",
    "Computing": "Computing",
    "Concurr. Comput. Pract. Exp.": "Concurrency and Computation: Practice and Experience",
    "Eng. Appl. Artif. Intell.": "Engineering Applications of Artificial Intelligence",
    "Future Gener. Comput. Syst.": "Future Generation Computer Systems",
    "Knowl. Inf. Syst.": "Knowledge and Information Systems",
    "IEEE Trans. Knowl. Data Eng.": "IEEE Transactions on Knowledge and Data Engineering",
    "Serv. Oriented Comput. Appl.": "Service Oriented Computing and Applications",
    "Wirel. Pers. Commun.": "Wireless Personal Communications",
    "J. Syst. Archit.": "Journal of Systems Architecture",
    "J. Comput. Lang.": "Journal of Computer Languages",
    "Dagstuhl Artifacts Ser.": "Dagstuhl Artifacts Series",
    "EURO J. Comput. Optim.": "EURO Journal on Computational Optimization",
    "Unmanned Syst.": "Unmanned Systems",
    "Rev. Symb. Log.": "Review of Symbolic Logic",
    "IEEE Trans. Emerg. Top. Comput.": "IEEE Transactions on Emerging Topics in Computing",
    "IEEE Commun. Mag.": "IEEE Communications Magazine",
    "IEEE Trans. Inf. Theory": "IEEE Transactions on Information Theory",
    "IEEE Trans. Wirel. Commun.": "IEEE Transactions on Wireless Communications",
    "IEEE Wirel. Commun. Lett.": "IEEE Wireless Communications Letters",
    "IEEE Trans. Aerosp. Electron. Syst.": "IEEE Transactions on Aerospace and Electronic Systems",
    "IEEE Wirel. Commun.": "IEEE Wireless Communications",
    "IEEE Internet Things J.": "IEEE Internet of Things Journal",
    "Int. J. Wirel. Inf. Networks": "International Journal of Wireless Information Networks",
    "IEEE Open J. Commun. Soc.": "IEEE Open Journal of the Communications Society",
}


def enrich_scimago():
    input_path = "data/cache/pubs_core.csv"
    if not os.path.exists(input_path):
        print("❌ Fichier pubs_core.csv non trouvé. Lancez le script 04 d'abord.")
        return

    pubs = pd.read_csv(input_path)

    # ============ Chargement de Scimago ============
    scimago_path = "data/scimago.csv"
    scimago_loaded = False

    if os.path.exists(scimago_path) and os.path.getsize(scimago_path) > 0:
        try:
            scimago = pd.read_csv(scimago_path, sep=';', encoding='utf-8')

            if 'Title' in scimago.columns:
                # Nettoyage du titre Scimago
                scimago['Title_clean'] = scimago['Title'].str.strip().str.upper()

                # ============ Mapping DBLP -> Scimago ============
                # On traduit les noms DBLP vers les noms Scimago
                pubs['scimago_lookup'] = pubs['venue_raw'].map(DBLP_TO_SCIMAGO)
                # Fallback : si pas dans le mapping, on tente le match direct
                pubs['scimago_lookup'] = pubs['scimago_lookup'].fillna(pubs['venue_raw'])
                pubs['scimago_lookup_clean'] = pubs['scimago_lookup'].str.strip().str.upper()

                cols_to_use = ['Title_clean']
                if 'SJR Best Quartile' in scimago.columns:
                    cols_to_use.append('SJR Best Quartile')
                if 'SJR' in scimago.columns:
                    cols_to_use.append('SJR')

                # Jointure sur le nom traduit
                pubs = pubs.merge(
                    scimago[cols_to_use].drop_duplicates(subset=['Title_clean']),
                    left_on='scimago_lookup_clean',
                    right_on='Title_clean',
                    how='left'
                )
                pubs.drop(columns=['Title_clean', 'scimago_lookup', 'scimago_lookup_clean'], inplace=True)
                scimago_loaded = True

                # Stats de couverture
                journals = pubs[pubs['type'] == 'journal']
                matched = journals[journals['SJR Best Quartile'].notna() & (journals['SJR Best Quartile'] != '')]
                print(f"📊 Couverture Scimago : {len(matched)}/{len(journals)} journaux ({round(len(matched)/len(journals)*100,1)}%)")

        except Exception as e:
            print(f"⚠️ Erreur lors de la lecture de scimago.csv : {e}")

    if not scimago_loaded:
        print("⚠️ Fichier scimago.csv absent ou vide. Quartiles mis à 'NC'.")
        if 'SJR Best Quartile' not in pubs.columns:
            pubs['SJR Best Quartile'] = None
        if 'SJR' not in pubs.columns:
            pubs['SJR'] = 0

    # ============ Nettoyage final ============
    pubs['quartile'] = pubs['SJR Best Quartile'].fillna("NC")
    pubs['SJR'] = pubs['SJR'].fillna(0)

    output_path = "data/cache/pubs_final.csv"
    pubs.to_csv(output_path, index=False)
    print(f"✅ Enrichissement Scimago terminé. {len(pubs)} lignes traitées.")


if __name__ == "__main__":
    enrich_scimago()
