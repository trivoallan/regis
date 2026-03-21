import React from "react";
import { Grid, Card, Text, Badge } from "@tremor/react";
import { StatCard } from "./StatCard";

interface EndOfLifeData {
  product: string;
  product_found: boolean;
  tag: string;
  matched_cycle?: string | null;
  is_eol?: boolean | null;
  active_cycles_count: number;
  eol_cycles_count: number;
}

export function EndOfLifeSection({
  data,
}: {
  data: EndOfLifeData;
}): React.JSX.Element {
  if (!data.product_found) {
    return (
      <Card>
        <Text>
          Product "<strong>{data.product}</strong>" not found in endoflife.date
          database.
        </Text>
      </Card>
    );
  }

  const isEol = data.is_eol;
  const statusLabel = isEol
    ? "End of Life"
    : isEol === false
      ? "Supported"
      : "Unknown";
  const statusColor = isEol ? "rose" : isEol === false ? "emerald" : "gray";

  return (
    <Grid numItemsSm={2} numItemsLg={5} className="gap-4">
      <StatCard label="Product" value={data.product} size="lg" />
      <StatCard
        label="Matched Cycle"
        value={data.matched_cycle ?? "—"}
        size="lg"
      />
      <StatCard
        label="Lifecycle Status"
        value={statusLabel}
        size="md"
        badge={<Badge color={statusColor}>{statusLabel}</Badge>}
      />
      <StatCard
        label="Active Cycles"
        value={data.active_cycles_count}
        badge={<Badge color="emerald">Active</Badge>}
      />
      <StatCard
        label="EOL Cycles"
        value={data.eol_cycles_count}
        badge={
          data.eol_cycles_count > 0 ? (
            <Badge color="rose">EOL</Badge>
          ) : undefined
        }
      />
    </Grid>
  );
}
