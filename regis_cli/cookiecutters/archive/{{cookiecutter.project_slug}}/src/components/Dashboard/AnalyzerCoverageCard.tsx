import React from "react";
import { Card, Flex, Text, Metric, ProgressBar, Badge } from "@tremor/react";

interface AnalyzerCoverageCardProps {
  analyzers: string[];
  totalExpected?: number;
}

const ANALYZER_LABELS: Record<string, string> = {
  skopeo: "Skopeo",
  trivy: "Trivy",
  hadolint: "Hadolint",
  sbom: "SBOM",
  dockle: "Dockle",
  freshness: "Freshness",
  size: "Size",
  endoflife: "End-of-Life",
  popularity: "Popularity",
  scorecarddev: "Scorecard",
  provenance: "Provenance",
  versioning: "Versioning",
};

export function AnalyzerCoverageCard({
  analyzers,
  totalExpected = 12,
}: AnalyzerCoverageCardProps) {
  const coverage = Math.round((analyzers.length / totalExpected) * 100);
  const color: "emerald" | "amber" | "rose" =
    coverage >= 80 ? "emerald" : coverage >= 50 ? "amber" : "rose";

  return (
    <Card className="flex flex-col">
      <Flex justifyContent="between" alignItems="start">
        <Text className="font-medium">Analyzer Coverage</Text>
        <Badge color={color} size="xs">
          {analyzers.length} run
        </Badge>
      </Flex>
      <div className="flex flex-1 items-center justify-center my-4">
        <span
          style={{ fontSize: "3.75rem", fontWeight: 700, lineHeight: 1 }}
          className={
            color === "emerald"
              ? "text-emerald-600 dark:text-emerald-400"
              : color === "amber"
                ? "text-amber-600 dark:text-amber-400"
                : "text-rose-600 dark:text-rose-400"
          }
        >
          {coverage}%
        </span>
      </div>
      <ProgressBar value={coverage} color={color} className="mt-4" />
    </Card>
  );
}
