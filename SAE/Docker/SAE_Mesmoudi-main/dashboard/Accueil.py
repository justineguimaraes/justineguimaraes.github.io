import streamlit as st
import os

st.set_page_config(page_title="LIAS Bibliométrie", layout="wide", page_icon="📊")

st.title("Analyse Bibliométrique — Laboratoire LIAS")
st.caption("Outil de pilotage stratégique · IDD & SETR · 2021–2025")

st.sidebar.success("Sélectionnez une page ci-dessus.")

st.markdown("""
### Bienvenue dans l'outil de pilotage stratégique du LIAS.

Cet outil permet d'analyser la production scientifique des équipes **IDD** (11 membres) et **SETR** (8 membres)
sur la période **janvier 2021 – décembre 2025**.

---

### Pages disponibles

| Page | Description | Indicateurs |
|------|-------------|-------------|
| **Vue d'ensemble** | KPI globaux, évolution temporelle, répartition | Volume, qualité, risque |
| **Comparaison** | Graphiques superposés IDD vs. SETR | Radar, évolution, fusion |
| **Fiche chercheur** | Publications, qualité, part dans l'équipe | Individuel, collaboration |
| **Collaboration** | Graphe de co-publications, centralité | Intra/inter, ponts |
| **Simulation** | Marginalisation, transfert, effet de lest | Scénarios avant/après |

---

### Indicateurs calculés

- **Volume** : publications totales, productivité/membre, productivité/actif, taux actifs, ratio J/C
- **Qualité** : rang CORE (A*→C), quartile Scimago (Q1→Q4), score pondéré, SJR moyen, top venues
- **Collaboration** : intra-équipe, inter-équipes, centralité, chercheurs ponts, taux d'ouverture
- **Doctoral** : thèses dirigées (via theses.fr)
- **Risque** : part de production, indice de Gini, statut d'activité, effet de lest
- **Simulation** : marginalisation (−50%, −100%), transfert inter-équipes

---

*Sources : DBLP · CORE Rankings · SCImago Journal Rank · theses.fr*
""")

# Health check
import api_client as api

data = api.get_membres()
if data is not None:
    nb_pubs = sum(m['publications'] for m in data)
    st.success(f"API connectée — {len(data)} membres identifiés — {nb_pubs} publications")
else:
    st.warning("L'API n'est pas encore accessible. Vérifiez que le conteneur `api` est démarré.")
    st.code("docker compose up --build", language="bash")
