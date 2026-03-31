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

interface HadolintIssue {
  code: string;
  message: string;
  level: string;
  line?: number;
}
interface HadolintData {
  passed: boolean;
  issues_count: number;
  issues_by_level?: Record<string, number>;
  issues?: HadolintIssue[];
}

const LEVEL_COLOR: Record<string, "rose" | "orange" | "blue" | "gray"> = {
  error: "rose",
  warning: "orange",
  info: "blue",
  style: "gray",
};

export function HadolintSection({
  data,
}: {
  data: HadolintData;
}): React.JSX.Element {
  const byLevel = Object.entries(data.issues_by_level ?? {}).filter(
    ([, n]) => n > 0,
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
            label={level.charAt(0).toUpperCase() + level.slice(1)}
            value={count}
            badge={<Badge color={LEVEL_COLOR[level] ?? "gray"}>{level}</Badge>}
          />
        ))}
      </Grid>

      {data.issues && data.issues.length > 0 && (
        <Card>
          <Text className="font-medium mb-4">
            Issues ({data.issues.length})
          </Text>
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Code</TableHeaderCell>
                <TableHeaderCell>Level</TableHeaderCell>
                <TableHeaderCell>Line</TableHeaderCell>
                <TableHeaderCell>Message</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.issues.map((issue, i) => (
                <TableRow key={i}>
                  <TableCell>
                    <a
                      href={`https://github.com/hadolint/hadolint/wiki/${issue.code}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-mono"
                    >
                      {issue.code}
                    </a>
                  </TableCell>
                  <TableCell>
                    <Badge color={LEVEL_COLOR[issue.level] ?? "gray"}>
                      {issue.level}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono">
                    {issue.line ?? "—"}
                  </TableCell>
                  <TableCell className="text-sm">{issue.message}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
