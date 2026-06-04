from fastapi import APIRouter, Query
from services import data_loader
from services import indicators
from models.membre import Membre, MembreDetail
import os

router = APIRouter()

@router.get("/api/membres", tags=["membres"])
def api_membres(equipe: str = Query(None)):
    data_path = os.getenv("DATA_PATH", "data")
    membres = data_loader.load_membres(os.path.join(data_path, "membres.csv"))
    result = []

    for membre in membres:
        if equipe and membre["equipe"] != equipe:
            continue

        nb_pub = indicators.count_publication(membre["pid_dblp"])

        result.append(
            Membre(
                id=membre["pid_dblp"],
                nom=membre["nom"],
                prenom=membre["prenom"],
                equipe=membre["equipe"],
                statut=membre["statut"],
                publications=nb_pub
            )
        )

    return result
@router.get("/api/membres/{id:path}", response_model=MembreDetail, tags=["membres"])
def api_membre_detail(id: str):
    detail = indicators.get_member_details(id)
    if not detail:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Membre non trouvé")
    return detail
