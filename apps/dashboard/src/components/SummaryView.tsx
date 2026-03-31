/**
 * SummaryView — Renders the report summary page.
 *
 * Extracted from index.mdx to avoid MDX acorn parsing issues
 * with TypeScript ternary/optional chaining syntax.
 */

import React from "react";
import {
  Grid,
  Card,
  Flex,
  Text,
  Metric,
  Title,
  BarChart,
  Badge,
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
} from "@tremor/react";
import Link from "@docusaurus/Link";
import { useReport } from "./ReportProvider";
import { TierBadge } from "./TierBadge";
import { RequestTable } from "./RequestTable";
import { ScoreBadge, levelToVariant } from "./ScoreBadge";
import { ScoreCard } from "./Dashboard/ScoreCard";
import { VulnerabilityChart } from "./Dashboard/VulnerabilityChart";
import { ComplianceDonut } from "./Dashboard/ComplianceDonut";
import { AnalyzerCoverageCard } from "./Dashboard/AnalyzerCoverageCard";
import { RulesByLevelCard } from "./Dashboard/RulesByLevelCard";
import { RulesByTagCard } from "./Dashboard/RulesByTagCard";

const LEVEL_ORDER = ["Gold", "Silver", "Bronze", "Critical", "Warning", "Info"];

function highestFailedLevel(
  rules: { level: string; passed: boolean }[],
): string | null {
  const failedLevels = new Set(
    rules.filter((r) => !r.passed).map((r) => r.level?.toLowerCase()),
  );
  return LEVEL_ORDER.find((l) => failedLevels.has(l.toLowerCase())) ?? null;
}

export function SummaryView(): React.JSX.Element {
  const { report, loading, error } = useReport();

  if (loading) return <p>Loading report data…</p>;
  if (error) return <div className="alert alert--danger">Error: {error}</div>;
  if (!report) return <p>No report data available.</p>;

  const req = report.request ?? {};
  const pb = report.playbook ?? report.playbooks?.[0];
  const rs = report.rules_summary ?? pb?.rules_summary;
  const score = rs?.score ?? 0;
  const passedRaw = rs?.passed;
  const totalRaw = rs?.total;
  const passedCount = Array.isArray(passedRaw)
    ? passedRaw.length
    : (passedRaw ?? 0);
  const totalCount = Array.isArray(totalRaw)
    ? totalRaw.length
    : (totalRaw ?? 0);
  const tier = report.tier ?? pb?.tier;
  const analyzers = req.analyzers ?? [];

  const trivyData = report.results?.trivy as Record<string, number> | undefined;
  const vulnerabilityData = trivyData
    ? [
        { severity: "Critical", count: trivyData.critical_count ?? 0 },
        { severity: "High", count: trivyData.high_count ?? 0 },
        { severity: "Medium", count: trivyData.medium_count ?? 0 },
        { severity: "Low", count: trivyData.low_count ?? 0 },
        { severity: "Unknown", count: trivyData.unknown_count ?? 0 },
      ]
    : [];

  const complianceData = [
    { name: "Passed", value: passedCount },
    { name: "Failed", value: Math.max(0, totalCount - passedCount) },
  ];

  const rules = report.rules ?? pb?.rules ?? [];
  const topFailedLevel = highestFailedLevel(rules);
  const failedAtTopLevel = topFailedLevel
    ? rules.filter(
        (r) =>
          !r.passed && r.level?.toLowerCase() === topFailedLevel.toLowerCase(),
      ).length
    : 0;

  const hasVulnerabilities =
    vulnerabilityData.length > 0 && vulnerabilityData.some((d) => d.count > 0);

  const badgeColor = (cls: string) =>
    cls === "success"
      ? "emerald"
      : cls === "warning"
        ? "amber"
        : cls === "error"
          ? "rose"
          : cls === "information"
            ? "indigo"
            : "gray";

  return (
    <div className="p-6 space-y-8">
      {/* Header — badges */}
      {(report.badges?.length ?? 0) > 0 && (
        <header className="flex flex-wrap gap-2">
          {report.badges!.map((badge, i) => (
            <Badge key={i} color={badgeColor(badge.class)} size="md">
              {badge.label}
            </Badge>
          ))}
        </header>
      )}

      {/* KPI Cards */}
      <section>
        <Grid numItemsSm={1} numItemsLg={3} className="gap-6">
          <Card className="flex flex-col">
            <Flex justifyContent="between" alignItems="start">
              <Text className="font-medium">Failure Level</Text>
              {rules.filter((r) => !r.passed).length > 0 && (
                <Badge color="rose" size="xs">
                  {rules.filter((r) => !r.passed).length} failed
                </Badge>
              )}
            </Flex>
            {topFailedLevel ? (
              <>
                <div className="flex flex-1 items-center justify-center">
                  <ScoreBadge
                    label={topFailedLevel}
                    variant={levelToVariant(topFailedLevel)}
                    size="lg"
                  />
                </div>
              </>
            ) : (
              <div className="flex flex-1 items-center justify-center">
                <ScoreBadge
                  label="All rules passed"
                  variant="success"
                  size="lg"
                />
              </div>
            )}
          </Card>
          <ScoreCard
            score={score}
            label="Compliance Score"
            passed={passedCount}
            total={totalCount}
            tier={tier ?? undefined}
          />

          <AnalyzerCoverageCard analyzers={analyzers} />
        </Grid>
      </section>

      {/* Rules by level & tag */}
      <section>
        <Grid numItemsSm={1} numItemsLg={2} className="gap-6">
          <RulesByLevelCard rules={rules} />
          <RulesByTagCard rules={rules} />
        </Grid>
      </section>

      {/* Failed rules — grouped by level */}
      {rules.filter((r) => !r.passed).length > 0 &&
        (() => {
          const failedByLevel = rules
            .filter((r) => !r.passed)
            .reduce<Record<string, typeof rules>>((acc, r) => {
              const lvl = r.level ?? "Other";
              (acc[lvl] ??= []).push(r);
              return acc;
            }, {});
          const groups = Object.entries(failedByLevel).sort(([a], [b]) => {
            const ai = LEVEL_ORDER.findIndex(
              (l) => l.toLowerCase() === a.toLowerCase(),
            );
            const bi = LEVEL_ORDER.findIndex(
              (l) => l.toLowerCase() === b.toLowerCase(),
            );
            return (
              (ai === -1 ? LEVEL_ORDER.length : ai) -
              (bi === -1 ? LEVEL_ORDER.length : bi)
            );
          });
          return (
            <section>
              <Title className="mb-4">Failed Rules</Title>
              <div className="space-y-6">
                {groups.map(([level, levelRules]) => (
                  <div key={level}>
                    <div className="flex items-center gap-3 mb-3">
                      <ScoreBadge
                        label={level}
                        variant={levelToVariant(level)}
                      />
                      <Text className="text-tremor-label text-tremor-content">
                        {levelRules.length} failed
                      </Text>
                    </div>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableHeaderCell style={{ width: "3rem" }}>
                            Status
                          </TableHeaderCell>
                          <TableHeaderCell>Rule</TableHeaderCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {levelRules.map((r, i) => (
                          <TableRow key={r.slug ?? i}>
                            <TableCell style={{ textAlign: "center" }}>
                              <span style={{ fontSize: "1.5rem" }}>
                                {r.status === "incomplete" ? "⚠️" : "❌"}
                              </span>
                            </TableCell>
                            <TableCell>
                              <strong>
                                {r.description ?? r.title ?? r.slug}
                              </strong>
                              {r.message && (
                                <Text className="mt-1 text-tremor-default text-tremor-content">
                                  {r.message}
                                </Text>
                              )}
                              {r.analyzers && r.analyzers.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-1">
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
                ))}
              </div>
            </section>
          );
        })()}

      {/* Resources */}
      {(report.links?.length ?? 0) > 0 && (
        <section className="pt-6 border-t border-gray-200 dark:border-gray-800">
          <Title className="mb-4">Resources</Title>
          <div className="flex flex-wrap gap-3">
            {report.links?.map((link, i) => (
              <a
                key={i}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 border border-gray-200 dark:border-gray-800 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                {link.label}
              </a>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
