/**
 * Docusaurus Root wrapper — wraps the entire app in ReportProvider.
 *
 * Supports a `?report=<url>` query parameter to load a report from an
 * arbitrary URL. Falls back to the default `report.json` served alongside
 * the site when the parameter is absent.
 *
 * @see https://docusaurus.io/docs/swizzling#wrapper-your-site-with-root
 */

import React, { useEffect } from "react";
import { ReportProvider, useReport } from "@site/src/components/ReportProvider";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import { useLocation, useHistory } from "@docusaurus/router";

interface RootProps {
  children: React.ReactNode;
}

/**
 * Inner component that can consume useReport() from the provider.
 */
function RootContent({
  children,
}: {
  children: React.ReactNode;
}): React.JSX.Element {
  const { search } = useLocation();
  const { error, loading } = useReport();
  const params = new URLSearchParams(search);
  const hasSpecificReport = params.has("url");

  // Redirection is no longer needed for the homepage as "/" is now the archive.
  // We only keep a fallback for explicit archive view requests if needed,
  // but since "/" is the archive, we can simplify.

  return <>{children}</>;
}

export default function Root({ children }: RootProps): React.JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  const { search } = useLocation();

  // 1. Determine the report URL to load
  // Order: 1. query param, 2. session storage, 3. default report.json
  const params = new URLSearchParams(search);
  const paramUrl = params.get("url");

  // On client side, read from sessionStorage if param is missing
  const [activeReportUrl, setActiveReportUrl] = React.useState<string | null>(
    null,
  );

  // 2. Handle archive URL persistence
  const paramArchiveUrl = params.get("archive_url");

  useEffect(() => {
    // Report persistence
    if (paramUrl) {
      sessionStorage.setItem("regis_active_url", paramUrl);
      setActiveReportUrl(paramUrl);
    } else {
      const savedReport = sessionStorage.getItem("regis_active_url");
      if (savedReport) setActiveReportUrl(savedReport);
    }

    // Archive persistence
    if (paramArchiveUrl) {
      sessionStorage.setItem("regis_active_archive_url", paramArchiveUrl);
    }
  }, [paramUrl, paramArchiveUrl]);

  const reportUrl =
    paramUrl || activeReportUrl || `${siteConfig.baseUrl}report.json`;

  return (
    <ReportProvider reportUrl={reportUrl}>
      <RootContent>{children}</RootContent>
    </ReportProvider>
  );
}
