/**
 * RulesTable — Filterable rules evaluation table with tag summary cards.
 *
 * Mirrors the Jinja2 rules.html template: tag cards at top, then a filterable
 * table with status, level, rule info, and tags.
 */

import React, { useState } from "react";
import { ScoreBadge, levelToVariant } from "./ScoreBadge";
import type { RuleResult, RulesSummary } from "./ReportProvider";

interface RulesTableProps {
  rules: RuleResult[];
  summary?: RulesSummary;
}

function StatusIcon({ passed, status }: { passed: boolean; status?: string }) {
  if (status === "incomplete") return <span title="Incomplete">⚠️</span>;
  return passed ? (
    <span title="Passed">✅</span>
  ) : (
    <span title="Failed">❌</span>
  );
}

export function RulesTable({
  rules,
  summary,
}: RulesTableProps): React.JSX.Element {
  const [activeTag, setActiveTag] = useState<string>("all");

  const filteredRules =
    activeTag === "all"
      ? rules
      : rules.filter((r) => r.tags?.includes(activeTag));

  const tagStats = summary?.by_tag ?? {};

  return (
    <div>
      {/* Tag summary cards */}
      {Object.keys(tagStats).length > 0 && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
            gap: "0.75rem",
            marginBottom: "1.5rem",
          }}
        >
          {Object.entries(tagStats)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([tag, stats]) => (
              <button
                type="button"
                key={tag}
                onClick={() => setActiveTag(activeTag === tag ? "all" : tag)}
                style={{
                  cursor: "pointer",
                  padding: "0.75rem",
                  textAlign: "center",
                  background: "var(--ifm-card-background-color)",
                  border:
                    activeTag === tag
                      ? "2px solid var(--ifm-color-primary)"
                      : "1px solid var(--ifm-color-emphasis-200)",
                  borderRadius: "8px",
                  transform: activeTag === tag ? "scale(1.03)" : "scale(1)",
                  transition: "all 0.2s ease",
                }}
              >
                <small
                  style={{
                    textTransform: "uppercase",
                    fontWeight: 700,
                    letterSpacing: "0.05em",
                    opacity: 0.8,
                  }}
                >
                  {tag}
                </small>
                <br />
                <span style={{ fontSize: "1.5rem", fontWeight: 700 }}>
                  {stats.score}%
                </span>
                <br />
                <small style={{ opacity: 0.6 }}>
                  {stats.passed_rules.length} / {stats.rules.length} passed
                </small>
              </button>
            ))}
        </div>
      )}

      {/* Filter controls */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "0.75rem",
        }}
      >
        <h4 style={{ margin: 0 }}>Detailed Results</h4>
        <select
          value={activeTag}
          onChange={(e) => setActiveTag(e.target.value)}
          style={{
            padding: "0.3rem 0.5rem",
            borderRadius: "4px",
            border: "1px solid var(--ifm-color-emphasis-300)",
            background: "var(--ifm-background-color)",
            color: "var(--ifm-font-color-base)",
          }}
        >
          <option value="all">All Tags</option>
          {Object.keys(tagStats)
            .sort()
            .map((tag) => (
              <option key={tag} value={tag}>
                {tag}
              </option>
            ))}
        </select>
      </div>

      {/* Rules table */}
      <div style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Status</th>
              <th>Level</th>
              <th>Rule</th>
              <th>Tags</th>
            </tr>
          </thead>
          <tbody>
            {filteredRules.map((r, i) => (
              <tr key={r.slug ?? i}>
                <td style={{ textAlign: "center" }}>
                  <StatusIcon passed={r.passed} status={r.status} />
                </td>
                <td>
                  <ScoreBadge
                    label={r.level}
                    variant={levelToVariant(r.level)}
                  />
                </td>
                <td>
                  <strong>{r.description ?? r.title ?? r.slug}</strong>
                  {r.message && (
                    <div
                      style={{
                        fontSize: "0.85rem",
                        opacity: 0.8,
                        marginTop: "0.2rem",
                      }}
                    >
                      {r.message}
                    </div>
                  )}
                  {r.analyzers && r.analyzers.length > 0 && (
                    <div style={{ marginTop: "0.3rem" }}>
                      {r.analyzers.map((a) => (
                        <ScoreBadge key={a} label={a} variant="outline" />
                      ))}
                    </div>
                  )}
                </td>
                <td>
                  <div
                    style={{
                      display: "flex",
                      gap: "0.25rem",
                      flexWrap: "wrap",
                    }}
                  >
                    {r.tags?.map((tag) => (
                      <ScoreBadge key={tag} label={tag} />
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
