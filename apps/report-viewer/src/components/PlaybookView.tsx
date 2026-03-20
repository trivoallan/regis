/**
 * PlaybookView — Renders all playbook pages with their sections.
 *
 * Extracted from playbook.mdx to avoid MDX acorn parsing issues
 * with TypeScript syntax (type assertions, complex generics).
 */

import React from "react";
import { useReport } from "./ReportProvider";
import { WidgetGrid } from "./WidgetGrid";
import { LevelsSummary } from "./LevelsSummary";
import { ScorecardTable } from "./ScorecardTable";
import { AnalyzerSection } from "./AnalyzerSection";
import { ErrorCard } from "./ErrorCard";
import type { PlaybookSection } from "./ReportProvider";

import { RequestTable } from "./RequestTable";

function getAnalyzerNameFromTemplate(template?: string): string | null {
  if (!template || !template.startsWith("analyzers/")) return null;
  const parts = template.split("/");
  return parts[1] || null;
}

function SectionBlock({
  block,
  section,
  results,
}: {
  block: string;
  section: PlaybookSection;
  results: Record<string, unknown>;
}) {
  switch (block) {
    case "widgets":
      if (!section.widgets) return null;

      // Extract unique analyzer names from widgets
      const analyzerNames = new Set<string>();
      const normalWidgets = section.widgets.filter((w) => {
        const analyzer = getAnalyzerNameFromTemplate(w.template);
        if (analyzer) {
          analyzerNames.add(analyzer);
          return false;
        }
        // Also handle the request table template
        if (w.template === "request/table.html") return false;
        return true;
      });

      const hasRequestTable = section.widgets.some(
        (w) => w.template === "request/table.html",
      );

      return (
        <>
          {normalWidgets.length > 0 && <WidgetGrid widgets={normalWidgets} />}
          {hasRequestTable && <RequestTable />}
          {Array.from(analyzerNames).map((name) => {
            const data = results[name];
            if (!data) return null;
            const record = data as Record<string, unknown>;
            if (record.error) {
              return (
                <ErrorCard
                  key={name}
                  analyzerName={name}
                  error={record.error as any}
                />
              );
            }
            return <AnalyzerSection key={name} name={name} data={record} />;
          })}
        </>
      );
    case "levels":
      return section.levels_summary ? (
        <LevelsSummary levels={section.levels_summary} />
      ) : null;
    case "tags":
      return section.tags_summary ? (
        <LevelsSummary levels={section.tags_summary} />
      ) : null;
    case "scorecards":
      return section.scorecards ? (
        <ScorecardTable
          scorecards={section.scorecards}
          showLevels={!!section.levels_summary}
        />
      ) : null;
    case "analyzers":
      return (
        <>
          {section.display?.analyzers?.map((analyzerName) => {
            const data = results[analyzerName];
            if (!data) return null;
            const record = data as Record<string, unknown>;
            if (record.error) {
              const err = record.error as { type?: string; message?: string };
              return (
                <ErrorCard
                  key={analyzerName}
                  analyzerName={analyzerName}
                  error={err}
                />
              );
            }
            return (
              <AnalyzerSection
                key={analyzerName}
                name={analyzerName}
                data={record}
              />
            );
          })}
        </>
      );
    default:
      return null;
  }
}

export function PlaybookView(): React.JSX.Element {
  const { report, loading, error } = useReport();

  if (loading) return <p>Loading report data…</p>;
  if (error) return <div className="alert alert--danger">Error: {error}</div>;
  if (!report) return <p>No report data available.</p>;

  const playbooks = report.playbooks ?? [];

  if (playbooks.length === 0) {
    return (
      <div className="alert alert--info">
        No playbooks were evaluated in this report.
      </div>
    );
  }

  const results = (report.results ?? {}) as Record<string, unknown>;

  return (
    <div>
      {playbooks.map((pb, pbIdx) => (
        <div key={pbIdx}>
          {pb.pages?.map((page, pageIdx) => (
            <div key={pageIdx}>
              {(pb.pages?.length ?? 0) > 1 && (
                <h3 style={{ color: "var(--ifm-color-primary)" }}>
                  {page.title}
                </h3>
              )}
              {page.sections?.map((section, secIdx) => (
                <div key={secIdx} style={{ marginBottom: "2rem" }}>
                  <h4>{section.name}</h4>
                  {section.hint && (
                    <p style={{ opacity: 0.7, fontStyle: "italic" }}>
                      {section.hint}
                    </p>
                  )}
                  {section.render_order?.map((block, blockIdx) => (
                    <SectionBlock
                      key={blockIdx}
                      block={block}
                      section={section}
                      results={results}
                    />
                  ))}
                </div>
              ))}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
