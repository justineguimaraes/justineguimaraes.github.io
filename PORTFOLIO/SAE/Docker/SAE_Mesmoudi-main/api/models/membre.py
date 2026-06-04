from pydantic import BaseModel
from typing import List, Optional
from .publication import Publication

class These(BaseModel):
    id_these: Optional[str] = None
    nom: str
    prenom: str
    status: str
    directeur: Optional[str] = None
    colaborateur: Optional[str] = None
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None

class Membre(BaseModel):
    id: str
    nom: str
    prenom: str
    equipe: str
    statut: str
    publications: int

class IndicateursMembre(BaseModel):
    nb_publications: int
    nb_journaux: int
    nb_conferences: int
    nb_theses: int
    score_qualite: float
    part_production_equipe: float
    statut_activite: str  # actif / peu actif / inactif

class QualiteMembre(BaseModel):
    core_distribution: dict  # {"A*": X, "A": Y, ...}
    scimago_distribution: dict  # {"Q1": X, "Q2": Y, ...}
    top_venues_count: int  # A*, A, Q1, Q2
    sjr_moyen: float

class CollaborationMembre(BaseModel):
    nb_coauteurs: int
    taux_ouverture: float  # % avec co-auteurs externes
    centralite: float

class MembreDetail(BaseModel):
    id: str
    nom: str
    prenom: str
    equipe: str
    statut: str
    indicateurs: IndicateursMembre
    qualite: QualiteMembre
    collaborations: CollaborationMembre
    publications: List[Publication]
    theses: List[These] = []