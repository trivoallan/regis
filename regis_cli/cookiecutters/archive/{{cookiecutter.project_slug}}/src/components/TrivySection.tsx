import React, { useState } from "react";
import {
  Grid,
  Card,
  Text,
  Badge,
  CategoryBar,
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
} from "@tremor/react";
import { StatCard } from "./StatCard";

interface TrivyVulnerability {
  VulnerabilityID: string;
  Severity: string;
  Title?: string;
  PkgName?: string;
  InstalledVersion?: string;
  FixedVersion?: string;
  PublishedDate?: string;
  LastModifiedDate?: string;
}
interface TrivyTarget {
  Target: string;
  Vulnerabilities?: TrivyVulnerability[];
}
interface TrivyData {
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

const SEVERITY_COLOR: Record<
  string,
  "rose" | "orange" | "amber" | "blue" | "gray"
> = {
  CRITICAL: "rose",
  HIGH: "orange",
  MEDIUM: "amber",
  LOW: "blue",
  UNKNOWN: "gray",
};

const PAGE_SIZE = 50;

function byDate(a: TrivyVulnerability, b: TrivyVulnerability): number {
  const da = a.PublishedDate ?? a.LastModifiedDate ?? "";
  const db = b.PublishedDate ?? b.LastModifiedDate ?? "";
  return db.localeCompare(da);
}

function VulnTable({
  vulns,
  severity,
}: {
  vulns: (TrivyVulnerability & { target: string })[];
  severity: "CRITICAL" | "HIGH";
}): React.JSX.Element | null {
  const [page, setPage] = useState(0);
  if (vulns.length === 0) return null;

  const color = SEVERITY_COLOR[severity];
  const pageCount = Math.ceil(vulns.length / PAGE_SIZE);
  const pageVulns = vulns.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const Pager = ({ className = "" }: { className?: string }) =>
    pageCount > 1 ? (
      <div className={`flex items-center gap-2 ${className}`}>
        <button
          onClick={() => setPage((p) => Math.max(0, p - 1))}
          disabled={page === 0}
          className="px-3 py-1 text-sm rounded border border-gray-300 dark:border-gray-600 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          ←
        </button>
        <Text className="text-sm">
          {page + 1} / {pageCount}
        </Text>
        <button
          onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
          disabled={page === pageCount - 1}
          className="px-3 py-1 text-sm rounded border border-gray-300 dark:border-gray-600 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          →
        </button>
      </div>
    ) : null;

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Badge color={color}>{severity}</Badge>
          <Text className="font-medium">{vulns.length} vulnerabilities</Text>
        </div>
        <Pager />
      </div>
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>ID</TableHeaderCell>
            <TableHeaderCell>Package</TableHeaderCell>
            <TableHeaderCell>Installed</TableHeaderCell>
            <TableHeaderCell>Fixed</TableHeaderCell>
            <TableHeaderCell>Published</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {pageVulns.map((v, i) => (
            <TableRow key={i}>
              <TableCell>
                <a
                  href={`https://nvd.nist.gov/vuln/detail/${v.VulnerabilityID}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-sm"
                >
                  {v.VulnerabilityID}
                </a>
              </TableCell>
              <TableCell className="font-mono text-sm">{v.PkgName}</TableCell>
              <TableCell className="font-mono text-sm">
                {v.InstalledVersion}
              </TableCell>
              <TableCell className="font-mono text-sm">
                {v.FixedVersion ?? "—"}
              </TableCell>
              <TableCell className="text-sm">
                {v.PublishedDate
                  ? new Date(v.PublishedDate).toLocaleDateString()
                  : "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {pageCount > 1 && (
        <div className="flex items-center justify-between mt-4">
          <Text className="text-sm opacity-60">
            {page * PAGE_SIZE + 1}–
            {Math.min((page + 1) * PAGE_SIZE, vulns.length)} / {vulns.length}
          </Text>
          <Pager />
        </div>
      )}
    </Card>
  );
}

export function TrivySection({ data }: { data: TrivyData }): React.JSX.Element {
  const allVulns = (
    data.targets?.flatMap(
      (t) => t.Vulnerabilities?.map((v) => ({ ...v, target: t.Target })) ?? [],
    ) ?? []
  ).sort(byDate);

  const criticalVulns = allVulns.filter((v) => v.Severity === "CRITICAL");
  const highVulns = allVulns.filter((v) => v.Severity === "HIGH");

  return (
    <div className="space-y-6">
      <Grid numItemsSm={2} numItemsLg={5} className="gap-4">
        <StatCard label="Total" value={data.vulnerability_count} />
        <StatCard
          label="Critical"
          value={data.critical_count}
          badge={
            data.critical_count > 0 ? (
              <Badge color="rose">Critical</Badge>
            ) : undefined
          }
        />
        <StatCard
          label="High"
          value={data.high_count}
          badge={
            data.high_count > 0 ? <Badge color="orange">High</Badge> : undefined
          }
        />
        <StatCard label="Fixable" value={data.fixed_count} />
        <StatCard
          label="Secrets"
          value={data.secrets_count}
          badge={
            data.secrets_count > 0 ? (
              <Badge color="rose">Detected</Badge>
            ) : undefined
          }
        />
      </Grid>

      {data.vulnerability_count > 0 && (
        <Card>
          <Text className="font-medium mb-3">Severity Distribution</Text>
          <CategoryBar
            values={[
              data.critical_count,
              data.high_count,
              data.medium_count,
              data.low_count,
              data.unknown_count,
            ]}
            colors={["rose", "orange", "amber", "blue", "gray"]}
            showLabels={false}
          />
          <div className="flex gap-2 mt-3 flex-wrap">
            {[
              { label: "Critical", count: data.critical_count, color: "rose" },
              { label: "High", count: data.high_count, color: "orange" },
              { label: "Medium", count: data.medium_count, color: "amber" },
              { label: "Low", count: data.low_count, color: "blue" },
              { label: "Unknown", count: data.unknown_count, color: "gray" },
            ]
              .filter((s) => s.count > 0)
              .map((s) => (
                <Badge key={s.label} color={s.color as never}>
                  {s.label}: {s.count}
                </Badge>
              ))}
          </div>
        </Card>
      )}

      {criticalVulns.length === 0 && highVulns.length === 0 ? (
        <Card>
          <Badge color="emerald" size="lg">
            No Critical or High vulnerabilities detected
          </Badge>
        </Card>
      ) : (
        <>
          <VulnTable vulns={criticalVulns} severity="CRITICAL" />
          <VulnTable vulns={highVulns} severity="HIGH" />
        </>
      )}
    </div>
  );
}
