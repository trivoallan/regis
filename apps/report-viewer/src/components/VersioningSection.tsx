/**
 * VersioningSection — Displays image tagging patterns and variants.
 */

import React from "react";

interface TagPattern {
  pattern: string;
  count: number;
  percentage: number;
  examples: string[];
}

interface VersioningData {
  analyzer: string;
  repository: string;
  total_tags: number;
  dominant_pattern?: string;
  semver_compliant_percentage?: number;
  patterns?: TagPattern[];
  variants?: string[];
  release_lines?: string[];
}

interface VersioningSectionProps {
  data: VersioningData;
}

export function VersioningSection({
  data,
}: VersioningSectionProps): React.JSX.Element {
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
          <div className="stat-card__label">Total Tags</div>
          <div className="stat-card__value">{data.total_tags}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">SemVer Compliance</div>
          <div className="stat-card__value">
            {data.semver_compliant_percentage?.toFixed(1)}%
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Dominant Pattern</div>
          <div
            className="stat-card__value"
            style={{
              fontSize: "1rem",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            <code>{data.dominant_pattern || "N/A"}</code>
          </div>
        </div>
      </div>

      <div
        style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}
      >
        {data.patterns && (
          <div>
            <h5>Tag Patterns</h5>
            <ul style={{ fontSize: "0.9rem" }}>
              {data.patterns.map((p) => (
                <li key={p.pattern}>
                  <code>{p.pattern}</code>: <strong>{p.count}</strong>{" "}
                  <span style={{ opacity: 0.5 }}>
                    ({p.percentage.toFixed(1)}%)
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {data.variants && data.variants.length > 0 && (
          <div>
            <h5>Detected Variants</h5>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
              {data.variants.map((v) => (
                <span
                  key={v}
                  style={{
                    padding: "2px 8px",
                    background: "var(--ifm-color-emphasis-200)",
                    borderRadius: "4px",
                    fontSize: "0.8rem",
                  }}
                >
                  {v}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
