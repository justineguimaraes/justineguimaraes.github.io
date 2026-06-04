import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import api_client as api

st.set_page_config(page_title="Collaboration", layout="wide", page_icon="🔗")
st.title("Graphe de collaboration")
st.caption("Réseau de co-publications entre les membres du LIAS (2021–2025)")

# ──────────── Filtre par équipe ────────────
equipe_filter = st.selectbox("Filtrer par équipe :", ["Toutes", "IDD", "SETR"])
equipe_param = None if equipe_filter == "Toutes" else equipe_filter

graph_data = api.get_collaboration_graphe(equipe_param)

if not graph_data:
    st.error("Impossible de charger le graphe de collaboration.")
    st.stop()

nodes = graph_data.get('nodes', [])
edges = graph_data.get('edges', [])
stats = graph_data.get('stats', {})

# ═══════════════════ STATISTIQUES DE COLLABORATION ═══════════════════
st.subheader("Statistiques de collaboration")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Chercheurs collaborants", stats.get('nb_noeuds', 0))
c2.metric("Liens de co-publication", stats.get('nb_aretes', 0))
c3.metric("Collaborations intra-équipe", stats.get('collaborations_intra_equipe', 0))
c4.metric("Collaborations inter-équipes", stats.get('collaborations_inter_equipes', 0))

# Taux d'ouverture global  
total_collab = stats.get('collaborations_intra_equipe', 0) + stats.get('collaborations_inter_equipes', 0)
if total_collab > 0:
    taux_inter = round(stats.get('collaborations_inter_equipes', 0) / total_collab * 100, 1)
    st.metric("Taux de collaboration inter-équipes", f"{taux_inter}%")

st.divider()

# ═══════════════════ VISUALISATION DU GRAPHE ═══════════════════
st.subheader("Réseau de co-publications")

if nodes and edges:
    import networkx as nx

    G = nx.Graph()
    for n in nodes:
        G.add_node(n['id'], label=n['label'], equipe=n['equipe'])
    for e in edges:
        G.add_edge(e['source'], e['target'], weight=e['weight'])

    pos = nx.spring_layout(G, seed=42, k=2)

    # Arêtes avec épaisseur variable
    edge_traces = []
    for e in G.edges(data=True):
        x0, y0 = pos[e[0]]
        x1, y1 = pos[e[1]]
        weight = e[2].get('weight', 1)
        
        # Déterminer si inter ou intra
        eq0 = G.nodes[e[0]].get('equipe', '')
        eq1 = G.nodes[e[1]].get('equipe', '')
        color = '#EF553B' if eq0 != eq1 else '#888'
        
        edge_traces.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode='lines',
            line=dict(width=max(0.5, weight * 0.5), color=color),
            hoverinfo='text',
            hovertext=f"{G.nodes[e[0]]['label']} ↔ {G.nodes[e[1]]['label']}: {weight} co-publications",
            showlegend=False
        ))

    # Nœuds
    node_x, node_y, node_text, node_color, node_size = [], [], [], [], []
    color_map = {'IDD': '#0068c9', 'SETR': '#83c8ff'}
    
    for n in nodes:
        x, y = pos[n['id']]
        node_x.append(x)
        node_y.append(y)
        degree = G.degree(n['id'])
        # Betweenness centrality
        bc = nx.betweenness_centrality(G)
        centrality = round(bc.get(n['id'], 0), 3)
        node_text.append(
            f"<b>{n['label']}</b><br>"
            f"Équipe: {n['equipe']}<br>"
            f"Co-auteurs: {degree}<br>"
            f"Centralité: {centrality}"
        )
        node_color.append(color_map.get(n['equipe'], '#999'))
        node_size.append(max(12, degree * 5))

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode='markers+text',
        text=[n['label'].split(' ')[-1] for n in nodes],
        textposition='top center',
        textfont=dict(size=10),
        hovertext=node_text,
        hoverinfo='text',
        marker=dict(
            size=node_size, color=node_color,
            line=dict(width=2, color='white'),
            opacity=0.9
        ),
        showlegend=False
    )

    fig = go.Figure(data=edge_traces + [node_trace])
    
    # Légende manuelle
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name='IDD',
                             marker=dict(size=12, color='#0068c9')))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name='SETR',
                             marker=dict(size=12, color='#83c8ff')))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name='Intra-équipe',
                             line=dict(color='#888', width=2)))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name='Inter-équipes',
                             line=dict(color='#EF553B', width=2)))
    
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=650,
        title="Réseau de co-publications (taille = nb co-auteurs, rouge = inter-équipes)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Centralité betweenness
    st.subheader("Centralité des chercheurs (betweenness centrality)")
    st.markdown("La centralité identifie les chercheurs **ponts** reliant les autres. Plus la valeur est élevée, plus le chercheur joue un rôle structurant dans le réseau.")
    
    bc = nx.betweenness_centrality(G)
    centrality_data = []
    for n in nodes:
        centrality_data.append({
            'Chercheur': n['label'],
            'Équipe': n['equipe'],
            'Centralité': round(bc.get(n['id'], 0), 4),
            'Degré (nb co-auteurs)': G.degree(n['id'])
        })
    df_bc = pd.DataFrame(centrality_data).sort_values('Centralité', ascending=False)
    st.dataframe(df_bc, use_container_width=True, hide_index=True)
    
    # Chercheur pont
    if not df_bc.empty and df_bc.iloc[0]['Centralité'] > 0:
        chercheur_pont = df_bc.iloc[0]
        st.success(f"**Chercheur pont** : {chercheur_pont['Chercheur']} ({chercheur_pont['Équipe']}) — centralité = {chercheur_pont['Centralité']}")

else:
    st.info("Aucune co-publication détectée avec les filtres actuels.")

st.divider()

# ═══════════════════ TABLEAU DES CO-PUBLICATIONS ═══════════════════
st.subheader("Détail des co-publications")

if edges:
    id_to_label = {n['id']: n['label'] for n in nodes}
    id_to_equipe = {n['id']: n['equipe'] for n in nodes}
    rows = []
    for e in edges:
        eq1 = id_to_equipe.get(e['source'], '?')
        eq2 = id_to_equipe.get(e['target'], '?')
        type_collab = "Intra" if eq1 == eq2 else "Inter"
        rows.append({
            "Chercheur 1": id_to_label.get(e['source'], '?'),
            "Équipe 1": eq1,
            "Chercheur 2": id_to_label.get(e['target'], '?'),
            "Équipe 2": eq2,
            "Co-publications": e['weight'],
            "Type": type_collab
        })
    df_edges = pd.DataFrame(rows).sort_values('Co-publications', ascending=False)
    st.dataframe(df_edges, use_container_width=True, hide_index=True)

    # Bar chart du nombre de co-publications par paire
    fig_copub = px.bar(df_edges.head(15), 
                       x='Co-publications', 
                       y=df_edges.head(15).apply(lambda r: f"{r['Chercheur 1']} ↔ {r['Chercheur 2']}", axis=1),
                       orientation='h', color='Type',
                       title="Top 15 des paires de co-auteurs",
                       color_discrete_map={'Intra': '#636EFA', 'Inter': '#FF6B6B'})
    fig_copub.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_copub, use_container_width=True)
