import React from "react";

type Variant = "success" | "warning" | "error" | "info" | "outline";

const VARIANT_STYLES: Record<Variant, string> = {
  success:
    "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200",
  warning: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  error: "bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-200",
  info: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  outline:
    "border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400",
};

const SIZE_STYLES = {
  sm: "text-xs px-2 py-0.5",
  md: "text-sm px-2.5 py-0.5",
  lg: "text-base px-3 py-1",
};

interface ScoreBadgeProps {
  label: string;
  variant?: Variant;
  size?: "sm" | "md" | "lg";
}

export function levelToVariant(level: string): Variant {
  const l = level.toLowerCase();
  if (l === "gold") return "success";
  if (l === "silver") return "info";
  if (l === "bronze") return "warning";
  if (l === "critical") return "error";
  if (l === "warning") return "warning";
  if (l === "info") return "info";
  return "outline";
}

export function ScoreBadge({
  label,
  variant = "outline",
  size = "md",
}: ScoreBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ${VARIANT_STYLES[variant]} ${SIZE_STYLES[size]}`}
    >
      {label}
    </span>
  );
}
