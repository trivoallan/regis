import React from "react";
import {
  Grid,
  Card,
  Text,
  Badge,
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
} from "@tremor/react";
import { StatCard } from "./StatCard";

interface DockleIssue {
  code: string;
  level: string;
  title: string;
  alerts: string[];
}
interface DockleData {
  passed: boolean;
  issues_count: number;
  issues_by_level: Record<string, number>;
  issues: DockleIssue[];
}

const LEVEL_COLOR: Record<string, "rose" | "orange" | "blue" | "gray"> = {
  FATAL: "rose",
  WARN: "orange",
  INFO: "blue",
  SKIP: "gray",
};

export function DockleSection({
  data,
}: {
  data: DockleData;
}): React.JSX.Element {
  const byLevel = Object.entries(data.issues_by_level ?? {}).filter(
    ([level, n]) => n > 0 && level !== "PASS" && level !== "SKIP",
  );
  const displayedIssues = (data.issues ?? []).filter(
    (i) => i.level !== "PASS" && i.level !== "SKIP",
  );

  return (
    <div className="space-y-6">
      <Grid
        numItemsSm={2}
        numItemsLg={Math.min(4, 2 + byLevel.length)}
        className="gap-4"
      >
        <StatCard
          label="Status"
          value={data.passed ? "Passed" : "Issues"}
          size="lg"
          badge={
            <Badge color={data.passed ? "emerald" : "rose"}>
              {data.passed ? "✓ Passed" : "✗ Failed"}
            </Badge>
          }
        />
        <StatCard label="Total Issues" value={data.issues_count} />
        {byLevel.map(([level, count]) => (
          <StatCard
            key={level}
            label={level}
            value={count}
            badge={<Badge color={LEVEL_COLOR[level] ?? "gray"}>{level}</Badge>}
          />
        ))}
      </Grid>

      {displayedIssues.length > 0 && (
        <Card>
          <Text className="font-medium mb-4">
            Issues ({displayedIssues.length})
          </Text>
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Code</TableHeaderCell>
                <TableHeaderCell>Level</TableHeaderCell>
                <TableHeaderCell>Description</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {displayedIssues.map((issue, i) => (
                <TableRow key={i}>
                  <TableCell className="font-mono font-semibold text-sm">
                    {issue.code}
                  </TableCell>
                  <TableCell>
                    <Badge color={LEVEL_COLOR[issue.level] ?? "gray"}>
                      {issue.level}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm font-semibold">{issue.title}</div>
                    {issue.alerts.length > 0 && (
                      <ul className="text-xs mt-1 opacity-70 list-disc list-inside">
                        {issue.alerts.map((a, j) => (
                          <li key={j}>{a}</li>
                        ))}
                      </ul>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
