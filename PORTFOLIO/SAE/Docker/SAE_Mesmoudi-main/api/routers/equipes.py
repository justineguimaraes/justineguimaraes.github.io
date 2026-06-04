from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from models.equipe import IndicateursEquipe
from services import indicators

router = APIRouter()

@router.get("/api/equipes/{id}/indicateurs", response_model=IndicateursEquipe, tags=["équipes"])
def get_equipe_indicators(id: str, annee_debut: Optional[int] = Query(None, description="Année de début pour l'analyse")):
    inds = indicators.get_equipe_indicators(id, annee_debut)
    if not inds:
        raise HTTPException(status_code=404, detail=f"Équipe {id} non trouvée ou sans données")
    return inds
