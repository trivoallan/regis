import React, { useState, useMemo } from "react";
import type { Rule, RulesSummary } from "../types/report";
import { getRuleLabel } from "../hooks/useReport";
import { StatusBadge } from "./ScoreBadge";

// -----------------------------------------------------------
// RulesTagSummary — grille des scores par tag (tag cards)
// -----------------------------------------------------------

interface RulesTagSummaryProps {
  summary: RulesSummary;
  activeTag: string;
  onTagChange: (tag: string) => void;
}

export function RulesTagSummary({
  summary,
  activeTag,
  onTagChange,
}: RulesTagSummaryProps) {
  if (!summary.by_tag) return null;

  const tags = Object.entries(summary.by_tag);

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
        gap: "0.75rem",
        marginBottom: "1.5rem",
      }}
    >
      {tags.map(([tag, data]) => {
        const isActive = activeTag === tag;
        const scoreColor =
          data.score >= 80
            ? "var(--regis-success)"
            : data.score >= 50
              ? "var(--regis-warning)"
              : "var(--regis-danger)";

        return (
          <button
            key={tag}
            onClick={() => onTagChange(isActive ? "all" : tag)}
            style={{
              padding: "0.75rem",
              borderRadius: "0.5rem",
              border: isActive
                ? "2px solid var(--regis-primary)"
                : "1px solid var(--regis-border)",
              background: isActive
                ? "var(--regis-primary-bg)"
                : "var(--regis-surface)",
              cursor: "pointer",
              textAlign: "center",
              transition: "all 0.15s ease",
            }}
          >
            <div
              style={{
                fontSize: "0.68rem",
                textTransform: "uppercase",
                letterSpacing: "0.07em",
                opacity: 0.65,
                marginBottom: "0.35rem",
                color: "var(--regis-text)",
              }}
            >
              {tag}
            </div>
            <div
              style={{
                fontSize: "1.5rem",
                fontWeight: 700,
                lineHeight: 1,
                color: scoreColor,
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {data.score}%
            </div>
            <div
              style={{
                fontSize: "0.7rem",
                opacity: 0.55,
                marginTop: "0.2rem",
                color: "var(--regis-text)",
              }}
            >
              {data.passed_rules.length} / {data.rules.length}
            </div>
          </button>
        );
      })}
    </div>
  );
}

// -----------------------------------------------------------
// RulesTable — table filtrée + triable
// -----------------------------------------------------------

type SortKey = "status" | "level" | "tag";
type SortDir = "asc" | "desc";

const LEVEL_ORDER: Record<string, number> = {
  critical: 0,
  warning: 1,
  info: 2,
};

const STATUS_ORDER: Record<string, number> = {
  failed: 0,
  incomplete: 1,
  passed: 2,
};

interface RulesTableProps {
  rules: Rule[];
  summary?: RulesSummary;
  /** If true, shows the tag summary grid above the table */
  showTagSummary?: boolean;
  /** Initial filter tag */
  defaultTag?: string;
}

export function RulesTable({
  rules,
  summary,
  showTagSummary = true,
  defaultTag = "all",
}: RulesTableProps) {
  const [activeTag, setActiveTag] = useState(defaultTag);
  const [sortKey, setSortKey] = useState<SortKey>("status");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [search, setSearch] = useState("");

  const allTags = useMemo(() => {
    const set = new Set<string>();
    rules.forEach((r) => r.tags?.forEach((t) => set.add(t)));
    return Array.from(set).sort();
  }, [rules]);

  const filtered = useMemo(() => {
    let list = rules;

    if (activeTag !== "all") {
      list = list.filter((r) => r.tags?.includes(activeTag));
    }

    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (r) =>
          getRuleLabel(r).toLowerCase().includes(q) ||
          r.slug.toLowerCase().includes(q) ||
          r.message.toLowerCase().includes(q),
      );
    }

    list = [...list].sort((a, b) => {
      let cmp = 0;
      if (sortKey === "status") {
        cmp = (STATUS_ORDER[a.status] ?? 99) - (STATUS_ORDER[b.status] ?? 99);
      } else if (sortKey === "level") {
        cmp =
          (LEVEL_ORDER[a.level ?? ""] ?? 99) -
          (LEVEL_ORDER[b.level ?? ""] ?? 99);
      } else if (sortKey === "tag") {
        cmp = (a.tags?.[0] ?? "").localeCompare(b.tags?.[0] ?? "");
      }
      return sortDir === "asc" ? cmp : -cmp;
    });

    return list;
  }, [rules, activeTag, search, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  function SortIndicator({ k }: { k: SortKey }) {
    if (sortKey !== k) return <span style={{ opacity: 0.3 }}> ↕</span>;
    return <span>{sortDir === "asc" ? " ↑" : " ↓"}</span>;
  }

  return (
    <div className="regis-rules-table">
      {/* Tag summary grid */}
      {showTagSummary && summary && (
        <RulesTagSummary
          summary={summary}
          activeTag={activeTag}
          onTagChange={setActiveTag}
        />
      )}

      {/* Controls */}
      <div
        style={{
          display: "flex",
          gap: "0.75rem",
          alignItems: "center",
          marginBottom: "1rem",
          flexWrap: "wrap",
        }}
      >
        {/* Search */}
        <input
          type="search"
          placeholder="Search rules…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            flex: "1 1 200px",
            padding: "0.4rem 0.75rem",
            borderRadius: "0.375rem",
            border: "1px solid var(--regis-border)",
            background: "var(--regis-surface)",
            color: "var(--regis-text)",
            fontSize: "0.875rem",
            outline: "none",
          }}
        />

        {/* Tag select (inline fallback when no summary grid) */}
        {(!showTagSummary || !summary) && (
          <select
            value={activeTag}
            onChange={(e) => setActiveTag(e.target.value)}
            style={{
              padding: "0.4rem 0.75rem",
              borderRadius: "0.375rem",
              border: "1px solid var(--regis-border)",
              background: "var(--regis-surface)",
              color: "var(--regis-text)",
              fontSize: "0.875rem",
            }}
          >
            <option value="all">All tags</option>
            {allTags.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        )}

        <span
          style={{ fontSize: "0.8rem", opacity: 0.55, whiteSpace: "nowrap" }}
        >
          {filtered.length} / {rules.length} rules
        </span>
      </div>

      {/* Table */}
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: "0.875rem",
          }}
        >
          <thead>
            <tr style={{ borderBottom: "2px solid var(--regis-border)" }}>
              <th style={thStyle} onClick={() => toggleSort("status")}>
                Status <SortIndicator k="status" />
              </th>
              <th style={thStyle} onClick={() => toggleSort("level")}>
                Level <SortIndicator k="level" />
              </th>
              <th style={{ ...thStyle, cursor: "default", width: "100%" }}>
                Rule
              </th>
              <th style={thStyle} onClick={() => toggleSort("tag")}>
                Tags <SortIndicator k="tag" />
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td
                  colSpan={4}
                  style={{ padding: "2rem", textAlign: "center", opacity: 0.5 }}
                >
                  No rules match the current filter.
                </td>
              </tr>
            )}
            {filtered.map((rule) => (
              <RuleRow key={rule.slug} rule={rule} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// -----------------------------------------------------------
// RuleRow
// -----------------------------------------------------------

function RuleRow({ rule }: { rule: Rule }) {
  const [expanded, setExpanded] = useState(false);
  const statusIcon = rule.passed
    ? "✅"
    : rule.status === "incomplete"
      ? "⚠️"
      : "❌";

  return (
    <>
      <tr
        style={{
          borderBottom: "1px solid var(--regis-border)",
          verticalAlign: "top",
          cursor: rule.analyzers?.length ? "pointer" : "default",
          background: expanded ? "var(--regis-surface-hover)" : "transparent",
          transition: "background 0.1s",
        }}
        onClick={() => setExpanded((e) => !e)}
      >
        {/* Status */}
        <td style={tdStyle}>
          <span style={{ fontSize: "1rem" }}>{statusIcon}</span>
        </td>

        {/* Level */}
        <td style={tdStyle}>
          {rule.level && (
            <StatusBadge
              badgeClass={
                rule.level === "critical"
                  ? "error"
                  : rule.level === "warning"
                    ? "warning"
                    : "information"
              }
              label={rule.level}
              size="sm"
            />
          )}
        </td>

        {/* Rule description */}
        <td style={{ ...tdStyle, maxWidth: 0 }}>
          <div style={{ fontWeight: 500, color: "var(--regis-text)" }}>
            {getRuleLabel(rule)}
          </div>
          <div
            style={{
              fontSize: "0.8rem",
              opacity: 0.7,
              marginTop: "0.2rem",
              color: "var(--regis-text)",
            }}
          >
            {rule.message}
          </div>
          {rule.analyzers && rule.analyzers.length > 0 && (
            <div
              style={{
                marginTop: "0.3rem",
                display: "flex",
                gap: "0.3rem",
                flexWrap: "wrap",
              }}
            >
              {rule.analyzers.map((a) => (
                <span
                  key={a}
                  style={{
                    fontSize: "0.68rem",
                    padding: "0.1rem 0.4rem",
                    borderRadius: "0.25rem",
                    background: "var(--regis-surface-raised)",
                    color: "var(--regis-text-muted)",
                    fontFamily: "monospace",
                  }}
                >
                  {a}
                </span>
              ))}
            </div>
          )}
        </td>

        {/* Tags */}
        <td style={tdStyle}>
          <div style={{ display: "flex", gap: "0.25rem", flexWrap: "wrap" }}>
            {rule.tags?.map((tag) => (
              <span
                key={tag}
                style={{
                  fontSize: "0.7rem",
                  padding: "0.15rem 0.5rem",
                  borderRadius: "2rem",
                  border: "1px solid var(--regis-border)",
                  color: "var(--regis-text-muted)",
                  whiteSpace: "nowrap",
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        </td>
      </tr>
    </>
  );
}

// -----------------------------------------------------------
// Styles partagés
// -----------------------------------------------------------

const thStyle: React.CSSProperties = {
  padding: "0.6rem 0.75rem",
  textAlign: "left",
  fontWeight: 600,
  fontSize: "0.8rem",
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  opacity: 0.75,
  cursor: "pointer",
  whiteSpace: "nowrap",
  userSelect: "none",
};

const tdStyle: React.CSSProperties = {
  padding: "0.75rem",
  verticalAlign: "top",
};
