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

interface Indicator {
  name: string;
  status: "success" | "failure" | "warning";
  message: string;
}
interface ProvenanceData {
  has_provenance: boolean;
  has_cosign_signature: boolean;
  source_tracked: boolean;
  indicators_count: number;
  indicators?: Indicator[];
}

const STATUS_COLOR: Record<string, "emerald" | "rose" | "amber"> = {
  success: "emerald",
  failure: "rose",
  warning: "amber",
};

export function ProvenanceSection({
  data,
}: {
  data: ProvenanceData;
}): React.JSX.Element {
  return (
    <div className="space-y-6">
      <Grid numItemsSm={2} numItemsLg={3} className="gap-4">
        <StatCard
          label="SLSA Provenance"
          value={data.has_provenance ? "Found" : "Missing"}
          size="lg"
          badge={
            <Badge color={data.has_provenance ? "emerald" : "rose"}>
              {data.has_provenance ? "✓ Present" : "✗ Absent"}
            </Badge>
          }
        />
        <StatCard
          label="Cosign Signature"
          value={data.has_cosign_signature ? "Signed" : "Unsigned"}
          size="lg"
          badge={
            <Badge color={data.has_cosign_signature ? "emerald" : "rose"}>
              {data.has_cosign_signature ? "✓ Signed" : "✗ Unsigned"}
            </Badge>
          }
        />
        <StatCard
          label="Source Tracked"
          value={data.source_tracked ? "Yes" : "No"}
          size="lg"
          badge={
            <Badge color={data.source_tracked ? "emerald" : "rose"}>
              {data.source_tracked ? "✓ Tracked" : "✗ Not tracked"}
            </Badge>
          }
        />
      </Grid>

      {data.indicators && data.indicators.length > 0 && (
        <Card>
          <Text className="font-medium mb-4">
            Indicators ({data.indicators.length})
          </Text>
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Indicator</TableHeaderCell>
                <TableHeaderCell>Details</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.indicators.map((ind, i) => (
                <TableRow key={i}>
                  <TableCell>
                    <Badge color={STATUS_COLOR[ind.status]}>{ind.status}</Badge>
                  </TableCell>
                  <TableCell className="font-semibold">{ind.name}</TableCell>
                  <TableCell className="text-sm">{ind.message}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
