from pydantic import BaseModel
from typing import Dict, List, Optional

class EvolutionAnnuelle(BaseModel):
    annee: int
    nb_publications: int

class IndicateursEquipe(BaseModel):
    id_equipe: str
    nombre_membres: int
    nb_publications_total: int
    nb_journaux: int
    nb_conferences: int
    score_qualite_moyen: float
    core_distribution: Dict[str, int]
    scimago_distribution: Dict[str, int]
    evolution_temporelle: List[EvolutionAnnuelle]
    nb_theses_soutenues: int = 0
    nb_theses_encours: int = 0
    taux_encadrement_hdr: float = 0.0
    nb_pubs_theses: int = 0
