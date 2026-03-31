/**
 * StatCard — Shared card for analyzer KPI metrics.
 * Mirrors the layout pattern of ScoreCard on the Summary page.
 */

import React from "react";
import { Card, Text } from "@tremor/react";

const SIZE_STYLE: Record<string, string> = {
  xl: "2.5rem",
  lg: "1.75rem",
  md: "1.25rem",
  sm: "1rem",
};

interface StatCardProps {
  label: string;
  value: React.ReactNode;
  badge?: React.ReactNode;
  /** xl=2.5rem (numbers), lg=1.75rem, md=1.25rem (text), sm=1rem */
  size?: "xl" | "lg" | "md" | "sm";
}

export function StatCard({ label, value, size = "xl" }: StatCardProps) {
  return (
    <Card className="flex flex-col">
      <Text className="font-medium">{label}</Text>
      <div className="flex flex-1 items-center justify-center my-4 text-center">
        <span
          style={{ fontSize: SIZE_STYLE[size], fontWeight: 700, lineHeight: 1 }}
        >
          {value}
        </span>
      </div>
    </Card>
  );
}
