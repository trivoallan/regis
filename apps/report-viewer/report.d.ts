// ============================================================
// regis-cli — Report TypeScript types
// Derived from JSON schemas + observed report.json structure
// ============================================================

// -----------------------------------------------------------
// Shared primitives
// -----------------------------------------------------------

export type BadgeClass = "success" | "warning" | "error" | "information";
export type RuleStatus = "passed" | "failed" | "incomplete";
export type RuleLevel = "critical" | "warning" | "info" | string;

export interface Badge {
  slug?: string;
  scope: string;
  value?: string | null;
  class: BadgeClass;
  label?: string;
}

export interface ReportLink {
  label: string;
  url: string;
}

export interface AnalyzerError {
  type: string;
  message: string;
}

// -----------------------------------------------------------
// Request
// -----------------------------------------------------------

export interface ReportRequest {
  url: string;
  registry: string;
  repository: string;
  tag: string;
  digest?: string;
  analyzers: string[];
  timestamp: string; // ISO 8601
  metadata?: Record<string, unknown>;
}

// -----------------------------------------------------------
// Rules
// -----------------------------------------------------------

export interface Rule {
  slug: string;
  /** `description` in schema, `title` in observed report.json — handle both */
  description?: string;
  title?: string;
  level?: RuleLevel;
  tags?: string[];
  passed: boolean;
  status: RuleStatus;
  message: string;
  analyzers?: string[];
}

export interface TagSummaryEntry {
  rules: string[];
  passed_rules: string[];
  score: number;
}

export interface RulesSummary {
  score: number;
  total: string[];
  passed: string[];
  by_tag?: Record<string, TagSummaryEntry>;
}

// -----------------------------------------------------------
// Analyzer results
// -----------------------------------------------------------

export interface TrivyVulnerability {
  VulnerabilityID: string;
  PkgName: string;
  InstalledVersion: string;
  FixedVersion?: string;
  Severity: string;
  Title?: string;
  Description?: string;
}

export interface TrivySecret {
  RuleID: string;
  Title: string;
  Severity: string;
  Match: string;
}

export interface TrivyTarget {
  Target: string;
  Vulnerabilities: TrivyVulnerability[] | null;
  Secrets?: TrivySecret[] | null;
}

export interface TrivyResult {
  analyzer: "trivy";
  repository?: string;
  tag?: string;
  error?: AnalyzerError;
  trivy_version?: string;
  vulnerability_count?: number;
  critical_count?: number;
  high_count?: number;
  medium_count?: number;
  low_count?: number;
  unknown_count?: number;
  fixed_count?: number;
  secrets_count?: number;
  targets?: TrivyTarget[];
}

export interface HadolintIssue {
  code: string;
  level: "error" | "warning" | "info" | "style";
  message: string;
  line?: number | null;
}

export interface HadolintResult {
  analyzer: "hadolint";
  repository?: string;
  tag?: string;
  error?: AnalyzerError;
  passed?: boolean;
  issues_count?: number;
  issues_by_level?: {
    error?: number;
    warning?: number;
    info?: number;
    style?: number;
  };
  issues?: HadolintIssue[];
  dockerfile?: string;
}

export interface DockleIssue {
  code: string;
  title: string;
  level: "FATAL" | "WARN" | "INFO" | "SKIP" | "PASS";
  alerts: string[];
}

export interface DockleResult {
  analyzer: "dockle";
  repository?: string;
  tag?: string;
  error?: AnalyzerError;
  passed?: boolean;
  issues_count?: number;
  issues_by_level?: {
    FATAL?: number;
    WARN?: number;
    INFO?: number;
    SKIP?: number;
    PASS?: number;
  };
  issues?: DockleIssue[];
}

export interface SkopeoLabel {
  [key: string]: string;
}

export interface SkopeoPlatform {
  architecture: string;
  os: string;
  variant?: string | null;
  digest?: string;
  created?: string | null;
  labels?: SkopeoLabel;
  layers_count?: number;
  size?: number;
  exposed_ports?: string[];
  env?: string[];
  user?: string | null;
}

export interface SkopeoResult {
  analyzer: "skopeo";
  repository?: string;
  tag?: string;
  platforms: SkopeoPlatform[];
  tags?: string[];
  inspect?: Record<string, unknown>;
}

export interface SbomComponent {
  name: string;
  version?: string | null;
  type: string;
  purl?: string | null;
  licenses?: string[];
}

export interface SbomResult {
  analyzer: "sbom";
  repository?: string;
  tag?: string;
  has_sbom?: boolean;
  sbom_format?: string;
  sbom_version?: string;
  total_components?: number;
  component_types?: Record<string, number>;
  total_dependencies?: number;
  licenses?: string[];
  components?: SbomComponent[];
}

export interface FreshnessResult {
  analyzer: "freshness";
  repository?: string;
  tag?: string;
  tag_created?: string | null;
  latest_created?: string | null;
  age_days?: number | null;
  behind_latest_days?: number | null;
  is_latest?: boolean;
}

export interface EndoflifeMatchedCycle {
  cycle: string;
  release_date?: string | null;
  eol?: string | boolean;
  latest?: string | null;
  latest_release_date?: string | null;
  lts?: boolean;
}

export interface EndoflifeResult {
  analyzer: "endoflife";
  repository?: string;
  product?: string;
  product_found?: boolean;
  tag?: string;
  matched_cycle?: EndoflifeMatchedCycle | null;
  is_eol?: boolean | null;
  active_cycles_count?: number | null;
  eol_cycles_count?: number | null;
}

export interface SizePlatform {
  platform: string;
  compressed_bytes: number;
  compressed_human: string;
  layer_count: number;
}

export interface SizeLayer {
  index: number;
  digest: string;
  size_bytes: number;
  size_human: string;
}

export interface SizeResult {
  analyzer: "size";
  repository?: string;
  tag?: string;
  multi_arch?: boolean;
  total_compressed_bytes?: number;
  total_compressed_human?: string;
  layer_count?: number;
  config_size_bytes?: number;
  layers?: SizeLayer[];
  platforms?: SizePlatform[] | null;
}

export interface ProvenanceIndicator {
  type: string;
  key: string;
  value: string;
}

export interface ProvenanceResult {
  analyzer: "provenance";
  repository?: string;
  tag?: string;
  has_provenance?: boolean;
  has_cosign_signature?: boolean;
  source_tracked?: boolean;
  indicators_count?: number;
  indicators?: ProvenanceIndicator[];
}

export interface ScorecardCheck {
  name: string;
  score: number;
  reason: string;
}

export interface ScorecarddevResult {
  analyzer: "scorecarddev";
  repository?: string;
  source_repo?: string | null;
  scorecard_available?: boolean;
  score?: number | null;
  checks?: ScorecardCheck[];
}

export interface VersioningPattern {
  pattern: string;
  count: number;
  percentage: number;
  examples: string[];
}

export interface VersioningVariant {
  name: string;
  count: number;
  percentage: number;
  examples: string[];
}

export interface VersioningResult {
  analyzer: "versioning";
  repository?: string;
  total_tags?: number;
  dominant_pattern?: string;
  semver_compliant_percentage?: number;
  release_lines?: string[];
  patterns?: VersioningPattern[];
  variants?: VersioningVariant[];
}

export interface PopularityResult {
  analyzer: "popularity";
  repository?: string;
  available?: boolean;
  pull_count?: number | null;
  star_count?: number | null;
  description?: string | null;
  last_updated?: string | null;
  date_registered?: string | null;
  is_official?: boolean;
}

/** Union de tous les résultats d'analyzer possibles */
export type AnalyzerResult =
  | TrivyResult
  | HadolintResult
  | DockleResult
  | SkopeoResult
  | SbomResult
  | FreshnessResult
  | EndoflifeResult
  | SizeResult
  | ProvenanceResult
  | ScorecarddevResult
  | VersioningResult
  | PopularityResult;

/** Map des résultats keyed par nom d'analyzer */
export interface AnalyzerResults {
  trivy?: TrivyResult;
  hadolint?: HadolintResult;
  dockle?: DockleResult;
  skopeo?: SkopeoResult;
  sbom?: SbomResult;
  freshness?: FreshnessResult;
  endoflife?: EndoflifeResult;
  size?: SizeResult;
  provenance?: ProvenanceResult;
  scorecarddev?: ScorecarddevResult;
  versioning?: VersioningResult;
  popularity?: PopularityResult;
  [key: string]: AnalyzerResult | undefined;
}

// -----------------------------------------------------------
// Playbook result
// -----------------------------------------------------------

export interface ResolvedWidget {
  label?: string;
  value?: string;
  url?: string;
  icon?: string;
  template?: string;
  options?: {
    title?: string;
    collapsed?: boolean;
    align?: "left" | "center" | "right";
    subvalue?: string;
    class?: string;
  };
  condition?: unknown;
  resolved_value?: unknown;
  resolved_url?: string;
  resolved_subvalue?: unknown;
}

export interface SectionLevelSummary {
  total: number;
  passed: number;
  percentage: number;
}

export interface Scorecard {
  name: string;
  description: string;
  level?: string | null;
  tags?: string[];
  analyzers?: string[];
  passed: boolean;
  status?: RuleStatus;
  condition?: string;
  details?: string;
}

export interface PlaybookSection {
  name: string;
  hint?: string;
  score: number;
  total_scorecards: number;
  passed_scorecards: number;
  levels_summary?: Record<string, SectionLevelSummary>;
  tags_summary?: Record<string, SectionLevelSummary>;
  scorecards: Scorecard[];
  widgets?: ResolvedWidget[];
  render_order?: string[];
  display?: {
    analyzers?: string[];
    widgets?: ResolvedWidget[];
  };
}

export interface PlaybookPage {
  title: string;
  slug?: string | null;
  score: number;
  total_scorecards: number;
  passed_scorecards: number;
  sections: PlaybookSection[];
}

export interface MrChecklistItem {
  label: string;
  checked: boolean;
}

export interface MrChecklist {
  title?: string;
  items: MrChecklistItem[];
}

export interface PlaybookResult {
  playbook_name: string;
  score: number;
  total_scorecards: number;
  passed_scorecards: number;
  pages: PlaybookPage[];
  rules?: Rule[];
  rules_summary?: RulesSummary;
  tier?: string | null;
  badges?: Badge[];
  links?: ReportLink[];
  sidebar?: unknown;
  mr_description_checklists?: MrChecklist[];
  mr_templates?: Array<{ url: string; directory?: string }>;
  slug?: string | null;
  _meta?: { source_name?: string };
}

// -----------------------------------------------------------
// Root report
// -----------------------------------------------------------

export interface Report {
  version?: string | null;
  tier?: string | null;
  badges?: Badge[];
  metadata?: Record<string, unknown>;
  links?: ReportLink[];
  request: ReportRequest;
  results: AnalyzerResults;
  playbooks?: PlaybookResult[];
  /** Shorthand for playbooks[0] */
  playbook?: PlaybookResult;
  rules?: Rule[];
  rules_summary?: RulesSummary;
}
