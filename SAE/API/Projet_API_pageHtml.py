# -*- coding: utf-8 -*-
"""
Created on Wed Oct 29 16:15:25 2025

@author: jguimara
"""

# -*- coding: utf-8 -*-
"""
Dashboard Vélib Paris avec indicateurs de rééquilibrage séparés
"""

import requests
import pandas as pd
import json
import webbrowser

# ------------------------------
# 1️⃣ Récupérer les données
# ------------------------------
url_base = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/records"

try:
    resultat = requests.get(url_base, timeout=10).json()
    resultat_final = []
    
    for i in range(0, resultat["total_count"], 100):
        temp = requests.get(url_base + f"?limit=100&offset={i}", timeout=10).json()
        resultat_final += temp["results"]
    
    data = pd.DataFrame(resultat_final)
    
except requests.RequestException as e:
    print(f"Erreur lors de la récupération des données : {e}")
    exit(1)

# On prend toutes les communes disponibles pour créer la carte
communes = data['nom_arrondissement_communes'].unique() 
# Filtrer les stations appartenant à ces communes
stations_selection = data[data['nom_arrondissement_communes'].isin(communes)]

# Calcul du taux de disponibilité
stations_selection['velo_dispo'] = stations_selection.apply(
    lambda row: (row['numbikesavailable'] / row['capacity'] * 100) if row['capacity'] > 0 else 0,
    axis=1
)

# Calcul du taux de vélos électriques disponible
stations_selection['taux_ebike'] = stations_selection.apply(
    lambda row: (row['ebike'] / row['numbikesavailable'] * 100) if row['numbikesavailable'] > 0 else 0,
    axis=1
)

# ------------------------------
# 2️⃣ Créer le JSON des stations
# ------------------------------
stations_json = []
for idx, row in stations_selection.iterrows():
    total_bikes = int(row['capacity']) if pd.notna(row['capacity']) else 0
    available_bikes = int(row['numbikesavailable']) if pd.notna(row['numbikesavailable']) else 0
    taux_dispo = (available_bikes / total_bikes * 100) if total_bikes > 0 else 0
    
    # Déterminer le type de rééquilibrage nécessaire
    is_empty = taux_dispo < 10  # Station vide
    is_full = taux_dispo > 90   # Station pleine
    
    stations_json.append({
        "name": row['name'],
        "stationcode": row['stationcode'],
        "lat": row['coordonnees_geo']['lat'],
        "lon": row['coordonnees_geo']['lon'],
        "capacity": total_bikes,
        "numbikesavailable": available_bikes,
        "mechanical": int(row.get('mechanical', 0)) if pd.notna(row.get('mechanical', 0)) else 0,
        "ebike": int(row.get('ebike', 0)) if pd.notna(row.get('ebike', 0)) else 0,
        "numdocksavailable": int(row.get('numdocksavailable', 0)) if pd.notna(row.get('numdocksavailable', 0)) else 0,
        "taux": round(taux_dispo, 1),
        "taux_ebike": round(row['taux_ebike'], 1),
        "arrondissement": row['nom_arrondissement_communes'],
        "is_empty": is_empty,
        "is_full": is_full
    })

arrondissements = sorted(stations_selection['nom_arrondissement_communes'].dropna().unique())

# ------------------------------
# 3️⃣ Créer la page HTML
# ------------------------------
html_base = """
<!DOCTYPE html>
    <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard Vélib Paris</title>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                * {{ margin:0; padding:0; box-sizing:border-box; }}
                body {{ font-family: Arial,sans-serif; background:#f5f5f5; }}
                .container {{ max-width:1800px; margin:0 auto; padding:20px; }}
                h1 {{ color:#0066cc; text-align:center; margin-bottom:20px; }}
                .controls {{ background:white; padding:20px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1); margin-bottom:20px; }}
                .controls label {{ font-weight:bold; margin-right:10px; }}
                .controls select {{ padding:10px; border:2px solid #0066cc; border-radius:5px; font-size:14px; min-width:250px; }}
                .stats {{ display:grid; grid-template-columns:repeat(6,1fr); gap:15px; margin-bottom:20px; }}
                .stat-card {{ background:white; padding:20px; border-radius:10px; text-align:center; box-shadow:0 2px 5px rgba(0,0,0,0.1); }}
                .stat-card.empty {{ background:#ffebee; border:2px solid #ef5350; }}
                .stat-card.full {{ background:#fff3e0; border:2px solid #ff9800; }}
                .stat-number {{ font-size:32px; font-weight:bold; color:#0066cc; }}
                .stat-number.empty {{ color:#d32f2f; }}
                .stat-number.full {{ color:#f57c00; }}
                .stat-label {{ font-size:14px; color:#666; margin-top:5px; }}
                .legend {{ display:flex; justify-content:center; gap:30px; margin-bottom:20px; padding:15px; background:white; border-radius:10px; }}
                .legend-item {{ display:flex; align-items:center; gap:10px; }}
                .legend-color {{ width:20px; height:20px; border-radius:50%; }}
                #map {{ height:600px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1); }}
                .chart-container {{ background:white; padding:30px; border-radius:10px; margin-top:20px; box-shadow:0 2px 5px rgba(0,0,0,0.1); height:600px; }}
                .charts-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-top:20px; }}
                canvas {{ width:100% !important; height:100% !important; }}
            </style>
        </head>
    <body>
        <div class="container">
        <h1>🚲 Dashboard Vélib Paris</h1>
        <div class="controls">
        <label for="arrondissement">Filtrer par commune :</label>
        <select id="arrondissement" onchange="filtrerStations()">
        <option value="">-- Toutes les stations --</option>
        {options}
        </select>
        </div>
        
        <div class="stats">
            <div class="stat-card"><div class="stat-number" id="stat-stations">0</div><div class="stat-label">Stations</div></div>
            <div class="stat-card"><div class="stat-number" id="stat-velos">0</div><div class="stat-label">Vélos disponibles</div></div>
            <div class="stat-card"><div class="stat-number" id="stat-capacity">0</div><div class="stat-label">Capacité totale</div></div>
            <div class="stat-card"><div class="stat-number" id="stat-taux">0%</div><div class="stat-label">Taux de disponibilité</div></div>
            <div class="stat-card empty">
                <div class="stat-number empty" id="stat-empty">0</div>
                <div class="stat-label">🔴 Stations vides (<10%)</div>
            </div>
            <div class="stat-card full">
                <div class="stat-number full" id="stat-full">0</div>
                <div class="stat-label">🟠 Stations pleines (>90%)</div>
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-item"><div class="legend-color" style="background:red;"></div><span><20%</span></div>
            <div class="legend-item"><div class="legend-color" style="background:orange;"></div><span>20-50%</span></div>
            <div class="legend-item"><div class="legend-color" style="background:blue;"></div><span>50-80%</span></div>
            <div class="legend-item"><div class="legend-color" style="background:green;"></div><span>>80%</span></div>
        </div>
        
        <div id="map"></div>
        
        <div class="charts-grid" style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-top:20px;">
        <div class="chart-container" style="height:400px;">
            <canvas id="chartDispo"></canvas>
        </div>
        <div class="chart-container" style="height:400px;">
            <canvas id="chartEbike"></canvas>
        </div>
        </div>

        </div>
        
        <script>
        let allStations = {stations_json};
        
        let map = L.map('map').setView([48.8566, 2.3522], 12);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution:'© OpenStreetMap contributors'
        }}).addTo(map);
        
        let markers = [];
        let chartDispo, chartEbike;
        
        function filtrerStations() {{
            const arrondissement = document.getElementById('arrondissement').value;
            let stationsFiltrees = arrondissement ? allStations.filter(s => s.arrondissement === arrondissement) : allStations;
        
            markers.forEach(m => map.removeLayer(m));
            markers = [];
        
            let totalVelos = 0, totalCapacity = 0, stationsEmpty = 0, stationsFull = 0;
            stationsFiltrees.forEach(station => {{
                totalVelos += station.numbikesavailable;
                totalCapacity += station.capacity;
                
                // Compter les stations vides et pleines séparément
                if (station.is_empty) stationsEmpty++;
                if (station.is_full) stationsFull++;
                
                let color = station.taux > 80 ? 'green' : 
                station.taux > 50 ? 'blue' : 
                station.taux > 20 ? 'orange' : 'red';
                let marker = L.circleMarker([station.lat, station.lon], {{
                    radius: 8,
                    fillColor: color,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }}).addTo(map);
                
                let warningText = '';
                if (station.is_empty) {{
                    warningText = '<br><span style="color:#d32f2f;font-weight:bold;">🔴 Station vide - Ajout de vélos nécessaire</span>';
                }} else if (station.is_full) {{
                    warningText = '<br><span style="color:#f57c00;font-weight:bold;">🟠 Station pleine - Retrait de vélos nécessaire</span>';
                }}
                
                marker.bindPopup(`<b>${{station.name}}</b><br>
                <b>Capacité:</b> ${{station.capacity}}<br>
                <b>Vélos disponibles:</b> ${{station.numbikesavailable}}<br>
                <b>Taux de remplissage:</b> ${{station.taux}}%<br>
                <b>Mécaniques:</b> ${{station.mechanical}}<br>
                <b>Électriques:</b> ${{station.ebike}}<br>
                <b>Commune:</b> ${{station.arrondissement}}${{warningText}}`);
                markers.push(marker);
            }});
        
            document.getElementById('stat-stations').textContent = stationsFiltrees.length;
            document.getElementById('stat-velos').textContent = totalVelos;
            document.getElementById('stat-capacity').textContent = totalCapacity;
            document.getElementById('stat-taux').textContent = totalCapacity > 0 ? ((totalVelos / totalCapacity * 100).toFixed(1) + '%') : '0%';
            document.getElementById('stat-empty').textContent = stationsEmpty;
            document.getElementById('stat-full').textContent = stationsFull;
        
            if (stationsFiltrees.length > 0) {{
                let lats = stationsFiltrees.map(s => s.lat);
                let lons = stationsFiltrees.map(s => s.lon);
                let bounds = [[Math.min(...lats), Math.min(...lons)], [Math.max(...lats), Math.max(...lons)]];
                map.fitBounds(bounds);
            }}
        
            updateCharts(arrondissement);
        }}
        
        function updateCharts(arrondissementSelectionne) {{
            // Calcul des moyennes par arrondissement
            let arrs = {{}};
            allStations.forEach(s => {{
                if (!arrs[s.arrondissement]) {{
                    arrs[s.arrondissement] = {{totalDispo: 0, totalEbike: 0, count: 0}};
                }}
                arrs[s.arrondissement].totalDispo += s.taux;
                arrs[s.arrondissement].totalEbike += s.taux_ebike;
                arrs[s.arrondissement].count += 1;
            }});
            
            let labels = Object.keys(arrs).sort();
            let dataDispo = labels.map(a => (arrs[a].totalDispo / arrs[a].count).toFixed(1));
            let dataEbike = labels.map(a => (arrs[a].totalEbike / arrs[a].count).toFixed(1));
            
            // Trier par ordre décroissant pour le graphique de disponibilité
            let sortedDispo = labels.map((label, i) => ({{label, value: parseFloat(dataDispo[i])}}))
                                    .sort((a, b) => b.value - a.value);
            let labelsDispo = sortedDispo.map(d => d.label);
            let valuesDispo = sortedDispo.map(d => d.value);
            
            // Couleurs pour le graphique de disponibilité (mise en évidence de la commune sélectionnée)
            let colorsDispo = labelsDispo.map(label => 
                label === arrondissementSelectionne ? '#ff6b35' : 'mediumseagreen'
            );
            
            // Trier par ordre décroissant pour le graphique des vélos électriques
            let sortedEbike = labels.map((label, i) => ({{label, value: parseFloat(dataEbike[i])}}))
                                    .sort((a, b) => b.value - a.value);
            let labelsEbike = sortedEbike.map(d => d.label);
            let valuesEbike = sortedEbike.map(d => d.value);
            
            // Couleurs pour le graphique des vélos électriques (mise en évidence de la commune sélectionnée)
            let colorsEbike = labelsEbike.map(label => 
                label === arrondissementSelectionne ? '#ff6b35' : 'dodgerblue'
            );
        
            // Graphique 1 : Taux de disponibilité
            if (chartDispo) chartDispo.destroy();
            const ctx1 = document.getElementById('chartDispo').getContext('2d');
            chartDispo = new Chart(ctx1, {{
                type: 'bar',
                data: {{
                    labels: labelsDispo,
                    datasets: [{{
                        label: 'Taux moyen (%)',
                        data: valuesDispo,
                        backgroundColor: colorsDispo,
                        borderColor: colorsDispo,
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 2.5,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Taux moyen de disponibilité des vélos par communes',
                            font: {{
                                size: 18,
                                weight: 'bold'
                            }},
                            padding: 20
                        }},
                        legend: {{
                            display: false
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: 100,
                            title: {{
                                display: true,
                                text: 'Taux moyen de vélos disponibles (%)',
                                font: {{
                                    size: 14,
                                    weight: 'bold'
                                }}
                            }},
                            ticks: {{
                                font: {{
                                    size: 12
                                }}
                            }}
                        }},
                        x: {{
                            title: {{
                                display: true,
                                text: 'Commune',
                                font: {{
                                    size: 14,
                                    weight: 'bold'
                                }}
                            }},
                            ticks: {{
                                autoSkip: false,
                                maxRotation: 45,
                                minRotation: 45,
                                font: {{
                                    size: 11
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        
            // Graphique 2 : Taux de vélos électriques
            if (chartEbike) chartEbike.destroy();
            const ctx2 = document.getElementById('chartEbike').getContext('2d');
            chartEbike = new Chart(ctx2, {{
                type: 'bar',
                data: {{
                    labels: labelsEbike,
                    datasets: [{{
                        label: 'Taux moyen (%)',
                        data: valuesEbike,
                        backgroundColor: colorsEbike,
                        borderColor: colorsEbike,
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 2.5,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Taux moyen de vélos électriques disponibles par communes',
                            font: {{
                                size: 18,
                                weight: 'bold'
                            }},
                            padding: 20
                        }},
                        legend: {{
                            display: false
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: 100,
                            title: {{
                                display: true,
                                text: 'Taux moyen de vélos électriques (%)',
                                font: {{
                                    size: 14,
                                    weight: 'bold'
                                }}
                            }},
                            ticks: {{
                                font: {{
                                    size: 12
                                }}
                            }}
                        }},
                        x: {{
                            title: {{
                                display: true,
                                text: 'Commune',
                                font: {{
                                    size: 14,
                                    weight: 'bold'
                                }}
                            }},
                            ticks: {{
                                autoSkip: false,
                                maxRotation: 45,
                                minRotation: 45,
                                font: {{
                                    size: 11
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
        
        filtrerStations();
        </script>
    </body>
</html>
"""

# Injecter les valeurs Python
html_final = html_base.format(
    options="\n".join(f'<option value="{arr}">{arr}</option>' for arr in arrondissements),
    stations_json=json.dumps(stations_json, ensure_ascii=False)
)

with open("dashboard_velib.html", "w", encoding="utf-8") as f:
    f.write(html_final)

print("✅ Dashboard créé avec succès : dashboard_velib.html")
webbrowser.open_new_tab("dashboard_velib.html")