/**
 * ProvenanceSection — Displays supply chain evidence and signatures.
 */

import React from "react";

interface Indicator {
  name: string;
  status: "success" | "failure" | "warning";
  message: string;
}

interface ProvenanceData {
  analyzer: string;
  repository: string;
  tag: string;
  has_provenance: boolean;
  has_cosign_signature: boolean;
  source_tracked: boolean;
  indicators_count: number;
  indicators?: Indicator[];
}

interface ProvenanceSectionProps {
  data: ProvenanceData;
}

const STATUS_ICONS: Record<string, string> = {
  success: "✅",
  failure: "❌",
  warning: "⚠️",
};

const STATUS_CLASSES: Record<string, string> = {
  success: "alert--success",
  failure: "alert--danger",
  warning: "alert--warning",
};

export function ProvenanceSection({
  data,
}: ProvenanceSectionProps): React.JSX.Element {
  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: "0.75rem",
          marginBottom: "1.5rem",
        }}
      >
        <div className="stat-card">
          <div className="stat-card__label">SLSA Provenance</div>
          <div className="stat-card__value">
            {data.has_provenance ? "✅ Found" : "❌ Missing"}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Cosign Signature</div>
          <div className="stat-card__value">
            {data.has_cosign_signature ? "✅ Signed" : "❌ No"}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Source Tracked</div>
          <div className="stat-card__value">
            {data.source_tracked ? "✅ Yes" : "❌ No"}
          </div>
        </div>
      </div>

      {data.indicators && data.indicators.length > 0 && (
        <div
          style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}
        >
          {data.indicators.map((indicator, i) => (
            <div
              key={i}
              className={`alert ${STATUS_CLASSES[indicator.status]}`}
              style={{ padding: "0.5rem 1rem" }}
            >
              <strong>
                {STATUS_ICONS[indicator.status]} {indicator.name}
              </strong>
              : {indicator.message}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
