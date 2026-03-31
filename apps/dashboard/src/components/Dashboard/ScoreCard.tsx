import React from "react";
import { Card, Flex, Text, Metric, CategoryBar, Badge } from "@tremor/react";
import { TierBadge } from "../TierBadge";

interface ScoreCardProps {
  score: number;
  label: string;
  passed?: number;
  total?: number;
  subtitle?: string;
  tier?: string;
}

export function ScoreCard({
  score,
  label,
  passed,
  total,
  subtitle,
  tier,
}: ScoreCardProps) {
  const failed = Math.max(0, (total ?? 0) - (passed ?? 0));
  const color: "emerald" | "amber" | "rose" =
    score >= 80 ? "emerald" : score >= 50 ? "amber" : "rose";

  return (
    <Card className="flex flex-col">
      <Flex justifyContent="between" alignItems="start">
        <Text className="font-medium">{label}</Text>
        {tier ? (
          <TierBadge tier={tier} size="sm" />
        ) : (
          <Badge color={color} size="xs">
            {score}%
          </Badge>
        )}
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
          {score}%
        </span>
      </div>
      {subtitle && (
        <Text className="text-tremor-default text-tremor-content">
          {subtitle}
        </Text>
      )}
      {total !== undefined && total > 0 && (
        <>
          <CategoryBar
            values={[passed ?? 0, failed]}
            colors={["emerald", "rose"]}
            className="mt-4"
            showLabels={false}
          />
        </>
      )}
    </Card>
  );
}
