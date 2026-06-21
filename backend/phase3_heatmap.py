"""
Phase 3 — Heatmap Builder (Dynamic Viewport & Fully Synchronized Timeline)
Flipkart Gridlock 2.0 | Parking Intelligence System
Run: python backend/phase3_heatmap.py
"""

import pandas as pd
import json
import folium
from folium.plugins import HeatMap, TimestampedGeoJson
from pathlib import Path

# ── CONFIG ───────────────────────────────────────────────────────────────────
DATA_DIR = Path("./data")
MAPS_DIR = Path("./maps")
MAPS_DIR.mkdir(exist_ok=True)

# Fallback center, will be overridden by dynamic bounds
MAP_CENTER = [12.9716, 77.5946]
MAP_ZOOM   = 12

PRIORITY_COLORS = {
    "CRITICAL": "#E24B4A",
    "HIGH":     "#EF9F27",
    "MEDIUM":   "#639922",
    "LOW":      "#378ADD",
}

MONTH_ORDER = ["November", "December", "January", "February", "March"]

MONTH_DATES = {
    "November": "2023-11-01T00:00:00",
    "December": "2023-12-01T00:00:00",
    "January":  "2024-01-01T00:00:00",
    "February": "2024-02-01T00:00:00",
    "March":    "2024-03-01T00:00:00"
}

# ── LOAD & SECURE DEDUPLICATE ────────────────────────────────────────────────
print("=" * 55)
print("  PHASE 3 — HEATMAP BUILDER (VIEWPORT SYNC)")
print("=" * 55)

print("\n[1/4] Loading and cleaning Phase 2 outputs...")
df = pd.read_csv(DATA_DIR / "df_clusters.csv")

with open(DATA_DIR / "hotspots.json") as f:
    raw_hotspots = json.load(f)

with open(DATA_DIR / "patrol_schedule.json") as f:
    raw_patrol = json.load(f)

unique_hotspots = {}
for idx, h in enumerate(raw_hotspots):
    coord_key = (round(h["centroid_lat"], 3), round(h["centroid_lng"], 3))
    
    h_score = h.get("zone_score", h.get("risk_score", 0))
    current_best = unique_hotspots.get(coord_key, {})
    current_best_score = current_best.get("hotspot", {}).get("zone_score", current_best.get("hotspot", {}).get("risk_score", 0))
    
    if coord_key not in unique_hotspots or h_score > current_best_score:
        p_data = raw_patrol[idx] if idx < len(raw_patrol) else {}
        unique_hotspots[coord_key] = {
            "hotspot": h,
            "patrol": p_data
        }

clean_data = list(unique_hotspots.values())
hotspots = [item["hotspot"] for item in clean_data]
patrols = [item["patrol"] for item in clean_data]

# -- DYNAMIC BOUNDING BOX CALCULATION --
min_lat = min(h["centroid_lat"] for h in hotspots)
max_lat = max(h["centroid_lat"] for h in hotspots)
min_lng = min(h["centroid_lng"] for h in hotspots)
max_lng = max(h["centroid_lng"] for h in hotspots)

# Add 5% padding so markers don't touch the edge of the screen
lat_pad = (max_lat - min_lat) * 0.05
lng_pad = (max_lng - min_lng) * 0.05

MAP_BOUNDS = [
    [min_lat - lat_pad, min_lng - lng_pad],
    [max_lat + lat_pad, max_lng + lng_pad]
]

print(f"      df_clusters   : {len(df):,} rows")
print(f"      raw hotspots  : {len(raw_hotspots)} (contained overlaps)")
print(f"      clean hotspots: {len(hotspots)} (merged distinct zones)")

# ── MAP 1: DYNAMIC TIMELINE HEATMAP & TEMPORAL ZONES ────────────────────────
print("\n[2/4] Generating fully synchronized heatmap and zone slider...")

m1 = folium.Map(
    location=MAP_CENTER,
    zoom_start=MAP_ZOOM,
    tiles="CartoDB dark_matter",
)
# THE FIX: Force Map 1 to snap to the exact bounds of the clusters
m1.fit_bounds(MAP_BOUNDS)

monthly_features = []
monthly_heat_data = {}

for month in MONTH_ORDER:
    date_str = MONTH_DATES.get(month)
    month_df = df[df["month_name"] == month]
    
    if len(month_df) == 0:
        continue
        
    # 1. Prepare raw Heatmap data for this specific month
    sample_size = min(len(month_df), 1500)
    sampled_df = month_df.sample(n=sample_size, random_state=42)
    monthly_heat_data[date_str] = sampled_df[["latitude", "longitude", "impact_score"]].values.tolist()
    
    # 2. Prepare Dynamic GeoJSON Zones for this specific month
    for h in hotspots:
        station_name = h.get("police_station", h.get("top_station", "Unknown"))
        near_mask = (abs(month_df['latitude'] - h['centroid_lat']) < 0.015) & \
                    (abs(month_df['longitude'] - h['centroid_lng']) < 0.015)
        
        local_vol = near_mask.sum()
        
        if local_vol < 10:
            continue
    
        if local_vol >= 7000:
            priority, radius = "CRITICAL", 35
        elif local_vol >= 4000:
            priority, radius = "HIGH", 25
        elif local_vol >= 750:
            priority, radius = "MEDIUM", 15
        else:
            priority, radius = "LOW", 8
            
        color = PRIORITY_COLORS.get(priority, "#888")
        
        monthly_score = min(100.0, (local_vol / 400.0) * 100.0) if local_vol < 750 else min(100.0, (local_vol / 7000.0) * 100.0)
        
        popup_html = f"""
        <div style='font-family:sans-serif;width:220px;'>
          <div style='background:{color};color:#fff;padding:8px 12px;border-radius:6px 6px 0 0;'>
            <b style='font-size:14px;'>{station_name}</b><br>
            <span style='font-size:11px;opacity:.85;'>{month} — {priority}</span>
          </div>
          <div style='padding:10px 12px;background:#1a1a2e;color:#eee;border-radius:0 0 6px 6px;'>
            <table style='font-size:12px;width:100%;'>
              <tr><td style='color:#aaa;'>Zone Score</td><td style='text-align:right;'><b>{monthly_score:.1f}</b></td></tr>
              <tr><td style='color:#aaa;'>Violations</td><td style='text-align:right;'><b>{local_vol:,}</b></td></tr>
            </table>
          </div>
        </div>
        """
        
        monthly_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [h["centroid_lng"], h["centroid_lat"]]
            },
            "properties": {
                "time": date_str,
                "popup": popup_html,
                "icon": "circle",
                "iconstyle": {
                    "fillColor": color,
                    "fillOpacity": 0.4,
                    "stroke": True,
                    "color": color,
                    "weight": 2.5,
                    "radius": radius
                }
            }
        })

TimestampedGeoJson(
    {
        "type": "FeatureCollection",
        "features": monthly_features
    },
    transition_time=400,
    period="P1M",
    duration="P27D",
    add_last_point=False,
    auto_play=False,
    time_slider_drag_update=True
).add_to(m1)

hm = HeatMap(
    [], 
    radius=15, 
    blur=18, 
    max_zoom=14, 
    gradient={0.2: "#1a9850", 0.4: "#fee08b", 0.6: "#fd8d3c", 0.8: "#e24b4a", 1.0: "#800026"},
    min_opacity=0.15
).add_to(m1)

map_id = m1.get_name()
hm_id = hm.get_name()
heat_data_json = json.dumps(monthly_heat_data)

js_injection = f"""
<script>
document.addEventListener("DOMContentLoaded", function() {{
    setTimeout(function() {{
        var myMap = {map_id};
        var myHeatLayer = {hm_id};
        var rawHeatData = {heat_data_json};
        
        if (window.L && L.Control.TimeDimensionCustom) {{
            L.Control.TimeDimensionCustom.prototype._getDisplayDateFormat = function(date) {{
                var d = new Date(date);
                var monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
                return monthNames[d.getMonth()] + " " + d.getFullYear();
            }};
            
            L.Control.TimeDimensionCustom.prototype._updateSpeed = function() {{
                if (this._speedLabel) {{
                    this._speedLabel.innerHTML = this._timeDimension.getSpeed() + "x Speed";
                }}
            }};
        }}
        
        if (myMap.timeDimension) {{
            var ct = myMap.timeDimension.getCurrentTime();
            myMap.timeDimension.setCurrentTime(ct); 
            
            var speedLabels = document.querySelectorAll('.timecontrol-speed');
            speedLabels.forEach(function(lbl) {{
                lbl.innerHTML = lbl.innerHTML.replace('fps', 'x Speed').replace('fpsrate', 'x Speed');
            }});
        }}
        
        var firstKey = Object.keys(rawHeatData)[0];
        myHeatLayer.setLatLngs(rawHeatData[firstKey]);
        
        if (myMap.timeDimension) {{
            myMap.timeDimension.on('timeload', function(e) {{
                var sliderDate = new Date(e.time);
                var sMonth = sliderDate.getMonth();
                var sYear = sliderDate.getFullYear();
                
                for (var key in rawHeatData) {{
                    var dataDate = new Date(key);
                    if (dataDate.getMonth() === sMonth && dataDate.getFullYear() === sYear) {{
                        myHeatLayer.setLatLngs(rawHeatData[key]);
                        break;
                    }}
                }}
            }});
        }}
    }}, 800);
}});
</script>
"""
m1.get_root().html.add_child(folium.Element(js_injection))

for h in hotspots:
    station_name = h.get("police_station", h.get("top_station", "Unknown"))
    priority = h.get("priority", "LOW")
    color = PRIORITY_COLORS.get(priority, "#888")
    
    label_html = f"""
    <div style='
        font-family: "Arial Black", sans-serif;
        font-size: 11px;
        font-weight: 900;
        color: {color} !important;
        text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0px 0px 8px rgba(0,0,0,0.9);
        white-space: nowrap;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    '>{station_name}</div>
    """
    folium.Marker(
        location=[h["centroid_lat"], h["centroid_lng"]],
        icon=folium.DivIcon(html=label_html, icon_size=(150, 20), icon_anchor=(-15, 10)),
    ).add_to(m1)

title_html = """
<div style='position:absolute;top:12px;left:60px;z-index:1000;
     background:rgba(10,10,30,0.88);color:#fff;padding:10px 16px;
     border-radius:8px;border:1px solid rgba(255,255,255,0.15);
     font-family:sans-serif;'>
  <div style='font-size:15px;font-weight:600;'>ParkAlert Temporal Sync Map</div>
  <div style='font-size:11px;opacity:.7;margin-top:2px;'>
    Nov 2023 – Mar 2024 · Heatmap Density & Zones Shift Simultaneously
  </div>
</div>
"""
m1.get_root().html.add_child(folium.Element(title_html))

out1 = MAPS_DIR / "heatmap_live.html"
m1.save(str(out1))
print(f"      Saved: maps/heatmap_live.html")


# ── MAP 2: TACTICAL PATROL DISPATCH OVERVIEW ─────────────────────────────────
print("\n[3/4] Building Tactical Patrol Dispatch map...")

m2 = folium.Map(
    location=MAP_CENTER,
    zoom_start=MAP_ZOOM,
    tiles="CartoDB dark_matter", 
)
# THE FIX: Force Map 2 to snap to the exact same bounds as Map 1
m2.fit_bounds(MAP_BOUNDS)

all_points = df[["latitude", "longitude", "impact_score"]].values.tolist()

HeatMap(
    all_points,
    radius=12,
    max_zoom=14,
    gradient={0.2: "#1a9850", 0.5: "#fee08b", 0.75: "#fd8d3c", 1.0: "#e24b4a"},
    min_opacity=0.3,
).add_to(m2)

for h, p in zip(hotspots, patrols):
    station_name = h.get("police_station", h.get("top_station", "Unknown"))
    zone_score = h.get("zone_score", h.get("risk_score", 0))
    priority = h.get("priority", "LOW")
    color  = PRIORITY_COLORS.get(priority, "#888")
    
    radius = max(16, min(55, int(zone_score / 2.5)))

    windows_html = "".join([
        f"<tr><td style='padding:5px 0; border-bottom:1px solid rgba(255,255,255,0.1); color:#ccc; font-size:12px;'>⏱️ {w['label']}</td>"
        f"<td style='padding:5px 0; border-bottom:1px solid rgba(255,255,255,0.1); text-align:right; font-size:12px; color:#ffcc00; font-weight:bold;'>⚡ {w['impact']:,.0f}</td></tr>"
        for w in p.get("patrol_windows", [])
    ])

    popup_html = f"""
    <div style='font-family:sans-serif;width:270px; background:#12121e; color:#fff; border-radius:8px; overflow:hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.5); border: 1px solid {color}40;'>
      <div style='background:{color}; color:#fff; padding:12px 15px;'>
        <b style='font-size:15px; text-transform:uppercase; letter-spacing: 0.5px;'>{station_name}</b><br>
        <span style='font-size:11px; opacity:0.9; font-weight:800; letter-spacing: 1px;'>[ DISPATCH PRIORITY: {priority} ]</span>
      </div>
      <div style='padding:15px;'>
        <div style='font-size:10px; text-transform:uppercase; color:#888; letter-spacing:1px; margin-bottom:4px;'>Deployment Requirement</div>
        <div style='font-size:24px; font-weight:900; margin-bottom:15px; color:#fff;'>
          👮 {p.get('recommended_officers', 2)} Officers
        </div>
        <div style='font-size:10px; text-transform:uppercase; color:#888; letter-spacing:1px; margin-bottom:6px;'>Target Patrol Windows</div>
        <table style='width:100%; border-collapse:collapse; margin-bottom:15px;'>
          {windows_html}
        </table>
        <div style='background:#1f1f2e; padding:10px; border-radius:6px; font-size:11px; color:#aaa; text-align:center; border: 1px solid rgba(255,255,255,0.05);'>
          Peak Congestion Hour: <b style='color:#fff; font-size:12px;'>{h.get('peak_hour', 0):02d}:00</b><br>
          Zone Threat Score: <b style='color:{color}; font-size:12px;'>{zone_score:.1f}/100</b>
        </div>
      </div>
    </div>
    """

    folium.CircleMarker(
        location=[h["centroid_lat"], h["centroid_lng"]],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.35,
        weight=3,
        popup=folium.Popup(popup_html, max_width=320),
        tooltip=f"[{priority}] {station_name} — Click for Dispatch Plan",
    ).add_to(m2)

    label_html = f"""
    <div style='
        font-family: "Arial Black", sans-serif;
        font-size: 11px;
        font-weight: 900;
        color: {color} !important;
        text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0px 0px 8px rgba(0,0,0,0.9);
        white-space: nowrap;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    '>{station_name}</div>
    """
    folium.Marker(
        location=[h["centroid_lat"], h["centroid_lng"]],
        icon=folium.DivIcon(html=label_html, icon_size=(150, 20), icon_anchor=(0, 20)),
    ).add_to(m2)

title_html = """
<div style='position:absolute;top:15px;left:60px;z-index:1000;
     background:rgba(15,15,25,0.95);color:#fff;padding:12px 20px;
     border-radius:8px;border:1px solid rgba(255,255,255,0.1);
     font-family:sans-serif; box-shadow: 0 4px 12px rgba(0,0,0,0.5);'>
  <div style='font-size:16px;font-weight:800; letter-spacing:1px; color:#4a90e2;'>🚨 TACTICAL PATROL DASHBOARD</div>
  <div style='font-size:12px;opacity:.7;margin-top:4px;'>
    Targeted Deployment Map · Clean Overview
  </div>
</div>
"""
m2.get_root().html.add_child(folium.Element(title_html))

out2 = MAPS_DIR / "heatmap_clusters.html"
m2.save(str(out2))
print(f"      Saved: maps/heatmap_clusters.html")

print("\n[4/4] Done.")
print("\n" + "=" * 55)
print("  PHASE 3 COMPLETE")
print("=" * 55)