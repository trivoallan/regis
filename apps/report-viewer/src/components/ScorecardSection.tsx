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

interface Check {
  name: string;
  score: number;
  reason: string;
  details?: string[];
}
interface ScorecardData {
  scorecard_available: boolean;
  source_repo?: string;
  score?: number;
  checks?: Check[];
}

function scoreColor(s: number): "emerald" | "amber" | "rose" {
  return s >= 8 ? "emerald" : s >= 5 ? "amber" : "rose";
}

export function ScorecardSection({
  data,
}: {
  data: ScorecardData;
}): React.JSX.Element {
  if (!data.scorecard_available) {
    return (
      <Card>
        <Text>OpenSSF Scorecard not available for this repository.</Text>
      </Card>
    );
  }

  const score = data.score ?? 0;

  return (
    <div className="space-y-6">
      <Grid numItemsSm={1} numItemsLg={2} className="gap-4">
        <StatCard
          label="Overall Score"
          value={
            <>
              {score.toFixed(1)}
              <span
                style={{ fontSize: "0.4em", fontWeight: 400, opacity: 0.6 }}
              >
                {" "}
                / 10
              </span>
            </>
          }
          badge={
            <Badge color={scoreColor(score)}>
              {score >= 8 ? "Good" : score >= 5 ? "Moderate" : "Poor"}
            </Badge>
          }
        />
        <Card className="flex flex-col">
          <Text className="font-medium">Source Repository</Text>
          <div className="flex flex-1 items-center justify-center my-4 text-center">
            {data.source_repo ? (
              <a
                href={data.source_repo}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm break-all"
              >
                {data.source_repo}
              </a>
            ) : (
              <Text>—</Text>
            )}
          </div>
        </Card>
      </Grid>

      {data.checks && data.checks.length > 0 && (
        <Card>
          <Text className="font-medium mb-4">
            Checks ({data.checks.length})
          </Text>
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Check</TableHeaderCell>
                <TableHeaderCell>Score</TableHeaderCell>
                <TableHeaderCell>Reason</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {[...data.checks]
                .sort((a, b) => a.score - b.score)
                .map((check, i) => (
                  <TableRow key={i}>
                    <TableCell className="font-semibold">
                      {check.name}
                    </TableCell>
                    <TableCell>
                      {check.score === -1 ? (
                        <Badge color="gray">N/A</Badge>
                      ) : (
                        <Badge color={scoreColor(check.score)}>
                          {check.score} / 10
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-sm">{check.reason}</TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
