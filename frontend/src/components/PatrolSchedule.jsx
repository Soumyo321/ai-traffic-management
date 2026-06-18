import React from "react";

/**
 * AI-generated patrol schedule for a selected cluster.
 * Props: schedule (array from /api/schedule), selectedClusterId
 */
export default function PatrolSchedule({ schedule, selectedClusterId }) {
  if (!schedule || schedule.length === 0) {
    return (
      <div className="panel">
        <h3>Patrol schedule</h3>
        <p className="empty-state">Select a zone to see its recommended patrol windows.</p>
      </div>
    );
  }

  // If a specific cluster is selected, show only that one; else show top 3
  const toShow =
    selectedClusterId != null
      ? schedule.filter((s) => s.cluster_id === selectedClusterId)
      : schedule.slice(0, 3);

  return (
    <div className="panel">
      <h3>AI patrol schedule</h3>
      {toShow.map((s) => (
        <div key={s.cluster_id} className="patrol-block">
          <div className="patrol-block-header">
            <span className="patrol-station">{s.top_station}</span>
            <span className={`patrol-priority p-${s.priority?.toLowerCase()}`}>
              {s.priority}
            </span>
          </div>
          <div className="patrol-meta">
            Recommended officers: <b>{s.recommended_officers}</b> &nbsp;·&nbsp; Risk score:{" "}
            <b>{s.risk_score}</b>
          </div>
          <div className="patrol-windows">
            {s.patrol_windows?.map((w, i) => (
              <div key={i} className="patrol-window-row">
                <span className="patrol-time">{w.label}</span>
                <div className="patrol-bar-bg">
                  <div
                    className="patrol-bar-fg"
                    style={{
                      width: `${Math.min(
                        100,
                        (w.impact / s.patrol_windows[0].impact) * 100
                      )}%`,
                    }}
                  />
                </div>
                <span className="patrol-impact">{Math.round(w.impact).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
