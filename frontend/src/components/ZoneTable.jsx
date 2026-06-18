import React, { useState } from "react";

/**
 * Ranked priority zone table — police-station level.
 * Props: zones (array from /api/zones), onSelectZone (callback)
 */
export default function ZoneTable({ zones, onSelectZone, selectedStation }) {
  const [filter, setFilter] = useState("ALL");

  if (!zones || zones.length === 0) return <div className="panel">Loading zones…</div>;

  const filtered = filter === "ALL" ? zones : zones.filter((z) => z.priority === filter);

  const priorityColor = {
    CRITICAL: "#E24B4A",
    HIGH: "#EF9F27",
    MEDIUM: "#639922",
    LOW: "#378ADD",
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>Priority zones</h3>
        <div className="filter-pills">
          {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((p) => (
            <button
              key={p}
              className={`pill-btn ${filter === p ? "active" : ""}`}
              onClick={() => setFilter(p)}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      <div className="zone-table">
        <div className="zone-table-head">
          <span>Station</span>
          <span>Score</span>
          <span>Violations</span>
          <span>Peak</span>
          <span>Top violation</span>
        </div>
        {filtered.map((z) => (
          <div
            key={z.police_station}
            className={`zone-table-row ${selectedStation === z.police_station ? "selected" : ""}`}
            onClick={() => onSelectZone && onSelectZone(z)}
          >
            <span className="zone-station">
              <span
                className="zone-dot"
                style={{ background: priorityColor[z.priority] || "#888" }}
              />
              {z.police_station}
            </span>
            <span className="zone-score">{z.zone_score?.toFixed(1)}</span>
            <span>{z.total_violations?.toLocaleString()}</span>
            <span>{String(z.peak_hour).padStart(2, "0")}:00</span>
            <span className="zone-violation">{z.top_violation}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
