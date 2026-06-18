import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

/**
 * Violations by hour of day — shows the twin morning/evening peaks.
 * Props: hourlyDistribution (object {hour: count} from /api/trends)
 */
export default function HourlyChart({ hourlyDistribution }) {
  if (!hourlyDistribution) return <div className="panel">Loading chart…</div>;

  const data = Array.from({ length: 24 }, (_, h) => ({
    hour: h,
    label: String(h).padStart(2, "0") + ":00",
    count: hourlyDistribution[h] ?? hourlyDistribution[String(h)] ?? 0,
  }));

  const maxCount = Math.max(...data.map((d) => d.count));

  const colorForHour = (h) => {
    if (h >= 7 && h <= 10) return "#E24B4A";   // morning rush
    if (h >= 17 && h <= 20) return "#EF9F27";  // evening rush
    if (h >= 11 && h <= 16) return "#639922";  // midday
    return "#378ADD";                          // off-peak
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>Violations by hour of day</h3>
        <div className="legend-inline">
          <span><i style={{ background: "#E24B4A" }} /> Morning rush</span>
          <span><i style={{ background: "#EF9F27" }} /> Evening rush</span>
          <span><i style={{ background: "#639922" }} /> Midday</span>
          <span><i style={{ background: "#378ADD" }} /> Off-peak</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.15)" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 10 }}
            interval={1}
            axisLine={{ stroke: "rgba(128,128,128,0.3)" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={36}
          />
          <Tooltip
            formatter={(value) => [value.toLocaleString(), "Violations"]}
            labelFormatter={(label) => `Hour: ${label}`}
            contentStyle={{ fontSize: 12, borderRadius: 8 }}
          />
          <Bar dataKey="count" radius={[3, 3, 0, 0]}>
            {data.map((entry, idx) => (
              <Cell key={idx} fill={colorForHour(entry.hour)} fillOpacity={entry.count === maxCount ? 1 : 0.75} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
