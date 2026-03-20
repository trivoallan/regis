/**
 * Docusaurus Root wrapper — wraps the entire app in ReportProvider.
 *
 * @see https://docusaurus.io/docs/swizzling#wrapper-your-site-with-root
 */

import React from "react";
import { ReportProvider } from "@site/src/components/ReportProvider";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";

interface RootProps {
  children: React.ReactNode;
}

export default function Root({ children }: RootProps): React.JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  const reportUrl = `${siteConfig.baseUrl}report.json`;

  return <ReportProvider reportUrl={reportUrl}>{children}</ReportProvider>;
}
