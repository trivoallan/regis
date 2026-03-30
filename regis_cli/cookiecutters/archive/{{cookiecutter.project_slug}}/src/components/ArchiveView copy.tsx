import React, { useEffect, useMemo, useState } from "react";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import { useLocation, useHistory } from "@docusaurus/router";
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
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return ts;
  }
}

function tierVariant(
  tier?: string,
): "success" | "warning" | "critical" | "info" | "outline" | "default" {
  if (!tier) return "outline";
  const t = tier.toLowerCase();
  if (t === "gold") return "success";
  if (t === "silver") return "info";
  if (t === "bronze") return "warning";
  return "outline";
}

const TIERS = ["All", "Gold", "Silver", "Bronze", "None"];

// ---------------------------------------------------------------------------
// Trend chart
// ---------------------------------------------------------------------------

function ImageTrendChart({
  entries,
}: {
  entries: ArchiveEntry[];
}): React.JSX.Element {
  const sorted = [...entries].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );
  const chartData = sorted.map((e) => ({
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
          data={chartData}
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
      {chartData.some((d) => d["CVE Critical"] > 0 || d["CVE High"] > 0) && (
        <Card>
          <Text className="font-medium mb-3">CVE counts over time</Text>
          <AreaChart
            data={chartData}
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
// Main ArchiveView
// ---------------------------------------------------------------------------

export function ArchiveView(): React.JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  const history = useHistory();
  const { search } = useLocation();
  const baseUrl = siteConfig.baseUrl;

  const [entries, setEntries] = useState<ArchiveEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [imageFilter, setImageFilter] = useState("");
  const [tierFilter, setTierFilter] = useState("All");
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const archiveUrl = useMemo(() => {
    const params = new URLSearchParams(search);
    return (
      params.get("archive_url") ||
      sessionStorage.getItem("regis_active_archive_url") ||
      `${window.location.origin}${baseUrl}archive/manifest.json`
    );
  }, [search, baseUrl]);

  useEffect(() => {
    setLoading(true);
    fetch(archiveUrl)
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
      })
      .then((data: ArchiveEntry[]) => {
        setEntries(data);
        setError(null);
        setLoading(false);
      })
      .catch((e) => {
        setError(`${e.message} (from ${archiveUrl})`);
        setLoading(false);
      });
  }, [archiveUrl]);

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

  const handleSelectReport = (entry: ArchiveEntry) => {
    const params = new URLSearchParams(search);
    // Resolve relative path to manifest URL
    const fullUrl = new URL(entry.path, archiveUrl).toString();
    params.set("url", fullUrl);
    params.delete("view");
    history.push({ pathname: `${baseUrl}report`, search: params.toString() });
  };

  if (loading)
    return (
      <div className="p-12 text-center">
        <Text>Loading archive…</Text>
      </div>
    );

  if (error) {
    const isManifestErr =
      error.includes("404") ||
      error.includes("Unexpected token '<'") ||
      error.includes("manifest.json");

    return (
      <div className="p-16 max-w-2xl mx-auto text-center">
        <div className="bg-gray-50/50 dark:bg-gray-800/20 p-10 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm transition-all hover:shadow-md">
          <div className="w-16 h-16 bg-blue-50 dark:bg-blue-900/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <svg
              className="w-8 h-8 text-blue-600 dark:text-blue-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
          </div>
          <Title className="text-2xl font-bold mb-3">
            {isManifestErr ? "No Archive Index" : "Archive Error"}
          </Title>
          <Text className="text-gray-500 dark:text-gray-400 mb-8 max-w-md mx-auto leading-relaxed">
            {isManifestErr
              ? "We couldn't find a local manifest.json. You can browse an external archive by providing its URL below."
              : error}
          </Text>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              const input = (e.currentTarget.elements[0] as HTMLInputElement)
                .value;
              if (input) {
                const searchParams = new URLSearchParams(search);
                searchParams.set("archive_url", input);
                history.push({
                  pathname: "/",
                  search: searchParams.toString(),
                });
              }
            }}
            className="flex flex-col gap-3 max-w-sm mx-auto"
          >
            <TextInput
              placeholder="https://example.com/manifest.json"
              className="rounded-xl"
              required
            />
            <button
              type="submit"
              className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-all shadow-sm active:scale-[0.98] cursor-pointer"
            >
              Explore Archive
            </button>
          </form>

          <div className="mt-8 pt-8 border-t border-gray-100 dark:border-gray-800">
            <Text className="text-xs opacity-40">
              Alternately, click <strong>Load URL</strong> in the top bar to
              load a single report JSON.
            </Text>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto">
      <div className="flex flex-col gap-2">
        <Title>Report Archive</Title>
        <Text>Browse historical reports archived from this repository.</Text>
      </div>

      {/* KPI */}
      <Grid numItemsSm={3} className="gap-4">
        {[
          { label: "Total Reports", value: entries.length },
          { label: "Unique Images", value: uniqueImagesAll },
          { label: "Avg. Score", value: `${avgScore}%` },
        ].map(({ label, value }) => (
          <Card key={label} decoration="top" decorationColor="blue">
            <Text className="font-medium">{label}</Text>
            <div className="flex items-center justify-center my-3">
              <span className="text-4xl font-bold text-gray-900 dark:text-gray-100">
                {value}
              </span>
            </div>
          </Card>
        ))}
      </Grid>

      {/* Filters */}
      <Flex className="gap-3 flex-wrap items-center">
        <TextInput
          placeholder="Filter by image name…"
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
        <div className="flex-grow" />
        <Text className="text-tremor-content italic">
          Showing {filtered.length} report{filtered.length !== 1 ? "s" : ""}
          {uniqueImages.length !== uniqueImagesAll
            ? ` (${uniqueImages.length} images)`
            : ""}
        </Text>
      </Flex>

      {/* Images Grouped View */}
      {uniqueImages.length > 0 && (
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Title>Images</Title>
            <Badge color="gray">{uniqueImages.length}</Badge>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {uniqueImages.map((img) => {
              const imgEntries = filtered.filter((e) => imageKey(e) === img);
              const latest = imgEntries[0];
              const isOpen = selectedImage === img;
              return (
                <Card key={img} className="p-4">
                  <Flex alignItems="center" justifyContent="between">
                    <div className="flex flex-col min-w-0">
                      <span className="text-sm font-mono font-bold truncate">
                        {img}
                      </span>
                      <Text className="text-xs opacity-60">
                        {imgEntries.length} execution
                        {imgEntries.length !== 1 ? "s" : ""}
                      </Text>
                    </div>
                    <div className="flex items-center gap-3">
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
                      <button
                        onClick={() => setSelectedImage(isOpen ? null : img)}
                        className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors text-xs"
                      >
                        {isOpen ? "Hide Trends" : "Show Trends"}
                      </button>
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

      {/* Full Reports Table */}
      <section>
        <Title className="mb-4">All Reports</Title>
        {filtered.length === 0 ? (
          <Card>
            <Text>No reports match the current filters.</Text>
          </Card>
        ) : (
          <Card className="p-0 overflow-hidden">
            <Table>
              <TableHead className="bg-gray-50 dark:bg-gray-800/50">
                <TableRow>
                  <TableHeaderCell>Date</TableHeaderCell>
                  <TableHeaderCell>Image</TableHeaderCell>
                  <TableHeaderCell>Tier</TableHeaderCell>
                  <TableHeaderCell>Score</TableHeaderCell>
                  <TableHeaderCell>Rules</TableHeaderCell>
                  <TableHeaderCell>CVE C/H</TableHeaderCell>
                  <TableHeaderCell className="text-right">
                    Action
                  </TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filtered.map((e) => (
                  <TableRow
                    key={e.id}
                    className="hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors"
                  >
                    <TableCell className="text-sm whitespace-nowrap">
                      {formatDate(e.timestamp)}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
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
                    <TableCell className="text-sm font-medium">
                      {e.rules_passed}/{e.rules_total}
                    </TableCell>
                    <TableCell className="text-sm">
                      {e.cve_critical != null || e.cve_high != null ? (
                        <Flex justifyContent="start" className="gap-1.5">
                          <span className="text-rose-600 font-bold">
                            {e.cve_critical ?? 0}
                          </span>
                          <span className="opacity-30">/</span>
                          <span className="text-orange-500 font-bold">
                            {e.cve_high ?? 0}
                          </span>
                        </Flex>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <button
                        onClick={() => handleSelectReport(e)}
                        className="px-3 py-1 text-xs font-semibold rounded bg-blue-50 text-blue-600 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400 border border-blue-200 dark:border-blue-800 transition-colors"
                      >
                        View Full Report
                      </button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        )}
      </section>
    </div>
  );
}
