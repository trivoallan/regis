import React from "react";
import { Card, Flex, Text, CategoryBar } from "@tremor/react";
import type { RuleResult } from "../ReportProvider";

interface RulesByTagCardProps {
  rules: RuleResult[];
}

export function RulesByTagCard({ rules }: RulesByTagCardProps) {
  const byTag = rules.reduce<
    Record<string, { passed: number; failed: number; incomplete: number }>
  >((acc, r) => {
    for (const tag of r.tags ?? []) {
      acc[tag] ??= { passed: 0, failed: 0, incomplete: 0 };
      if (r.status === "incomplete") acc[tag].incomplete++;
      else if (r.passed) acc[tag].passed++;
      else acc[tag].failed++;
    }
    return acc;
  }, {});

  const entries = Object.entries(byTag).sort(([a], [b]) => a.localeCompare(b));

  if (entries.length === 0) return null;

  return (
    <Card>
      <Text className="font-medium mb-4">Rules by Tag</Text>
      <div className="space-y-4">
        {entries.map(([tag, stats]) => {
          const total = stats.passed + stats.failed + stats.incomplete;
          const score = Math.round((stats.passed / total) * 100);
          return (
            <div key={tag}>
              <Flex
                justifyContent="between"
                alignItems="center"
                className="mb-1"
              >
                <Text className="text-tremor-default font-medium capitalize">
                  {tag}
                </Text>
                <Text className="text-tremor-label text-tremor-content">
                  {stats.passed}/{total} passed · {score}%
                </Text>
              </Flex>
              <CategoryBar
                values={[stats.passed, stats.failed, stats.incomplete]}
                colors={["emerald", "rose", "amber"]}
                showLabels={false}
              />
            </div>
          );
        })}
      </div>
    </Card>
  );
}
