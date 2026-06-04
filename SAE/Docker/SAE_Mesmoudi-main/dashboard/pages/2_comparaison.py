import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import api_client as api

st.set_page_config(page_title="Comparaison des équipes", layout="wide", page_icon="⚖️")
st.title("Comparaison IDD vs SETR")
st.caption("Comparaison détaillée des deux équipes sur tous les indicateurs du sujet")

# ──────────── Chargement ────────────
inds_idd = api.get_equipe_indicateurs("IDD")
inds_setr = api.get_equipe_indicateurs("SETR")
membres = api.get_membres()

if not inds_idd or not inds_setr or not membres:
    st.error("Impossible de charger les indicateurs des deux équipes.")
    st.stop()

df_membres = pd.DataFrame(membres)

# ═══════════════════ 1. INDICATEURS DE VOLUME COMPARÉS ═══════════════════
st.subheader("Indicateurs de volume comparés")

# Calculs dérivés
prod_idd = round(inds_idd['nb_publications_total'] / inds_idd['nombre_membres'], 2)
prod_setr = round(inds_setr['nb_publications_total'] / inds_setr['nombre_membres'], 2)

# Membres actifs par équipe
df_idd = df_membres[df_membres['equipe'] == 'IDD']
df_setr = df_membres[df_membres['equipe'] == 'SETR']
actifs_idd = int((df_idd['publications'].astype(int) >= 1).sum())
actifs_setr = int((df_setr['publications'].astype(int) >= 1).sum())
prod_actif_idd = round(inds_idd['nb_publications_total'] / actifs_idd, 2) if actifs_idd > 0 else 0
prod_actif_setr = round(inds_setr['nb_publications_total'] / actifs_setr, 2) if actifs_setr > 0 else 0
taux_actifs_idd = round(actifs_idd / inds_idd['nombre_membres'] * 100, 1)
taux_actifs_setr = round(actifs_setr / inds_setr['nombre_membres'] * 100, 1)

ratio_jc_idd = round(inds_idd['nb_journaux'] / inds_idd['nb_conferences'], 2) if inds_idd['nb_conferences'] > 0 else 0
ratio_jc_setr = round(inds_setr['nb_journaux'] / inds_setr['nb_conferences'], 2) if inds_setr['nb_conferences'] > 0 else 0

# Tableau comparatif
indicateurs_data = {
    'Indicateur': [
        'Nombre de membres',
        'Publications totales',
        'Journaux',
        'Conférences',
        'Productivité / membre',
        'Productivité / membre actif',
        'Taux de membres actifs',
        'Ratio journaux / conférences',
        'Score qualité moyen',
    ],
    'IDD': [
        str(inds_idd['nombre_membres']),
        str(inds_idd['nb_publications_total']),
        str(inds_idd['nb_journaux']),
        str(inds_idd['nb_conferences']),
        str(prod_idd),
        str(prod_actif_idd),
        f"{taux_actifs_idd}%",
        str(ratio_jc_idd),
        str(inds_idd['score_qualite_moyen']),
    ],
    'SETR': [
        str(inds_setr['nombre_membres']),
        str(inds_setr['nb_publications_total']),
        str(inds_setr['nb_journaux']),
        str(inds_setr['nb_conferences']),
        str(prod_setr),
        str(prod_actif_setr),
        f"{taux_actifs_setr}%",
        str(ratio_jc_setr),
        str(inds_setr['score_qualite_moyen']),
    ],
    'Écart': [
        '',
        f"{inds_idd['nb_publications_total'] - inds_setr['nb_publications_total']:+d}",
        f"{inds_idd['nb_journaux'] - inds_setr['nb_journaux']:+d}",
        f"{inds_idd['nb_conferences'] - inds_setr['nb_conferences']:+d}",
        f"{prod_idd - prod_setr:+.2f}",
        f"{prod_actif_idd - prod_actif_setr:+.2f}",
        f"{taux_actifs_idd - taux_actifs_setr:+.1f}pp",
        f"{ratio_jc_idd - ratio_jc_setr:+.2f}",
        f"{inds_idd['score_qualite_moyen'] - inds_setr['score_qualite_moyen']:+.2f}",
    ]
}
df_comp = pd.DataFrame(indicateurs_data)
st.dataframe(df_comp, use_container_width=True, hide_index=True)

# KPIs delta
c1, c2, c3, c4 = st.columns(4)
c1.metric("Productivité IDD", prod_idd, delta=f"{prod_idd - prod_setr:+.2f} vs SETR")
c2.metric("Productivité SETR", prod_setr, delta=f"{prod_setr - prod_idd:+.2f} vs IDD")
c3.metric("Score IDD", inds_idd['score_qualite_moyen'], delta=f"{inds_idd['score_qualite_moyen'] - inds_setr['score_qualite_moyen']:+.2f} vs SETR")
c4.metric("Score SETR", inds_setr['score_qualite_moyen'], delta=f"{inds_setr['score_qualite_moyen'] - inds_idd['score_qualite_moyen']:+.2f} vs IDD")

st.divider()

# ═══════════════════ 2. ÉVOLUTION TEMPORELLE ═══════════════════
st.subheader("Évolution temporelle comparée")

evo_idd = pd.DataFrame(inds_idd.get('evolution_temporelle', []))
evo_setr = pd.DataFrame(inds_setr.get('evolution_temporelle', []))

if not evo_idd.empty and not evo_setr.empty:
    evo_idd['equipe'] = 'IDD'
    evo_setr['equipe'] = 'SETR'
    evo_combined = pd.concat([evo_idd, evo_setr])
    fig_evo = px.line(evo_combined, x='annee', y='nb_publications', color='equipe',
                      title="Nombre de publications par année",
                      markers=True,
                      labels={'annee': 'Année', 'nb_publications': 'Publications', 'equipe': 'Équipe'},
                      color_discrete_map={'IDD': '#0068c9', 'SETR': '#83c8ff'})
    fig_evo.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(fig_evo, use_container_width=True)

    # Tendance : croissance ou déclin ?
    if len(evo_idd) >= 2:
        trend_idd = evo_idd.iloc[-1]['nb_publications'] - evo_idd.iloc[0]['nb_publications']
        trend_setr = evo_setr.iloc[-1]['nb_publications'] - evo_setr.iloc[0]['nb_publications']
        tc1, tc2 = st.columns(2)
        tc1.metric("Tendance IDD (2021→2025)", f"{trend_idd:+d} publications",
                   delta="Croissance" if trend_idd > 0 else ("Stable" if trend_idd == 0 else "Déclin"),
                   delta_color="normal" if trend_idd >= 0 else "inverse")
        tc2.metric("Tendance SETR (2021→2025)", f"{trend_setr:+d} publications",
                   delta="Croissance" if trend_setr > 0 else ("Stable" if trend_setr == 0 else "Déclin"),
                   delta_color="normal" if trend_setr >= 0 else "inverse")

st.divider()

# ═══════════════════ 3. QUALITÉ COMPARÉE ═══════════════════
st.subheader("Distribution des rangs CORE (conférences)")

core_idd = inds_idd.get('core_distribution', {})
core_setr = inds_setr.get('core_distribution', {})
ranks = ['A*', 'A', 'B', 'C', 'NC']

fig_core = go.Figure()
fig_core.add_trace(go.Bar(name='IDD', x=ranks, y=[core_idd.get(r, 0) for r in ranks], marker_color='#0068c9'))
fig_core.add_trace(go.Bar(name='SETR', x=ranks, y=[core_setr.get(r, 0) for r in ranks], marker_color='#83c8ff'))
fig_core.update_layout(barmode='group', title="Rangs CORE comparés")
st.plotly_chart(fig_core, use_container_width=True)

st.subheader("Distribution des quartiles Scimago (journaux)")

sci_idd = inds_idd.get('scimago_distribution', {})
sci_setr = inds_setr.get('scimago_distribution', {})
quartiles = ['Q1', 'Q2', 'Q3', 'Q4', 'NC']

fig_sci = go.Figure()
fig_sci.add_trace(go.Bar(name='IDD', x=quartiles, y=[sci_idd.get(q, 0) for q in quartiles], marker_color='#0068c9'))
fig_sci.add_trace(go.Bar(name='SETR', x=quartiles, y=[sci_setr.get(q, 0) for q in quartiles], marker_color='#83c8ff'))
fig_sci.update_layout(barmode='group', title="Quartiles Scimago comparés")
st.plotly_chart(fig_sci, use_container_width=True)

# % Q1
pct_q1_idd = round(sci_idd.get('Q1', 0) / inds_idd['nb_journaux'] * 100, 1) if inds_idd['nb_journaux'] > 0 else 0
pct_q1_setr = round(sci_setr.get('Q1', 0) / inds_setr['nb_journaux'] * 100, 1) if inds_setr['nb_journaux'] > 0 else 0
qm1, qm2 = st.columns(2)
qm1.metric("% Q1 journaux IDD", f"{pct_q1_idd}%")
qm2.metric("% Q1 journaux SETR", f"{pct_q1_setr}%")

st.divider()

# ═══════════════════ 4. RATIO J/C ET TOP VENUES ═══════════════════
st.subheader("Ratio Journaux / Conférences")

data_ratio = pd.DataFrame({
    'Équipe': ['IDD', 'IDD', 'SETR', 'SETR'],
    'Type': ['Journaux', 'Conférences', 'Journaux', 'Conférences'],
    'Nombre': [inds_idd['nb_journaux'], inds_idd['nb_conferences'],
               inds_setr['nb_journaux'], inds_setr['nb_conferences']]
})
fig_ratio = px.bar(data_ratio, x='Équipe', y='Nombre', color='Type', barmode='stack',
                   title="Répartition Journaux vs Conférences")
st.plotly_chart(fig_ratio, use_container_width=True)

st.divider()

# ═══════════════════ 5. RADAR COMPARATIF ═══════════════════
st.subheader("🕸️ Radar comparatif")

# Normaliser les indicateurs pour le radar
max_pub = max(inds_idd['nb_publications_total'], inds_setr['nb_publications_total'])
max_prod = max(prod_idd, prod_setr)
max_score = max(inds_idd['score_qualite_moyen'], inds_setr['score_qualite_moyen'])
max_taux = max(taux_actifs_idd, taux_actifs_setr)
max_q1 = max(pct_q1_idd, pct_q1_setr)

categories = ['Publications', 'Productivité', 'Score qualité', 'Taux actifs', '% Q1']

fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(
    r=[inds_idd['nb_publications_total']/max_pub*100, prod_idd/max_prod*100,
       inds_idd['score_qualite_moyen']/max_score*100, taux_actifs_idd/max_taux*100,
       pct_q1_idd/max_q1*100 if max_q1 > 0 else 0],
    theta=categories, fill='toself', name='IDD', line_color='#0068c9'
))
fig_radar.add_trace(go.Scatterpolar(
    r=[inds_setr['nb_publications_total']/max_pub*100, prod_setr/max_prod*100,
       inds_setr['score_qualite_moyen']/max_score*100, taux_actifs_setr/max_taux*100,
       pct_q1_setr/max_q1*100 if max_q1 > 0 else 0],
    theta=categories, fill='toself', name='SETR', line_color='#83c8ff'
))
fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    showlegend=True, title="Radar comparatif (valeurs normalisées en %)"
)
st.plotly_chart(fig_radar, use_container_width=True)

st.divider()

# ═══════════════════ 6. PERSPECTIVE FUSION ═══════════════════
st.subheader("Perspective : équipe fusionnée IDD + SETR")

total_mbr = inds_idd['nombre_membres'] + inds_setr['nombre_membres']
total_pubs = inds_idd['nb_publications_total'] + inds_setr['nb_publications_total']
total_journaux = inds_idd['nb_journaux'] + inds_setr['nb_journaux']
total_conf = inds_idd['nb_conferences'] + inds_setr['nb_conferences']
total_actifs = actifs_idd + actifs_setr
prod_fusionnee = round(total_pubs / total_mbr, 2)
prod_actif_fusionnee = round(total_pubs / total_actifs, 2) if total_actifs > 0 else 0
taux_actifs_fusionnee = round(total_actifs / total_mbr * 100, 1)

fc1, fc2, fc3, fc4, fc5 = st.columns(5)
fc1.metric("Membres fusionnée", total_mbr)
fc2.metric("Publications", total_pubs)
fc3.metric("Productivité/membre", prod_fusionnee)
fc4.metric("Productivité/actif", prod_actif_fusionnee)
fc5.metric("Taux actifs", f"{taux_actifs_fusionnee}%")

st.info("""
💡 **Analyse de la fusion** : L'équipe fusionnée compterait 19 membres et {} publications.
La productivité par membre ({}) se situerait entre celle de l'IDD ({}) et de SETR ({}).
Le taux de membres actifs serait de {}%.
""".format(total_pubs, prod_fusionnee, prod_idd, prod_setr, taux_actifs_fusionnee))
