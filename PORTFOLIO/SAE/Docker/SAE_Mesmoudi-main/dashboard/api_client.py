"""
Client HTTP centralisé pour communiquer avec l'API FastAPI.
"""
import os
import requests

API_URL = os.getenv("API_URL", "http://api:8000")


def get(endpoint: str, params: dict = None):
    """GET request vers l'API."""
    url = f"{API_URL}{endpoint}"
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None


def post(endpoint: str, json_data: dict = None):
    """POST request vers l'API."""
    url = f"{API_URL}{endpoint}"
    try:
        r = requests.post(url, json=json_data, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None


# ─── Endpoints raccourcis ──────────────────────────────────────

def get_membres(equipe: str = None):
    params = {"equipe": equipe} if equipe else None
    return get("/api/membres", params)

def get_membre_detail(pid: str):
    return get(f"/api/membres/{pid}")

def get_publications(**filters):
    params = {k: v for k, v in filters.items() if v is not None}
    return get("/api/publications", params)

def get_equipe_indicateurs(equipe_id: str, annee_debut: int = None):
    params = {"annee_debut": annee_debut} if annee_debut else None
    return get(f"/api/equipes/{equipe_id}/indicateurs", params)

def get_collaboration_graphe(equipe: str = None):
    params = {"equipe": equipe} if equipe else None
    return get("/api/collaboration/graphe", params)

def simulate_marginalisation(member_ids: list, taux: float = 1.0):
    return post("/api/simulation/marginalisation", {
        "member_ids": member_ids,
        "taux_reduction": taux
    })

def simulate_transfert(member_id: str, origine: str, destination: str):
    return post("/api/simulation/transfert", {
        "member_id": member_id,
        "equipe_origine": origine,
        "equipe_destination": destination
    })

def get_fusion_projection():
    return get("/api/simulation/projection_fusion")
