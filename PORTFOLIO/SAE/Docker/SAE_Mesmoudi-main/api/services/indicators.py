import pandas as pd
import os
from models.membre import MembreDetail, IndicateursMembre, QualiteMembre, CollaborationMembre, Publication, These
from models.equipe import IndicateursEquipe, EvolutionAnnuelle
from services import data_loader

def get_member_details(member_id: str) -> MembreDetail:
    data_path = os.getenv("DATA_PATH", "data")
    # 1. Charger les données membres
    membres = data_loader.load_membres(os.path.join(data_path, "membres.csv"))
    member_idx = -1
    target_membre = None
    
    for idx, m in enumerate(membres):
        if m['pid_dblp'] == member_id:
            member_idx = idx
            target_membre = m
            break
            
    if not target_membre:
        return None

    # 2. Charger toutes les publications enrichies
    pubs_path = os.path.join(data_path, "cache", "pubs_final.csv")
    if not os.path.exists(pubs_path):
        # Fallback si pubs_final n'existe pas encore (on prend le parsed)
        pubs_path = os.path.join(data_path, "cache", "all_publications_parsed.csv")
        if not os.path.exists(pubs_path):
            return None
        
    all_pubs = pd.read_csv(pubs_path)
    # Filtrer pour le membre
    member_pubs = all_pubs[all_pubs['author_id'] == member_idx]
    
    # 3. Calculer les indicateurs de volume
    nb_pubs = len(member_pubs)
    nb_journaux = len(member_pubs[member_pubs['type'] == 'journal'])
    nb_conferences = len(member_pubs[member_pubs['type'] == 'conference'])
    
    # Part de production équipe
    team_name = target_membre['equipe']
    # On a besoin des IDs des membres de la même équipe
    team_member_indices = [i for i, m in enumerate(membres) if m['equipe'] == team_name]
    team_pubs_total = len(all_pubs[all_pubs['author_id'].isin(team_member_indices)])
    part_equipe = (nb_pubs / team_pubs_total * 100) if team_pubs_total > 0 else 0
    
    # Statut d'activité (actif >= 3, peu actif 1-2, inactif 0) sur la période 2021-2025
    if nb_pubs >= 3:
        statut_act = "actif"
    elif nb_pubs >= 1:
        statut_act = "peu actif"
    else:
        statut_act = "inactif"
        
    # 4. Charger les thèses (nouvelle méthode via all_theses.csv)
    theses_path = os.path.join(data_path, "all_theses.csv")
    nb_theses = 0
    theses_list = []
    
    if os.path.exists(theses_path):
        theses_df = pd.read_csv(theses_path)
        # Filtrer avec le même système que la génération Excel (Directeur contient le nom de famille)
        m_theses = theses_df[theses_df['directeur'].str.contains(target_membre['nom'], na=False, case=False)]
        nb_theses = len(m_theses)
        
        for _, t_row in m_theses.iterrows():
            theses_list.append(These(
                id_these=str(t_row.get('id_these', '')),
                nom=str(t_row.get('nom', '')),
                prenom=str(t_row.get('prenom', '')),
                status=str(t_row.get('status', '')),
                directeur=str(t_row.get('directeur', '')),
                colaborateur=str(t_row.get('colaborateur', '')),
                date_debut=str(t_row.get('date_debut', '')),
                date_fin=str(t_row.get('date_fin', ''))
            ))

    # 5. Calculer la Qualité
    score_total = 0
    core_dist = {"A*": 0, "A": 0, "B": 0, "C": 0, "NC": 0}
    scimago_dist = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0, "NC": 0}
    top_venues = 0
    sjr_sum = 0
    
    for _, row in member_pubs.iterrows():
        # CORE
        rk = str(row['rank'])
        score_c = 0
        if rk == 'A*': 
            score_c = 4
            core_dist["A*"] += 1
            top_venues += 1
        elif rk == 'A': 
            score_c = 3
            core_dist["A"] += 1
            top_venues += 1
        elif rk == 'B': 
            score_c = 2
            core_dist["B"] += 1
        elif rk == 'C': 
            score_c = 1
            core_dist["C"] += 1
        else:
            core_dist["NC"] += 1
            
        # Scimago
        q = str(row['quartile'])
        score_s = 0
        if q == 'Q1': 
            score_s = 4
            scimago_dist["Q1"] += 1
            top_venues += 1
        elif q == 'Q2': 
            score_s = 3
            scimago_dist["Q2"] += 1
            top_venues += 1
        elif q == 'Q3': 
            score_s = 2
            scimago_dist["Q3"] += 1
        elif q == 'Q4': 
            score_s = 1
            scimago_dist["Q4"] += 1
        else:
            scimago_dist["NC"] += 1
            
        score_total += max(score_c, score_s)
            
        sjr_val = str(row.get('SJR', '0')).replace(',', '.')
        sjr_sum += float(sjr_val)

    score_qualite = score_total / nb_pubs if nb_pubs > 0 else 0
    sjr_moyen = sjr_sum / nb_pubs if nb_pubs > 0 else 0
    
    # 6. Collaboration — calcul basé sur les co-publications
    coauteurs_set = set()
    for _, row in member_pubs.iterrows():
        title = row['titre'].strip().lower()
        # Chercher les autres auteurs de la même publication
        coauthors_for_title = all_pubs[all_pubs['titre'].str.strip().str.lower() == title]
        for _, ca_row in coauthors_for_title.iterrows():
            ca_idx = ca_row['author_id']
            if ca_idx != member_idx:
                coauteurs_set.add(ca_idx)

    nb_coauteurs = len(coauteurs_set)
    # Taux d'ouverture : % de co-auteurs dans une équipe différente
    if nb_coauteurs > 0:
        nb_externes = 0
        for ca_idx in coauteurs_set:
            if ca_idx < len(membres) and membres[int(ca_idx)]['equipe'] != team_name:
                nb_externes += 1
        taux_ouverture = round(nb_externes / nb_coauteurs * 100, 2)
    else:
        taux_ouverture = 0.0

    # Centralité (Betweenness)
    import networkx as nx
    G = nx.Graph()
    
    # Récupérer les paires de coauteurs de toute l'équipe pour avoir un graphe représentatif
    # On va calculer la betweenness sur le sous-graphe des publications de l'équipe
    team_pubs_df = all_pubs[all_pubs['author_id'].isin(team_member_indices)]
    pubs_by_title_team = {}
    for _, row in team_pubs_df.iterrows():
        title = str(row['titre']).strip().lower()
        if title not in pubs_by_title_team:
            pubs_by_title_team[title] = set()
        pubs_by_title_team[title].add(row['author_id'])
        
    for title, authors in pubs_by_title_team.items():
        authors_list = list(authors)
        for i in range(len(authors_list)):
            for j in range(i + 1, len(authors_list)):
                G.add_edge(authors_list[i], authors_list[j])
                
    b_centralities = nx.betweenness_centrality(G)
    centralite = round(b_centralities.get(member_idx, 0.0), 3)

    collab = CollaborationMembre(
        nb_coauteurs=nb_coauteurs,
        taux_ouverture=taux_ouverture,
        centralite=centralite
    )
    
    # 7. Liste des publications formattée
    pubs_list = []
    for _, row in member_pubs.iterrows():
        pubs_list.append(Publication(
            titre=row['titre'],
            annee=int(row['annee']),
            type=row['type'],
            venue=row['venue_raw'],
            journal=row['venue_raw'] if row['type'] == 'journal' else None,
            rang_core=row['rank'] if row['rank'] != 'NC' else None,
            quartile=row['quartile'] if row['quartile'] != 'NC' else None,
            sjr=float(str(row.get('SJR', '0')).replace(',', '.'))
        ))

    return MembreDetail(
        id=member_id,
        nom=target_membre['nom'],
        prenom=target_membre['prenom'],
        equipe=target_membre['equipe'],
        statut=target_membre['statut'],
        indicateurs=IndicateursMembre(
            nb_publications=nb_pubs,
            nb_journaux=nb_journaux,
            nb_conferences=nb_conferences,
            nb_theses=nb_theses,
            score_qualite=round(score_qualite, 2),
            part_production_equipe=round(part_equipe, 2),
            statut_activite=statut_act
        ),
        qualite=QualiteMembre(
            core_distribution=core_dist,
            scimago_distribution=scimago_dist,
            top_venues_count=top_venues,
            sjr_moyen=round(sjr_moyen, 3)
        ),
        collaborations=collab,
        publications=pubs_list,
        theses=theses_list
    )

def count_publication(pid):
    if not pid: return 0
    data_path = os.getenv("DATA_PATH", "data")
    membres = data_loader.load_membres(os.path.join(data_path, "membres.csv"))
    idx = -1
    for i, m in enumerate(membres):
        if m['pid_dblp'] == pid:
            idx = i
            break
    if idx == -1: return 0
    
    pubs_path = os.path.join(data_path, "cache", "all_publications_parsed.csv")
    if not os.path.exists(pubs_path): return 0
    df = pd.read_csv(pubs_path)
    return len(df[df['author_id'] == idx])

def get_equipe_indicators(equipe_id: str, annee_debut: int = None) -> IndicateursEquipe:
    data_path = os.getenv("DATA_PATH", "data")
    membres = data_loader.load_membres(os.path.join(data_path, "membres.csv"))
    
    # 1. Filtrer les membres de l'équipe
    team_members = [m for m in membres if m['equipe'] == equipe_id]
    team_member_indices = [idx for idx, m in enumerate(membres) if m['equipe'] == equipe_id]
    
    if not team_members:
        return None

    # 2. Charger les publications
    all_pubs = data_loader.load_all_publications()
    
    # Filtrer par auteur et par année
    team_pubs = []
    for p in all_pubs:
        try:
            auth_id = int(p['author_id'])
            if auth_id in team_member_indices:
                year = int(p['annee'])
                if annee_debut and year < annee_debut:
                    continue
                team_pubs.append(p)
        except:
            continue

    # 3. Calculer les agrégats
    nb_total = len(team_pubs)
    nb_journaux = len([p for p in team_pubs if p['type'] == 'journal'])
    nb_conferences = len([p for p in team_pubs if p['type'] == 'conference'])
    
    core_dist = {"A*": 0, "A": 0, "B": 0, "C": 0, "NC": 0}
    scimago_dist = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0, "NC": 0}
    score_total = 0
    
    nb_theses_soutenues = 0
    nb_theses_encours = 0
    taux_encadrement_hdr = 0.0
    nb_pubs_theses = 0
    
    # Traitement thèses
    theses_path = os.path.join(data_path, "all_theses.csv")
    team_noms = [m['nom'] for m in team_members]
    doctorants = set()
    
    if os.path.exists(theses_path) and team_noms:
        import re
        theses_df = pd.read_csv(theses_path)
        pattern = '|'.join([re.escape(n) for n in team_noms])
        team_theses_df = theses_df[theses_df['directeur'].str.contains(pattern, na=False, case=False, regex=True)]
        
        def is_in_2021_2025(row):
            d1 = str(row.get('date_debut', ''))
            d2 = str(row.get('date_fin', ''))
            return any(str(y) in d1 or str(y) in d2 for y in range(2021, 2026))

        t_filtered = team_theses_df[team_theses_df.apply(is_in_2021_2025, axis=1)]
        nb_theses_soutenues = len(t_filtered[t_filtered['status'] == 'Fini'])
        nb_theses_encours = len(t_filtered[t_filtered['status'] == 'En cours'])
        
        doctorants = set(t_filtered['nom'].dropna().str.lower().str.strip())
        
        hdr_pr_members = [m for m in team_members if 'Professeur' in m['statut'] or 'HDR' in m['statut']]
        if hdr_pr_members:
            directeurs_strs = " ".join(t_filtered['directeur'].dropna().str.lower().tolist())
            encadrent = sum(1 for m in hdr_pr_members if m['nom'].lower() in directeurs_strs)
            taux_encadrement_hdr = round((encadrent / len(hdr_pr_members)) * 100, 2)
            
    # Évolution
    evolution_map = {}
    
    for p in team_pubs:
        # Evolution
        y = int(p['annee'])
        evolution_map[y] = evolution_map.get(y, 0) + 1
        
        # CORE
        rk = p.get('rank', 'NC')
        if rk in core_dist: core_dist[rk] += 1
        else: core_dist["NC"] += 1
        
        # Scimago
        q = p.get('quartile', 'NC')
        if q in scimago_dist: scimago_dist[q] += 1
        else: scimago_dist["NC"] += 1
        
        # Score Qualité
        score_c = 0
        if rk == 'A*': score_c = 4
        elif rk == 'A': score_c = 3
        elif rk == 'B': score_c = 2
        elif rk == 'C': score_c = 1
        
        score_s = 0
        if q == 'Q1': score_s = 4
        elif q == 'Q2': score_s = 3
        elif q == 'Q3': score_s = 2
        elif q == 'Q4': score_s = 1

        score_total += max(score_c, score_s)

    score_moyen = score_total / nb_total if nb_total > 0 else 0
    
    # Sort evolution
    evolution_list = []
    for y in sorted(evolution_map.keys()):
        evolution_list.append(EvolutionAnnuelle(annee=y, nb_publications=evolution_map[y]))
        
    # Pubs theses
    if doctorants:
        for p in team_pubs:
            auteurs_pub = str(p.get('auteurs', '')).lower()
            if any(doc in auteurs_pub for doc in doctorants if len(doc) > 2): # >2 to avoid matching trivial substrings
                nb_pubs_theses += 1

    return IndicateursEquipe(
        id_equipe=equipe_id,
        nombre_membres=len(team_members),
        nb_publications_total=nb_total,
        nb_journaux=nb_journaux,
        nb_conferences=nb_conferences,
        score_qualite_moyen=round(score_moyen, 2),
        core_distribution=core_dist,
        scimago_distribution=scimago_dist,
        evolution_temporelle=evolution_list,
        nb_theses_soutenues=nb_theses_soutenues,
        nb_theses_encours=nb_theses_encours,
        taux_encadrement_hdr=taux_encadrement_hdr,
        nb_pubs_theses=nb_pubs_theses
    )