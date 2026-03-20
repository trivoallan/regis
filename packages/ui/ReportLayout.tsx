import React from "react";
import { NavLink } from "react-router-dom";
import type { Report, PlaybookResult } from "@regis-cli/ui";
import { ScoreBadge, BadgeList, getOverallScore } from "@regis-cli/ui";

interface ReportLayoutProps {
  report: Report;
  playbook: PlaybookResult | null;
  children: React.ReactNode;
}

export function ReportLayout({
  report,
  playbook,
  children,
}: ReportLayoutProps) {
  const score = getOverallScore(report);
  const pages = playbook?.pages ?? [];
  const errors = getAnalyzerErrors(report);

  return (
    <div className="regis-report regis-layout">
      {/* Sidebar */}
      <aside className="regis-sidebar">
        {/* Image identity */}
        <div style={{ marginBottom: "1.5rem" }}>
          <div
            style={{
              fontSize: "0.7rem",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              opacity: 0.5,
              marginBottom: "0.25rem",
            }}
          >
            {report.request.registry}
          </div>
          <div
            style={{
              fontWeight: 600,
              fontSize: "0.95rem",
              wordBreak: "break-all",
              lineHeight: 1.3,
            }}
          >
            {report.request.repository}
          </div>
          <div
            style={{ fontSize: "0.85rem", opacity: 0.6, marginTop: "0.2rem" }}
          >
            :{report.request.tag}
          </div>
        </div>

        {/* Score + tier */}
        {score !== null && (
          <div style={{ marginBottom: "1.25rem" }}>
            <ScoreBadge
              score={score}
              tier={playbook?.tier ?? report.tier ?? undefined}
              size="sm"
              showLabel
            />
          </div>
        )}

        {/* Badges */}
        {(playbook?.badges ?? report.badges ?? []).length > 0 && (
          <div style={{ marginBottom: "1.25rem" }}>
            <BadgeList badges={playbook?.badges ?? report.badges ?? []} />
          </div>
        )}

        {/* Nav */}
        <nav>
          <div style={navGroupLabel}>Navigation</div>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {/* Overview synthétique (rules) — toujours visible */}
            <li>
              <SidebarLink to="/overview" label="Overview" />
            </li>

            {/* Pages du playbook */}
            {pages.map((page) => {
              const slug =
                page.slug ??
                page.title.toLowerCase().replace(/[^a-z0-9]+/g, "-");
              return (
                <li key={slug}>
                  <SidebarLink
                    to={`/${slug}`}
                    label={page.title}
                    score={page.score}
                  />
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Analyzer errors summary */}
        {errors.length > 0 && (
          <div style={{ marginTop: "1.5rem" }}>
            <div style={navGroupLabel}>Analyzer errors</div>
            {errors.map((name) => (
              <div
                key={name}
                style={{
                  fontSize: "0.75rem",
                  padding: "0.2rem 0.5rem",
                  borderRadius: "0.25rem",
                  background: "var(--regis-danger-bg)",
                  color: "var(--regis-danger)",
                  marginBottom: "0.25rem",
                  fontFamily: "monospace",
                }}
              >
                {name}
              </div>
            ))}
          </div>
        )}

        {/* Footer */}
        <div
          style={{
            marginTop: "auto",
            paddingTop: "2rem",
            fontSize: "0.72rem",
            opacity: 0.4,
          }}
        >
          regis-cli {report.version ?? ""}
          <br />
          {formatTimestamp(report.request.timestamp)}
        </div>
      </aside>

      {/* Main content */}
      <main className="regis-main">{children}</main>
    </div>
  );
}

// -----------------------------------------------------------
// SidebarLink
// -----------------------------------------------------------

interface SidebarLinkProps {
  to: string;
  label: string;
  score?: number;
}

function SidebarLink({ to, label, score }: SidebarLinkProps) {
  return (
    <NavLink
      to={to}
      style={({ isActive }) => ({
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0.4rem 0.6rem",
        borderRadius: "0.375rem",
        textDecoration: "none",
        fontSize: "0.9rem",
        fontWeight: isActive ? 600 : 400,
        color: isActive ? "var(--regis-primary)" : "var(--regis-text)",
        background: isActive ? "var(--regis-primary-bg)" : "transparent",
        marginBottom: "0.1rem",
        transition: "background 0.1s, color 0.1s",
      })}
    >
      <span>{label}</span>
      {score !== undefined && (
        <span
          style={{
            fontSize: "0.7rem",
            opacity: 0.6,
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {score}%
        </span>
      )}
    </NavLink>
  );
}

// -----------------------------------------------------------
// Helpers
// -----------------------------------------------------------

const navGroupLabel: React.CSSProperties = {
  fontSize: "0.65rem",
  textTransform: "uppercase",
  letterSpacing: "0.1em",
  opacity: 0.45,
  marginBottom: "0.4rem",
  paddingLeft: "0.6rem",
};

function getAnalyzerErrors(report: Report): string[] {
  return Object.entries(report.results)
    .filter(([, result]) => result && "error" in result && result.error != null)
    .map(([name]) => name);
}

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}
