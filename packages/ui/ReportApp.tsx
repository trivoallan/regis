import React from "react";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import { useReport } from "@regis-cli/ui";
import { ReportLayout } from "./layouts/ReportLayout";
import { PlaybookPage } from "./pages/PlaybookPage";
import { OverviewPage } from "./pages/OverviewPage";
import { LoadingScreen } from "./components/LoadingScreen";
import { ErrorScreen } from "./components/ErrorScreen";

export function ReportApp() {
  const { report, loading, error } = useReport({ kind: "window" });

  if (loading) return <LoadingScreen />;
  if (error || !report)
    return <ErrorScreen message={error ?? "No report data found."} />;

  // Pages du premier playbook, ou fallback sur une page Overview synthétique
  const playbook = report.playbook ?? report.playbooks?.[0];
  const pages = playbook?.pages ?? [];

  // Slug de la première page pour la redirection initiale
  const firstSlug =
    pages[0]?.slug ??
    pages[0]?.title.toLowerCase().replace(/\s+/g, "-") ??
    "overview";

  return (
    <HashRouter>
      <ReportLayout report={report} playbook={playbook ?? null}>
        <Routes>
          {/* Redirection racine → première page */}
          <Route path="/" element={<Navigate to={`/${firstSlug}`} replace />} />

          {/* Page synthétique des rules (toujours présente) */}
          <Route path="/overview" element={<OverviewPage report={report} />} />

          {/* Une route par page de playbook */}
          {pages.map((page) => {
            const slug =
              page.slug ?? page.title.toLowerCase().replace(/[^a-z0-9]+/g, "-");
            return (
              <Route
                key={slug}
                path={`/${slug}`}
                element={<PlaybookPage page={page} report={report} />}
              />
            );
          })}

          {/* Fallback */}
          <Route path="*" element={<Navigate to={`/${firstSlug}`} replace />} />
        </Routes>
      </ReportLayout>
    </HashRouter>
  );
}
