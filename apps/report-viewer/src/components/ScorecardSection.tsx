/**
 * ScorecardSection — Displays OpenSSF Scorecard results.
 */

import React from "react";

interface Check {
  name: string;
  score: number;
  reason: string;
  details?: string[];
}

interface ScorecardData {
  analyzer: string;
  repository: string;
  source_repo?: string;
  scorecard_available: boolean;
  score?: number;
  checks?: Check[];
}

interface ScorecardSectionProps {
  data: ScorecardData;
}

function getScoreColor(score: number): string {
  if (score >= 8) return "#22c55e";
  if (score >= 5) return "#d97706";
  return "#dc2626";
}

export function ScorecardSection({
  data,
}: ScorecardSectionProps): React.JSX.Element {
  if (!data.scorecard_available) {
    return (
      <div className="alert alert--info">
        OpenSSF Scorecard results not available for this repository.
      </div>
    );
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "2rem",
          marginBottom: "1.5rem",
        }}
      >
        <div
          className="score-circle"
          style={{
            background: getScoreColor(data.score ?? 0),
            width: "100px",
            height: "100px",
            fontSize: "2rem",
          }}
        >
          {data.score?.toFixed(1) ?? "N/A"}
        </div>
        <div>
          <h3 style={{ margin: 0 }}>OpenSSF Scorecard</h3>
          <p style={{ opacity: 0.6, margin: 0 }}>
            Source:{" "}
            <a
              href={data.source_repo}
              target="_blank"
              rel="noopener noreferrer"
            >
              {data.source_repo}
            </a>
          </p>
        </div>
      </div>

      {data.checks && data.checks.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Check</th>
              <th>Score</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {[...data.checks]
              .sort((a, b) => a.score - b.score)
              .map((check, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>{check.name}</td>
                  <td>
                    <span
                      style={{
                        color: getScoreColor(check.score),
                        fontWeight: 700,
                        fontSize: "1.1rem",
                      }}
                    >
                      {check.score === -1 ? "N/A" : check.score}
                    </span>
                  </td>
                  <td style={{ fontSize: "0.85rem" }}>{check.reason}</td>
                </tr>
              ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
