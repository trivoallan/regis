import React from "react";
import {
  Grid,
  Card,
  Text,
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
} from "@tremor/react";
import { StatCard } from "./StatCard";

interface PopularityData {
  available: boolean;
  pull_count?: number;
  star_count?: number;
  description?: string;
  last_updated?: string;
  date_registered?: string;
}

function fmt(n?: number): string {
  if (n === undefined) return "N/A";
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return n.toLocaleString();
}

export function PopularitySection({
  data,
}: {
  data: PopularityData;
}): React.JSX.Element {
  if (!data.available) {
    return (
      <Card>
        <Text>Popularity metrics not available for this registry.</Text>
      </Card>
    );
  }

  const details = [
    { label: "Description", value: data.description ?? "—" },
    {
      label: "Last Updated",
      value: data.last_updated
        ? new Date(data.last_updated).toLocaleDateString()
        : "—",
    },
    {
      label: "Registered",
      value: data.date_registered
        ? new Date(data.date_registered).toLocaleDateString()
        : "—",
    },
  ];

  return (
    <div className="space-y-6">
      <Grid numItemsSm={2} numItemsLg={2} className="gap-4">
        <StatCard label="Pulls" value={fmt(data.pull_count)} size="lg" />
        <StatCard label="Stars" value={fmt(data.star_count)} size="lg" />
      </Grid>

      <Card>
        <Text className="font-medium mb-4">Details</Text>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>Field</TableHeaderCell>
              <TableHeaderCell>Value</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {details.map((row) => (
              <TableRow key={row.label}>
                <TableCell className="font-medium">{row.label}</TableCell>
                <TableCell>{row.value}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
