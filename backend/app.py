"""
Flask API — Parking Intelligence Dashboard
Flipkart Gridlock 2.0
Run: python backend/app.py
Serves data from data/summary.json, hotspots.json, patrol_schedule.json
"""

import json
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

import config

app = Flask(__name__)
CORS(app, origins=config.CORS_ORIGINS)


# ── HELPERS ──────────────────────────────────────────────────────────────────
def load_json(path):
    with open(path) as f:
        return json.load(f)


# ── ROOT / HEALTH ────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return jsonify({
        "status": "ok",
        "service": "ParkAlert API — Flipkart Gridlock 2.0",
        "endpoints": [
            "/api/summary",
            "/api/zones",
            "/api/hotspots",
            "/api/schedule",
            "/api/trends",
            "/api/violations",
        ]
    })


# ── /api/summary — top-level KPI cards ───────────────────────────────────────
@app.route("/api/summary")
def get_summary():
    """
    Returns overall KPIs: total violations, date range, cluster breakdown,
    top zone, peak hour, etc. Used for the 4 KPI cards on the dashboard.
    """
    try:
        summary = load_json(config.SUMMARY_FILE)
        return jsonify(summary)
    except FileNotFoundError:
        return jsonify({"error": "summary.json not found. Run Phase 1 & 2 first."}), 404


# ── /api/zones — ranked priority zone list (police-station level) ───────────
@app.route("/api/zones")
def get_zones():
    """
    Returns the police-station level aggregation (df_zones.csv) as JSON,
    optionally filtered by priority via ?priority=CRITICAL
    """
    try:
        df = pd.read_csv(config.ZONES_FILE)
        priority_filter = request.args.get("priority")
        if priority_filter:
            df = df[df["priority"].str.upper() == priority_filter.upper()]
        df = df.sort_values("zone_score", ascending=False)
        return jsonify(df.to_dict(orient="records"))
    except FileNotFoundError:
        return jsonify({"error": "df_zones.csv not found. Run Phase 1 first."}), 404


# ── /api/hotspots — K-Means cluster profiles ─────────────────────────────────
@app.route("/api/hotspots")
def get_hotspots():
    """
    Returns the 12 K-Means cluster profiles with risk scores, centroids,
    peak hours, top violation/vehicle types. Used to render map markers.
    """
    try:
        hotspots = load_json(config.HOTSPOTS_FILE)
        priority_filter = request.args.get("priority")
        if priority_filter:
            hotspots = [h for h in hotspots if h["priority"].upper() == priority_filter.upper()]
        return jsonify(hotspots)
    except FileNotFoundError:
        return jsonify({"error": "hotspots.json not found. Run Phase 2 first."}), 404


# ── /api/schedule — AI patrol schedule ───────────────────────────────────────
@app.route("/api/schedule")
def get_schedule():
    """
    Returns the AI-generated patrol schedule: time windows + recommended
    officer counts per cluster. Optionally filter by ?cluster_id=7
    """
    try:
        schedule = load_json(config.PATROL_SCHEDULE_FILE)
        cluster_id = request.args.get("cluster_id")
        if cluster_id is not None:
            schedule = [s for s in schedule if str(s["cluster_id"]) == str(cluster_id)]
        return jsonify(schedule)
    except FileNotFoundError:
        return jsonify({"error": "patrol_schedule.json not found. Run Phase 2 first."}), 404


# ── /api/trends — hourly / monthly / vehicle / violation breakdowns ─────────
@app.route("/api/trends")
def get_trends():
    """
    Returns chart-ready breakdowns: violations by hour, by month,
    by vehicle type, by violation type. Used for HourlyChart.jsx etc.
    """
    try:
        summary = load_json(config.SUMMARY_FILE)
        trends = {
            "hourly_distribution":   summary.get("hourly_distribution", {}),
            "monthly_trend":         summary.get("monthly_trend", {}),
            "vehicle_breakdown":     summary.get("vehicle_breakdown", {}),
            "violation_breakdown":   summary.get("violation_breakdown", {}),
            "time_bucket_dist":      summary.get("time_bucket_dist", {}),
        }
        return jsonify(trends)
    except FileNotFoundError:
        return jsonify({"error": "summary.json not found. Run Phase 1 first."}), 404


# ── /api/violations — raw filtered records (for advanced/debug use) ─────────
@app.route("/api/violations")
def get_violations():
    """
    Returns a paginated slice of raw clustered violations.
    Query params: ?cluster_id=7&limit=50&offset=0
    """
    try:
        df = pd.read_csv(config.CLUSTERS_FILE)

        cluster_id = request.args.get("cluster_id")
        if cluster_id is not None:
            df = df[df["cluster_id"] == int(cluster_id)]

        limit  = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        total = len(df)
        df_page = df.iloc[offset: offset + limit]

        return jsonify({
            "total":  total,
            "limit":  limit,
            "offset": offset,
            "data":   df_page.to_dict(orient="records"),
        })
    except FileNotFoundError:
        return jsonify({"error": "df_clusters.csv not found. Run Phase 2 first."}), 404


# ── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  ParkAlert API — Flipkart Gridlock 2.0")
    print("=" * 55)
    print(f"  Running on http://localhost:{config.API_PORT}")
    print(f"  CORS enabled for: {config.CORS_ORIGINS}")
    print("=" * 55)
    app.run(host=config.API_HOST, port=config.API_PORT, debug=config.DEBUG)
