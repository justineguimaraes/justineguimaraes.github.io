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
var VELIB_CODE = [
  "import requests",
  "import pandas as pd",
  "import json",
  "import webbrowser",
  "",
  "url_base = (",
  "    \"https://opendata.paris.fr/api/explore/v2.1\"",
  "    \"/catalog/datasets/velib-disponibilite-en-temps-reel/records\"",
  ")",
  "",
  "resultat = requests.get(url_base, timeout=10).json()",
  "resultat_final = []",
  "",
  "for i in range(0, resultat[\"total_count\"], 100):",
  "    temp = requests.get(url_base + f\"?limit=100&offset={i}\", timeout=10).json()",
  "    resultat_final += temp[\"results\"]",
  "",
  "data = pd.DataFrame(resultat_final)",
  "",
  "sel = data.copy()",
  "sel[\"velo_dispo\"] = sel.apply(",
  "    lambda r: (r[\"numbikesavailable\"] / r[\"capacity\"] * 100) if r[\"capacity\"] > 0 else 0, axis=1",
  ")",
  "sel[\"taux_ebike\"] = sel.apply(",
  "    lambda r: (r[\"ebike\"] / r[\"numbikesavailable\"] * 100) if r[\"numbikesavailable\"] > 0 else 0, axis=1",
  ")",
  "",
  "stations_json = []",
  "for _, row in sel.iterrows():",
  "    cap = int(row[\"capacity\"]) if pd.notna(row[\"capacity\"]) else 0",
  "    dispo = int(row[\"numbikesavailable\"]) if pd.notna(row[\"numbikesavailable\"]) else 0",
  "    taux = (dispo / cap * 100) if cap > 0 else 0",
  "    stations_json.append({",
  "        \"name\": row[\"name\"], \"lat\": row[\"coordonnees_geo\"][\"lat\"],",
  "        \"lon\": row[\"coordonnees_geo\"][\"lon\"], \"taux\": round(taux,1),",
  "        \"is_empty\": taux < 10, \"is_full\": taux > 90",
  "    })",
  "",
  "with open(\"dashboard_velib.html\", \"w\", encoding=\"utf-8\") as f:",
  "    f.write(HTML_TEMPLATE.format(stations_json=json.dumps(stations_json, ensure_ascii=False)))",
  "webbrowser.open_new_tab(\"dashboard_velib.html\")"
].join("\n");


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
    icon: "📊",
    badge: "Statistiques",
    badgeClass: "badge-stat",
    title: "Analyse bibliométrique d’un laboratoire de recherche à partir de données ouvertes",
    image: null,
    desc: "Analyse statistique des facteurs influençant les recettes au box-office et les notes des films. Régressions linéaires multiples, tests d'hypothèses et visualisation des résultats sous RStudio. Rapport rédigé en anglais.",
    objectifs: [
      "Mettre en oeuvre des régressions linéaires simples et multiples",
      "Tester la significativité des variables explicatives",
      "Produire des visualisations lisibles et interprétables",
      "Rédiger un rapport d'analyse en anglais"
    ],
    skills: ["Régression linéaire", "Tests d'hypothèses", "Visualisation statistique", "Rédaction anglais"],
    tools: ["RStudio", "ggplot2", "dplyr", "R Markdown"],
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
    image: null,
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
    tools: ["Excel", "Buys-Ballot", "Régression linéaire", "Boîtes à moustaches", "FMI Open Data"],
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
      "Regrouper et catégoriser des réponses textuelles pour les représenter graphiquement",
      "Produire une analyse critique et des propositions d'amélioration",
      "Développer la communication orale et la pédagogie"
    ],
    skills: ["Communication orale", "Analyse de données qualitatives", "Data visualisation", "Pédagogie", "Travail en équipe"],
    tools: ["Excel", "Power BI", "Questionnaire", "Graphiques statistiques"],
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
    tools: ["R", "R Shiny", "ggplot2", "shinyapps.io"],
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
    tools: ["QGIS", "Group Stats", "Données INSEE", "OpenData SNCF / RATP / IDFM", "Lambert 93 (EPSG:2154)"],
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