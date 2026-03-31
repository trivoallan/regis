/**
 * AnalyzerPage — Renders a single analyzer's results from report.results.
 * Used by each per-analyzer MDX page.
 */

import React from "react";
import { useReport } from "./ReportProvider";
import { AnalyzerSection } from "./AnalyzerSection";

interface AnalyzerPageProps {
  name: string;
}

export function AnalyzerPage({ name }: AnalyzerPageProps): React.JSX.Element {
  const { report, loading, error } = useReport();

  if (loading) return <p>Loading report data…</p>;
  if (error) return <div className="alert alert--danger">Error: {error}</div>;
  if (!report) return <p>No report data available.</p>;

  const data = (report.results ?? {})[name] as
    | Record<string, unknown>
    | undefined;

  if (!data) {
    return (
      <div className="alert alert--warning">
        This analyzer was not run for this report.
      </div>
    );
  }

  return (
    <div className="p-6">
      <AnalyzerSection name={name} data={data} />
    </div>
  );
}
