from fastapi import APIRouter, Query
from typing import Optional
from services import collaboration

router = APIRouter()

@router.get("/api/collaboration/graphe", tags=["collaboration"])
def get_collaboration_graph(equipe: Optional[str] = Query(None, description="Filtrer par équipe (ex: IDD, SETR)")):
    """
    Retourne le graphe de co-publications au format JSON.
    Nœuds = chercheurs, Arêtes = co-publications pondérées.
    """
    return collaboration.generate_collaboration_graph(equipe)
