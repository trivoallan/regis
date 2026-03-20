/**
 * OverviewView — Renders the report overview page.
 *
 * Extracted from index.mdx to avoid MDX acorn parsing issues
 * with TypeScript ternary/optional chaining syntax.
 */

import React from "react";
import { useReport } from "./ReportProvider";
import { TierBadge } from "./TierBadge";
import { ScoreBadge, levelToVariant } from "./ScoreBadge";

export function OverviewView(): React.JSX.Element {
  const { report, loading, error } = useReport();

  if (loading) return <p>Loading report data…</p>;
  if (error) return <div className="alert alert--danger">Error: {error}</div>;
  if (!report) return <p>No report data available.</p>;

  const req = report.request ?? {};
  const pb =
    report.playbook ?? (report.playbooks ? report.playbooks[0] : undefined);
  const score = pb?.score ?? report.rules_summary?.score;
  const tier = report.tier ?? pb?.tier;
  const analyzers = req.analyzers ?? [];

  let scoreClass = "score-circle--low";
  if (score !== undefined) {
    if (score >= 80) scoreClass = "score-circle--high";
    else if (score >= 50) scoreClass = "score-circle--medium";
  }

  return (
    <div>
      <h1>
        {req.registry}/{req.repository}:{req.tag}
      </h1>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "1rem",
          flexWrap: "wrap",
          marginBottom: "1rem",
        }}
      >
        {tier && <TierBadge tier={tier} />}
        {report.badges?.map((b, i) => (
          <ScoreBadge
            key={i}
            label={b.label}
            variant={levelToVariant(b.class)}
          />
        ))}
      </div>

      {score !== undefined && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "1.5rem",
            marginBottom: "1.5rem",
          }}
        >
          <div className={`score-circle ${scoreClass}`}>{score}%</div>
          <div>
            <div style={{ fontSize: "0.85rem", opacity: 0.7 }}>
              Overall Score
            </div>
            <div style={{ fontSize: "0.85rem", opacity: 0.7 }}>
              {pb?.passed_scorecards ?? "?"}/{pb?.total_scorecards ?? "?"}{" "}
              scorecards passed
            </div>
          </div>
        </div>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "0.75rem",
          marginBottom: "1.5rem",
        }}
      >
        <div className="stat-card">
          <div className="stat-card__label">Registry</div>
          <div className="stat-card__value" style={{ fontSize: "1rem" }}>
            {req.registry ?? "unknown"}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Tag</div>
          <div className="stat-card__value" style={{ fontSize: "1rem" }}>
            {req.tag ?? "latest"}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Analyzers</div>
          <div className="stat-card__value" style={{ fontSize: "1rem" }}>
            {analyzers.length}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Timestamp</div>
          <div className="stat-card__value" style={{ fontSize: "0.85rem" }}>
            {req.timestamp ? new Date(req.timestamp).toLocaleString() : "N/A"}
          </div>
        </div>
      </div>

      {report.links && report.links.length > 0 && (
        <div className="report-links">
          {report.links.map((link, i) => (
            <a
              key={i}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              {link.label}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
