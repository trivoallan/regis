/**
 * FreshnessCard — Shows image age and freshness information.
 */

import React from "react";

interface FreshnessData {
  analyzer: string;
  repository: string;
  tag: string;
  tag_created?: string;
  latest_created?: string | null;
  age_days?: number;
  behind_latest_days?: number | null;
  is_latest?: boolean;
}

interface FreshnessSectionProps {
  data: FreshnessData;
}

function AgeBadge({ days }: { days: number }) {
  let color = "#22c55e";
  let label = "Fresh";
  if (days > 180) {
    color = "#dc2626";
    label = "Stale";
  } else if (days > 90) {
    color = "#d97706";
    label = "Aging";
  } else if (days > 30) {
    color = "#2563eb";
    label = "OK";
  }

  return (
    <span
      style={{
        padding: "3px 10px",
        borderRadius: "12px",
        fontSize: "0.75rem",
        fontWeight: 700,
        color: "#fff",
        background: color,
      }}
    >
      {label}
    </span>
  );
}

export function FreshnessSection({
  data,
}: FreshnessSectionProps): React.JSX.Element {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        gap: "0.75rem",
      }}
    >
      <div className="stat-card">
        <div className="stat-card__label">Image Age</div>
        <div className="stat-card__value">
          {data.age_days ?? "?"}{" "}
          <span style={{ fontSize: "0.7em", opacity: 0.6 }}>days</span>
        </div>
        {data.age_days !== undefined && (
          <div style={{ marginTop: "0.25rem" }}>
            <AgeBadge days={data.age_days} />
          </div>
        )}
      </div>
      <div className="stat-card">
        <div className="stat-card__label">Is Latest</div>
        <div className="stat-card__value">
          {data.is_latest ? "✅ Yes" : "❌ No"}
        </div>
      </div>
      <div className="stat-card">
        <div className="stat-card__label">Behind Latest</div>
        <div className="stat-card__value">
          {data.behind_latest_days != null
            ? `${data.behind_latest_days} days`
            : "N/A"}
        </div>
      </div>
      <div className="stat-card">
        <div className="stat-card__label">Created</div>
        <div className="stat-card__value" style={{ fontSize: "0.85rem" }}>
          {data.tag_created
            ? new Date(data.tag_created).toLocaleDateString()
            : "N/A"}
        </div>
      </div>
    </div>
  );
}
