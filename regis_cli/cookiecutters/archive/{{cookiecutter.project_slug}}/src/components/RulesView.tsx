/**
 * RulesView — Wraps RulesTable with data loading from ReportProvider.
 */

import React from "react";
import { useReport } from "./ReportProvider";
import { RulesTable } from "./RulesTable";

export function RulesView(): React.JSX.Element {
  const { report, loading, error } = useReport();

  if (loading) return <p>Loading report data…</p>;
  if (error) return <div className="alert alert--danger">Error: {error}</div>;
  if (!report) return <p>No report data available.</p>;

  const rules = report.rules ?? report.playbook?.rules ?? [];
  const summary = report.rules_summary ?? report.playbook?.rules_summary;

  if (rules.length === 0) {
    return (
      <div className="alert alert--info">
        No rules were evaluated in this report.
      </div>
    );
  }

  return <RulesTable rules={rules} summary={summary} />;
}
