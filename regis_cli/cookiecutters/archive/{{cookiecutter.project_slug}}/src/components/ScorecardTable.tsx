/**
 * ScorecardTable — Displays pass/fail scorecards from a playbook section.
 */

import React from "react";
import { ScoreBadge, levelToVariant } from "./ScoreBadge";
import type { Scorecard } from "./ReportProvider";

interface ScorecardTableProps {
  scorecards: Scorecard[];
  showLevels?: boolean;
}

export function ScorecardTable({
  scorecards,
  showLevels = true,
}: ScorecardTableProps): React.JSX.Element {
  return (
    <div style={{ overflowX: "auto" }}>
      <table>
        <thead>
          <tr>
            <th>Status</th>
            {showLevels && <th>Level</th>}
            <th>Scorecard</th>
            <th>Analyzers</th>
          </tr>
        </thead>
        <tbody>
          {scorecards.map((sc, i) => (
            <tr key={i}>
              <td style={{ textAlign: "center" }}>
                {sc.passed ? (
                  <span title="Passed">✅</span>
                ) : (
                  <span title="Failed">❌</span>
                )}
              </td>
              {showLevels && (
                <td>
                  <ScoreBadge
                    label={sc.level ?? "info"}
                    variant={levelToVariant(sc.level ?? "info")}
                  />
                </td>
              )}
              <td>
                <strong>{sc.title}</strong>
                {sc.tags && sc.tags.length > 0 && (
                  <div
                    style={{
                      marginTop: "0.2rem",
                      display: "flex",
                      gap: "0.25rem",
                      flexWrap: "wrap",
                    }}
                  >
                    {sc.tags.map((tag) => (
                      <ScoreBadge key={tag} label={tag} />
                    ))}
                  </div>
                )}
                {sc.details && (
                  <div
                    style={{
                      fontSize: "0.8rem",
                      opacity: 0.7,
                      marginTop: "0.3rem",
                    }}
                  >
                    {sc.details}
                  </div>
                )}
              </td>
              <td>
                <div
                  style={{ display: "flex", gap: "0.25rem", flexWrap: "wrap" }}
                >
                  {sc.analyzers?.map((a) => (
                    <ScoreBadge key={a} label={a} variant="outline" />
                  ))}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
