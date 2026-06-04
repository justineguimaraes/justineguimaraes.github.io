import pandas as pd
import os

def generate_excel():
    data_dir = os.getenv("DATA_PATH", "data")
    pubs_path = os.path.join(data_dir, "cache", "pubs_final.csv")
    membres_path = os.path.join(data_dir, "membres.csv")
    theses_path = os.path.join(data_dir, "all_theses.csv")
    output_dir = os.path.join(data_dir, "output", "chercheurs")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(pubs_path):
        print("❌ Fichier pubs_final.csv absent.")
        return

    # 1. Chargement des données
    pubs_df = pd.read_csv(pubs_path)
    membres_df = pd.read_csv(membres_path)
    theses_df = pd.read_csv(theses_path) if os.path.exists(theses_path) else pd.DataFrame(columns=['id_these', 'id_personne', 'nom', 'prenom', 'status', 'directeur', 'colaborateur', 'date_debut', 'date_fin'])
    
    membres_df['author_id'] = membres_df.index
    
    # 2. Génération des fichiers individuels (Livrable #2)
    for idx, row in membres_df.iterrows():
        m_pubs = pubs_df[pubs_df['author_id'] == idx].copy()
        # On cherche toutes les theses où la personne est listée comme directeur
        nom_complet = f"{row['prenom']} {row['nom']}"
        m_theses_val = theses_df[theses_df['directeur'].str.contains(row['nom'], na=False, case=False)]
        nb_theses = len(m_theses_val)
        
        filename = f"{row['nom']}_{row['prenom']}.xlsx"
        filepath = os.path.join(output_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            # Onglet Journaux
            journaux = m_pubs[m_pubs['type'] == 'journal'][['titre', 'annee', 'venue_raw', 'quartile', 'SJR']]
            journaux.to_excel(writer, sheet_name='Journaux', index=False)
            
            # Onglet Conférences
            confs = m_pubs[m_pubs['type'] == 'conference'][['titre', 'annee', 'venue_raw', 'rank']]
            confs.to_excel(writer, sheet_name='Conférences', index=False)
            
            # Onglet Thèses
            if not m_theses_val.empty:
                m_theses_val.to_excel(writer, sheet_name='Thèses', index=False)
            else:
                pd.DataFrame([{'Information': 'Aucune thèse trouvée'}]).to_excel(writer, sheet_name='Thèses', index=False)
            
            # Onglet Résumé
            resume = {
                'Indicateur': ['Total Publications', 'Journaux', 'Conférences', 'Thèses dirigées', 'Score Qualité'],
                'Valeur': [
                    len(m_pubs),
                    len(journaux),
                    len(confs),
                    nb_theses,
                    round(m_pubs.apply(lambda r: (4 if r['rank'] in ['A*', 'Q1'] else (3 if r['rank'] in ['A', 'Q2'] else (2 if r['rank'] in ['B', 'Q3'] else (1 if r['rank'] in ['C', 'Q4'] else 0)))), axis=1).mean() if len(m_pubs)>0 else 0, 2)
                ]
            }
            pd.DataFrame(resume).to_excel(writer, sheet_name='Résumé', index=False)

    # 3. Fichier consolidé (Livrable #2 suite)
    combined_pubs = pubs_df.merge(membres_df[['author_id', 'nom', 'prenom', 'equipe']], on='author_id', how='left')
    
    # Résumé par Chercheur
    chercheur_stats = combined_pubs.groupby(['author_id', 'nom', 'prenom', 'equipe']).agg(
        nb_publications=('titre', 'count'),
        nb_A_star=('rank', lambda x: (x == 'A*').sum()),
        nb_A=('rank', lambda x: (x == 'A').sum()),
        nb_Q1=('quartile', lambda x: (x == 'Q1').sum()),
        nb_Q2=('quartile', lambda x: (x == 'Q2').sum())
    ).reset_index()
    # Agrégation des thèses pour le résumé consolidé
    if not theses_df.empty:
        # On va créer une colonne nb_theses pour chaque personne via la même logique
        def count_theses(r):
            return len(theses_df[theses_df['directeur'].str.contains(r['nom'], na=False, case=False)])
        chercheur_stats['nb_theses'] = chercheur_stats.apply(count_theses, axis=1)
    else:
        chercheur_stats['nb_theses'] = 0

    consolidated_path = os.path.join(data_dir, "output", "consolidated.xlsx")
    with pd.ExcelWriter(consolidated_path, engine='xlsxwriter') as writer:
        chercheur_stats.to_excel(writer, sheet_name='Synthèse Chercheurs', index=False)
        # Résumé par Équipe
        equipe_stats = chercheur_stats.groupby('equipe').agg(
            nb_membres=('nom', 'count'),
            total_pubs=('nb_publications', 'sum'),
            moy_pubs=('nb_publications', 'mean')
        ).reset_index()
        equipe_stats.to_excel(writer, sheet_name='Synthèse Équipes', index=False)
        combined_pubs.to_excel(writer, sheet_name='Détail Publications', index=False)

    print(f"✨ Rapports générés dans {output_dir}")
    print(f"✨ Fichier consolidé : {consolidated_path}")

if __name__ == "__main__":
    generate_excel()
