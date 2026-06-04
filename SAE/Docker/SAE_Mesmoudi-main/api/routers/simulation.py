from fastapi import APIRouter
from models.simulation import (
    MarginalisationRequest, MarginalisationResult,
    TransfertRequest, TransfertResult, FusionProjectionResult
)
from services import simulation

router = APIRouter()

@router.post("/api/simulation/marginalisation", response_model=MarginalisationResult, tags=["simulation"])
def simulate_marginalization(req: MarginalisationRequest):
    """
    Simule la marginalisation d'un ou plusieurs membres.
    Recalcule les indicateurs de leur équipe en réduisant leur production.
    """
    return simulation.run_marginalization(req.member_ids, req.taux_reduction)

@router.post("/api/simulation/transfert", response_model=TransfertResult, tags=["simulation"])
def simulate_transfer(req: TransfertRequest):
    """
    Simule le transfert d'un membre d'une équipe vers une autre.
    Recalcule les indicateurs des deux équipes (avant / après).
    """
    return simulation.run_transfer(req.member_id, req.equipe_origine, req.equipe_destination)

@router.get("/api/simulation/projection_fusion", response_model=FusionProjectionResult, tags=["simulation"])
def simulate_fusion_projection():
    """
    Retourne la projection à 5 ans pour l'équipe fusionnée IDD+SETR sous 3 scénarios (Baseline, Optimiste, Pessimiste).
    """
    return simulation.run_fusion_projection()
