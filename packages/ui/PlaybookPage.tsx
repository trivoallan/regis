import React, { useState } from "react";
import type {
  PlaybookPage as PlaybookPageType,
  PlaybookSection,
  ResolvedWidget,
  Report,
} from "@regis-cli/ui";
import { StatusBadge, ScoreBadge } from "@regis-cli/ui";

interface PlaybookPageProps {
  page: PlaybookPageType;
  report: Report;
}

export function PlaybookPage({ page, report }: PlaybookPageProps) {
  return (
    <div>
      <header style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "1.2rem", fontWeight: 600, margin: 0 }}>
          {page.title}
        </h1>
        {page.total_scorecards > 0 && (
          <div
            style={{ fontSize: "0.82rem", opacity: 0.55, marginTop: "0.35rem" }}
          >
            {page.passed_scorecards} / {page.total_scorecards} scorecards passed
            &nbsp;·&nbsp;
            <strong>{page.score}%</strong>
          </div>
        )}
      </header>

      {page.sections.map((section, i) => (
        <SectionBlock key={i} section={section} report={report} />
      ))}
    </div>
  );
}

// -----------------------------------------------------------
// SectionBlock
// -----------------------------------------------------------

interface SectionBlockProps {
  section: PlaybookSection;
  report: Report;
}

function SectionBlock({ section, report }: SectionBlockProps) {
  return (
    <section className="regis-section">
      {section.name && section.name.trim() && (
        <h2 className="regis-section-title">{section.name}</h2>
      )}
      {section.hint && (
        <p
          style={{
            fontSize: "0.85rem",
            opacity: 0.65,
            marginTop: "-0.5rem",
            marginBottom: "1rem",
          }}
        >
          {section.hint}
        </p>
      )}

      {/* Widgets résolus */}
      {(section.widgets ?? []).length > 0 && (
        <WidgetGrid widgets={section.widgets!} report={report} />
      )}

      {/* Scorecards */}
      {section.scorecards.length > 0 && (
        <ScorecardList
          scorecards={section.scorecards}
          levelsSummary={section.levels_summary}
        />
      )}
    </section>
  );
}

// -----------------------------------------------------------
// WidgetGrid — grille de widgets résolus
// -----------------------------------------------------------

interface WidgetGridProps {
  widgets: ResolvedWidget[];
  report: Report;
}

function WidgetGrid({ widgets, report }: WidgetGridProps) {
  // Séparer les widgets KPI (label + resolved_value) des widgets template
  const kpiWidgets = widgets.filter(
    (w) => w.label && w.resolved_value !== undefined && !w.template,
  );
  const templateWidgets = widgets.filter((w) => w.template);

  return (
    <div>
      {/* KPI cards */}
      {kpiWidgets.length > 0 && (
        <div className="regis-kpi-grid" style={{ marginBottom: "1rem" }}>
          {kpiWidgets.map((w, i) => (
            <KpiCard key={i} widget={w} />
          ))}
        </div>
      )}

      {/* Template widgets — rendu générique avec les données du report */}
      {templateWidgets.map((w, i) => (
        <TemplateWidget key={i} widget={w} report={report} />
      ))}
    </div>
  );
}

// -----------------------------------------------------------
// KpiCard
// -----------------------------------------------------------

function KpiCard({ widget }: { widget: ResolvedWidget }) {
  const value = String(widget.resolved_value ?? "—");
  const subvalue = widget.options?.subvalue
    ? String(widget.resolved_subvalue ?? widget.options.subvalue)
    : undefined;
  const align = widget.options?.align ?? "left";
  const hasUrl = !!widget.resolved_url;

  const inner = (
    <div
      className="regis-kpi-card"
      style={{ textAlign: align as React.CSSProperties["textAlign"] }}
    >
      <div className="regis-kpi-label">{widget.label}</div>
      <div
        className="regis-kpi-value"
        style={{
          color: getValueColor(value),
          fontSize: value.length > 8 ? "1.1rem" : undefined,
        }}
      >
        {value}
      </div>
      {subvalue && (
        <div
          style={{ fontSize: "0.78rem", opacity: 0.55, marginTop: "0.2rem" }}
        >
          {subvalue}
        </div>
      )}
    </div>
  );

  if (hasUrl) {
    return (
      <a href={widget.resolved_url} style={{ textDecoration: "none" }}>
        {inner}
      </a>
    );
  }
  return inner;
}

function getValueColor(value: string): string | undefined {
  const v = value.toUpperCase();
  if (v === "GO" || v === "PASSED" || v === "YES")
    return "var(--regis-success)";
  if (v === "NOGO" || v === "FAILED") return "var(--regis-danger)";
  return undefined;
}

// -----------------------------------------------------------
// TemplateWidget — rendu des templates analyzer/* via les données réelles
// -----------------------------------------------------------

interface TemplateWidgetProps {
  widget: ResolvedWidget;
  report: Report;
}

function TemplateWidget({ widget, report }: TemplateWidgetProps) {
  const [open, setOpen] = useState(!(widget.options?.collapsed ?? false));
  const title = widget.options?.title;

  // Résoudre l'analyzer depuis le chemin du template (ex: "analyzers/trivy/cards.html")
  const analyzerName = widget.template?.split("/")?.[1];
  const templateType = widget.template?.split("/")?.[2]?.replace(".html", "");
  const analyzerData = analyzerName
    ? (report.results as Record<string, unknown>)[analyzerName]
    : null;

  const content = renderAnalyzerTemplate(
    analyzerName,
    templateType,
    analyzerData,
    report,
  );

  if (!content) return null;

  if (!title) {
    return <div style={{ marginBottom: "0.75rem" }}>{content}</div>;
  }

  return (
    <details
      className="regis-details"
      open={open}
      onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}
      style={{ marginBottom: "0.75rem" }}
    >
      <summary>{title}</summary>
      <div className="regis-details-body">{content}</div>
    </details>
  );
}

// -----------------------------------------------------------
// renderAnalyzerTemplate — dispatche vers le bon composant React
// -----------------------------------------------------------

function renderAnalyzerTemplate(
  analyzer: string | undefined,
  type: string | undefined,
  data: unknown,
  report: Report,
): React.ReactNode {
  if (!analyzer || !type) return null;

  // Erreur analyzer
  if (
    data &&
    typeof data === "object" &&
    "error" in data &&
    (data as { error: unknown }).error
  ) {
    const err = (data as { error: { type: string; message: string } }).error;
    return (
      <div className="regis-analyzer-error">
        <strong style={{ fontFamily: "monospace" }}>{analyzer}</strong>
        <span
          style={{ marginLeft: "0.5rem", opacity: 0.6, fontSize: "0.8rem" }}
        >
          {err.type}
        </span>
        <div style={{ marginTop: "0.25rem", fontSize: "0.82rem" }}>
          {err.message}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <p style={{ opacity: 0.5, fontStyle: "italic", fontSize: "0.85rem" }}>
        No data available for <code>{analyzer}</code>.
      </p>
    );
  }

  // Dispatch par analyzer + type
  switch (`${analyzer}/${type}`) {
    case "trivy/cards":
      return (
        <TrivyCards data={data as Parameters<typeof TrivyCards>[0]["data"]} />
      );
    case "trivy/table":
      return (
        <TrivyTable data={data as Parameters<typeof TrivyTable>[0]["data"]} />
      );
    case "hadolint/cards":
      return (
        <HadolintCards
          data={data as Parameters<typeof HadolintCards>[0]["data"]}
        />
      );
    case "hadolint/table":
      return (
        <HadolintTable
          data={data as Parameters<typeof HadolintTable>[0]["data"]}
        />
      );
    case "sbom/cards":
      return (
        <SbomCards data={data as Parameters<typeof SbomCards>[0]["data"]} />
      );
    case "sbom/table":
      return (
        <SbomTable data={data as Parameters<typeof SbomTable>[0]["data"]} />
      );
    case "freshness/cards":
      return (
        <FreshnessCards
          data={data as Parameters<typeof FreshnessCards>[0]["data"]}
        />
      );
    case "freshness/table":
      return (
        <FreshnessTable
          data={data as Parameters<typeof FreshnessTable>[0]["data"]}
        />
      );
    case "size/cards":
      return (
        <SizeCards data={data as Parameters<typeof SizeCards>[0]["data"]} />
      );
    case "size/table":
      return (
        <SizeTable data={data as Parameters<typeof SizeTable>[0]["data"]} />
      );
    case "provenance/cards":
      return (
        <ProvenanceCards
          data={data as Parameters<typeof ProvenanceCards>[0]["data"]}
        />
      );
    case "skopeo/cards":
      return (
        <SkopeoCards data={data as Parameters<typeof SkopeoCards>[0]["data"]} />
      );
    case "skopeo/table":
      return (
        <SkopeoTable data={data as Parameters<typeof SkopeoTable>[0]["data"]} />
      );
    case "versioning/cards":
      return (
        <VersioningCards
          data={data as Parameters<typeof VersioningCards>[0]["data"]}
        />
      );
    case "request/table":
      return <RequestTable report={report} />;
    default:
      return (
        <p style={{ opacity: 0.4, fontSize: "0.8rem" }}>
          Template{" "}
          <code>
            {analyzer}/{type}
          </code>{" "}
          not yet implemented.
        </p>
      );
  }
}

// -----------------------------------------------------------
// Analyzer sub-components
// -----------------------------------------------------------

// Trivy
function TrivyCards({
  data,
}: {
  data: {
    critical_count?: number;
    high_count?: number;
    medium_count?: number;
    low_count?: number;
  };
}) {
  return (
    <div className="regis-kpi-grid">
      {[
        { label: "Critical", value: data.critical_count ?? 0, danger: true },
        { label: "High", value: data.high_count ?? 0, warn: true },
        { label: "Medium", value: data.medium_count ?? 0 },
        { label: "Low", value: data.low_count ?? 0 },
      ].map(({ label, value, danger, warn }) => (
        <div
          key={label}
          className="regis-kpi-card"
          style={{ textAlign: "center" }}
        >
          <div className="regis-kpi-label">{label}</div>
          <div
            className="regis-kpi-value"
            style={{
              color:
                danger && value > 0
                  ? "var(--regis-danger)"
                  : warn && value > 0
                    ? "var(--regis-warning)"
                    : undefined,
            }}
          >
            {value}
          </div>
        </div>
      ))}
    </div>
  );
}

function TrivyTable({
  data,
}: {
  data: {
    targets?: Array<{
      Target: string;
      Vulnerabilities?: Array<{
        VulnerabilityID: string;
        PkgName: string;
        InstalledVersion: string;
        FixedVersion?: string;
        Severity: string;
        Title?: string;
      }> | null;
    }>;
  };
}) {
  const vulns = (data.targets ?? []).flatMap((t) =>
    (t.Vulnerabilities ?? []).filter(
      (v) => v.Severity === "CRITICAL" || v.Severity === "HIGH",
    ),
  );

  if (!vulns.length) {
    return (
      <p style={{ opacity: 0.5, fontStyle: "italic", fontSize: "0.85rem" }}>
        No HIGH or CRITICAL vulnerabilities found.
      </p>
    );
  }

  return (
    <div style={{ overflowX: "auto" }}>
      <table className="regis-table">
        <thead>
          <tr>
            <th>CVE</th>
            <th>Package</th>
            <th>Version</th>
            <th>Fixed</th>
            <th>Severity</th>
          </tr>
        </thead>
        <tbody>
          {vulns.slice(0, 50).map((v, i) => (
            <tr key={i}>
              <td>
                <code style={{ fontSize: "0.8rem" }}>{v.VulnerabilityID}</code>
              </td>
              <td>{v.PkgName}</td>
              <td>
                <code style={{ fontSize: "0.8rem" }}>{v.InstalledVersion}</code>
              </td>
              <td
                style={{
                  color: v.FixedVersion ? "var(--regis-success)" : undefined,
                }}
              >
                {v.FixedVersion ?? "—"}
              </td>
              <td>
                <StatusBadge
                  badgeClass={v.Severity === "CRITICAL" ? "error" : "warning"}
                  label={v.Severity}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Hadolint
function HadolintCards({
  data,
}: {
  data: {
    passed?: boolean;
    issues_count?: number;
    issues_by_level?: Record<string, number>;
  };
}) {
  return (
    <div className="regis-kpi-grid">
      <div className="regis-kpi-card" style={{ textAlign: "center" }}>
        <div className="regis-kpi-label">Status</div>
        <div
          className="regis-kpi-value"
          style={{
            color: data.passed ? "var(--regis-success)" : "var(--regis-danger)",
            fontSize: "1.1rem",
          }}
        >
          {data.passed ? "PASSED" : "FAILED"}
        </div>
      </div>
      {Object.entries(data.issues_by_level ?? {}).map(([level, count]) => (
        <div
          key={level}
          className="regis-kpi-card"
          style={{ textAlign: "center" }}
        >
          <div className="regis-kpi-label">{level}</div>
          <div className="regis-kpi-value">{count}</div>
        </div>
      ))}
    </div>
  );
}

function HadolintTable({
  data,
}: {
  data: {
    issues?: Array<{
      code: string;
      level: string;
      message: string;
      line?: number | null;
    }>;
    dockerfile?: string;
  };
}) {
  return (
    <div>
      {(data.issues ?? []).length > 0 ? (
        <table className="regis-table" style={{ marginBottom: "1rem" }}>
          <thead>
            <tr>
              <th>Level</th>
              <th>Code</th>
              <th>Line</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {(data.issues ?? []).map((issue, i) => (
              <tr key={i}>
                <td>
                  <StatusBadge
                    badgeClass={
                      issue.level === "error"
                        ? "error"
                        : issue.level === "warning"
                          ? "warning"
                          : "information"
                    }
                    label={issue.level}
                  />
                </td>
                <td>
                  <code>{issue.code}</code>
                </td>
                <td>{issue.line ?? "—"}</td>
                <td style={{ fontSize: "0.85rem" }}>{issue.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p style={{ opacity: 0.5, fontStyle: "italic", fontSize: "0.85rem" }}>
          No linting issues found.
        </p>
      )}
      {data.dockerfile && (
        <details>
          <summary
            style={{ cursor: "pointer", fontSize: "0.85rem", opacity: 0.7 }}
          >
            Reconstructed Dockerfile
          </summary>
          <pre
            style={{
              fontSize: "0.8rem",
              marginTop: "0.5rem",
              overflow: "auto",
            }}
          >
            <code>{data.dockerfile}</code>
          </pre>
        </details>
      )}
    </div>
  );
}

// SBOM
function SbomCards({
  data,
}: {
  data: {
    total_components?: number;
    total_dependencies?: number;
    licenses?: string[];
  };
}) {
  return (
    <div className="regis-kpi-grid">
      {[
        { label: "Components", value: data.total_components ?? 0 },
        { label: "Dependencies", value: data.total_dependencies ?? 0 },
        { label: "Licenses", value: (data.licenses ?? []).length },
      ].map(({ label, value }) => (
        <div
          key={label}
          className="regis-kpi-card"
          style={{ textAlign: "center" }}
        >
          <div className="regis-kpi-label">{label}</div>
          <div className="regis-kpi-value">{value}</div>
        </div>
      ))}
    </div>
  );
}

function SbomTable({
  data,
}: {
  data: {
    component_types?: Record<string, number>;
    licenses?: string[];
    components?: Array<{
      name: string;
      version?: string | null;
      type: string;
      licenses?: string[];
    }>;
  };
}) {
  return (
    <div>
      {/* Licenses */}
      {(data.licenses ?? []).length > 0 && (
        <div
          style={{
            marginBottom: "1rem",
            display: "flex",
            flexWrap: "wrap",
            gap: "0.3rem",
          }}
        >
          {(data.licenses ?? []).map((l) => (
            <span
              key={l}
              style={{
                fontSize: "0.75rem",
                padding: "0.15rem 0.5rem",
                borderRadius: "0.25rem",
                border: "1px solid var(--regis-border)",
                color: "var(--regis-text-muted)",
              }}
            >
              {l}
            </span>
          ))}
        </div>
      )}
      {/* Components */}
      <div style={{ overflowX: "auto" }}>
        <table className="regis-table">
          <thead>
            <tr>
              <th>Package</th>
              <th>Version</th>
              <th>Type</th>
              <th>License</th>
            </tr>
          </thead>
          <tbody>
            {(data.components ?? []).slice(0, 50).map((c, i) => (
              <tr key={i}>
                <td>
                  <code style={{ fontSize: "0.8rem" }}>{c.name}</code>
                </td>
                <td style={{ fontSize: "0.85rem" }}>{c.version ?? "—"}</td>
                <td style={{ fontSize: "0.8rem", opacity: 0.65 }}>{c.type}</td>
                <td style={{ fontSize: "0.8rem" }}>
                  {(c.licenses ?? []).join(", ") || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Freshness
function FreshnessCards({
  data,
}: {
  data: {
    age_days?: number | null;
    behind_latest_days?: number | null;
    is_latest?: boolean;
  };
}) {
  return (
    <div className="regis-kpi-grid">
      <div className="regis-kpi-card" style={{ textAlign: "center" }}>
        <div className="regis-kpi-label">Age</div>
        <div className="regis-kpi-value">
          {data.age_days ?? "—"}
          <small style={{ fontSize: "0.8rem", opacity: 0.5 }}> days</small>
        </div>
      </div>
      <div className="regis-kpi-card" style={{ textAlign: "center" }}>
        <div className="regis-kpi-label">Behind latest</div>
        <div className="regis-kpi-value">
          {data.behind_latest_days != null
            ? `${data.behind_latest_days}d`
            : "N/A"}
        </div>
      </div>
      <div className="regis-kpi-card" style={{ textAlign: "center" }}>
        <div className="regis-kpi-label">Is latest</div>
        <div
          className="regis-kpi-value"
          style={{
            color: data.is_latest
              ? "var(--regis-success)"
              : "var(--regis-danger)",
          }}
        >
          {data.is_latest ? "✓" : "✗"}
        </div>
      </div>
    </div>
  );
}

function FreshnessTable({
  data,
}: {
  data: { tag?: string; tag_created?: string | null; is_latest?: boolean };
}) {
  return (
    <table className="regis-table">
      <tbody>
        <tr>
          <td>
            <strong>Tag</strong>
          </td>
          <td>
            <code>{data.tag ?? "—"}</code>
          </td>
        </tr>
        <tr>
          <td>
            <strong>Created</strong>
          </td>
          <td>{data.tag_created ?? "—"}</td>
        </tr>
        <tr>
          <td>
            <strong>Status</strong>
          </td>
          <td>
            {data.is_latest ? (
              <StatusBadge status="passed" label="Latest" />
            ) : (
              "—"
            )}
          </td>
        </tr>
      </tbody>
    </table>
  );
}

// Size
function SizeCards({
  data,
}: {
  data: {
    total_compressed_human?: string;
    layer_count?: number;
    platforms?: unknown[] | null;
  };
}) {
  return (
    <div className="regis-kpi-grid">
      {[
        { label: "Total size", value: data.total_compressed_human ?? "—" },
        { label: "Layers", value: data.layer_count ?? "—" },
        { label: "Platforms", value: (data.platforms ?? []).length || "—" },
      ].map(({ label, value }) => (
        <div
          key={label}
          className="regis-kpi-card"
          style={{ textAlign: "center" }}
        >
          <div className="regis-kpi-label">{label}</div>
          <div
            className="regis-kpi-value"
            style={{
              fontSize: typeof value === "string" ? "1.2rem" : undefined,
            }}
          >
            {value}
          </div>
        </div>
      ))}
    </div>
  );
}

function SizeTable({
  data,
}: {
  data: {
    platforms?: Array<{
      platform: string;
      compressed_human: string;
      layer_count: number;
    }> | null;
  };
}) {
  if (!(data.platforms ?? []).length)
    return (
      <p style={{ opacity: 0.5, fontSize: "0.85rem", fontStyle: "italic" }}>
        No platform data.
      </p>
    );
  return (
    <table className="regis-table">
      <thead>
        <tr>
          <th>Platform</th>
          <th>Compressed size</th>
          <th>Layers</th>
        </tr>
      </thead>
      <tbody>
        {(data.platforms ?? []).map((p, i) => (
          <tr key={i}>
            <td>
              <strong>{p.platform}</strong>
            </td>
            <td>
              <code>{p.compressed_human}</code>
            </td>
            <td>{p.layer_count}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// Provenance
function ProvenanceCards({
  data,
}: {
  data: {
    has_provenance?: boolean;
    has_cosign_signature?: boolean;
    source_tracked?: boolean;
    indicators_count?: number;
  };
}) {
  return (
    <div className="regis-kpi-grid">
      {[
        { label: "Attestations", value: data.indicators_count ?? 0 },
        {
          label: "Cosign",
          value: data.has_cosign_signature ? "✓" : "✗",
          ok: data.has_cosign_signature,
        },
        {
          label: "Source link",
          value: data.source_tracked ? "✓" : "✗",
          ok: data.source_tracked,
        },
      ].map(({ label, value, ok }) => (
        <div
          key={label}
          className="regis-kpi-card"
          style={{ textAlign: "center" }}
        >
          <div className="regis-kpi-label">{label}</div>
          <div
            className="regis-kpi-value"
            style={{
              color:
                ok === undefined
                  ? undefined
                  : ok
                    ? "var(--regis-success)"
                    : "var(--regis-danger)",
            }}
          >
            {value}
          </div>
        </div>
      ))}
    </div>
  );
}

// Skopeo
function SkopeoCards({
  data,
}: {
  data: { platforms?: unknown[]; tags?: unknown[] };
}) {
  const rootPlatforms = (
    (data.platforms as Array<{ os: string }>) ?? []
  ).filter((p) => p.os !== "unknown");
  return (
    <div className="regis-kpi-grid">
      <div className="regis-kpi-card" style={{ textAlign: "center" }}>
        <div className="regis-kpi-label">Platforms</div>
        <div className="regis-kpi-value">{rootPlatforms.length}</div>
      </div>
      <div className="regis-kpi-card" style={{ textAlign: "center" }}>
        <div className="regis-kpi-label">Tags</div>
        <div className="regis-kpi-value">{(data.tags ?? []).length}</div>
      </div>
    </div>
  );
}

function SkopeoTable({
  data,
}: {
  data: {
    platforms?: Array<{
      architecture: string;
      os: string;
      variant?: string | null;
      digest?: string;
      created?: string | null;
      layers_count?: number;
      user?: string | null;
    }>;
    tags?: string[];
  };
}) {
  return (
    <div>
      <div style={{ overflowX: "auto", marginBottom: "1rem" }}>
        <table className="regis-table">
          <thead>
            <tr>
              <th>Platform</th>
              <th>Digest</th>
              <th>User</th>
              <th>Created</th>
              <th>Layers</th>
            </tr>
          </thead>
          <tbody>
            {(data.platforms ?? []).map((p, i) => (
              <tr key={i}>
                <td>
                  <strong>
                    {p.os}/{p.architecture}
                    {p.variant ? `/${p.variant}` : ""}
                  </strong>
                </td>
                <td>
                  <code style={{ fontSize: "0.75rem" }} title={p.digest}>
                    {p.digest ? p.digest.slice(0, 14) + "…" : "—"}
                  </code>
                </td>
                <td
                  style={{
                    color:
                      !p.user || p.user === "root" || p.user === ""
                        ? "var(--regis-danger)"
                        : undefined,
                  }}
                >
                  {p.user || "root"}
                </td>
                <td style={{ fontSize: "0.8rem" }}>
                  {p.created ? new Date(p.created).toLocaleDateString() : "—"}
                </td>
                <td>{p.layers_count ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {(data.tags ?? []).length > 0 && (
        <div style={{ fontSize: "0.8rem" }}>
          <strong>Recent tags: </strong>
          <code style={{ opacity: 0.7 }}>
            {(data.tags ?? []).slice(0, 10).join(", ")}…
          </code>
        </div>
      )}
    </div>
  );
}

// Versioning
function VersioningCards({
  data,
}: {
  data: {
    dominant_pattern?: string;
    semver_compliant_percentage?: number;
    total_tags?: number;
    release_lines?: string[];
  };
}) {
  return (
    <div className="regis-kpi-grid">
      {[
        { label: "Dominant pattern", value: data.dominant_pattern ?? "—" },
        {
          label: "Semver compliance",
          value:
            data.semver_compliant_percentage != null
              ? `${data.semver_compliant_percentage}%`
              : "—",
        },
        { label: "Total tags", value: data.total_tags ?? "—" },
      ].map(({ label, value }) => (
        <div
          key={label}
          className="regis-kpi-card"
          style={{ textAlign: "center" }}
        >
          <div className="regis-kpi-label">{label}</div>
          <div className="regis-kpi-value" style={{ fontSize: "1.1rem" }}>
            {value}
          </div>
        </div>
      ))}
    </div>
  );
}

// Request table
function RequestTable({ report }: { report: Report }) {
  const rows: [string, string][] = [
    ["url", report.request.url],
    ["registry", report.request.registry],
    ["repository", report.request.repository],
    ["tag", report.request.tag],
    ...(report.request.digest
      ? [["digest", report.request.digest] as [string, string]]
      : []),
    ["analyzers", report.request.analyzers.join(", ")],
    ["timestamp", report.request.timestamp],
  ];
  return (
    <table className="regis-table">
      <tbody>
        {rows.map(([k, v]) => (
          <tr key={k}>
            <td style={{ fontWeight: 500, whiteSpace: "nowrap", width: "30%" }}>
              {k}
            </td>
            <td style={{ fontSize: "0.85rem", wordBreak: "break-all" }}>{v}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// -----------------------------------------------------------
// ScorecardList
// -----------------------------------------------------------

interface ScorecardListProps {
  scorecards: PlaybookSection["scorecards"];
  levelsSummary?: PlaybookSection["levels_summary"];
}

function ScorecardList({ scorecards, levelsSummary }: ScorecardListProps) {
  return (
    <div>
      {levelsSummary && Object.keys(levelsSummary).length > 0 && (
        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            marginBottom: "0.75rem",
            flexWrap: "wrap",
          }}
        >
          {Object.entries(levelsSummary).map(([level, summary]) => (
            <div
              key={level}
              style={{
                fontSize: "0.8rem",
                padding: "0.2rem 0.6rem",
                borderRadius: "0.25rem",
                background: "var(--regis-surface-raised)",
                color: "var(--regis-text-muted)",
              }}
            >
              {level}: {summary.passed}/{summary.total}
            </div>
          ))}
        </div>
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
        {scorecards.map((sc, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "0.75rem",
              padding: "0.6rem 0.75rem",
              borderRadius: "0.375rem",
              background: "var(--regis-surface)",
              border: "1px solid var(--regis-border)",
            }}
          >
            <span style={{ fontSize: "1rem", flexShrink: 0 }}>
              {sc.passed ? "✅" : sc.status === "incomplete" ? "⚠️" : "❌"}
            </span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 500, fontSize: "0.875rem" }}>
                {sc.description}
              </div>
              {sc.details && (
                <div
                  style={{
                    fontSize: "0.8rem",
                    opacity: 0.65,
                    marginTop: "0.15rem",
                  }}
                >
                  {sc.details}
                </div>
              )}
            </div>
            {sc.level && (
              <StatusBadge
                badgeClass={
                  sc.level === "critical"
                    ? "error"
                    : sc.level === "warning"
                      ? "warning"
                      : "information"
                }
                label={sc.level}
                size="sm"
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
