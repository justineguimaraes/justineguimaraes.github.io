from pydantic import BaseModel
from typing import List, Optional, Dict

# ─── Requêtes ────────────────────────────────────────────────
class MarginalisationRequest(BaseModel):
    member_ids: List[str]            # PID DBLP des membres à marginaliser
    taux_reduction: float = 1.0      # 0.5 = -50%, 1.0 = -100%

class TransfertRequest(BaseModel):
    member_id: str                   # PID DBLP du membre à transférer
    equipe_origine: str              # ex: "IDD"
    equipe_destination: str          # ex: "SETR"

# ─── Indicateurs (avant / après) ─────────────────────────────
class IndicateursSnapshot(BaseModel):
    nb_publications: int
    nb_journaux: int
    nb_conferences: int
    productivite_par_membre: float
    productivite_par_membre_actif: float
    taux_membres_actifs: float
    score_qualite_moyen: float
    indice_gini: float
    core_distribution: Dict[str, int]
    scimago_distribution: Dict[str, int]

# ─── Réponses ────────────────────────────────────────────────
class MarginalisationResult(BaseModel):
    avant: IndicateursSnapshot
    apres: IndicateursSnapshot
    ecarts: Dict[str, float]         # clé = indicateur, valeur = écart en %

class TransfertResult(BaseModel):
    equipe_origine_avant: IndicateursSnapshot
    equipe_origine_apres: IndicateursSnapshot
    equipe_destination_avant: IndicateursSnapshot
    equipe_destination_apres: IndicateursSnapshot
    ecarts_origine: Dict[str, float]
    ecarts_destination: Dict[str, float]

# ─── Projections Fusion ──────────────────────────────────────
class ProjectionAnnuelle(BaseModel):
    annee: int
    nb_publications: int

class ProjectionScenario(BaseModel):
    nom: str
    historique: List[ProjectionAnnuelle] # 2021-2025 (réel, commun)
    projection: List[ProjectionAnnuelle] # 2026-2030 (projeté)
    total_5_ans: int
    productivite_moyenne: float
    indice_gini_moyen: float
    score_qualite_estime: float

class FusionProjectionResult(BaseModel):
    scenarios: List[ProjectionScenario]
