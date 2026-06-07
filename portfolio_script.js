// ── NAVIGATION ──────────────────────────────────────────────
function navigate(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
  const target = document.getElementById(pageId);
  if (target) target.classList.add('active');
  const navLink = document.getElementById('nav-' + pageId);
  if (navLink) navLink.classList.add('active');
  if (pageId === 'competences') animateSkillBars();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── ONGLETS PROJETS ──────────────────────────────────────────
function showProjPanel(id) {
  document.querySelectorAll('.proj-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.proj-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('proj-' + id).classList.add('active');
  document.getElementById('tab-' + id).classList.add('active');
}

// ── ANIMATION BARRES DE COMPÉTENCES ──────────────────────────
function animateSkillBars() {
  setTimeout(() => {
    document.querySelectorAll('.skill-bar').forEach(bar => bar.classList.add('animated'));
  }, 100);
}

// ── CODE PYTHON VÉLIB ────────────────────────────────────────
var VELIB_CODE = `# -*- coding: utf-8 -*-
import requests
import pandas as pd
import folium
import webbrowser
import matplotlib.pyplot as plt
import unicodedata

# Pour normaliser le texte, faire en sorte de trouver la commune même en oubliant une majuscule ou un tiret
def normalize_text(text: str) -> str:
    if pd.isna(text):
        return ""
    normalized = unicodedata.normalize('NFD', text)
    clean_text = "".join(
        char for char in normalized if unicodedata.category(char) != 'Mn'
    )
    return clean_text.lower().replace('-', ' ').replace("'", ' ').strip()

#import de l'API comme dans le cours
url_base = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/records"
resultat = requests.get(url_base).json()
resultat_final = []
for i in range(0, resultat["total_count"], 100):
 temp = requests.get(url_base + "?limit=100&offset=" + str(i)).json()
 resultat_final += temp["results"]

data = pd.DataFrame(resultat_final)

# On prend toutes les communes disponibles pour créer la carte
communes = sorted(data['nom_arrondissement_communes'].unique())  #cette ligne tri par ordre alphabétique et permets d'afficher seulement une commune même si elle apparait plusieurs fois
print("Choisir parmis les communes suivantes :", communes)

# DataFrame avec toutes les données 
stations_selection = data[data['nom_arrondissement_communes'].isin(communes)]

# Demander à l'utilisateur de saisir le nom de la commune
commune_choisie = input("Entrez le nom de la commune (ou 'TOUT' pour tout Paris) : ")

# Normaliser la commune choisie et les noms de communes dans le dataset
commune_choisie_norm = normalize_text(commune_choisie)

# Filtrer les stations de cet arrondissement
if commune_choisie_norm == "tout":
    stations_arr = stations_selection  # toutes les stations
    lat_centre, lon_centre = 48.8566, 2.3522  # centre de Paris
    zoom = 12  # zoom plus large pour voir toute la ville
else:
    # Créer une colonne normalisée pour la recherche
    stations_selection['commune_normalized'] = stations_selection['nom_arrondissement_communes'].apply(normalize_text)
    
    # Filtrer avec la version normalisée
    stations_arr = stations_selection[stations_selection['commune_normalized'] == commune_choisie_norm]
    
    if not stations_arr.empty:
        lat_centre = stations_arr['coordonnees_geo'].apply(lambda x: x['lat']).mean()
        lon_centre = stations_arr['coordonnees_geo'].apply(lambda x: x['lon']).mean()
    else:
        print(" Erreur : Commune non trouvée. Affichage de tout Paris.")
        stations_arr = stations_selection
        lat_centre, lon_centre = 48.8566, 2.3522
    zoom = 15  # zoom sur la commune

# Créer la carte centrée sur la commune, comme dans le cours
map_paris = folium.Map(location=[lat_centre, lon_centre], zoom_start=zoom)

# Ajouter un marqueur pour chaque station avec couleur selon la disponibilité
for idx, row in stations_arr.iterrows():
    if pd.notna(row['capacity']):
        total_bikes = row['capacity'] 
    else :
        total_bikes = 0
    if pd.notna(row['numbikesavailable']):
        available_bikes = row['numbikesavailable']
    else:
        available_bikes = 0
    
    # Calcul du pourcentage  de vélos disponibles
    velo_dispo = (available_bikes / total_bikes * 100) if total_bikes > 0 else 0
    
    # Choix de la couleur selon le pourcentage
    if velo_dispo > 80:
        couleur = 'green'
    elif velo_dispo > 50:
        couleur = 'blue'
    elif velo_dispo > 20:
        couleur = 'orange'
    else:
        couleur = 'red'
        
     # Création de l'info-bulle
    info_bulle = f"{row['name']} - {available_bikes}/{total_bikes} vélos disponible"
    
    # carte 
    folium.Marker(
        location=[row['coordonnees_geo']['lat'], row['coordonnees_geo']['lon']],
        tooltip=info_bulle,
        icon=folium.Icon(icon='bicycle', prefix='fa', color=couleur)
    ).add_to(map_paris)


# Afficher la carte
carte=map_paris

carte.save('1-exo2_2.html')
webbrowser.open_new_tab("1-exo2_2.html")

# QUESTION 2 : GRAPHIQUE COMPARATIF
#  Calculer le taux de disponibilité pour toutes les stations
stations_selection['velo_dispo'] = stations_selection.apply(
    lambda row: (row['numbikesavailable'] / row['capacity'] * 100) if row['capacity'] > 0 else 0,
    axis=1
)

#  Moyenne par arrondissement
taux_moyen_arrondissement = stations_selection.groupby('nom_arrondissement_communes')['velo_dispo'].mean().reset_index()
taux_moyen_arrondissement = taux_moyen_arrondissement.sort_values(by='velo_dispo', ascending=False)


plt.figure(figsize=(14,6))

# Barres verticales
bars = plt.bar(taux_moyen_arrondissement['nom_arrondissement_communes'], 
               taux_moyen_arrondissement['velo_dispo'], color='mediumseagreen')

plt.ylabel("Taux moyen de vélos disponibles (%)")
plt.xlabel("Arrondissement / Commune")
plt.title("Taux moyen de disponibilité des vélos par communes")
plt.ylim(0,100)


# Rotation des labels pour les lire facilement
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()


#### QUESTION 3 : Indicateur taux moyen de vélos électriques
#  Calculer le taux de vélos électriques par station
stations_selection['taux_ebike'] = stations_selection.apply(
    lambda row: (row['ebike'] / row['numbikesavailable'] * 100) if row['numbikesavailable'] > 0 else 0,
    axis=1
)

#  Moyenne par communes
taux_moyen_ebike = stations_selection.groupby('nom_arrondissement_communes')['taux_ebike'].mean().reset_index()
taux_moyen_ebike = taux_moyen_ebike.sort_values(by='taux_ebike', ascending=False)

#  Graphique vertical (barres) avec Matplotlib
plt.figure(figsize=(14,6))
bars = plt.bar(taux_moyen_ebike['nom_arrondissement_communes'], 
               taux_moyen_ebike['taux_ebike'], color='dodgerblue')

plt.ylabel("Taux moyen de vélos électriques (%)")
plt.xlabel("Arrondissement / Commune")
plt.title("Taux moyen de vélos électriques disponibles par communes")
plt.ylim(0,100)


# Rotation des labels pour les lire facilement
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

#### QUESTION 4 
# Calcul de l'indicateur
# Trouver la station avec la plus grande capacité par commune
station_max_capacite = stations_arr.loc[
    stations_arr.groupby('nom_arrondissement_communes')['capacity'].idxmax()
]

# Afficher le résultat
print("\n=== Station avec la plus grande capacité par commune ===\n")
for idx, row in station_max_capacite.iterrows():
    print(f"🏙️ {row['nom_arrondissement_communes']}")
    print(f"   📍 Station : {row['name']}")
    print(f"   🚲 Capacité : {int(row['capacity'])} places")
    print()`;


// ── DONNÉES DES PROJETS ──────────────────────────────────────
var PROJECTS = {

  velib: {
    icon: "🚲",
    badge: "API · DataViz",
    badgeClass: "badge-api",
    title: "Dashboard Vélib Paris",
    image: 'assets/velib_map.png',
    desc: "Collecte en temps réel de la disponibilité des stations Vélib via l'API OpenData Paris. Les données (1 500+ stations) sont récupérées par pagination, traitées avec Pandas, puis restituées dans un dashboard HTML interactif généré automatiquement par le script Python : carte Leaflet colorisée par taux de disponibilité, indicateurs clés (stations vides/pleines) et graphiques Chart.js par commune.",
    objectifs: [
      "Consommer une API REST paginée et parser du JSON",
      "Traiter et agréger des données tabulaires avec Pandas",
      "Générer dynamiquement une page HTML depuis Python",
      "Visualiser des données géolocalisées avec Leaflet.js",
      "Produire des graphiques comparatifs avec Chart.js"
    ],
    skills: ["API REST", "Pandas", "JSON", "Visualisation géospatiale", "HTML dynamique", "Chart.js"],
    tools: ["Python 3", "requests", "Pandas", "Leaflet.js", "Chart.js", "API OpenData Paris"],
    code: VELIB_CODE,
    rapport: null,
    link: null
  },

  cinema: {
    icon: "📚",
    badge: "Bibliométrie, API",
    badgeClass: "badge-api",
    title: "Analyse bibliométrique d’un laboratoire de recherche à partir de données ouvertes",
    image: null,
    desc: "Dans le cadre d'une SAE, avec mes collègues, nous avons mené une analyse bibliométrique complète du laboratoire de recherche LIAS (Université de Poitiers), portant sur 19 chercheurs permanents des équipes IDD et SETR sur la période 2021–2025. L'objectif stratégique était d'aider la direction à évaluer la pertinence d'une fusion des deux équipes, en identifiant les chercheurs clés, les membres peu actifs et les dynamiques de collaboration. Le projet a abouti à une application web interactive permettant de simuler des scénarios de marginalisation et de transfert de chercheurs.",
    objectifs: [
      "Collecter et fiabiliser des données bibliographiques via des API ouvertes (DBLP, theses.fr)",
      "Calculer des indicateurs de volume, qualité et collaboration (rangs CORE, quartiles Scimago)",
      "Identifier les chercheurs clés et les risques de dépendance au sein de chaque équipe",
      "RDévelopper une API REST et un dashboard interactif pour la simulation de scénarios",
      "Formuler des recommandations stratégiques argumentées sur la fusion IDD + SETR"
    ],
    skills: ["Collecte de données", "Nettoyage et fiabilisation de données", "Calcul d'indicateurs statistiques", "Conteneurisation", "Analyse stratégique et data storytelling"],
    tools: ["Python", "FastAPI,", "Streamlit", "Docker"],
    code: null,
    rapport: "assets/reports/Rapport_Docker.pdf",
    link: null
  },

  talend: {
    icon: "📈",
    badge: "Visualisation",
    badgeClass: "badge-viz",
    title: "Intégration des données dans un DataWarehouse",
    image: 'assets/talend.png',
    desc: "Conception d'un tableau de bord interactif destiné à l'aide à la décision, avec automatisation de l'alimentation des données via un pipeline ETL.",
    objectifs: [
      "Modéliser le besoin métier et définir les KPIs",
      "Construire un pipeline ETL avec Talend",
      "Concevoir un dashboard interactif sous Power BI",
      "Documenter et présenter les choix de visualisation"
    ],
    skills: ["Business Intelligence", "ETL", "Power BI", "Data storytelling"],
    tools: ["Talend"],
    code: null,
    rapport: null,
    link: null
  },

  bdd: {
    icon: "🗄️",
    badge: "Base de données",
    badgeClass: "badge-ml",
    title: "Modélisation base de données",
    image: 'assets/MCD.jpg',
    desc: "Conception et implémentation d'une base de données relationnelle complète : modélisation Merise, création des tables, requêtes complexes et interface PHP de consultation.",
    objectifs: [
      "Réaliser un MCD et MLD avec la méthode Merise",
      "Implémenter la base en SQL avec requêtes avancées",
      "Développer une interface de consultation en PHP",
      "Optimiser les performances par l'indexation"
    ],
    skills: ["Modélisation Merise", "SQL avancé", "PHP", "Optimisation BDD"],
    tools: ["MySQL", "SQL", "Merise", "PHP", "phpMyAdmin"],
    code: null,
    rapport: null,
    link: null
  },

  aluminium: {
    icon: "📉",
    badge: "Séries temporelles",
    badgeClass: "badge-ts",
    title: "Prévision du prix de l'aluminium",
    image: 'assets/aluminium.png',
    desc: "Analyse et prévision du prix unitaire d'une tonne métrique d'aluminium (données FMI, 1992-2025). Le projet comprend la détection de saisonnalité, le choix du modèle additif, la comparaison de tendances (linéaire, quadratique, exponentielle) et la production de prévisions jusqu'à fin 2026. Conclusion : stabilisation attendue autour de 2 045 $ en l'absence de chocs extérieurs.",
    objectifs: [
      "Décrire et visualiser une série temporelle mensuelle sur 30 ans",
      "Détecter les composantes saisonnières (moyennes mensuelles, boîtes à moustaches)",
      "Identifier le modèle additif via le test de Buys-Ballot",
      "Comparer les ajustements linéaire, quadratique et exponentiel (R²)",
      "Produire des prévisions et calculer les erreurs de prévision"
    ],
    skills: ["Séries temporelles", "Modèle additif", "Prévision", "Analyse de tendance", "Visualisation Excel"],
    tools: ["Excel", "Régression linéaire", "Boîtes à moustaches", "FMI Open Data"],
    code: null,
    rapport: "assets/reports/Rapport_Aluminium.pdf",
    link: null
  },

  futurIA: {
    icon: "🤖",
    badge: "Besoins du territoire",
    badgeClass: "badge-territory",
    title: "Sensibilisation à l'IA — Future of IA",
    image: 'assets/futur_of_ia.jpeg',
    desc: "Dans le cadre du projet Latitudes, animation de 4 séances de sensibilisation à l'intelligence artificielle auprès d'élèves de seconde du Lycée de la Venise Verte (Niort). Le projet inclut l'analyse critique du jeu Future of IA, le traitement et la visualisation des questionnaires de satisfaction (68 élèves), et la rédaction de propositions d'amélioration pour l'association.",
    objectifs: [
      "Animer des ateliers pédagogiques sur l'IA devant un public lycéen",
      "Traiter et visualiser des données de questionnaires ouverts",
      "Mettre en avant le BUT au travers d'une mini-présentation de la formation",
      "Produire une analyse critique et des propositions d'amélioration au jeu",
      "Développer la communication orale et la pédagogie"
    ],
    skills: ["Communication orale", "Vulgarisation", "Pédagogie", "Travail en équipe"],
    tools: ["Jeu de cartes Futur of IA"],
    code: null,
    rapport: "assets/reports/Rapport_FuturIA.pdf",
    link: null
  },

  rshiny: {
    icon: "📐",
    badge: "Analyse multivariée",
    badgeClass: "badge-stat",
    title: "Reporting analyse multivariée (R Shiny)",
    image: 'assets/r_shiny.png',
    desc: "Application interactive de reporting statistique développée avec R Shiny, permettant d'explorer des données multivariées. L'outil propose des analyses dynamiques accessibles en ligne, illustrant la capacité à transformer une analyse statistique en outil décisionnel interactif partageable.",
    objectifs: [
      "Développer une application interactive avec R Shiny",
      "Mettre en oeuvre des méthodes d'analyse multivariée",
      "Rendre une analyse statistique accessible via une interface web",
      "Déployer l'application en ligne (shinyapps.io)"
    ],
    skills: ["R Shiny", "Analyse multivariée", "Visualisation interactive", "Déploiement web"],
    tools: ["R", "R Shiny", "ggplot2"],
    code: null,
    rapport: null,
    link: "https://eguena.shinyapps.io/Reporting_analyse_multivariee/"
  }

  ,carte: {
    icon: "🗺️",
    badge: "SIG · Cartographie",
    badgeClass: "badge-viz",
    title: "QGIS : Les McDonald's en France métropolitaine",
    image: 'assets/carte_SIG.png',
    desc: "Étude spatiale complète de la distribution des restaurants McDonald's en France métropolitaine réalisée sous QGIS. Le projet couvre l'import et la reprojection des données (Lambert 93), l'analyse statistique par Group Stats, la production de cartes choroplèthes de densité par département (nombre pour 100 000 habitants), l'étude de proximité aux gares SNCF / stations de métro RATP / gares IDFM (zones tampons de 500 m), et une cartographie par cercles proportionnels de la population dans un rayon de 15 km autour de chaque restaurant sur l'ex-Poitou-Charentes.",
    objectifs: [
      "Importer et reprojeter des données CSV en Lambert 93 (EPSG:2154)",
      "Calculer des statistiques par groupe (Group Stats) : top 15 villes, ouvertures par année et par région",
      "Produire une carte choroplèthe de densité McDonald's pour 100 000 habitants par département",
      "Réaliser des zones tampons de 500 m autour des gares SNCF, stations RATP et gares IDFM",
      "Créer des cercles proportionnels (population 15 km) sur l'ex-Poitou-Charentes"
    ],
    skills: ["SIG / QGIS", "Cartographie thématique", "Analyse spatiale", "Zones tampons", "Cercles proportionnels", "Lambert 93"],
    tools: ["QGIS"],
    code: null,
    rapport: "assets/reports/Rapport_SIG.pdf",
    link: null
  }

};


// ── OUVERTURE DU MODAL ────────────────────────────────────────
function openProjectModal(id) {
  var proj = PROJECTS[id];
  if (!proj) return;

  document.getElementById('modalIcon').textContent  = proj.icon;
  document.getElementById('modalTitle').textContent = proj.title;
  document.getElementById('modalDesc').textContent  = proj.desc;

  document.getElementById('modalBadgeWrap').innerHTML =
    '<span class="proj-badge ' + proj.badgeClass + '">' + proj.badge + '</span>';

  document.getElementById('modalObjectifs').innerHTML =
    proj.objectifs.map(function(o) { return '<li>' + o + '</li>'; }).join('');

  document.getElementById('modalSkills').innerHTML =
    proj.skills.map(function(s) { return '<span class="modal-skill-tag">' + s + '</span>'; }).join('');

  document.getElementById('modalTools').innerHTML =
    proj.tools.map(function(t) { return '<span class="proj-tool">' + t + '</span>'; }).join('');

  // Image
  var imgSection = document.getElementById('modalImageSection');
  var imgEl = document.getElementById('modalImage');
  if (proj.image) {
    imgEl.src = proj.image;
    imgEl.alt = proj.title;
    imgSection.style.display = 'block';
  } else {
    imgSection.style.display = 'none';
  }

  // Code
  var codeSection = document.getElementById('modalCodeSection');
  if (proj.code) {
    document.getElementById('modalCode').textContent = proj.code;
    codeSection.style.display = 'block';
  } else {
    codeSection.style.display = 'none';
  }

  // Boutons rapport + lien
  var actionsSection = document.getElementById('modalActionsSection');
  var rapportBtn = document.getElementById('modalRapportBtn');
  var linkBtn    = document.getElementById('modalLinkBtn');
  var hasAction  = false;

  if (proj.rapport) {
    rapportBtn.href = proj.rapport;
    rapportBtn.style.display = 'inline-flex';
    hasAction = true;
  } else {
    rapportBtn.style.display = 'none';
  }

  if (proj.link) {
    linkBtn.href = proj.link;
    linkBtn.style.display = 'inline-flex';
    hasAction = true;
  } else {
    linkBtn.style.display = 'none';
  }

  actionsSection.style.display = hasAction ? 'flex' : 'none';

  document.getElementById('projModalOverlay').classList.add('active');
  document.body.style.overflow = 'hidden';
}

// ── FERMETURE DU MODAL ────────────────────────────────────────
function closeProjectModal(event) {
  if (event && event.target !== document.getElementById('projModalOverlay')) return;
  document.getElementById('projModalOverlay').classList.remove('active');
  document.body.style.overflow = '';
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeProjectModal(null);
});

// ── COPIER LE CODE ────────────────────────────────────────────
function copyCode() {
  var code = document.getElementById('modalCode').textContent;
  var btn  = document.getElementById('codeCopyBtn');
  navigator.clipboard.writeText(code).then(function() {
    btn.textContent = 'Copié !';
    setTimeout(function() { btn.textContent = 'Copier'; }, 2000);
  });
}

// ── INIT ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  navigate('accueil');
});