"""
Phase 3 — Heatmap Builder
Flipkart Gridlock 2.0 | Parking Intelligence System
Run: python backend/phase3_heatmap.py
Reads:  data/df_clusters.csv, data/hotspots.json, data/patrol_schedule.json
Writes: maps/heatmap_live.html, maps/heatmap_clusters.html
"""

import pandas as pd
import json
import folium
from folium.plugins import HeatMap, HeatMapWithTime
from pathlib import Path

# ── CONFIG ───────────────────────────────────────────────────────────────────
DATA_DIR = Path("../data")
MAPS_DIR = Path("../maps")
MAPS_DIR.mkdir(exist_ok=True)

# Bengaluru city centre
MAP_CENTER = [12.9716, 77.5946]
MAP_ZOOM   = 12

PRIORITY_COLORS = {
    "CRITICAL": "#E24B4A",
    "HIGH":     "#EF9F27",
    "MEDIUM":   "#639922",
    "LOW":      "#378ADD",
}

MONTH_ORDER = ["November", "December", "January", "February", "March"]

# ── LOAD ─────────────────────────────────────────────────────────────────────
print("=" * 55)
print("  PHASE 3 — HEATMAP BUILDER")
print("=" * 55)

print("\n[1/4] Loading Phase 2 outputs...")
df = pd.read_csv(DATA_DIR / "df_clusters.csv")

with open(DATA_DIR / "hotspots.json") as f:
    hotspots = json.load(f)

with open(DATA_DIR / "patrol_schedule.json") as f:
    patrol = json.load(f)

print(f"      df_clusters   : {len(df):,} rows")
print(f"      hotspots      : {len(hotspots)} clusters")
print(f"      patrol_sched  : {len(patrol)} entries")

# ── MAP 1: HeatMapWithTime (time-slider) ─────────────────────────────────────
print("\n[2/4] Building HeatMapWithTime (month-by-month slider)...")

m1 = folium.Map(
    location=MAP_CENTER,
    zoom_start=MAP_ZOOM,
    tiles="CartoDB dark_matter",
)

# Build one heatmap layer per month in order
heat_data = []
time_index = []

for month in MONTH_ORDER:
    month_df = df[df["month_name"] == month]
    if len(month_df) == 0:
        continue
    points = month_df[["latitude", "longitude", "impact_score"]].values.tolist()
    heat_data.append(points)
    time_index.append(month)
    print(f"      {month:<12}: {len(month_df):,} violations")

HeatMapWithTime(
    heat_data,
    index=time_index,
    auto_play=False,
    max_opacity=0.85,
    min_opacity=0.1,
    radius=14,
    gradient={0.2: "#1a9850", 0.4: "#fee08b", 0.6: "#fd8d3c", 0.8: "#e24b4a", 1.0: "#800026"},
    name="Violations by month",
).add_to(m1)

# Add cluster markers on top
for h in hotspots:
    color  = PRIORITY_COLORS.get(h["priority"], "#888")
    radius = max(10, min(40, int(h["risk_score"] / 4)))

    popup_html = f"""
    <div style='font-family:sans-serif;width:220px;'>
      <div style='background:{color};color:#fff;padding:8px 12px;border-radius:6px 6px 0 0;'>
        <b style='font-size:14px;'>{h['top_station']}</b><br>
        <span style='font-size:11px;opacity:.85;'>{h['priority']} — Score {h['risk_score']}/100</span>
      </div>
      <div style='padding:10px 12px;background:#1a1a2e;color:#eee;border-radius:0 0 6px 6px;'>
        <table style='font-size:12px;width:100%;'>
          <tr><td style='color:#aaa;'>Violations</td><td style='text-align:right;'><b>{h['total_violations']:,}</b></td></tr>
          <tr><td style='color:#aaa;'>Peak hour</td><td style='text-align:right;'><b>{h['peak_hour']:02d}:00</b></td></tr>
          <tr><td style='color:#aaa;'>Top vehicle</td><td style='text-align:right;'><b>{h['top_vehicle']}</b></td></tr>
          <tr><td style='color:#aaa;'>Top violation</td><td style='text-align:right;'><b>{h['top_violation'][:18]}</b></td></tr>
          <tr><td style='color:#aaa;'>Weekend %</td><td style='text-align:right;'><b>{h['weekend_pct']}%</b></td></tr>
        </table>
      </div>
    </div>
    """

    folium.CircleMarker(
        location=[h["centroid_lat"], h["centroid_lng"]],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.25,
        weight=2,
        popup=folium.Popup(popup_html, max_width=240),
        tooltip=f"{h['top_station']} | {h['priority']} | Score {h['risk_score']}",
    ).add_to(m1)

# Title overlay
title_html = """
<div style='position:absolute;top:12px;left:60px;z-index:1000;
     background:rgba(10,10,30,0.88);color:#fff;padding:10px 16px;
     border-radius:8px;border:1px solid rgba(255,255,255,0.15);
     font-family:sans-serif;'>
  <div style='font-size:15px;font-weight:600;'>ParkAlert — Bengaluru</div>
  <div style='font-size:11px;opacity:.7;margin-top:2px;'>
    115,400 violations · Nov 2023 – Mar 2024 · Use slider to explore by month
  </div>
</div>
"""
m1.get_root().html.add_child(folium.Element(title_html))

out1 = MAPS_DIR / "heatmap_live.html"
m1.save(str(out1))
print(f"      Saved: maps/heatmap_live.html")

# ── MAP 2: Cluster overview map ───────────────────────────────────────────────
print("\n[3/4] Building cluster overview map...")

m2 = folium.Map(
    location=MAP_CENTER,
    zoom_start=MAP_ZOOM,
    tiles="CartoDB positron",
)

# Full static heatmap background
all_points = df[["latitude", "longitude", "impact_score"]].values.tolist()
HeatMap(
    all_points,
    radius=12,
    max_zoom=14,
    max_val=df["impact_score"].max(),
    gradient={0.2: "#1a9850", 0.5: "#fee08b", 0.75: "#fd8d3c", 1.0: "#e24b4a"},
    min_opacity=0.3,
).add_to(m2)

# Cluster circles with patrol schedule popup
for h, p in zip(hotspots, patrol):
    color  = PRIORITY_COLORS.get(h["priority"], "#888")
    radius = max(14, min(50, int(h["risk_score"] / 3)))

    windows_html = "".join([
        f"<tr><td style='color:#555;font-size:11px;'>{w['label']}</td>"
        f"<td style='text-align:right;font-size:11px;'>{w['impact']:,.0f}</td></tr>"
        for w in p["patrol_windows"]
    ])

    popup_html = f"""
    <div style='font-family:sans-serif;width:240px;'>
      <div style='background:{color};color:#fff;padding:8px 12px;border-radius:6px 6px 0 0;'>
        <b style='font-size:14px;'>{h['top_station']}</b><br>
        <span style='font-size:11px;opacity:.85;'>{h['priority']} · Score {h['risk_score']}/100 · {h['total_violations']:,} violations</span>
      </div>
      <div style='padding:10px 12px;background:#fff;border-radius:0 0 6px 6px;'>
        <div style='font-size:11px;font-weight:600;color:#333;margin-bottom:6px;'>
          Recommended patrol windows
        </div>
        <table style='width:100%;'>
          <tr>
            <th style='font-size:10px;color:#888;text-align:left;'>Time window</th>
            <th style='font-size:10px;color:#888;text-align:right;'>Impact score</th>
          </tr>
          {windows_html}
        </table>
        <div style='margin-top:8px;padding-top:6px;border-top:1px solid #eee;font-size:11px;color:#555;'>
          Officers recommended: <b>{p['recommended_officers']}</b>
          &nbsp;|&nbsp; Peak hour: <b>{h['peak_hour']:02d}:00</b>
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
        fill_opacity=0.3,
        weight=2.5,
        popup=folium.Popup(popup_html, max_width=260),
        tooltip=f"[{h['priority']}] {h['top_station']} — click for patrol schedule",
    ).add_to(m2)

    # Label the cluster
    folium.Marker(
        location=[h["centroid_lat"], h["centroid_lng"]],
        icon=folium.DivIcon(
            html=f"""<div style='font-family:sans-serif;font-size:10px;font-weight:700;
                     color:{color};text-shadow:0 0 4px #fff,0 0 4px #fff;
                     white-space:nowrap;'>{h['top_station']}</div>""",
            icon_size=(120, 20),
            icon_anchor=(0, 20),
        ),
    ).add_to(m2)

# Legend
legend_html = """
<div style='position:absolute;bottom:30px;left:30px;z-index:1000;
     background:rgba(255,255,255,0.95);padding:12px 16px;
     border-radius:8px;border:1px solid #ddd;font-family:sans-serif;'>
  <div style='font-size:12px;font-weight:600;margin-bottom:8px;'>Priority level</div>
  <div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>
    <div style='width:12px;height:12px;border-radius:50%;background:#E24B4A;'></div>
    <span style='font-size:11px;'>Critical (&ge;70)</span>
  </div>
  <div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>
    <div style='width:12px;height:12px;border-radius:50%;background:#EF9F27;'></div>
    <span style='font-size:11px;'>High (40–69)</span>
  </div>
  <div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>
    <div style='width:12px;height:12px;border-radius:50%;background:#639922;'></div>
    <span style='font-size:11px;'>Medium (20–39)</span>
  </div>
  <div style='display:flex;align-items:center;gap:8px;'>
    <div style='width:12px;height:12px;border-radius:50%;background:#378ADD;'></div>
    <span style='font-size:11px;'>Low (&lt;20)</span>
  </div>
  <div style='margin-top:8px;padding-top:8px;border-top:1px solid #eee;
       font-size:10px;color:#888;'>Click any circle for patrol schedule</div>
</div>
"""
m2.get_root().html.add_child(folium.Element(legend_html))

out2 = MAPS_DIR / "heatmap_clusters.html"
m2.save(str(out2))
print(f"      Saved: maps/heatmap_clusters.html")

# ── FINAL REPORT ─────────────────────────────────────────────────────────────
print("\n[4/4] Done.")
print("\n" + "=" * 55)
print("  PHASE 3 COMPLETE")
print("=" * 55)
print(f"  heatmap_live.html     -> time-slider by month (demo wow)")
print(f"  heatmap_clusters.html -> cluster map + patrol popups")
print(f"\n  Open both files directly in any browser.")
print(f"  heatmap_live.html is your MAIN demo slide.")
print("=" * 55)
