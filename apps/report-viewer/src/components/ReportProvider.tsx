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
  total?: number;
  passed?: number;
  failed?: number;
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
}

const ReportContext = createContext<ReportContextValue>({
  report: null,
  loading: true,
  error: null,
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
    fetch(reportUrl)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load report: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setReport(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [reportUrl]);

  return (
    <ReportContext.Provider value={{ report, loading, error }}>
      {children}
    </ReportContext.Provider>
  );
}
