/**
 * LevelsSummary — Displays level stat cards (Gold/Silver/Bronze/None).
 */

import React from "react";

const LEVEL_ICONS: Record<string, string> = {
  bronze: "🥉",
  silver: "🥈",
  gold: "🥇",
  none: "⭕",
};

interface LevelsSummaryProps {
  levels: Record<string, { passed: number; total: number; percentage: number }>;
}

export function LevelsSummary({
  levels,
}: LevelsSummaryProps): React.JSX.Element {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
        gap: "0.75rem",
        marginBottom: "1.5rem",
      }}
    >
      {Object.entries(levels).map(([name, stats]) => (
        <div
          key={name}
          style={{
            textAlign: "center",
            padding: "0.75rem",
            background: "var(--ifm-card-background-color)",
            borderRadius: "8px",
            border: "1px solid var(--ifm-color-emphasis-200)",
          }}
        >
          <strong
            style={{
              fontSize: "0.75rem",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              opacity: 0.8,
            }}
          >
            {LEVEL_ICONS[name] ?? ""} {name}
          </strong>
          <br />
          <span
            style={{ fontSize: "1.6rem", fontWeight: 700, lineHeight: 1.2 }}
          >
            {stats.passed}
            <small style={{ fontSize: "0.9rem", opacity: 0.5 }}>
              /{stats.total}
            </small>
          </span>
          <div
            style={{ fontSize: "0.75rem", marginTop: "0.2rem", opacity: 0.6 }}
          >
            {stats.percentage}% pass
          </div>
        </div>
      ))}
    </div>
  );
}
