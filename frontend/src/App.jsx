import React, { useEffect, useState } from "react";
import { api } from "./api";
import KpiCards from "./components/KpiCards";
import ZoneTable from "./components/ZoneTable";
import PatrolSchedule from "./components/PatrolSchedule";
import HourlyChart from "./components/HourlyChart";
import MapEmbed from "./components/MapEmbed";
import "./App.css";

export default function App() {
  const [summary, setSummary]     = useState(null);
  const [zones, setZones]         = useState([]);
  const [schedule, setSchedule]   = useState([]);
  const [trends, setTrends]       = useState(null);
  const [selectedZone, setSelectedZone] = useState(null);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);

  useEffect(() => {
    async function loadAll() {
      try {
        const [summaryData, zonesData, scheduleData, trendsData] = await Promise.all([
          api.getSummary(),
          api.getZones(),
          api.getSchedule(),
          api.getTrends(),
        ]);
        setSummary(summaryData);
        setZones(zonesData);
        setSchedule(scheduleData);
        setTrends(trendsData);
      } catch (err) {
        console.error(err);
        setError("Could not reach the API. Is Flask running on port 5000?");
      } finally {
        setLoading(false);
      }
    }
    loadAll();
  }, []);

  // Find the matching cluster_id for the selected police station, if any
  // const selectedClusterId =
  //   (selectedZone &&
  //     schedule.find((s) => s.top_station === selectedZone.police_station)?.cluster_id) ??
  //   null;
  const matchingClusters = selectedZone
    ? schedule.filter((s) => s.top_station === selectedZone.police_station)
    : [];
const selectedClusterId =
    matchingClusters.length > 0
      ? matchingClusters.sort((a, b) => b.risk_score - a.risk_score)[0].cluster_id
      : null;
  if (error) {
    return (
      <div className="app-shell">
        <div className="error-banner">
          {error}
          <div className="error-sub">Run: python backend/app.py</div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>ParkAlert</h1>
          <p>AI-driven parking intelligence — Flipkart Gridlock 2.0</p>
        </div>
        <div className="app-header-meta">
          {summary && (
            <span>
              Data: {summary.date_range?.start} → {summary.date_range?.end}
            </span>
          )}
        </div>
      </header>

      {loading ? (
        <div className="loading-state">Loading dashboard…</div>
      ) : (
        <main className="app-main">
          <KpiCards summary={summary} />

          <div className="main-grid">
            <MapEmbed />
            <div className="side-stack">
              <PatrolSchedule schedule={schedule} selectedClusterId={selectedClusterId} />
            </div>
          </div>

          <div className="bottom-grid">
            <ZoneTable
              zones={zones}
              onSelectZone={setSelectedZone}
              selectedStation={selectedZone?.police_station}
            />
            <HourlyChart hourlyDistribution={trends?.hourly_distribution} />
          </div>
        </main>
      )}
    </div>
  );
}