/**
 * Docusaurus Root wrapper — wraps the entire app in ReportProvider.
 *
 * Supports a `?report=<url>` query parameter to load a report from an
 * arbitrary URL. Falls back to the default `report.json` served alongside
 * the site when the parameter is absent.
 *
 * @see https://docusaurus.io/docs/swizzling#wrapper-your-site-with-root
 */

import React from "react";
import { ReportProvider } from "@site/src/components/ReportProvider";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import { useLocation } from "@docusaurus/router";

interface RootProps {
  children: React.ReactNode;
}

export default function Root({ children }: RootProps): React.JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  const { search } = useLocation();

  const reportUrl =
    new URLSearchParams(search).get("report") ??
    `${siteConfig.baseUrl}report.json`;

  return <ReportProvider reportUrl={reportUrl}>{children}</ReportProvider>;
}
