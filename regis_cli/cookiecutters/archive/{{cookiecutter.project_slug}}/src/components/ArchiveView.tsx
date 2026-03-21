import React, { useEffect, useMemo, useState } from "react";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import {
  AreaChart,
  Badge,
  Card,
  Flex,
  Grid,
  Select,
  SelectItem,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  Text,
  TextInput,
  Title,
} from "@tremor/react";
import { ScoreBadge, levelToVariant } from "./ScoreBadge";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ArchiveEntry {
  id: string;
  timestamp: string;
  registry: string;
  repository: string;
  tag: string;
  digest?: string;
  score: number;
  tier?: string;
  rules_passed: number;
  rules_total: number;
  cve_critical?: number;
  cve_high?: number;
  cve_medium?: number;
  cve_low?: number;
  age_days?: number;
  sbom_component_count?: number;
  scorecard_score?: number;
  path: string;
}

interface RuleResult {
  slug: string;
  description?: string;
  level: string;
  passed: boolean;
  message?: string;
  analyzers?: string[];
}

interface ReportData {
  request?: {
    registry?: string;
    repository?: string;
    tag?: string;
    timestamp?: string;
  };
  rules?: RuleResult[];
  rules_summary?: {
    score?: number;
    total?: number | unknown[];
    passed?: number | unknown[];
  };
  tier?: string;
  badges?: Array<{
    label: string;
    class: string;
    scope?: string;
    value?: string;
  }>;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function imageKey(e: ArchiveEntry) {
  return `${e.registry}/${e.repository}:${e.tag}`;
}

function formatDate(ts: string) {
  try {
    return new Date(ts).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return ts;
  }
}

function tierVariant(
  tier?: string,
): "success" | "warning" | "info" | "outline" {
  if (!tier) return "outline";
  const t = tier.toLowerCase();
  if (t === "gold") return "success";
  if (t === "silver") return "info";
  if (t === "bronze") return "warning";
  return "outline";
}

function badgeColor(
  cls: string,
): "emerald" | "amber" | "rose" | "indigo" | "gray" {
  if (cls === "success") return "emerald";
  if (cls === "warning") return "amber";
  if (cls === "error") return "rose";
  if (cls === "information") return "indigo";
  return "gray";
}

const TIERS = ["All", "Gold", "Silver", "Bronze", "None"];
const LEVEL_ORDER = ["critical", "warning", "info"];

// ---------------------------------------------------------------------------
// Trend chart
// ---------------------------------------------------------------------------

function ImageTrendChart({ entries }: { entries: ArchiveEntry[] }) {
  const sorted = [...entries].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );
  const scoreData = sorted.map((e) => ({
    date: formatDate(e.timestamp),
    Score: e.score,
    "CVE Critical": e.cve_critical ?? 0,
    "CVE High": e.cve_high ?? 0,
  }));
  return (
    <div className="space-y-4 mt-4">
      <Card>
        <Text className="font-medium mb-3">Score over time</Text>
        <AreaChart
          data={scoreData}
          index="date"
          categories={["Score"]}
          colors={["blue"]}
          valueFormatter={(v) => `${v}%`}
          showLegend={false}
          minValue={0}
          maxValue={100}
          className="h-36"
        />
      </Card>
      {scoreData.some((d) => d["CVE Critical"] > 0 || d["CVE High"] > 0) && (
        <Card>
          <Text className="font-medium mb-3">CVE counts over time</Text>
          <AreaChart
            data={scoreData}
            index="date"
            categories={["CVE Critical", "CVE High"]}
            colors={["rose", "orange"]}
            showLegend
            minValue={0}
            className="h-36"
          />
        </Card>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Report detail panel
// ---------------------------------------------------------------------------

function ReportDetailPanel({
  entry,
  baseUrl,
  onClose,
}: {
  entry: ArchiveEntry;
  baseUrl: string;
  onClose: () => void;
}) {
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${baseUrl}archive/${entry.path}`)
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status}`);
        return r.json();
      })
      .then((d) => {
        setReport(d);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [baseUrl, entry.path]);

  const rules = report?.rules ?? [];
  const failedRules = rules.filter((r) => !r.passed);
  const failedByLevel = failedRules.reduce<Record<string, RuleResult[]>>(
    (acc, r) => {
      const lvl = r.level ?? "other";
      (acc[lvl] ??= []).push(r);
      return acc;
    },
    {},
  );
  const groups = Object.entries(failedByLevel).sort(([a], [b]) => {
    return LEVEL_ORDER.indexOf(a) - LEVEL_ORDER.indexOf(b);
  });

  return (
    <div className="mt-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Title>{imageKey(entry)}</Title>
          <Text className="text-tremor-content">
            {formatDate(entry.timestamp)}
          </Text>
        </div>
        <button
          onClick={onClose}
          className="px-3 py-1.5 text-sm rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          ← Back to archive
        </button>
      </div>

      {/* KPI */}
      <Grid numItemsSm={4} className="gap-4">
        <Card>
          <Text className="font-medium">Score</Text>
          <div className="flex items-center justify-center my-3">
            <span style={{ fontSize: "2.5rem", fontWeight: 700 }}>
              {entry.score}%
            </span>
          </div>
        </Card>
        <Card>
          <Text className="font-medium">Tier</Text>
          <div className="flex items-center justify-center my-3">
            {entry.tier ? (
              <ScoreBadge
                label={entry.tier}
                variant={tierVariant(entry.tier)}
                size="lg"
              />
            ) : (
              <Text>—</Text>
            )}
          </div>
        </Card>
        <Card>
          <Text className="font-medium">Rules</Text>
          <div className="flex items-center justify-center my-3">
            <span style={{ fontSize: "2rem", fontWeight: 700 }}>
              {entry.rules_passed}/{entry.rules_total}
            </span>
          </div>
        </Card>
        <Card>
          <Text className="font-medium">CVE C / H</Text>
          <div className="flex items-center justify-center gap-2 my-3">
            <span className="text-rose-600 font-bold text-2xl">
              {entry.cve_critical ?? "—"}
            </span>
            <span className="text-gray-400">/</span>
            <span className="text-orange-500 font-bold text-2xl">
              {entry.cve_high ?? "—"}
            </span>
          </div>
        </Card>
      </Grid>

      {/* Badges */}
      {(report?.badges?.length ?? 0) > 0 && (
        <div className="flex flex-wrap gap-2">
          {report!.badges!.map((b, i) => (
            <Badge key={i} color={badgeColor(b.class)}>
              {b.label}
            </Badge>
          ))}
        </div>
      )}

      {/* Failed rules */}
      {loading && <Text>Loading report…</Text>}
      {error && (
        <div className="alert alert--warning">
          Could not load full report: {error}
        </div>
      )}
      {!loading && !error && groups.length > 0 && (
        <div>
          <Title className="mb-4">Failed Rules</Title>
          <div className="space-y-4">
            {groups.map(([level, levelRules]) => (
              <div key={level}>
                <div className="flex items-center gap-2 mb-2">
                  <ScoreBadge label={level} variant={levelToVariant(level)} />
                  <Text className="text-sm">{levelRules.length} failed</Text>
                </div>
                <Card>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableHeaderCell>Rule</TableHeaderCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {levelRules.map((r, i) => (
                        <TableRow key={r.slug ?? i}>
                          <TableCell>
                            <Text className="font-medium">
                              {r.description ?? r.slug}
                            </Text>
                            {r.message && (
                              <Text className="text-sm opacity-70 mt-0.5">
                                {r.message}
                              </Text>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Card>
              </div>
            ))}
          </div>
        </div>
      )}
      {!loading && !error && groups.length === 0 && (
        <Card>
          <Badge color="emerald" size="lg">
            All rules passed
          </Badge>
        </Card>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main ArchiveView
// ---------------------------------------------------------------------------

export function ArchiveView(): React.JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  const baseUrl = siteConfig.baseUrl;

  const [entries, setEntries] = useState<ArchiveEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [imageFilter, setImageFilter] = useState("");
  const [tierFilter, setTierFilter] = useState("All");
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [detailEntry, setDetailEntry] = useState<ArchiveEntry | null>(null);

  useEffect(() => {
    fetch(`${baseUrl}archive/manifest.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
      })
      .then((data: ArchiveEntry[]) => {
        setEntries(data);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [baseUrl]);

  const filtered = useMemo(
    () =>
      entries.filter((e) => {
        if (
          imageFilter &&
          !imageKey(e).toLowerCase().includes(imageFilter.toLowerCase())
        )
          return false;
        if (tierFilter !== "All") {
          if (tierFilter === "None" && e.tier) return false;
          if (
            tierFilter !== "None" &&
            e.tier?.toLowerCase() !== tierFilter.toLowerCase()
          )
            return false;
        }
        return true;
      }),
    [entries, imageFilter, tierFilter],
  );

  const uniqueImages = useMemo(
    () => Array.from(new Set(filtered.map(imageKey))),
    [filtered],
  );
  const uniqueImagesAll = new Set(entries.map(imageKey)).size;
  const avgScore =
    entries.length > 0
      ? Math.round(entries.reduce((s, e) => s + e.score, 0) / entries.length)
      : 0;

  if (loading) return <p className="p-6">Loading archive…</p>;

  if (error)
    return (
      <div className="p-6">
        <div className="alert alert--warning">
          <p>Archive not available: {error}</p>
          <p className="text-sm mt-2 opacity-70">
            Run <code>regis-cli analyze … --archive ./static/archive</code> to
            populate the archive.
          </p>
        </div>
      </div>
    );

  if (detailEntry)
    return (
      <div className="p-6">
        <ReportDetailPanel
          entry={detailEntry}
          baseUrl={baseUrl}
          onClose={() => setDetailEntry(null)}
        />
      </div>
    );

  return (
    <div className="p-6 space-y-8">
      {/* KPI */}
      <Grid numItemsSm={3} className="gap-4">
        {[
          { label: "Total Reports", value: entries.length },
          { label: "Unique Images", value: uniqueImagesAll },
          { label: "Avg. Score", value: `${avgScore}%` },
        ].map(({ label, value }) => (
          <Card key={label}>
            <Text className="font-medium">{label}</Text>
            <div className="flex items-center justify-center my-3">
              <span style={{ fontSize: "2.5rem", fontWeight: 700 }}>
                {value}
              </span>
            </div>
          </Card>
        ))}
      </Grid>

      {/* Filters */}
      <Flex className="gap-3 flex-wrap">
        <TextInput
          placeholder="Filter by image…"
          value={imageFilter}
          onValueChange={setImageFilter}
          className="max-w-xs"
        />
        <Select
          value={tierFilter}
          onValueChange={setTierFilter}
          className="max-w-[10rem]"
        >
          {TIERS.map((t) => (
            <SelectItem key={t} value={t}>
              {t}
            </SelectItem>
          ))}
        </Select>
        <Text className="text-tremor-content self-center">
          {filtered.length} report{filtered.length !== 1 ? "s" : ""}
          {uniqueImages.length !== uniqueImagesAll
            ? ` · ${uniqueImages.length} image${uniqueImages.length !== 1 ? "s" : ""}`
            : ""}
        </Text>
      </Flex>

      {/* Images */}
      {uniqueImages.length > 0 && (
        <section>
          <Title className="mb-4">Images</Title>
          <div className="space-y-2">
            {uniqueImages.map((img) => {
              const imgEntries = filtered.filter((e) => imageKey(e) === img);
              const latest = imgEntries[0];
              const isOpen = selectedImage === img;
              return (
                <Card
                  key={img}
                  className="cursor-pointer"
                  onClick={() => setSelectedImage(isOpen ? null : img)}
                >
                  <Flex alignItems="center" justifyContent="between">
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="text-sm font-mono font-semibold truncate">
                        {img}
                      </span>
                      <Badge color="gray" size="xs">
                        {imgEntries.length} report
                        {imgEntries.length !== 1 ? "s" : ""}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {latest.tier && (
                        <ScoreBadge
                          label={latest.tier}
                          variant={tierVariant(latest.tier)}
                        />
                      )}
                      <Badge
                        color={
                          latest.score >= 90
                            ? "emerald"
                            : latest.score >= 70
                              ? "blue"
                              : latest.score >= 50
                                ? "amber"
                                : "rose"
                        }
                      >
                        {latest.score}%
                      </Badge>
                      <span className="text-tremor-content text-xs">
                        {isOpen ? "▲" : "▼"}
                      </span>
                    </div>
                  </Flex>
                  {isOpen && imgEntries.length > 1 && (
                    <ImageTrendChart entries={imgEntries} />
                  )}
                </Card>
              );
            })}
          </div>
        </section>
      )}

      {/* Table */}
      <section>
        <Title className="mb-4">All Reports</Title>
        {filtered.length === 0 ? (
          <Card>
            <Text>No reports match the current filters.</Text>
          </Card>
        ) : (
          <Card>
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Date</TableHeaderCell>
                  <TableHeaderCell>Image</TableHeaderCell>
                  <TableHeaderCell>Tier</TableHeaderCell>
                  <TableHeaderCell>Score</TableHeaderCell>
                  <TableHeaderCell>Rules</TableHeaderCell>
                  <TableHeaderCell>CVE C/H</TableHeaderCell>
                  <TableHeaderCell></TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filtered.map((e) => (
                  <TableRow key={e.id}>
                    <TableCell className="text-sm whitespace-nowrap">
                      {formatDate(e.timestamp)}
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {imageKey(e)}
                    </TableCell>
                    <TableCell>
                      {e.tier ? (
                        <ScoreBadge
                          label={e.tier}
                          variant={tierVariant(e.tier)}
                        />
                      ) : (
                        <Text className="text-xs opacity-50">—</Text>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge
                        color={
                          e.score >= 90
                            ? "emerald"
                            : e.score >= 70
                              ? "blue"
                              : e.score >= 50
                                ? "amber"
                                : "rose"
                        }
                      >
                        {e.score}%
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      {e.rules_passed}/{e.rules_total}
                    </TableCell>
                    <TableCell className="text-sm">
                      {e.cve_critical != null || e.cve_high != null ? (
                        <span>
                          <span className="text-rose-600 font-medium">
                            {e.cve_critical ?? "—"}
                          </span>
                          {" / "}
                          <span className="text-orange-500 font-medium">
                            {e.cve_high ?? "—"}
                          </span>
                        </span>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell>
                      <button
                        onClick={() => setDetailEntry(e)}
                        className="px-2 py-1 text-xs rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                      >
                        View
                      </button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        )}
      </section>

      {/* PowerBI hint */}
      <div className="pt-4 border-t border-gray-200 dark:border-gray-800">
        <Text className="text-xs opacity-50">
          PowerBI: <strong>Get Data → JSON</strong> →{" "}
          <code>{baseUrl}archive/data.json</code>
        </Text>
      </div>
    </div>
  );
}
