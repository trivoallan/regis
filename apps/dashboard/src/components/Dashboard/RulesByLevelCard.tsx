import React from "react";
import { Card, Flex, Text, CategoryBar } from "@tremor/react";
import { ScoreBadge, levelToVariant } from "../ScoreBadge";
import type { RuleResult } from "../ReportProvider";

const LEVEL_ORDER = ["Gold", "Silver", "Bronze", "Critical", "Warning", "Info"];

function levelSortIndex(level: string): number {
  const idx = LEVEL_ORDER.findIndex(
    (l) => l.toLowerCase() === level?.toLowerCase(),
  );
  return idx === -1 ? LEVEL_ORDER.length : idx;
}

interface RulesByLevelCardProps {
  rules: RuleResult[];
}

export function RulesByLevelCard({ rules }: RulesByLevelCardProps) {
  const byLevel = rules.reduce<
    Record<string, { passed: number; failed: number; incomplete: number }>
  >((acc, r) => {
    const lvl = r.level ?? "Other";
    acc[lvl] ??= { passed: 0, failed: 0, incomplete: 0 };
    if (r.status === "incomplete") acc[lvl].incomplete++;
    else if (r.passed) acc[lvl].passed++;
    else acc[lvl].failed++;
    return acc;
  }, {});

  const entries = Object.entries(byLevel).sort(
    ([a], [b]) => levelSortIndex(a) - levelSortIndex(b),
  );

  if (entries.length === 0) return null;

  return (
    <Card>
      <Text className="font-medium mb-4">Rules by Level</Text>
      <div className="space-y-4">
        {entries.map(([level, stats]) => {
          const total = stats.passed + stats.failed + stats.incomplete;
          return (
            <div key={level}>
              <Flex
                justifyContent="between"
                alignItems="center"
                className="mb-1"
              >
                <ScoreBadge label={level} variant={levelToVariant(level)} />
                <Text className="text-tremor-label text-tremor-content">
                  {stats.passed}/{total} passed
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
