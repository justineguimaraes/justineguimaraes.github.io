"""
Moteur de simulation : marginalisation et transfert de chercheurs.
"""
import os
import math
from typing import List, Dict
from services import data_loader
from models.simulation import (
    IndicateursSnapshot, MarginalisationResult, TransfertResult,
    ProjectionAnnuelle, ProjectionScenario, FusionProjectionResult
)
import numpy as np

# ──────────────────────────── Utilitaires ────────────────────────────

def _gini(values: List[int]) -> float:
    """Calcule l'indice de Gini sur une liste de valeurs entières."""
    n = len(values)
    if n == 0:
        return 0.0
    s = sorted(values)
    total = sum(s)
    if total == 0:
        return 0.0
    cumul = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(s))
    return cumul / (n * total)


def _score_pub(p: dict) -> float:
    """Score qualité pondéré d'une publication (CORE + Scimago)."""
    score = 0.0
    rk = p.get('rank', 'NC')
    q = p.get('quartile', 'NC')
    core_scores = {'A*': 4, 'A': 3, 'B': 2, 'C': 1}
    scimago_scores = {'Q1': 4, 'Q2': 3, 'Q3': 2, 'Q4': 1}
    score_c = core_scores.get(rk, 0)
    score_s = scimago_scores.get(q, 0)
    score += max(score_c, score_s)
    return score


def _compute_snapshot(membres_team: List[dict], all_members: List[dict],
                      all_pubs: List[dict], pubs_override: dict = None) -> IndicateursSnapshot:
    """
    Calcule un IndicateursSnapshot pour une liste de membres d'équipe.
    pubs_override: dict {author_idx: [pubs]} pour remplacer les publications d'un auteur.
    """
    team_indices = []
    for m in membres_team:
        for idx, am in enumerate(all_members):
            if am['pid_dblp'] == m['pid_dblp']:
                team_indices.append(idx)
                break

    # Collecter publications par membre
    pubs_per_member = {idx: [] for idx in team_indices}
    for p in all_pubs:
        try:
            aid = int(p['author_id'])
        except:
            continue
        if aid in pubs_per_member:
            pubs_per_member[aid].append(p)

    # Appliquer les overrides
    if pubs_override:
        for idx, pubs in pubs_override.items():
            if idx in pubs_per_member:
                pubs_per_member[idx] = pubs

    # Agrégation
    nb_total = 0
    nb_journaux = 0
    nb_conferences = 0
    score_total = 0.0
    core_dist = {"A*": 0, "A": 0, "B": 0, "C": 0, "NC": 0}
    scimago_dist = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0, "NC": 0}
    counts = []  # nb pubs par membre

    for idx in team_indices:
        member_pubs = pubs_per_member.get(idx, [])
        nb = len(member_pubs)
        counts.append(nb)
        nb_total += nb
        for p in member_pubs:
            if p['type'] == 'journal':
                nb_journaux += 1
            else:
                nb_conferences += 1
            score_total += _score_pub(p)
            rk = p.get('rank', 'NC')
            if rk in core_dist:
                core_dist[rk] += 1
            else:
                core_dist["NC"] += 1
            q = p.get('quartile', 'NC')
            if q in scimago_dist:
                scimago_dist[q] += 1
            else:
                scimago_dist["NC"] += 1

    nb_membres = len(team_indices)
    nb_actifs = len([c for c in counts if c >= 1])

    return IndicateursSnapshot(
        nb_publications=nb_total,
        nb_journaux=nb_journaux,
        nb_conferences=nb_conferences,
        productivite_par_membre=round(nb_total / nb_membres, 2) if nb_membres > 0 else 0,
        productivite_par_membre_actif=round(nb_total / nb_actifs, 2) if nb_actifs > 0 else 0,
        taux_membres_actifs=round(nb_actifs / nb_membres * 100, 2) if nb_membres > 0 else 0,
        score_qualite_moyen=round(score_total / nb_total, 2) if nb_total > 0 else 0,
        indice_gini=round(_gini(counts), 4),
        core_distribution=core_dist,
        scimago_distribution=scimago_dist
    )


def _ecarts(avant: IndicateursSnapshot, apres: IndicateursSnapshot) -> Dict[str, float]:
    """Calcule les écarts en % entre deux snapshots."""
    result = {}
    fields = ['nb_publications', 'productivite_par_membre', 'productivite_par_membre_actif',
              'taux_membres_actifs', 'score_qualite_moyen', 'indice_gini']
    for f in fields:
        v_avant = getattr(avant, f)
        v_apres = getattr(apres, f)
        if v_avant != 0:
            result[f] = round((v_apres - v_avant) / abs(v_avant) * 100, 2)
        else:
            result[f] = 0.0
    return result


# ──────────────────────────── Simulation ─────────────────────────────

def run_marginalization(member_ids: List[str], taux_reduction: float) -> MarginalisationResult:
    """
    Simule la marginalisation : réduit la production de certains membres.
    taux_reduction = 1.0 => -100% (suppression totale)
    taux_reduction = 0.5 => -50%  (moitié supprimée)
    """
    data_path = os.getenv("DATA_PATH", "data")
    all_members = data_loader.load_membres(os.path.join(data_path, "membres.csv"))
    all_pubs = data_loader.load_all_publications()

    # Identifier l'équipe (on prend l'équipe du premier membre ciblé)
    target_equipe = None
    for m in all_members:
        if m['pid_dblp'] in member_ids:
            target_equipe = m['equipe']
            break

    if not target_equipe:
        # Fallback : toutes les équipes
        team_members = all_members
    else:
        team_members = [m for m in all_members if m['equipe'] == target_equipe]

    # Snapshot AVANT
    avant = _compute_snapshot(team_members, all_members, all_pubs)

    # Préparer l'override : réduire les publications des membres ciblés
    overrides = {}
    for m in all_members:
        if m['pid_dblp'] in member_ids:
            idx = None
            for i, am in enumerate(all_members):
                if am['pid_dblp'] == m['pid_dblp']:
                    idx = i
                    break
            if idx is not None:
                # Récupérer les pubs actuelles
                current_pubs = [p for p in all_pubs if int(p.get('author_id', -1)) == idx]
                nb_keep = int(len(current_pubs) * (1 - taux_reduction))
                overrides[idx] = current_pubs[:nb_keep]

    # Snapshot APRÈS
    apres = _compute_snapshot(team_members, all_members, all_pubs, pubs_override=overrides)

    return MarginalisationResult(
        avant=avant,
        apres=apres,
        ecarts=_ecarts(avant, apres)
    )


def run_transfer(member_id: str, equipe_origine: str, equipe_destination: str) -> TransfertResult:
    """
    Simule le transfert d'un membre d'une équipe à une autre.
    Recalcule les indicateurs des deux équipes (avant / après).
    """
    data_path = os.getenv("DATA_PATH", "data")
    all_members = data_loader.load_membres(os.path.join(data_path, "membres.csv"))
    all_pubs = data_loader.load_all_publications()

    # Membres par équipe
    team_orig = [m for m in all_members if m['equipe'] == equipe_origine]
    team_dest = [m for m in all_members if m['equipe'] == equipe_destination]

    # Snapshots AVANT
    orig_avant = _compute_snapshot(team_orig, all_members, all_pubs)
    dest_avant = _compute_snapshot(team_dest, all_members, all_pubs)

    # Trouver le membre transféré
    transferred = None
    for m in team_orig:
        if m['pid_dblp'] == member_id:
            transferred = m
            break

    if not transferred:
        # Le membre n'est pas dans l'équipe source
        return TransfertResult(
            equipe_origine_avant=orig_avant,
            equipe_origine_apres=orig_avant,
            equipe_destination_avant=dest_avant,
            equipe_destination_apres=dest_avant,
            ecarts_origine={},
            ecarts_destination={}
        )

    # Simuler la recomposition des équipes
    team_orig_after = [m for m in team_orig if m['pid_dblp'] != member_id]
    team_dest_after = team_dest + [transferred]

    # Snapshots APRÈS
    orig_apres = _compute_snapshot(team_orig_after, all_members, all_pubs)
    dest_apres = _compute_snapshot(team_dest_after, all_members, all_pubs)

    return TransfertResult(
        equipe_origine_avant=orig_avant,
        equipe_origine_apres=orig_apres,
        equipe_destination_avant=dest_avant,
        equipe_destination_apres=dest_apres,
        ecarts_origine=_ecarts(orig_avant, orig_apres),
        ecarts_destination=_ecarts(dest_avant, dest_apres)
    )

def run_fusion_projection() -> FusionProjectionResult:
    """
    Simule la production 2026-2030 d'IDD+SETR sous 3 scénarios (Baseline, Optimiste, Pessimiste).
    """
    data_path = os.getenv("DATA_PATH", "data")
    all_members = data_loader.load_membres(os.path.join(data_path, "membres.csv"))
    all_pubs = data_loader.load_all_publications()

    # Membres fusionnés IDD + SETR
    merged_members = [m for m in all_members if m['equipe'] in ['IDD', 'SETR']]
    
    # Historique 2021-2025 global
    hist_years = [2021, 2022, 2023, 2024, 2025]
    proj_years = [2026, 2027, 2028, 2029, 2030]
    
    # Préparer le décompte par chercheur par année
    member_idx_to_pubs = {}
    for m in merged_members:
        idx = next((i for i, am in enumerate(all_members) if am['pid_dblp'] == m['pid_dblp']), None)
        if idx is not None:
            member_idx_to_pubs[idx] = {y: 0 for y in hist_years}

    total_score = 0
    total_pubs_21_25 = 0

    for p in all_pubs:
        try:
            aid = int(p['author_id'])
            y = int(p['annee'])
        except:
            continue
            
        if aid in member_idx_to_pubs and y in hist_years:
            member_idx_to_pubs[aid][y] += 1
            total_pubs_21_25 += 1
            total_score += _score_pub(p)

    score_moyen_base = round(total_score / total_pubs_21_25, 2) if total_pubs_21_25 > 0 else 0

    # 1. Calcul des modèles individuels
    member_projections = {}
    total_pubs_member = {}
    
    for aid, y_dict in member_idx_to_pubs.items():
        y_vals = [y_dict[y] for y in hist_years]
        total_pubs_member[aid] = sum(y_vals)
        
        x_hist = np.array([0, 1, 2, 3, 4])
        y_hist = np.array(y_vals)
        
        if sum(y_vals) > 0:
            z = np.polyfit(x_hist, y_hist, 1)
            p = np.poly1d(z)
            x_proj = np.array([5, 6, 7, 8, 9])
            y_proj = p(x_proj)
            y_proj = np.maximum(y_proj, 0)
        else:
            y_proj = np.zeros(5)
            
        member_projections[aid] = y_proj

    # Trouver le Top 1 (le chercheur avec le plus de pubs 2021-2025)
    top1_aid = max(total_pubs_member.items(), key=lambda x: x[1])[0] if total_pubs_member else None

    # Historique agrégé commun
    historique_total = [sum(member_idx_to_pubs[aid][y] for aid in member_idx_to_pubs) for y in hist_years]
    hist_objs = [ProjectionAnnuelle(annee=y, nb_publications=int(nb)) for y, nb in zip(hist_years, historique_total)]

    # ================= SCOPE: Baseline =================
    proj_baseline_annual = np.zeros(5)
    baseline_counts_per_member = []
    
    for aid, y_proj in member_projections.items():
        proj_baseline_annual += y_proj
        baseline_counts_per_member.append(int(round(np.sum(y_proj))))
        
    hist_total_sum = sum(historique_total)
    
    s_baseline = ProjectionScenario(
        nom="Tendanciel (Baseline)",
        historique=hist_objs,
        projection=[ProjectionAnnuelle(annee=y, nb_publications=int(round(nb))) for y, nb in zip(proj_years, proj_baseline_annual)],
        total_5_ans=int(round(np.sum(proj_baseline_annual))),
        productivite_moyenne=round(np.sum(proj_baseline_annual) / len(merged_members), 2) if len(merged_members) > 0 else 0,
        indice_gini_moyen=round(_gini(baseline_counts_per_member), 4),
        score_qualite_estime=score_moyen_base
    )

    # ================= SCOPE: Optimiste =================
    proj_optimiste_annual = np.zeros(5)
    optimiste_counts_per_member = []
    
    for aid, y_proj in member_projections.items():
        y_opt = y_proj.copy()
        if total_pubs_member[aid] <= 2:
            # On force à 1 pub/an minimum
            y_opt = np.maximum(y_opt, 1.0)
            
        proj_optimiste_annual += y_opt
        optimiste_counts_per_member.append(int(round(np.sum(y_opt))))
        
    # Effet synergie + 15% global
    proj_optimiste_annual = proj_optimiste_annual * 1.15
    opt_counts_final = [int(round(c * 1.15)) for c in optimiste_counts_per_member]

    s_opt = ProjectionScenario(
        nom="Optimiste (Synergie & Stimulation)",
        historique=hist_objs,
        projection=[ProjectionAnnuelle(annee=y, nb_publications=int(round(nb))) for y, nb in zip(proj_years, proj_optimiste_annual)],
        total_5_ans=int(round(np.sum(proj_optimiste_annual))),
        productivite_moyenne=round(np.sum(proj_optimiste_annual) / len(merged_members), 2) if len(merged_members) > 0 else 0,
        indice_gini_moyen=round(_gini(opt_counts_final), 4),
        score_qualite_estime=score_moyen_base
    )

    # ================= SCOPE: Pessimiste =================
    proj_pessi_annual = np.zeros(5)
    pessi_counts_per_member = []
    
    for aid, y_proj in member_projections.items():
        y_pes = y_proj.copy()
        if aid == top1_aid:
            # Marginalisation du top contributeur (-50%)
            y_pes = y_pes * 0.5
        
        proj_pessi_annual += y_pes
        pessi_counts_per_member.append(int(round(np.sum(y_pes))))

    s_pes = ProjectionScenario(
        nom="Pessimiste (Marginalisation Leader)",
        historique=hist_objs,
        projection=[ProjectionAnnuelle(annee=y, nb_publications=int(round(nb))) for y, nb in zip(proj_years, proj_pessi_annual)],
        total_5_ans=int(round(np.sum(proj_pessi_annual))),
        productivite_moyenne=round(np.sum(proj_pessi_annual) / len(merged_members), 2) if len(merged_members) > 0 else 0,
        indice_gini_moyen=round(_gini(pessi_counts_per_member), 4),
        score_qualite_estime=score_moyen_base
    )

    return FusionProjectionResult(scenarios=[s_baseline, s_opt, s_pes])
