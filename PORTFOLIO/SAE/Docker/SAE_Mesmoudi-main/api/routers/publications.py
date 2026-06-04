from fastapi import APIRouter, Query
from typing import List, Optional
from models.publication import Publication
from services import data_loader
import os

router = APIRouter()

@router.get("/api/publications", response_model=List[Publication], tags=["publications"])
def get_publications(
    equipe: Optional[str] = Query(None, description="Filtrer par équipe (ex: IDD, SETR)"),
    annee: Optional[int] = Query(None, description="Filtrer par année (2021-2025)"),
    type_pub: Optional[str] = Query(None, alias="type", description="Filtrer par type (journal ou conference)"),
    rank: Optional[str] = Query(None, description="Filtrer par rang CORE (A*, A, B, C, NC)"),
    quartile: Optional[str] = Query(None, description="Filtrer par quartile Scimago (Q1, Q2, Q3, Q4, NC)")
):
    # 1. Chargement des données
    all_pubs = data_loader.load_all_publications()
    
    # 2. Si on filtre par équipe, on a besoin de la correspondance auteur -> équipe
    member_team_map = {}
    if equipe:
        data_dir = os.getenv("DATA_PATH", "data")
        membres = data_loader.load_membres(os.path.join(data_dir, "membres.csv"))
        for idx, m in enumerate(membres):
            member_team_map[idx] = m['equipe']

    filtered_pubs = []
    
    for p in all_pubs:
        # Filtre équipe
        if equipe:
            auth_id = int(p['author_id'])
            if member_team_map.get(auth_id) != equipe:
                continue
        
        # Filtre année
        if annee and int(p['annee']) != annee:
            continue
            
        # Filtre type
        if type_pub and p['type'] != type_pub:
            continue
            
        # Filtre rang CORE
        if rank:
            current_rank = p.get('rank', 'NC')
            if current_rank != rank:
                continue
                
        # Filtre quartile
        if quartile:
            current_q = p.get('quartile', 'NC')
            if current_q != quartile:
                continue

        # Conversion vers le modèle Publication
        # Gestion du SJR (virgule -> point)
        sjr_raw = str(p.get('SJR', '0')).replace(',', '.')
        try:
            sjr_val = float(sjr_raw)
        except:
            sjr_val = 0.0

        filtered_pubs.append(Publication(
            titre=p['titre'],
            annee=int(p['annee']),
            type=p['type'],
            venue=p.get('venue_raw'),
            journal=p.get('venue_raw') if p['type'] == 'journal' else None,
            rang_core=p.get('rank') if p.get('rank') != 'NC' else None,
            quartile=p.get('quartile') if p.get('quartile') != 'NC' else None,
            sjr=sjr_val
        ))

    return filtered_pubs
