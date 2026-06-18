import React, { useState } from "react";

/**
 * Embeds the Folium-generated HTML maps via iframe.
 * Toggle between the time-slider heatmap and the cluster/patrol map.
 *
 * IMPORTANT: this assumes maps/heatmap_live.html and maps/heatmap_clusters.html
 * have been copied into frontend/public/maps/ so they're servable by
 * react-scripts' dev server. See README for the copy step.
 */
export default function MapEmbed() {
  const [activeMap, setActiveMap] = useState("live");

  const mapSrc =
    activeMap === "live" ? "/maps/heatmap_live.html" : "/maps/heatmap_clusters.html";

  return (
    <div className="panel map-panel">
      <div className="panel-header">
        <h3>Violation heatmap</h3>
        <div className="map-toggle">
          <button
            className={activeMap === "live" ? "active" : ""}
            onClick={() => setActiveMap("live")}
          >
            Time-slider view
          </button>
          <button
            className={activeMap === "clusters" ? "active" : ""}
            onClick={() => setActiveMap("clusters")}
          >
            Patrol cluster view
          </button>
        </div>
      </div>
      <iframe
        key={mapSrc}
        src={mapSrc}
        title="Parking violation heatmap"
        className="map-iframe"
        frameBorder="0"
      />
    </div>
  );
}
