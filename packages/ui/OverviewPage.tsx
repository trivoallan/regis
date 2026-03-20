import React from "react";
import type { Report } from "@regis-cli/ui";
import { RulesTable, hasAnalyzerError } from "@regis-cli/ui";

interface OverviewPageProps {
  report: Report;
}

export function OverviewPage({ report }: OverviewPageProps) {
  const rules = report.rules ?? report.playbook?.rules ?? [];
  const summary = report.rules_summary ?? report.playbook?.rules_summary;

  // Erreurs d'analyzers à afficher en bas de page
  const analyzerErrors = Object.entries(report.results).filter(([, result]) =>
    hasAnalyzerError(result),
  ) as [string, { error: { type: string; message: string } }][];

  return (
    <div>
      <header style={{ marginBottom: "2rem" }}>
        <h1 style={h1Style}>
          {report.request.registry}/{report.request.repository}:
          {report.request.tag}
        </h1>
        {report.request.digest && (
          <div
            style={{
              fontSize: "0.78rem",
              opacity: 0.45,
              fontFamily: "monospace",
              marginTop: "0.25rem",
            }}
          >
            {report.request.digest}
          </div>
        )}
      </header>

      {/* Rules */}
      {rules.length > 0 ? (
        <section className="regis-section">
          <h2 style={h2Style}>Rules evaluation</h2>
          <RulesTable rules={rules} summary={summary} showTagSummary />
        </section>
      ) : (
        <div style={{ opacity: 0.5, fontStyle: "italic" }}>
          No rules found in this report.
        </div>
      )}

      {/* Analyzer errors */}
      {analyzerErrors.length > 0 && (
        <section style={{ marginTop: "2rem" }}>
          <h2 style={h2Style}>Analyzer errors</h2>
          {analyzerErrors.map(([name, result]) => (
            <div key={name} className="regis-analyzer-error">
              <strong style={{ fontFamily: "monospace" }}>{name}</strong>
              <span
                style={{
                  opacity: 0.6,
                  marginLeft: "0.5rem",
                  fontSize: "0.8rem",
                }}
              >
                {result.error.type}
              </span>
              <div
                style={{
                  marginTop: "0.35rem",
                  fontSize: "0.82rem",
                  opacity: 0.85,
                }}
              >
                {result.error.message}
              </div>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}

const h1Style: React.CSSProperties = {
  fontSize: "1.1rem",
  fontWeight: 600,
  margin: 0,
  lineHeight: 1.3,
};

const h2Style: React.CSSProperties = {
  fontSize: "1rem",
  fontWeight: 600,
  marginBottom: "1rem",
  marginTop: 0,
};
