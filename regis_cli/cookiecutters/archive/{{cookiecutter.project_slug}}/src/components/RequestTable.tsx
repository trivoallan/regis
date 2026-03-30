/**
 * RequestTable — Displays the request parameters as a grid of cards.
 */

import React from "react";
import { Card, Grid, Text } from "@tremor/react";
import { useReport } from "./ReportProvider";

export function RequestTable(): React.JSX.Element {
  const { report } = useReport();
  if (!report?.request) return <p>No request metadata available.</p>;

  const req = report.request;
  const fields = [
    {
      label: "Timestamp",
      value: req.timestamp
        ? new Date(req.timestamp).toLocaleString()
        : undefined,
    },
    { label: "Platform", value: req.platform },
  ].filter((f) => f.value);

  return (
    <Grid numItemsSm={2} numItemsLg={3} className="gap-4">
      {fields.map((field) => (
        <Card key={field.label} className="p-4">
          <Text className="text-tremor-label text-tremor-content uppercase tracking-wider font-semibold">
            {field.label}
          </Text>
          <p className="mt-1 text-sm font-mono break-all text-tremor-content-strong dark:text-dark-tremor-content-strong">
            {field.value}
          </p>
        </Card>
      ))}
    </Grid>
  );
}
