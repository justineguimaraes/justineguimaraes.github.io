import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import api_client as api

st.set_page_config(page_title="Vue d'ensemble", layout="wide", page_icon="📈")
st.title("Vue d'ensemble du laboratoire LIAS")
st.caption("Période d'analyse : janvier 2021 – décembre 2025 · Équipes IDD & SETR")

# ──────────── Chargement des données ────────────
membres = api.get_membres()
if not membres:
    st.error("Impossible de charger les membres depuis l'API.")
    st.stop()

df_membres = pd.DataFrame(membres)
pubs = api.get_publications()
inds_idd = api.get_equipe_indicateurs("IDD")
inds_setr = api.get_equipe_indicateurs("SETR")

if not pubs or not inds_idd or not inds_setr:
    st.error("Impossible de charger les publications ou indicateurs.")
    st.stop()

df_pubs = pd.DataFrame(pubs)

# ═══════════════════ 1. KPI GLOBAUX ═══════════════════
st.subheader("Indicateurs de volume")

total_pubs = len(df_pubs)
nb_membres = len(df_membres)
nb_journaux = len(df_pubs[df_pubs['type'] == 'journal'])
nb_conferences = len(df_pubs[df_pubs['type'] == 'conference'])
productivite = round(total_pubs / nb_membres, 2) if nb_membres > 0 else 0

# Membres actifs (au moins 1 publication)
pubs_par_membre = df_membres['publications'].astype(int)
nb_actifs = int((pubs_par_membre >= 1).sum())
nb_inactifs = nb_membres - nb_actifs
prod_par_actif = round(total_pubs / nb_actifs, 2) if nb_actifs > 0 else 0
taux_actifs = round(nb_actifs / nb_membres * 100, 1) if nb_membres > 0 else 0
ratio_jc = round(nb_journaux / nb_conferences, 2) if nb_conferences > 0 else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Membres", nb_membres)
c2.metric("Publications", total_pubs)
c3.metric("Productivité/membre", productivite)
c4.metric("Productivité/actif", prod_par_actif)
c5.metric("Taux actifs", f"{taux_actifs}%")
c6.metric("Ratio Journaux/Conférences", ratio_jc)

c7, c8, c9, c10 = st.columns(4)
c7.metric("Journaux", nb_journaux)
c8.metric("Conférences", nb_conferences)
c9.metric("Membres actifs", nb_actifs)
c10.metric("Membres inactifs", nb_inactifs)

st.divider()

# ═══════════════════ 2. ÉVOLUTION TEMPORELLE ═══════════════════
st.subheader("Évolution temporelle (2021–2025)")

evo_idd = pd.DataFrame(inds_idd.get('evolution_temporelle', []))
evo_setr = pd.DataFrame(inds_setr.get('evolution_temporelle', []))

if not evo_idd.empty and not evo_setr.empty:
    evo_idd['equipe'] = 'IDD'
    evo_setr['equipe'] = 'SETR'
    
    # Total fusionné
    evo_total = pd.merge(evo_idd[['annee', 'nb_publications']], 
                         evo_setr[['annee', 'nb_publications']], 
                         on='annee', suffixes=('_idd', '_setr'))
    evo_total['nb_publications'] = evo_total['nb_publications_idd'] + evo_total['nb_publications_setr']
    evo_total['equipe'] = 'TOTAL'
    evo_total = evo_total[['annee', 'nb_publications', 'equipe']]
    
    evo_combined = pd.concat([evo_idd[['annee', 'nb_publications', 'equipe']], 
                              evo_setr[['annee', 'nb_publications', 'equipe']], 
                              evo_total])
    
    fig_evo = px.line(evo_combined, x='annee', y='nb_publications', color='equipe',
                      title="Évolution du nombre de publications",
                      markers=True,
                      labels={'annee': 'Année', 'nb_publications': 'Publications', 'equipe': 'Équipe'},
                      color_discrete_map={'IDD': '#0068c9', 'SETR': '#83c8ff', 'TOTAL': '#00CC96'})
    fig_evo.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(fig_evo, use_container_width=True)

st.divider()

# ═══════════════════ 3. RÉPARTITION PAR ÉQUIPE ═══════════════════
st.subheader("Répartition par équipe")
c1, c2, c3 = st.columns(3)

# Publications par équipe
pubs_by_equipe = df_membres.groupby('equipe')['publications'].sum().reset_index()
fig_pubs = px.bar(pubs_by_equipe, x='equipe', y='publications',
                  color='equipe', title="Publications par équipe",
                  color_discrete_map={'IDD': "#0068c9", 'SETR': '#83c8ff'},
                  labels={'publications': 'Nombre', 'equipe': 'Équipe'})
c1.plotly_chart(fig_pubs, use_container_width=True)

# Membres par équipe
membres_by_equipe = df_membres.groupby('equipe').size().reset_index(name='count')
fig_mbr = px.pie(membres_by_equipe, names='equipe', values='count', color='equipe',
                 title="Répartition des membres",
                 color_discrete_map={'IDD': "#0068c9", 'SETR': '#83c8ff'})
c2.plotly_chart(fig_mbr, use_container_width=True)

# Ratio journaux/conférences par équipe
data_jc = pd.DataFrame({
    'Équipe': ['IDD', 'IDD', 'SETR', 'SETR'],
    'Type': ['Journaux', 'Conférences', 'Journaux', 'Conférences'],
    'Nombre': [inds_idd['nb_journaux'], inds_idd['nb_conferences'],
               inds_setr['nb_journaux'], inds_setr['nb_conferences']]
})
fig_jc = px.bar(data_jc, x='Équipe', y='Nombre', color='Type', barmode='stack',
                title="Ratio Journaux / Conférences", color_discrete_map={'Journaux': '#0068c9', 'Conférences': '#83c8ff'})
c3.plotly_chart(fig_jc, use_container_width=True)

st.divider()

# ═══════════════════ 4. ENCADREMENT ET THÈSES ═══════════════════
st.subheader("Encadrement et Thèses")

tc1, tc2, tc3, tc4 = st.columns(4)

# Thèses soutenues
soutenues_idd = inds_idd.get('nb_theses_soutenues', 0)
soutenues_setr = inds_setr.get('nb_theses_soutenues', 0)
tc1.metric("Thèses soutenues (2021-2025)", f"IDD: {soutenues_idd} | SETR: {soutenues_setr}", help="Nombre de thèses avec le statut 'Fini'")

# Thèses en cours
encours_idd = inds_idd.get('nb_theses_encours', 0)
encours_setr = inds_setr.get('nb_theses_encours', 0)
tc2.metric("Thèses en cours (2021-2025)", f"IDD: {encours_idd} | SETR: {encours_setr}", help="Nombre de thèses actives sur la période")

# Taux d'encadrement HDR/PR
taux_idd = inds_idd.get('taux_encadrement_hdr', 0)
taux_setr = inds_setr.get('taux_encadrement_hdr', 0)
tc3.metric("Taux d'encadrement HDR/PR", f"IDD: {taux_idd}% | SETR: {taux_setr}%", help="% de membres PR/HDR qui encadrent au moins une thèse")

# Pubs thèses
pubs_th_idd = inds_idd.get('nb_pubs_theses', 0)
pubs_th_setr = inds_setr.get('nb_pubs_theses', 0)
tc4.metric("Publis issues de thèses", f"IDD: {pubs_th_idd} | SETR: {pubs_th_setr}", help="Nombre de publications co-signées par un doctorant de l'équipe")

st.divider()

# ═══════════════════ 5. QUALITÉ & IMPACT ═══════════════════
st.subheader("Indicateurs de qualité et d'impact")

qc1, qc2 = st.columns(2)

# Distribution CORE globale
core_idd = inds_idd.get('core_distribution', {})
core_setr = inds_setr.get('core_distribution', {})
ranks = ['A*', 'A', 'B', 'C', 'NC']
core_total = {r: core_idd.get(r, 0) + core_setr.get(r, 0) for r in ranks}

fig_core = go.Figure()
fig_core.add_trace(go.Bar(name='IDD', x=ranks, y=[core_idd.get(r, 0) for r in ranks], marker_color='#0068c9'))
fig_core.add_trace(go.Bar(name='SETR', x=ranks, y=[core_setr.get(r, 0) for r in ranks], marker_color='#83c8ff'))
fig_core.update_layout(barmode='group', title="Distribution CORE (conférences)")
qc1.plotly_chart(fig_core, use_container_width=True)

# Distribution Scimago globale
sci_idd = inds_idd.get('scimago_distribution', {})
sci_setr = inds_setr.get('scimago_distribution', {})
quartiles = ['Q1', 'Q2', 'Q3', 'Q4', 'NC']

fig_sci = go.Figure()
fig_sci.add_trace(go.Bar(name='IDD', x=quartiles, y=[sci_idd.get(q, 0) for q in quartiles], marker_color='#0068c9'))
fig_sci.add_trace(go.Bar(name='SETR', x=quartiles, y=[sci_setr.get(q, 0) for q in quartiles], marker_color='#83c8ff'))
fig_sci.update_layout(barmode='group', title="Distribution Scimago (journaux)")
qc2.plotly_chart(fig_sci, use_container_width=True)

# Top venues et scores
sc1, sc2, sc3, sc4 = st.columns(4)

# Calculer le % de Q1
nb_j_total = inds_idd['nb_journaux'] + inds_setr['nb_journaux']
nb_q1_total = sci_idd.get('Q1', 0) + sci_setr.get('Q1', 0)
pct_q1 = round(nb_q1_total / nb_j_total * 100, 1) if nb_j_total > 0 else 0

top_venues_total = (core_idd.get('A*', 0) + core_idd.get('A', 0) + core_setr.get('A*', 0) + core_setr.get('A', 0)
                    + sci_idd.get('Q1', 0) + sci_idd.get('Q2', 0) + sci_setr.get('Q1', 0) + sci_setr.get('Q2', 0))

sc1.metric("Top venues (A*/A + Q1/Q2)", top_venues_total)
sc2.metric("Score qualité IDD", inds_idd['score_qualite_moyen'])
sc3.metric("Score qualité SETR", inds_setr['score_qualite_moyen'])
sc4.metric("% de Q1", f"{pct_q1}%")

st.divider()

# ═══════════════════ 6. DIVERSITÉ DES VENUES ═══════════════════
st.subheader("Diversité des venues")

venues = df_pubs['venue'].dropna().unique()
nb_venues = len(venues)
st.metric("Nombre de venues différentes", nb_venues)

# Top 10 venues
top_venues = df_pubs['venue'].value_counts().head(10).reset_index()
top_venues.columns = ['Venue', 'Nombre']
fig_venues = px.bar(top_venues, x='Nombre', y='Venue', orientation='h',
                    title="Top 10 des venues les plus publiées",
                    color='Nombre', color_continuous_scale='Blues')
fig_venues.update_layout(yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig_venues, use_container_width=True)

st.divider()

# ═══════════════════ 7. INDICATEURS DE RISQUE ═══════════════════
st.subheader("Indicateurs d'importance et de risque")

rc1, rc2 = st.columns(2)

# Classement des chercheurs par production
df_ranking = df_membres[['nom', 'prenom', 'equipe', 'publications']].copy()
df_ranking['publications'] = df_ranking['publications'].astype(int)
df_ranking = df_ranking.sort_values('publications', ascending=True)

fig_ranking = px.bar(df_ranking, x='publications', y=df_ranking.apply(lambda r: f"{r['prenom']} {r['nom']}", axis=1),
                     color='equipe', orientation='h',
                     title="Production par chercheur",
                     color_discrete_map={'IDD': '#0068c9', 'SETR': '#83c8ff'},
                     labels={'publications': 'Publications', 'y': 'Chercheur'})
fig_ranking.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
rc1.plotly_chart(fig_ranking, use_container_width=True)

# Statut d'activité
actifs = int((pubs_par_membre >= 3).sum())
peu_actifs = int(((pubs_par_membre >= 1) & (pubs_par_membre < 3)).sum())
inactifs_count = int((pubs_par_membre == 0).sum())

df_status = pd.DataFrame({
    'Statut': ['Actif (≥3 pubs)', 'Peu actif (1-2)', 'Inactif (0)'],
    'Nombre': [actifs, peu_actifs, inactifs_count]
})
fig_status = px.pie(df_status, names='Statut', values='Nombre',
                    title="Répartition par statut d'activité",
                    color='Statut',
                    color_discrete_map={'Actif (≥3 pubs)': '#00CC96', 'Peu actif (1-2)': '#FFA15A', 'Inactif (0)': '#EF553B'})
rc2.plotly_chart(fig_status, use_container_width=True)

# Part de production (chercheurs > 25% = alerte)
st.markdown("#### Concentration de la production")
for equipe in ['IDD', 'SETR']:
    df_eq = df_membres[df_membres['equipe'] == equipe].copy()
    df_eq['publications'] = df_eq['publications'].astype(int)
    total_eq = df_eq['publications'].sum()
    if total_eq > 0:
        df_eq['part_%'] = round(df_eq['publications'] / total_eq * 100, 1)
        locomotives = df_eq[df_eq['part_%'] > 25]
        if not locomotives.empty:
            for _, l in locomotives.iterrows():
                st.warning(f"**{l['prenom']} {l['nom']}** ({equipe}) : {l['part_%']}% de la production — risque de dépendance")
        else:
            st.success(f"{equipe} : aucun membre ne dépasse 25% de la production")

st.divider()

# ═══════════════════ 8. TABLEAU COMPLET ═══════════════════
st.subheader("👥 Tableau détaillé des membres")

# Ajouter le statut d'activité
df_display = df_membres[['nom', 'prenom', 'equipe', 'statut', 'publications']].copy()
df_display['publications'] = df_display['publications'].astype(int)
df_display['statut_activite'] = df_display['publications'].apply(
    lambda x: '🟢 Actif' if x >= 3 else ('🟡 Peu actif' if x >= 1 else '🔴 Inactif')
)
df_display = df_display.sort_values('publications', ascending=False)

st.dataframe(
    df_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "nom": "Nom",
        "prenom": "Prénom",
        "equipe": "Équipe",
        "statut": "Grade",
        "publications": st.column_config.NumberColumn("Publications"),
        "statut_activite": "Activité"
    }
)


