import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import api_client as api

st.set_page_config(page_title="Fiche chercheur", layout="wide", page_icon="👤")
st.title("Fiche chercheur")
st.caption("Indicateurs individuels : volume, qualité, collaboration, thèses")

# ──────────── Sélection du membre ────────────
membres = api.get_membres()
if not membres:
    st.error("Impossible de charger les membres depuis l'API.")
    st.stop()

options = {f"{m['prenom']} {m['nom']} ({m['equipe']})": m['id'] for m in membres}
selection = st.selectbox("Sélectionnez un chercheur :", list(options.keys()))

if selection:
    pid = options[selection]
    detail = api.get_membre_detail(pid)

    if not detail:
        st.error("Impossible de charger le détail de ce membre.")
        st.stop()

    # ═══════════════════ EN-TÊTE ═══════════════════
    st.markdown(f"## {detail['prenom']} {detail['nom']}")
    st.markdown(f"**Équipe :** {detail['equipe']} · **Statut :** {detail['statut']} · **PID DBLP :** `{detail['id']}`")

    st.divider()

    # ═══════════════════ INDICATEURS DE VOLUME ═══════════════════
    st.subheader("Indicateurs de volume")
    ind = detail['indicateurs']

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Publications", ind['nb_publications'])
    c2.metric("Journaux", ind['nb_journaux'])
    c3.metric("Conférences", ind['nb_conferences'])
    c4.metric("Thèses dirigées", ind['nb_theses'])
    
    # Statut d'activité avec couleur
    status_icons = {'actif': '🟢', 'peu actif': '🟡', 'inactif': '🔴'}
    status_txt = ind['statut_activite']
    c5.metric("Statut activité", f"{status_icons.get(status_txt, '⚪')} {status_txt}")

    c6, c7, c8 = st.columns(3)
    c6.metric("Score qualité", ind['score_qualite'])
    c7.metric("Part production équipe", f"{ind['part_production_equipe']}%")
    
    ratio_jc = round(ind['nb_journaux'] / ind['nb_conferences'], 2) if ind['nb_conferences'] > 0 else "∞" if ind['nb_journaux'] > 0 else "0"
    c8.metric("Ratio Journaux/Conférences", ratio_jc)

    # Alerte part de production
    if ind['part_production_equipe'] > 25:
        st.warning(f"**Alerte dépendance** : {detail['prenom']} {detail['nom']} représente {ind['part_production_equipe']}% de la production de l'équipe {detail['equipe']} (seuil critique : 25%)")
    elif ind['part_production_equipe'] > 15:
        st.info(f"ℹ{detail['prenom']} {detail['nom']} contribue de manière significative ({ind['part_production_equipe']}%) à la production de {detail['equipe']}")

    st.divider()

    # ═══════════════════ QUALITÉ & IMPACT ═══════════════════
    st.subheader("Qualité et impact des publications")
    qual = detail['qualite']

    qc1, qc2 = st.columns(2)

    # CORE distribution
    core = qual.get('core_distribution', {})
    if core:
        df_core = pd.DataFrame(list(core.items()), columns=['Rang', 'Nombre'])
        colors_core = {'A*': '#FFD700', 'A': '#C0C0C0', 'B': '#CD7F32', 'C': '#999', 'NC': '#DDD'}
        fig_core = px.bar(df_core, x='Rang', y='Nombre', title="Distribution CORE (conférences)",
                         color='Rang', color_discrete_map=colors_core)
        qc1.plotly_chart(fig_core, use_container_width=True)

    # Scimago distribution
    sci = qual.get('scimago_distribution', {})
    if sci:
        df_sci = pd.DataFrame(list(sci.items()), columns=['Quartile', 'Nombre'])
        colors_sci = {'Q1': '#00CC96', 'Q2': '#636EFA', 'Q3': '#FFA15A', 'Q4': '#EF553B', 'NC': '#DDD'}
        fig_sci = px.bar(df_sci, x='Quartile', y='Nombre', title="Distribution Scimago (journaux)",
                        color='Quartile', color_discrete_map=colors_sci)
        qc2.plotly_chart(fig_sci, use_container_width=True)

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Top venues (A*/A + Q1/Q2)", qual.get('top_venues_count', 0))
    mc2.metric("SJR moyen", qual.get('sjr_moyen', 0))
    
    # % dans top venues
    if ind['nb_publications'] > 0:
        pct_top = round(qual.get('top_venues_count', 0) / ind['nb_publications'] * 100, 1)
        mc3.metric("% publications top venues", f"{pct_top}%")

    st.divider()

    # ═══════════════════ COLLABORATION ═══════════════════
    st.subheader("Indicateurs de collaboration")
    collab = detail.get('collaborations', {})

    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Co-auteurs (membres LIAS)", collab.get('nb_coauteurs', 0))
    cc2.metric("Taux d'ouverture", f"{collab.get('taux_ouverture', 0)}%")
    cc3.metric("Centralité", collab.get('centralite', 0))

    if collab.get('nb_coauteurs', 0) == 0:
        st.info("Ce chercheur n'a pas de co-publications avec d'autres membres du LIAS dans le périmètre 2021–2025.")

    st.divider()

    # ═══════════════════ PUBLICATIONS ═══════════════════
    st.subheader("Liste des publications")
    pubs = detail.get('publications', [])
    if pubs:
        df_pubs = pd.DataFrame(pubs)
        df_pubs = df_pubs.sort_values('annee', ascending=False)

        # Filtres
        fc1, fc2 = st.columns(2)
        with fc1:
            annees = sorted(df_pubs['annee'].unique(), reverse=True)
            annee_filter = st.multiselect("Filtrer par année :", annees, default=annees)
        with fc2:
            type_filter = st.multiselect("Filtrer par type :", df_pubs['type'].unique(),
                                         default=list(df_pubs['type'].unique()))
        
        df_pubs = df_pubs[df_pubs['annee'].isin(annee_filter) & df_pubs['type'].isin(type_filter)]

        st.dataframe(
            df_pubs[['titre', 'annee', 'type', 'venue', 'rang_core', 'quartile', 'sjr']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "titre": "Titre",
                "annee": "Année",
                "type": "Type",
                "venue": "Venue",
                "rang_core": "Rang CORE",
                "quartile": "Quartile",
                "sjr": st.column_config.NumberColumn("SJR", format="%.3f")
            }
        )

        # Évolution temporelle personnelle
        st.subheader("Évolution de ma production")
        evo = df_pubs.groupby('annee').size().reset_index(name='nb')
        fig_evo = px.bar(evo, x='annee', y='nb', title="Publications par année",
                        labels={'annee': 'Année', 'nb': 'Nombre'},
                        color_discrete_sequence=['#636EFA'])
        fig_evo.update_layout(xaxis=dict(dtick=1))
        st.plotly_chart(fig_evo, use_container_width=True)

        # Répartition par type par année
        type_year = df_pubs.groupby(['annee', 'type']).size().reset_index(name='nb')
        if not type_year.empty:
            fig_ty = px.bar(type_year, x='annee', y='nb', color='type', barmode='stack',
                           title="Répartition par type et par année",
                           labels={'annee': 'Année', 'nb': 'Nombre', 'type': 'Type'})
            fig_ty.update_layout(xaxis=dict(dtick=1))
            st.plotly_chart(fig_ty, use_container_width=True)
    else:
        st.info("Aucune publication trouvée pour ce chercheur sur la période 2021–2025.")

    st.divider()

    # ═══════════════════ THÈSES ═══════════════════
    st.subheader("Liste des thèses (direction / encadrement)")
    theses = detail.get('theses', [])
    if theses:
        df_theses = pd.DataFrame(theses)
        # On va tenter de trier par année de début si possible
        st.dataframe(
            df_theses[['nom', 'prenom', 'status', 'directeur', 'colaborateur', 'date_debut', 'date_fin']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "nom": "Nom étudiant",
                "prenom": "Prénom étudiant",
                "status": "Statut",
                "directeur": "Directeur(s)",
                "colaborateur": "Collaborateur(s)",
                "date_debut": "Début",
                "date_fin": "Fin"
            }
        )
    else:
        st.info("Aucune thèse n'a été trouvée pour ce chercheur.")
