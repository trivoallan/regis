/**
 * TierBadge — Displays the tier with an icon and styling.
 */

import React from "react";

interface TierBadgeProps {
  tier: string;
}

const TIER_CONFIG: Record<string, { icon: string; gradient: string }> = {
  gold: {
    icon: "🥇",
    gradient: "linear-gradient(135deg, #f9a825, #ff8f00)",
  },
  silver: {
    icon: "🥈",
    gradient: "linear-gradient(135deg, #90a4ae, #607d8b)",
  },
  bronze: {
    icon: "🥉",
    gradient: "linear-gradient(135deg, #a1887f, #795548)",
  },
  none: {
    icon: "⭕",
    gradient: "linear-gradient(135deg, #757575, #424242)",
  },
};

export function TierBadge({ tier }: TierBadgeProps): React.JSX.Element {
  const config = TIER_CONFIG[tier?.toLowerCase()] ?? TIER_CONFIG.none;

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.4rem",
        background: config.gradient,
        color: "#fff",
        padding: "0.3rem 0.8rem",
        borderRadius: "6px",
        fontSize: "0.9rem",
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: "0.05em",
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
      }}
    >
      <span style={{ fontSize: "1.1rem" }}>{config.icon}</span>
      {tier} Tier
    </span>
  );
}
