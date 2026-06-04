"""
Service de collaboration : construction du graphe de co-publications.
"""
import os
from typing import List, Dict, Optional
from services import data_loader


def generate_collaboration_graph(equipe: Optional[str] = None) -> Dict:
    """
    Construit le graphe de co-publications au format JSON pour la visualisation.
    Nœuds = chercheurs, Arêtes = nombre de co-publications.

    Retourne:
      {"nodes": [...], "edges": [...]}
    """
    data_path = os.getenv("DATA_PATH", "data")
    all_members = data_loader.load_membres(os.path.join(data_path, "membres.csv"))
    all_pubs = data_loader.load_all_publications()

    # Filtrer les membres par équipe si demandé
    if equipe:
        members = [m for m in all_members if m['equipe'] == equipe]
    else:
        members = all_members

    # Créer un mapping idx -> info membre
    idx_to_member = {}
    for idx, m in enumerate(all_members):
        idx_to_member[idx] = m

    member_indices = set()
    for m in members:
        for idx, am in enumerate(all_members):
            if am['pid_dblp'] == m['pid_dblp']:
                member_indices.add(idx)
                break

    # Grouper les publications par titre (pour trouver les co-publications)
    pubs_by_title = {}
    for p in all_pubs:
        try:
            aid = int(p['author_id'])
        except:
            continue
        if aid not in member_indices:
            continue
        title = p['titre'].strip().lower()
        if title not in pubs_by_title:
            pubs_by_title[title] = set()
        pubs_by_title[title].add(aid)

    # Construire les arêtes
    edges_count = {}
    for title, authors in pubs_by_title.items():
        authors_list = sorted(authors)
        for i in range(len(authors_list)):
            for j in range(i + 1, len(authors_list)):
                pair = (authors_list[i], authors_list[j])
                edges_count[pair] = edges_count.get(pair, 0) + 1

    # Collecter les nœuds qui apparaissent dans au moins une publication
    active_nodes = set()
    for p in all_pubs:
        try:
            aid = int(p['author_id'])
        except:
            continue
        if aid in member_indices:
            active_nodes.add(aid)

    # Construire le résultat
    nodes = []
    for idx in active_nodes:
        m = idx_to_member.get(idx, {})
        nodes.append({
            "id": idx,
            "label": f"{m.get('prenom', '')} {m.get('nom', '')}".strip(),
            "equipe": m.get('equipe', ''),
            "pid": m.get('pid_dblp', '')
        })

    edges = []
    for (a, b), weight in edges_count.items():
        edges.append({
            "source": a,
            "target": b,
            "weight": weight
        })

    import networkx as nx

    G = nx.Graph()
    for node in nodes:
        G.add_node(node['id'])
    for edge in edges:
        G.add_edge(edge['source'], edge['target'], weight=edge['weight'])

    # Computing Betweenness Centrality
    b_centralities = nx.betweenness_centrality(G, weight='weight')
    
    for node in nodes:
        node['betweenness'] = round(b_centralities.get(node['id'], 0.0), 3)

    # Métriques
    nb_intra = 0
    nb_inter = 0
    for (a, b), weight in edges_count.items():
        eq_a = idx_to_member.get(a, {}).get('equipe', '')
        eq_b = idx_to_member.get(b, {}).get('equipe', '')
        if eq_a == eq_b:
            nb_intra += weight
        else:
            nb_inter += weight

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "nb_noeuds": len(nodes),
            "nb_aretes": len(edges),
            "collaborations_intra_equipe": nb_intra,
            "collaborations_inter_equipes": nb_inter
        }
    }
