/**
 * RulesTable — Rules grouped by level, filterable by tag.
 * Uses Tremor Table components for consistent styling.
 */

import React, { useState, useEffect } from "react";
import Link from "@docusaurus/Link";
import {
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  CategoryBar,
  TabGroup,
  TabList,
  Tab,
  Card,
  Flex,
  Text,
} from "@tremor/react";
import { ScoreBadge, levelToVariant } from "./ScoreBadge";
import type { RuleResult, RulesSummary } from "./ReportProvider";

interface RulesTableProps {
  rules: RuleResult[];
  summary?: RulesSummary;
}

/** Display order for known levels. Unknown levels appear last. */
const LEVEL_ORDER = ["Gold", "Silver", "Bronze", "Critical", "Warning", "Info"];

function levelSortIndex(level: string): number {
  const idx = LEVEL_ORDER.findIndex(
    (l) => l.toLowerCase() === level?.toLowerCase(),
  );
  return idx === -1 ? LEVEL_ORDER.length : idx;
}

function StatusIcon({ passed, status }: { passed: boolean; status?: string }) {
  const style = { fontSize: "1.5rem" };
  if (status === "incomplete")
    return (
      <span title="Incomplete" style={style}>
        ⚠️
      </span>
    );
  return passed ? (
    <span title="Passed" style={style}>
      ✅
    </span>
  ) : (
    <span title="Failed" style={style}>
      ❌
    </span>
  );
}

interface LevelGroupProps {
  level: string;
  rules: RuleResult[];
}

function LevelGroup({ level, rules }: LevelGroupProps): React.JSX.Element {
  const passedCount = rules.filter((r) => r.passed).length;

  return (
    <div style={{ marginBottom: "2rem" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
          marginBottom: "0.75rem",
        }}
      >
        <ScoreBadge label={level} variant={levelToVariant(level)} />
        <small style={{ opacity: 0.6 }}>
          {passedCount} / {rules.length} passed
        </small>
      </div>

      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell style={{ width: "3rem" }}>Status</TableHeaderCell>
            <TableHeaderCell>Rule</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rules.map((r, i) => (
            <TableRow key={r.slug ?? i}>
              <TableCell style={{ textAlign: "center" }}>
                <StatusIcon passed={r.passed} status={r.status} />
              </TableCell>
              <TableCell>
                <strong>{r.description ?? r.title ?? r.slug}</strong>
                {r.message && (
                  <div
                    style={{
                      fontSize: "0.85rem",
                      opacity: 0.8,
                      marginTop: "0.2rem",
                    }}
                  >
                    {r.message}
                  </div>
                )}
                {r.analyzers && r.analyzers.length > 0 && (
                  <div
                    style={{
                      marginTop: "0.3rem",
                      display: "flex",
                      gap: "0.25rem",
                      flexWrap: "wrap",
                    }}
                  >
                    {r.analyzers.map((a) => (
                      <Link
                        key={a}
                        to={`/analyzers/${a}`}
                        style={{ textDecoration: "none" }}
                      >
                        <ScoreBadge label={a} variant="outline" />
                      </Link>
                    ))}
                  </div>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export function RulesTable({
  rules,
  summary,
}: RulesTableProps): React.JSX.Element {
  const [activeTag, setActiveTag] = useState<string>("all");
  const [activeTab, setActiveTab] = useState<number>(0);

  const tagFilteredRules =
    activeTag === "all"
      ? rules
      : rules.filter((r) => r.tags?.includes(activeTag));

  useEffect(() => {
    const hasFailed = tagFilteredRules.some((r) => !r.passed);
    setActiveTab(hasFailed ? 0 : 1);
  }, [activeTag]);

  const filteredRules =
    activeTab === 0
      ? tagFilteredRules.filter((r) => !r.passed)
      : tagFilteredRules.filter((r) => r.passed);

  const groups = Object.entries(
    filteredRules.reduce<Record<string, RuleResult[]>>((acc, r) => {
      const lvl = r.level ?? "Other";
      (acc[lvl] ??= []).push(r);
      return acc;
    }, {}),
  ).sort(([a], [b]) => levelSortIndex(a) - levelSortIndex(b));

  const tagStats = summary?.by_tag ?? {};

  return (
    <div>
      {/* Tag summary cards */}
      {Object.keys(tagStats).length > 0 && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
            gap: "0.75rem",
            marginBottom: "1.5rem",
          }}
        >
          {Object.entries(tagStats)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([tag, stats]) => (
              <button
                type="button"
                key={tag}
                onClick={() => setActiveTag(activeTag === tag ? "all" : tag)}
                style={{
                  cursor: "pointer",
                  padding: "0.75rem",
                  textAlign: "center",
                  background: "var(--ifm-card-background-color)",
                  border:
                    activeTag === tag
                      ? "2px solid var(--ifm-color-primary)"
                      : "1px solid var(--ifm-color-emphasis-200)",
                  borderRadius: "8px",
                  transform: activeTag === tag ? "scale(1.03)" : "scale(1)",
                  transition: "all 0.2s ease",
                }}
              >
                <small
                  style={{
                    textTransform: "uppercase",
                    fontWeight: 700,
                    letterSpacing: "0.05em",
                    opacity: 0.8,
                  }}
                >
                  {tag}
                </small>
                <br />
                <span style={{ fontSize: "1.5rem", fontWeight: 700 }}>
                  {stats.score}%
                </span>
                <br />
                <small style={{ opacity: 0.6 }}>
                  {stats.passed_rules.length} / {stats.rules.length} passed
                </small>
                <CategoryBar
                  values={[
                    stats.passed_rules.length,
                    stats.rules.length - stats.passed_rules.length,
                  ]}
                  colors={["emerald", "rose"]}
                  showLabels={false}
                  className="mt-2"
                />
              </button>
            ))}
        </div>
      )}

      {/* Tabs + rules grouped by level */}
      <TabGroup index={activeTab} onIndexChange={setActiveTab} className="mb-6">
        <TabList>
          <Tab>Failed ({tagFilteredRules.filter((r) => !r.passed).length})</Tab>
          <Tab>Passed ({tagFilteredRules.filter((r) => r.passed).length})</Tab>
        </TabList>
      </TabGroup>

      {groups.length === 0 ? (
        <p style={{ opacity: 0.6 }}>No rules match the selected filter.</p>
      ) : (
        groups.map(([level, levelRules]) => (
          <LevelGroup key={level} level={level} rules={levelRules} />
        ))
      )}
    </div>
  );
}
