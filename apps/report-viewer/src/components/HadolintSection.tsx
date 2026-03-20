/**
 * HadolintSection — Displays Dockerfile linting results.
 */

import React from "react";

interface HadolintIssue {
  code: string;
  message: string;
  level: string;
  line?: number;
  column?: number;
  file?: string;
}

interface HadolintData {
  analyzer: string;
  repository: string;
  tag: string;
  passed: boolean;
  issues_count: number;
  issues_by_level?: Record<string, number>;
  issues?: HadolintIssue[];
  dockerfile?: string;
}

interface HadolintSectionProps {
  data: HadolintData;
}

const LEVEL_COLORS: Record<string, string> = {
  error: "#dc2626",
  warning: "#d97706",
  info: "#2563eb",
  style: "#6b7280",
};

export function HadolintSection({
  data,
}: HadolintSectionProps): React.JSX.Element {
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
            .filter(([, count]) => count > 0)
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
              <th>Line</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {data.issues.map((issue, i) => (
              <tr key={i}>
                <td>
                  <a
                    href={`https://github.com/hadolint/hadolint/wiki/${issue.code}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ fontFamily: "monospace" }}
                  >
                    {issue.code}
                  </a>
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
                <td style={{ fontFamily: "monospace" }}>{issue.line ?? "—"}</td>
                <td style={{ fontSize: "0.85rem" }}>{issue.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
