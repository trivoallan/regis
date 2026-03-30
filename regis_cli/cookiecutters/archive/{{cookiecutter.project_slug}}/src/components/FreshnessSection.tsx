import React from "react";
import { Grid, Badge } from "@tremor/react";
import { StatCard } from "./StatCard";

interface FreshnessData {
  tag_created?: string;
  latest_created?: string | null;
  age_days?: number;
  behind_latest_days?: number | null;
  is_latest?: boolean;
}

function ageBadge(days: number): {
  label: string;
  color: "emerald" | "blue" | "amber" | "rose";
} {
  if (days > 180) return { label: "Stale", color: "rose" };
  if (days > 90) return { label: "Aging", color: "amber" };
  if (days > 30) return { label: "OK", color: "blue" };
  return { label: "Fresh", color: "emerald" };
}

export function FreshnessSection({
  data,
}: {
  data: FreshnessData;
}): React.JSX.Element {
  const age = data.age_days !== undefined ? ageBadge(data.age_days) : null;

  return (
    <Grid numItemsSm={2} numItemsLg={4} className="gap-4">
      <StatCard
        label="Image Age"
        value={
          <>
            {data.age_days ?? "?"}{" "}
            <span style={{ fontSize: "0.4em", fontWeight: 400, opacity: 0.6 }}>
              days
            </span>
          </>
        }
        badge={age ? <Badge color={age.color}>{age.label}</Badge> : undefined}
      />
      <StatCard
        label="Is Latest"
        value={data.is_latest ? "Yes" : "No"}
        size="lg"
        badge={
          <Badge color={data.is_latest ? "emerald" : "rose"}>
            {data.is_latest ? "Latest" : "Not latest"}
          </Badge>
        }
      />
      <StatCard
        label="Behind Latest"
        value={
          data.behind_latest_days != null ? (
            <>
              {data.behind_latest_days}{" "}
              <span
                style={{ fontSize: "0.4em", fontWeight: 400, opacity: 0.6 }}
              >
                days
              </span>
            </>
          ) : (
            "—"
          )
        }
        size={data.behind_latest_days != null ? "xl" : "lg"}
      />
      <StatCard
        label="Created"
        value={
          data.tag_created
            ? new Date(data.tag_created).toLocaleDateString()
            : "N/A"
        }
        size="md"
      />
    </Grid>
  );
}
