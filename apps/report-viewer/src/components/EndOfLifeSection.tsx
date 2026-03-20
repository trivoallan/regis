/**
 * EndOfLifeSection — Displays software lifecycle status.
 */

import React from "react";

interface EndOfLifeData {
  analyzer: string;
  repository: string;
  product: string;
  product_found: boolean;
  tag: string;
  matched_cycle?: string | null;
  is_eol?: boolean | null;
  active_cycles_count: number;
  eol_cycles_count: number;
}

interface EndOfLifeSectionProps {
  data: EndOfLifeData;
}

export function EndOfLifeSection({
  data,
}: EndOfLifeSectionProps): React.JSX.Element {
  if (!data.product_found) {
    return (
      <div className="alert alert--warning">
        Product <strong>{data.product}</strong> not found in endoflife.date
        database.
      </div>
    );
  }

  const isEol = data.is_eol;
  const statusColor = isEol
    ? "#dc2626"
    : isEol === false
      ? "#22c55e"
      : "#6b7280";
  const statusLabel = isEol
    ? "End of Life"
    : isEol === false
      ? "Supported"
      : "Unknown Status";

  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "0.75rem",
          marginBottom: "1rem",
        }}
      >
        <div className="stat-card">
          <div className="stat-card__label">Product</div>
          <div
            className="stat-card__value"
            style={{ textTransform: "capitalize" }}
          >
            {data.product}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Cycle</div>
          <div className="stat-card__value">{data.matched_cycle || "N/A"}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Status</div>
          <div
            className="stat-card__value"
            style={{
              color: statusColor,
              fontSize: "1.2rem",
              paddingTop: "0.5rem",
            }}
          >
            {statusLabel}
          </div>
        </div>
      </div>

      <div className="alert alert--secondary">
        This product has <strong>{data.active_cycles_count}</strong> active
        cycles and <strong>{data.eol_cycles_count}</strong> cycles that have
        reached end-of-life.
      </div>
    </div>
  );
}
