import React from "react";
import type { Badge, BadgeClass } from "../types/report";

// -----------------------------------------------------------
// ScoreBadge — Score circulaire avec tier optionnel
// -----------------------------------------------------------

interface ScoreBadgeProps {
  score: number;
  tier?: string | null;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
}

const SIZE_CONFIG = {
  sm: { radius: 26, stroke: 4, fontSize: "0.9rem", wh: 64 },
  md: { radius: 36, stroke: 5, fontSize: "1.2rem", wh: 88 },
  lg: { radius: 48, stroke: 6, fontSize: "1.6rem", wh: 112 },
};

function scoreToColor(score: number): string {
  if (score >= 80) return "var(--regis-success)";
  if (score >= 50) return "var(--regis-warning)";
  return "var(--regis-danger)";
}

export function ScoreBadge({
  score,
  tier,
  size = "md",
  showLabel = true,
  className = "",
}: ScoreBadgeProps) {
  const cfg = SIZE_CONFIG[size];
  const circumference = 2 * Math.PI * cfg.radius;
  const offset = circumference - (score / 100) * circumference;
  const color = scoreToColor(score);

  return (
    <div
      className={`regis-score-badge ${className}`}
      style={{
        display: "inline-flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "0.5rem",
      }}
    >
      <div style={{ position: "relative", width: cfg.wh, height: cfg.wh }}>
        <svg
          width={cfg.wh}
          height={cfg.wh}
          viewBox={`0 0 ${cfg.wh} ${cfg.wh}`}
          style={{ transform: "rotate(-90deg)" }}
        >
          {/* Track */}
          <circle
            cx={cfg.wh / 2}
            cy={cfg.wh / 2}
            r={cfg.radius}
            fill="none"
            stroke="var(--regis-border)"
            strokeWidth={cfg.stroke}
          />
          {/* Progress */}
          <circle
            cx={cfg.wh / 2}
            cy={cfg.wh / 2}
            r={cfg.radius}
            fill="none"
            stroke={color}
            strokeWidth={cfg.stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 0.6s ease" }}
          />
        </svg>
        {/* Score text */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: cfg.fontSize,
            fontWeight: 700,
            color,
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {score}
        </div>
      </div>

      {showLabel && (
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              fontSize: "0.7rem",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              opacity: 0.6,
            }}
          >
            Score
          </div>
          {tier && <TierBadge tier={tier} />}
        </div>
      )}
    </div>
  );
}

// -----------------------------------------------------------
// TierBadge — Gold / Silver / Bronze
// -----------------------------------------------------------

interface TierBadgeProps {
  tier: string;
}

const TIER_STYLES: Record<string, React.CSSProperties> = {
  Gold: {
    background: "linear-gradient(135deg, #ffd700, #ffae00)",
    color: "#5c4b00",
    border: "1px solid #d4af37",
  },
  Silver: {
    background: "linear-gradient(135deg, #d0d0d0, #a9a9a9)",
    color: "#2a2a2a",
    border: "1px solid #999",
  },
  Bronze: {
    background: "linear-gradient(135deg, #cd7f32, #a0522d)",
    color: "#fff",
    border: "1px solid #8b4513",
  },
};

export function TierBadge({ tier }: TierBadgeProps) {
  const style = TIER_STYLES[tier] ?? {
    background: "var(--regis-surface)",
    color: "var(--regis-text)",
    border: "1px solid var(--regis-border)",
  };

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.3rem",
        padding: "0.2rem 0.7rem",
        borderRadius: "2rem",
        fontSize: "0.72rem",
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: "0.06em",
        marginTop: "0.25rem",
        ...style,
      }}
    >
      {tier}
    </span>
  );
}

// -----------------------------------------------------------
// StatusBadge — passed / failed / incomplete + badge class
// -----------------------------------------------------------

interface StatusBadgeProps {
  status?: "passed" | "failed" | "incomplete";
  badgeClass?: BadgeClass;
  label?: string;
  size?: "sm" | "md";
}

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  passed: { bg: "var(--regis-success-bg)", text: "var(--regis-success)" },
  failed: { bg: "var(--regis-danger-bg)", text: "var(--regis-danger)" },
  incomplete: { bg: "var(--regis-warning-bg)", text: "var(--regis-warning)" },
  success: { bg: "var(--regis-success-bg)", text: "var(--regis-success)" },
  warning: { bg: "var(--regis-warning-bg)", text: "var(--regis-warning)" },
  error: { bg: "var(--regis-danger-bg)", text: "var(--regis-danger)" },
  information: { bg: "var(--regis-info-bg)", text: "var(--regis-info)" },
};

export function StatusBadge({
  status,
  badgeClass,
  label,
  size = "sm",
}: StatusBadgeProps) {
  const key = status ?? badgeClass ?? "incomplete";
  const colors = STATUS_COLORS[key] ?? STATUS_COLORS.incomplete;
  const displayLabel = label ?? key;

  return (
    <span
      style={{
        display: "inline-block",
        padding: size === "sm" ? "0.15rem 0.5rem" : "0.25rem 0.7rem",
        borderRadius: "0.25rem",
        fontSize: size === "sm" ? "0.72rem" : "0.85rem",
        fontWeight: 600,
        textTransform: "uppercase",
        letterSpacing: "0.04em",
        background: colors.bg,
        color: colors.text,
        whiteSpace: "nowrap",
      }}
    >
      {displayLabel}
    </span>
  );
}

// -----------------------------------------------------------
// BadgeList — liste de badges de playbook
// -----------------------------------------------------------

interface BadgeListProps {
  badges: Badge[];
}

export function BadgeList({ badges }: BadgeListProps) {
  if (!badges.length) return null;

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
      {badges.map((badge, i) => (
        <StatusBadge
          key={badge.slug ?? i}
          badgeClass={badge.class}
          label={
            badge.label ??
            (badge.value ? `${badge.scope}: ${badge.value}` : badge.scope)
          }
          size="sm"
        />
      ))}
    </div>
  );
}
