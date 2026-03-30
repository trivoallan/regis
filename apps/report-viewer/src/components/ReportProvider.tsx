/**
 * ReportProvider — React context that loads and provides the report data.
 *
 * In Docusaurus, static assets are served from /static/. We load
 * /report.json at runtime so the same built site can be re-used
 * with different report data if needed.
 */

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

/** Minimal typing for the report JSON (extend as needed). */
export interface ReportData {
  version?: string;
  request?: {
    url?: string;
    registry?: string;
    repository?: string;
    tag?: string;
    digest?: string;
    timestamp?: string;
    platform?: string;
    analyzers?: string[];
  };
  results?: Record<string, unknown>;
  rules?: RuleResult[];
  rules_summary?: RulesSummary;
  tier?: string;
  badges?: Array<{ label: string; class: string }>;
  links?: Array<{ label: string; url: string }>;
  playbooks?: PlaybookResult[];
  playbook?: PlaybookResult;
}

export interface RuleResult {
  slug: string;
  description?: string;
  title?: string;
  level: string;
  passed: boolean;
  status?: string;
  message?: string;
  tags?: string[];
  analyzers?: string[];
}

export interface RulesSummary {
  total?: number | string[];
  passed?: number | string[];
  failed?: number | string[];
  score?: number;
  by_tag?: Record<
    string,
    {
      rules: string[];
      passed_rules: string[];
      score: number;
    }
  >;
}

export interface PlaybookResult {
  playbook_name?: string;
  slug?: string;
  score?: number;
  tier?: string;
  badges?: Array<{ label: string; class: string }>;
  passed_scorecards?: number;
  total_scorecards?: number;
  rules?: RuleResult[];
  rules_summary?: RulesSummary;
  pages?: PlaybookPage[];
  sidebar?: unknown;
  _meta?: { source_name?: string };
}

export interface PlaybookPage {
  title?: string;
  slug?: string;
  sections?: PlaybookSection[];
}

export interface PlaybookSection {
  name?: string;
  hint?: string;
  render_order?: string[];
  widgets?: Widget[];
  scorecards?: Scorecard[];
  levels_summary?: Record<
    string,
    { passed: number; total: number; percentage: number }
  >;
  tags_summary?: Record<
    string,
    { passed: number; total: number; percentage: number }
  >;
  display?: { analyzers?: string[] };
}

export interface Widget {
  label?: string;
  icon?: string;
  resolved_value?: unknown;
  resolved_subvalue?: string;
  resolved_url?: string;
  template?: string;
  options?: Record<string, unknown>;
}

export interface Scorecard {
  title?: string;
  passed: boolean;
  level?: string;
  details?: string;
  tags?: string[];
  analyzers?: string[];
}

interface ReportContextValue {
  report: ReportData | null;
  loading: boolean;
  error: string | null;
  reportUrl: string;
}

const ReportContext = createContext<ReportContextValue>({
  report: null,
  loading: true,
  error: null,
  reportUrl: "",
});

export function useReport(): ReportContextValue {
  return useContext(ReportContext);
}

interface ReportProviderProps {
  children: ReactNode;
  reportUrl?: string;
}

export function ReportProvider({
  children,
  reportUrl = "/report.json",
}: ReportProviderProps): React.JSX.Element {
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetch(reportUrl)
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        const contentType = res.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
          throw new Error(
            "Response was not a valid JSON report (check if file exists)",
          );
        }
        return res.json();
      })
      .then((data) => {
        if (Array.isArray(data)) {
          // It's a manifest, redirect to archive view
          const params = new URLSearchParams(window.location.search);
          params.set("archive_url", reportUrl);
          params.delete("url");
          // Navigate to archive view (usually at root / or some base path)
          const newPath = window.location.pathname.replace(/\/report\/?$/, "/");
          window.location.href = `${newPath}?${params.toString()}`;
          return;
        }
        setReport(data);
        setError(null);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [reportUrl]);

  return (
    <ReportContext.Provider value={{ report, loading, error, reportUrl }}>
      {children}
    </ReportContext.Provider>
  );
}
