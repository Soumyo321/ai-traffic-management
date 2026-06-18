import React from "react";

/**
 * Top KPI strip — 4 headline metrics.
 * Props: summary (object from /api/summary)
 */
export default function KpiCards({ summary }) {
  if (!summary) return null;

  const totalViolations = summary.total_violations?.toLocaleString() ?? "—";
  const criticalZones    = summary.clusters?.critical ?? "—";
  const highZones        = summary.clusters?.high ?? "—";
  const topZone          = summary.peak_stats?.worst_station ?? "—";
  const topZoneCount     = summary.peak_stats?.worst_station_count?.toLocaleString() ?? "—";
  const peakHour         = summary.peak_stats?.worst_hour;
  const peakHourLabel    = peakHour != null ? `${String(peakHour).padStart(2, "0")}:00` : "—";

  const cards = [
    {
      label: "Total violations",
      value: totalViolations,
      sub: `${summary.date_range?.start ?? ""} → ${summary.date_range?.end ?? ""}`,
      tone: "neutral",
    },
    {
      label: "Critical + high zones",
      value: `${criticalZones} / ${highZones}`,
      sub: "critical / high priority",
      tone: "danger",
    },
    {
      label: "Worst hotspot",
      value: topZone,
      sub: `${topZoneCount} violations recorded`,
      tone: "warning",
    },
    {
      label: "Citywide peak hour",
      value: peakHourLabel,
      sub: "highest violation density",
      tone: "info",
    },
  ];

  return (
    <div className="kpi-row">
      {cards.map((c) => (
        <div key={c.label} className={`kpi-card kpi-${c.tone}`}>
          <div className="kpi-label">{c.label}</div>
          <div className="kpi-value">{c.value}</div>
          <div className="kpi-sub">{c.sub}</div>
        </div>
      ))}
    </div>
  );
}
