/**
 * PopularitySection — Displays image popularity metrics (stars, pulls).
 */

import React from "react";

interface PopularityData {
  analyzer: string;
  repository: string;
  available: boolean;
  pull_count?: number;
  star_count?: number;
  description?: string;
  last_updated?: string;
  date_registered?: string;
}

interface PopularitySectionProps {
  data: PopularityData;
}

function formatNumber(num?: number): string {
  if (num === undefined) return "N/A";
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toString();
}

export function PopularitySection({
  data,
}: PopularitySectionProps): React.JSX.Element {
  if (!data.available) {
    return (
      <div className="alert alert--info">
        Popularity metrics not available for this registry/repository.
      </div>
    );
  }

  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: "0.75rem",
          marginBottom: "1rem",
        }}
      >
        <div className="stat-card">
          <div className="stat-card__label">Pulls</div>
          <div className="stat-card__value">
            {formatNumber(data.pull_count)}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Stars</div>
          <div className="stat-card__value">
            {formatNumber(data.star_count)}
          </div>
        </div>
      </div>

      {data.description && (
        <div
          style={{
            marginTop: "1rem",
            fontSize: "0.9rem",
            color: "var(--ifm-color-emphasis-700)",
          }}
        >
          <strong>Description:</strong> {data.description}
        </div>
      )}

      <div style={{ marginTop: "0.5rem", fontSize: "0.8rem", opacity: 0.6 }}>
        {data.last_updated &&
          `Last Updated: ${new Date(data.last_updated).toLocaleDateString()}`}
        {data.date_registered &&
          ` | Registered: ${new Date(data.date_registered).toLocaleDateString()}`}
      </div>
    </div>
  );
}
