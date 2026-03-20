/**
 * DockleSection — Displays container image linting results for security.
 */

import React from "react";

interface DockleIssue {
  code: string;
  level: string;
  title: string;
  alerts: string[];
}

interface DockleData {
  analyzer: string;
  repository: string;
  tag: string;
  passed: boolean;
  issues_count: number;
  issues_by_level: Record<string, number>;
  issues: DockleIssue[];
}

interface DockleSectionProps {
  data: DockleData;
}

const LEVEL_COLORS: Record<string, string> = {
  FATAL: "#dc2626",
  WARN: "#d97706",
  INFO: "#2563eb",
  SKIP: "#6b7280",
  PASS: "#22c55e",
};

export function DockleSection({ data }: DockleSectionProps): React.JSX.Element {
  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          gap: "0.75rem",
          marginBottom: "1rem",
        }}
      >
        <div className="stat-card">
          <div className="stat-card__label">Status</div>
          <div className="stat-card__value">
            {data.passed ? "✅ Passed" : "⚠️ Issues"}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Issues</div>
          <div className="stat-card__value">{data.issues_count}</div>
        </div>
        {data.issues_by_level &&
          Object.entries(data.issues_by_level)
            .filter(
              ([level, count]) =>
                count > 0 && level !== "PASS" && level !== "SKIP",
            )
            .map(([level, count]) => (
              <div className="stat-card" key={level}>
                <div className="stat-card__label">{level}</div>
                <div
                  className="stat-card__value"
                  style={{ color: LEVEL_COLORS[level] ?? "inherit" }}
                >
                  {count}
                </div>
              </div>
            ))}
      </div>

      {data.issues && data.issues.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Level</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {data.issues
              .filter((i) => i.level !== "PASS" && i.level !== "SKIP")
              .map((issue, i) => (
                <tr key={i}>
                  <td
                    style={{
                      fontFamily: "monospace",
                      fontSize: "0.85rem",
                      fontWeight: 600,
                    }}
                  >
                    {issue.code}
                  </td>
                  <td>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: "4px",
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        color: "#fff",
                        background: LEVEL_COLORS[issue.level] ?? "#6b7280",
                      }}
                    >
                      {issue.level}
                    </span>
                  </td>
                  <td>
                    <div style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                      {issue.title}
                    </div>
                    {issue.alerts && issue.alerts.length > 0 && (
                      <ul
                        style={{
                          fontSize: "0.8rem",
                          marginTop: "0.4rem",
                          opacity: 0.8,
                        }}
                      >
                        {issue.alerts.map((alert, j) => (
                          <li key={j}>{alert}</li>
                        ))}
                      </ul>
                    )}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
