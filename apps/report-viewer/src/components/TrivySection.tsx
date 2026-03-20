/**
 * TrivySection — Displays vulnerability scan results from Trivy.
 *
 * Shows a severity breakdown bar and a vulnerability table.
 */

import React from "react";

interface TrivyVulnerability {
  VulnerabilityID: string;
  Severity: string;
  Title?: string;
  PkgName?: string;
  InstalledVersion?: string;
  FixedVersion?: string;
}

interface TrivyTarget {
  Target: string;
  Vulnerabilities?: TrivyVulnerability[];
}

interface TrivyData {
  analyzer: string;
  repository: string;
  tag: string;
  trivy_version?: string;
  vulnerability_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  unknown_count: number;
  fixed_count: number;
  secrets_count: number;
  targets?: TrivyTarget[];
}

interface TrivySectionProps {
  data: TrivyData;
}

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: "#dc2626",
  HIGH: "#ea580c",
  MEDIUM: "#d97706",
  LOW: "#2563eb",
  UNKNOWN: "#6b7280",
};

function SeverityBar({ data }: { data: TrivyData }) {
  const total = data.vulnerability_count || 1;
  const segments = [
    {
      label: "Critical",
      count: data.critical_count,
      color: SEVERITY_COLORS.CRITICAL,
    },
    { label: "High", count: data.high_count, color: SEVERITY_COLORS.HIGH },
    {
      label: "Medium",
      count: data.medium_count,
      color: SEVERITY_COLORS.MEDIUM,
    },
    { label: "Low", count: data.low_count, color: SEVERITY_COLORS.LOW },
    {
      label: "Unknown",
      count: data.unknown_count,
      color: SEVERITY_COLORS.UNKNOWN,
    },
  ].filter((s) => s.count > 0);

  return (
    <div>
      <div
        style={{
          display: "flex",
          height: "12px",
          borderRadius: "6px",
          overflow: "hidden",
          marginBottom: "0.5rem",
          background: "var(--ifm-color-emphasis-200)",
        }}
      >
        {segments.map((s) => (
          <div
            key={s.label}
            style={{
              width: `${(s.count / total) * 100}%`,
              background: s.color,
              minWidth: s.count > 0 ? "4px" : 0,
            }}
            title={`${s.label}: ${s.count}`}
          />
        ))}
      </div>
      <div
        style={{
          display: "flex",
          gap: "1rem",
          flexWrap: "wrap",
          fontSize: "0.8rem",
        }}
      >
        {segments.map((s) => (
          <span
            key={s.label}
            style={{ display: "flex", alignItems: "center", gap: "4px" }}
          >
            <span
              style={{
                width: "10px",
                height: "10px",
                borderRadius: "2px",
                background: s.color,
                display: "inline-block",
              }}
            />
            {s.label}: <strong>{s.count}</strong>
          </span>
        ))}
      </div>
    </div>
  );
}

export function TrivySection({ data }: TrivySectionProps): React.JSX.Element {
  const allVulns =
    data.targets?.flatMap(
      (t) =>
        t.Vulnerabilities?.map((v) => ({
          ...v,
          target: t.Target,
        })) ?? [],
    ) ?? [];

  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          gap: "0.75rem",
          marginBottom: "1.5rem",
        }}
      >
        <div className="stat-card">
          <div className="stat-card__label">Total</div>
          <div className="stat-card__value">{data.vulnerability_count}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Fixable</div>
          <div className="stat-card__value">{data.fixed_count}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Secrets</div>
          <div className="stat-card__value">{data.secrets_count}</div>
        </div>
      </div>

      <SeverityBar data={data} />

      {allVulns.length > 0 && (
        <table style={{ marginTop: "1rem" }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Severity</th>
              <th>Package</th>
              <th>Installed</th>
              <th>Fixed</th>
              <th>Title</th>
            </tr>
          </thead>
          <tbody>
            {allVulns.map((v, i) => (
              <tr key={i}>
                <td>
                  <a
                    href={`https://nvd.nist.gov/vuln/detail/${v.VulnerabilityID}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ fontFamily: "monospace", fontSize: "0.85rem" }}
                  >
                    {v.VulnerabilityID}
                  </a>
                </td>
                <td>
                  <span
                    style={{
                      padding: "2px 8px",
                      borderRadius: "4px",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      color: "#fff",
                      background: SEVERITY_COLORS[v.Severity] ?? "#6b7280",
                    }}
                  >
                    {v.Severity}
                  </span>
                </td>
                <td style={{ fontFamily: "monospace", fontSize: "0.85rem" }}>
                  {v.PkgName}
                </td>
                <td style={{ fontFamily: "monospace", fontSize: "0.85rem" }}>
                  {v.InstalledVersion}
                </td>
                <td style={{ fontFamily: "monospace", fontSize: "0.85rem" }}>
                  {v.FixedVersion ?? "—"}
                </td>
                <td style={{ fontSize: "0.85rem" }}>{v.Title ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {allVulns.length === 0 && data.vulnerability_count === 0 && (
        <div className="alert alert--success" style={{ marginTop: "1rem" }}>
          ✅ No vulnerabilities detected.
        </div>
      )}
    </div>
  );
}
