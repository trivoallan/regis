/**
 * ScoreBadge — Colored badge for severity levels and status indicators.
 */

import React from "react";

interface ScoreBadgeProps {
  label: string;
  variant?: "info" | "warning" | "critical" | "success" | "outline" | "default";
}

const VARIANT_STYLES: Record<string, React.CSSProperties> = {
  info: {
    background: "var(--ifm-color-info-contrast-background)",
    color: "var(--ifm-color-info-contrast-foreground)",
    border: "1px solid var(--ifm-color-info-dark)",
  },
  warning: {
    background: "var(--ifm-color-warning-contrast-background)",
    color: "var(--ifm-color-warning-contrast-foreground)",
    border: "1px solid var(--ifm-color-warning-dark)",
  },
  critical: {
    background: "var(--ifm-color-danger-contrast-background)",
    color: "var(--ifm-color-danger-contrast-foreground)",
    border: "1px solid var(--ifm-color-danger-dark)",
  },
  success: {
    background: "var(--ifm-color-success-contrast-background)",
    color: "var(--ifm-color-success-contrast-foreground)",
    border: "1px solid var(--ifm-color-success-dark)",
  },
  outline: {
    background: "transparent",
    color: "var(--ifm-font-color-base)",
    border: "1px solid var(--ifm-color-emphasis-300)",
  },
  default: {
    background: "var(--ifm-color-emphasis-200)",
    color: "var(--ifm-font-color-base)",
    border: "1px solid var(--ifm-color-emphasis-300)",
  },
};

export function ScoreBadge({
  label,
  variant = "default",
}: ScoreBadgeProps): React.JSX.Element {
  const style: React.CSSProperties = {
    ...(VARIANT_STYLES[variant] ?? VARIANT_STYLES.default),
    padding: "0.15rem 0.5rem",
    borderRadius: "4px",
    fontSize: "0.75rem",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.03em",
    display: "inline-block",
    lineHeight: 1.4,
  };

  return <span style={style}>{label}</span>;
}

/** Map a level string to the appropriate variant */
export function levelToVariant(level: string): ScoreBadgeProps["variant"] {
  switch (level?.toLowerCase()) {
    case "critical":
      return "critical";
    case "warning":
      return "warning";
    case "info":
      return "info";
    case "gold":
    case "silver":
    case "bronze":
      return "success";
    default:
      return "default";
  }
}
