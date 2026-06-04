import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import api_client as api

st.set_page_config(page_title="Simulation", layout="wide", page_icon="🧪")
st.title("Module de simulation")
st.caption("Marginalisation, transfert et effet de lest — Conformément au sujet")

# ──────────── Chargement des membres ────────────
membres = api.get_membres()
if not membres:
    st.error("Impossible de charger les membres.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["Marginalisation", "Transfert", "Effet de lest", "Fusion à 5 ans"])


def display_snapshot_comparison(avant, apres, ecarts, title_avant="AVANT", title_apres="APRÈS"):
    """Affiche un snapshot avant/après complet avec ecarts."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"#### ⬅️ {title_avant}")
        st.metric("Publications", avant['nb_publications'])
        st.metric("Productivité/membre", avant['productivite_par_membre'])
        st.metric("Productivité/membre actif", avant['productivite_par_membre_actif'])
        st.metric("Taux membres actifs", f"{avant['taux_membres_actifs']}%")
        st.metric("Score qualité moyen", avant['score_qualite_moyen'])
        st.metric("Indice de Gini", avant['indice_gini'])

    with col2:
        st.markdown(f"#### ➡️ {title_apres}")
        st.metric(" Publications", apres['nb_publications'],
                 delta=f"{ecarts.get('nb_publications', 0):+.2f}%",
                 delta_color="inverse" if ecarts.get('nb_publications', 0) < 0 else "normal")
        st.metric("Productivité/membre", apres['productivite_par_membre'],
                 delta=f"{ecarts.get('productivite_par_membre', 0):+.2f}%",
                 delta_color="inverse" if ecarts.get('productivite_par_membre', 0) < 0 else "normal")
        st.metric("Productivité/membre actif", apres['productivite_par_membre_actif'],
                 delta=f"{ecarts.get('productivite_par_membre_actif', 0):+.2f}%",
                 delta_color="inverse" if ecarts.get('productivite_par_membre_actif', 0) < 0 else "normal")
        st.metric("Taux membres actifs", f"{apres['taux_membres_actifs']}%",
                 delta=f"{ecarts.get('taux_membres_actifs', 0):+.2f}%",
                 delta_color="inverse" if ecarts.get('taux_membres_actifs', 0) < 0 else "normal")
        st.metric("Score qualité moyen", apres['score_qualite_moyen'],
                 delta=f"{ecarts.get('score_qualite_moyen', 0):+.2f}%",
                 delta_color="inverse" if ecarts.get('score_qualite_moyen', 0) < 0 else "normal")
        st.metric("Indice de Gini", apres['indice_gini'],
                 delta=f"{ecarts.get('indice_gini', 0):+.2f}%",
                 delta_color="inverse" if ecarts.get('indice_gini', 0) > 0 else "normal")

    # Distributions CORE/Scimago avant/après
    st.markdown("---")
    dc1, dc2 = st.columns(2)
    
    # CORE
    ranks = ['A*', 'A', 'B', 'C', 'NC']
    core_avant = avant.get('core_distribution', {})
    core_apres = apres.get('core_distribution', {})
    fig_core = go.Figure()
    fig_core.add_trace(go.Bar(name='Avant', x=ranks, y=[core_avant.get(r, 0) for r in ranks], marker_color='#636EFA'))
    fig_core.add_trace(go.Bar(name='Après', x=ranks, y=[core_apres.get(r, 0) for r in ranks], marker_color='#EF553B'))
    fig_core.update_layout(barmode='group', title="CORE avant/après", height=350)
    dc1.plotly_chart(fig_core, use_container_width=True)
    
    # Scimago
    quartiles = ['Q1', 'Q2', 'Q3', 'Q4', 'NC']
    sci_avant = avant.get('scimago_distribution', {})
    sci_apres = apres.get('scimago_distribution', {})
    fig_sci = go.Figure()
    fig_sci.add_trace(go.Bar(name='Avant', x=quartiles, y=[sci_avant.get(q, 0) for q in quartiles], marker_color='#636EFA'))
    fig_sci.add_trace(go.Bar(name='Après', x=quartiles, y=[sci_apres.get(q, 0) for q in quartiles], marker_color='#EF553B'))
    fig_sci.update_layout(barmode='group', title="Scimago avant/après", height=350)
    dc2.plotly_chart(fig_sci, use_container_width=True)

    # Tableau récapitulatif
    st.markdown("#### Tableau récapitulatif des écarts")
    df_ecarts = pd.DataFrame([
        {"Indicateur": "Publications", "Avant": avant['nb_publications'], "Après": apres['nb_publications'], "Écart (%)": ecarts.get('nb_publications', 0)},
        {"Indicateur": "Productivité/membre", "Avant": avant['productivite_par_membre'], "Après": apres['productivite_par_membre'], "Écart (%)": ecarts.get('productivite_par_membre', 0)},
        {"Indicateur": "Productivité/membre actif", "Avant": avant['productivite_par_membre_actif'], "Après": apres['productivite_par_membre_actif'], "Écart (%)": ecarts.get('productivite_par_membre_actif', 0)},
        {"Indicateur": "Taux membres actifs", "Avant": f"{avant['taux_membres_actifs']}%", "Après": f"{apres['taux_membres_actifs']}%", "Écart (%)": ecarts.get('taux_membres_actifs', 0)},
        {"Indicateur": "Score qualité moyen", "Avant": avant['score_qualite_moyen'], "Après": apres['score_qualite_moyen'], "Écart (%)": ecarts.get('score_qualite_moyen', 0)},
        {"Indicateur": "Indice de Gini", "Avant": avant['indice_gini'], "Après": apres['indice_gini'], "Écart (%)": ecarts.get('indice_gini', 0)},
    ])
    st.dataframe(df_ecarts, use_container_width=True, hide_index=True)


# ═══════════════════ ONGLET 1 : MARGINALISATION ═══════════════════
with tab1:
    st.subheader("Simulation de marginalisation")
    st.markdown("""
    **Principe** : Simulez la réduction de production d'un ou plusieurs chercheurs et observez l'impact 
    sur les indicateurs de l'équipe. Utile pour identifier les chercheurs « locomotives ».
    
    - **-50%** : le chercheur voit sa production réduite de moitié
    - **-100%** : le chercheur est totalement exclu (ses publications ne comptent plus)
    """)

    # Sélection par équipe
    equipe_marg = st.selectbox("Équipe :", ["IDD", "SETR"], key="marg_equipe")
    membres_equipe = [m for m in membres if m['equipe'] == equipe_marg]
    
    options_marg = {f"{m['prenom']} {m['nom']} ({m['publications']} pubs)": m['id'] for m in membres_equipe}
    selected_members = st.multiselect(
        "Sélectionnez le(s) membre(s) à marginaliser :",
        list(options_marg.keys()),
        key="marg_members"
    )

    taux = st.slider("Taux de réduction de production (%)", 0, 100, 100, 5, key="marg_taux")

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        run_marg = st.button("Lancer la marginalisation", type="primary", key="btn_marg")

    if run_marg:
        if not selected_members:
            st.warning("Sélectionnez au moins un membre.")
        else:
            member_ids = [options_marg[s] for s in selected_members]
            with st.spinner("Simulation en cours..."):
                result = api.simulate_marginalisation(member_ids, taux / 100.0)

            if result:
                st.markdown("### Résultats de la marginalisation")
                st.markdown(f"**Membres marginalisés :** {', '.join(selected_members)}")
                st.markdown(f"**Taux de réduction :** {taux}% · **Équipe :** {equipe_marg}")
                
                display_snapshot_comparison(result['avant'], result['apres'], result['ecarts'])

                # Seuils critiques
                st.markdown("#### Alertes")
                if abs(result['ecarts'].get('nb_publications', 0)) > 30:
                    st.error(f"❌ Perte de publications > 30% ({result['ecarts']['nb_publications']:+.1f}%) — IMPACT CRITIQUE")
                elif abs(result['ecarts'].get('nb_publications', 0)) > 15:
                    st.warning(f"⚠️ Perte de publications > 15% ({result['ecarts']['nb_publications']:+.1f}%) — Impact significatif")
                else:
                    st.success(f"✅ Impact limité sur les publications ({result['ecarts']['nb_publications']:+.1f}%)")
            else:
                st.error("Erreur lors de la simulation.")

    # Auto-analyse : Top 3 chercheurs les plus impactants
    st.divider()
    st.subheader("Top 3 chercheurs les plus impactants")
    st.markdown("Simulation automatique : marginalisation à 100% de chaque membre")

    if st.button("Calculer le classement", key="btn_top3"):
        impacts = []
        for m in membres_equipe:
            if int(m['publications']) == 0:
                continue
            res = api.simulate_marginalisation([m['id']], 1.0)
            if res:
                impacts.append({
                    'Chercheur': f"{m['prenom']} {m['nom']}",
                    'Publications': int(m['publications']),
                    'Impact pubs (%)': res['ecarts'].get('nb_publications', 0),
                    'Impact score (%)': res['ecarts'].get('score_qualite_moyen', 0),
                    'Impact Gini (%)': res['ecarts'].get('indice_gini', 0),
                })
        
        if impacts:
            df_impacts = pd.DataFrame(impacts).sort_values('Impact pubs (%)')
            st.dataframe(df_impacts, use_container_width=True, hide_index=True)
            
            # Graphique
            fig_impact = px.bar(df_impacts, x='Impact pubs (%)', y='Chercheur', orientation='h',
                               title=f"Impact de la marginalisation (100%) — {equipe_marg}",
                               color='Impact pubs (%)', color_continuous_scale='RdYlGn')
            fig_impact.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_impact, use_container_width=True)
            
            # Top 3
            top3 = df_impacts.head(3)
            for i, (_, row) in enumerate(top3.iterrows()):
                medal = ["🥇", "🥈", "🥉"][i]
                st.warning(f"{medal} **{row['Chercheur']}** : sa marginalisation entraînerait **{row['Impact pubs (%)']:.1f}%** de perte de publications")


# ═══════════════════ ONGLET 2 : TRANSFERT ═══════════════════
with tab2:
    st.subheader("Simulation de transfert")
    st.markdown("""
    **Principe** : Simulez le déplacement d'un chercheur d'une équipe vers une autre.
    Les indicateurs des **deux** équipes sont recalculés.
    
    **Cas d'usage** : Préparer la fusion IDD+SETR en transférant progressivement les membres.
    """)

    # Sélection du membre
    options_trans = {f"{m['prenom']} {m['nom']} ({m['equipe']}, {m['publications']} pubs)": m for m in membres}
    selected_transfer = st.selectbox(
        "Sélectionnez le membre à transférer :",
        list(options_trans.keys()),
        key="transfer_select"
    )

    if selected_transfer:
        membre = options_trans[selected_transfer]
        equipe_origine = membre['equipe']
        equipes_dispo = [e for e in ['IDD', 'SETR'] if e != equipe_origine]
        equipe_dest = st.selectbox(
            f"Équipe destination (origine : {equipe_origine}) :",
            equipes_dispo,
            key="transfer_dest"
        )

        if st.button("Lancer la simulation de transfert", type="primary", key="btn_trans"):
            with st.spinner("Simulation en cours..."):
                result = api.simulate_transfert(membre['id'], equipe_origine, equipe_dest)

            if result:
                st.markdown("### Résultats du transfert")
                st.markdown(f"**{selected_transfer}** : {equipe_origine} → {equipe_dest}")

                # Équipe origine
                st.markdown(f"---\n### Équipe d'origine : {equipe_origine}")
                display_snapshot_comparison(
                    result['equipe_origine_avant'], 
                    result['equipe_origine_apres'], 
                    result['ecarts_origine'],
                    title_avant=f"{equipe_origine} avant",
                    title_apres=f"{equipe_origine} après"
                )

                # Équipe destination  
                st.markdown(f"---\n### Équipe de destination : {equipe_dest}")
                display_snapshot_comparison(
                    result['equipe_destination_avant'], 
                    result['equipe_destination_apres'], 
                    result['ecarts_destination'],
                    title_avant=f"{equipe_dest} avant",
                    title_apres=f"{equipe_dest} après"
                )

                # Bilan
                st.markdown("---\n### Bilan du transfert")
                bc1, bc2 = st.columns(2)
                with bc1:
                    delta_pub_orig = result['ecarts_origine'].get('nb_publications', 0)
                    delta_pub_dest = result['ecarts_destination'].get('nb_publications', 0)
                    st.metric(f"Impact {equipe_origine}", f"{delta_pub_orig:+.1f}% pubs",
                             delta_color="inverse" if delta_pub_orig < 0 else "normal")
                with bc2:
                    st.metric(f"Impact {equipe_dest}", f"{delta_pub_dest:+.1f}% pubs",
                             delta_color="normal" if delta_pub_dest > 0 else "inverse")
                
                if delta_pub_orig < -30:
                    st.error(f"Le transfert affaiblit significativement {equipe_origine} ({delta_pub_orig:.1f}%)")
                elif delta_pub_dest > 20:
                    st.success(f"Le transfert renforce significativement {equipe_dest} (+{delta_pub_dest:.1f}%)")
            else:
                st.error("Erreur lors de la simulation de transfert.")


# ═══════════════════ ONGLET 3 : EFFET DE LEST ═══════════════════
with tab3:
    st.subheader("Effet de lest — Impact des membres inactifs")
    st.markdown("""
    **Principe** : Recalcul des indicateurs d'équipe en excluant les membres inactifs (0 publication).
    
    Cela mesure le **gain de productivité** et de **score qualité** si l'équipe ne comptait que ses membres actifs.
    Utile pour évaluer la « dilution » de la performance par les membres non impliqués.
    """)

    equipe_lest = st.selectbox("Équipe à analyser :", ["IDD", "SETR"], key="lest_equipe")
    
    if st.button("Analyser l'effet de lest", type="primary", key="btn_lest"):
        # Identifier les membres inactifs de l'équipe
        membres_eq = [m for m in membres if m['equipe'] == equipe_lest]
        inactifs = [m for m in membres_eq if int(m['publications']) == 0]
        actifs = [m for m in membres_eq if int(m['publications']) > 0]
        
        st.markdown(f"### Analyse de l'équipe {equipe_lest}")
        st.markdown(f"- **{len(membres_eq)}** membres au total")
        st.markdown(f"- **{len(actifs)}** membres actifs (≥ 1 publication)")
        st.markdown(f"- **{len(inactifs)}** membres inactifs (0 publication)")
        
        if inactifs:
            st.markdown("**Membres inactifs :**")
            for m in inactifs:
                st.markdown(f"  - {m['prenom']} {m['nom']} ({m['statut']})")
            
            # Simuler la marginalisation des inactifs (en réalité ils ont 0 pub, 
            # donc on simule l'exclusion en recalculant manuellement)
            # On marginalise à 100% (ça n'enlèvera pas de pubs mais changera le dénominateur)
            inactif_ids = [m['id'] for m in inactifs]
            result = api.simulate_marginalisation(inactif_ids, 1.0)
            
            if result:
                avant = result['avant']
                apres = result['apres']
                ecarts = result['ecarts']
                
                st.divider()
                st.markdown("### Indicateurs actuels vs. sans inactifs")
                
                display_snapshot_comparison(avant, apres, ecarts,
                    title_avant="Avec inactifs", title_apres="Sans inactifs")
                
                # Interprétation
                st.markdown("### Interprétation")
                delta_prod = ecarts.get('productivite_par_membre', 0)
                delta_gini = ecarts.get('indice_gini', 0)
                
                if abs(delta_prod) > 15:
                    st.warning(f"Les membres inactifs diluent fortement la productivité apparente de {equipe_lest} ({delta_prod:+.1f}%)")
                elif abs(delta_prod) > 5:
                    st.info(f"ℹL'impact des inactifs sur la productivité est modéré ({delta_prod:+.1f}%)")
                else:
                    st.success(f"Les membres inactifs ont un impact limité ({delta_prod:+.1f}%)")
                    
                if abs(delta_gini) > 10:
                    st.warning(f"L'exclusion des inactifs modifie significativement l'indice de Gini ({delta_gini:+.1f}%)")
            else:
                st.error("Erreur lors du calcul.")
        else:
            st.success(f"Tous les membres de {equipe_lest} sont actifs — pas d'effet de lest.")

    st.divider()
    
    # Comparaison IDD vs SETR : qui est le plus pénalisé ?
    st.subheader("Comparaison : quelle équipe est la plus pénalisée ?")
    
    if st.button("Comparer les deux équipes", key="btn_lest_compare"):
        results = {}
        for eq in ['IDD', 'SETR']:
            membres_eq = [m for m in membres if m['equipe'] == eq]
            inactifs = [m for m in membres_eq if int(m['publications']) == 0]
            
            if inactifs:
                inactif_ids = [m['id'] for m in inactifs]
                res = api.simulate_marginalisation(inactif_ids, 1.0)
                if res:
                    results[eq] = {
                        'nb_inactifs': len(inactifs),
                        'nb_total': len(membres_eq),
                        'pct_inactifs': round(len(inactifs) / len(membres_eq) * 100, 1),
                        'delta_prod': res['ecarts'].get('productivite_par_membre', 0),
                        'delta_score': res['ecarts'].get('score_qualite_moyen', 0),
                        'delta_gini': res['ecarts'].get('indice_gini', 0),
                    }
            else:
                results[eq] = {
                    'nb_inactifs': 0,
                    'nb_total': len(membres_eq),
                    'pct_inactifs': 0,
                    'delta_prod': 0,
                    'delta_score': 0,
                    'delta_gini': 0,
                }
        
        if results:
            df_lest = pd.DataFrame([
                {
                    'Équipe': eq,
                    'Membres': data['nb_total'],
                    'Inactifs': data['nb_inactifs'],
                    '% Inactifs': f"{data['pct_inactifs']}%",
                    'Impact productivité (%)': data['delta_prod'],
                    'Impact score qualité (%)': data['delta_score'],
                    'Impact Gini (%)': data['delta_gini'],
                }
                for eq, data in results.items()
            ])
            st.dataframe(df_lest, use_container_width=True, hide_index=True)
            
            # Conclusion
            most_penalized = max(results.items(), key=lambda x: abs(x[1]['delta_prod']))
            if most_penalized[1]['delta_prod'] != 0:
                st.warning(f"L'équipe **{most_penalized[0]}** est la plus pénalisée par ses membres inactifs "
                          f"({most_penalized[1]['nb_inactifs']} inactifs, impact productivité : {most_penalized[1]['delta_prod']:+.1f}%)")

    st.divider()
    st.markdown("""
    ###  Impact sur la fusion IDD+SETR
    
    Dans la perspective d'une fusion, le **cumul des membres inactifs** des deux équipes 
    pourrait constituer un risque de dilution de la performance. Utilisez les simulations 
    ci-dessus pour évaluer ce risque.
    """)

# ═══════════════════ ONGLET 4 : PROJECTION 5 ANS ═══════════════════
with tab4:
    st.subheader("Projection à 5 ans (2026-2030) : Équipe fusionnée IDD + SETR")
    st.markdown("""
    **Principe** : Extrapolation des tendances individuelles (2021-2025) sous 3 scénarios (Baseline, Optimiste, Pessimiste).  
    ⚠️ *Limites : Le modèle est linéaire, suppose un effectif constant (sans retraites/recrutements) et s'appuie uniquement sur le passé (sans tenir compte des réels projets futurs).*
    """)
    
    if st.button("Lancer la simulation de Projection", type="primary", key="btn_proj"):
        with st.spinner("Calcul des scénarios par Machine Learning et agrégation..."):
            proj_data = api.get_fusion_projection()
            
        if proj_data and 'scenarios' in proj_data:
            scenarios = proj_data['scenarios']
            
            # Afficher 3 colonnes pour les KPIs
            c1, c2, c3 = st.columns(3)
            cols = [c1, c2, c3]
            
            # Préparation des données pour le graphe
            df_plot_list = []
            
            for i, s in enumerate(scenarios):
                # KPIs
                with cols[i]:
                    st.markdown(f"#### {s['nom']}")
                    st.metric("Total projeté (5 ans)", s['total_5_ans'])
                    st.metric("Productivité moy. (2026-2030)", round(s['productivite_moyenne'], 2))
                    st.metric("Indice de Gini projeté", round(s['indice_gini_moyen'], 4))
                    st.metric("Score Qualité Estimé", round(s['score_qualite_estime'], 2))
                
                # Format graphe
                for h in s['historique']:
                    df_plot_list.append({
                        "Année": h['annee'],
                        "Publications": h['nb_publications'],
                        "Période": "Historique",
                        "Scénario": s['nom']
                    })
                for p in s['projection']:
                    df_plot_list.append({
                        "Année": p['annee'],
                        "Publications": p['nb_publications'],
                        "Période": "Projection",
                        "Scénario": s['nom']
                    })
                    
            st.divider()
            
            df_plot = pd.DataFrame(df_plot_list)
            
            # Tracé du graphe
            fig_proj = px.line(df_plot, x="Année", y="Publications", color="Scénario", 
                               line_dash="Période", markers=True, 
                               title="Évolution & Projections de l'équipe fusionnée (IDD + SETR)",
                               color_discrete_map={
                                   "Tendanciel (Baseline)": "blue",
                                   "Optimiste (Synergie & Stimulation)": "green",
                                   "Pessimiste (Marginalisation Leader)": "red"
                               })
            fig_proj.add_vline(x=2025.5, line_width=2, line_dash="dash", line_color="black")
            fig_proj.add_annotation(x=2025.5, y=max(df_plot['Publications'])*0.9, text="Fusion", showarrow=False, bgcolor="yellow")
            fig_proj.update_layout(xaxis=dict(dtick=1))
            st.plotly_chart(fig_proj, use_container_width=True)
            
        else:
            st.error("Erreur lors de la récupération des données de projection.")
