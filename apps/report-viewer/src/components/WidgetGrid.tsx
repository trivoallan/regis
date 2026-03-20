/**
 * WidgetGrid — Grid of KPI cards from a playbook section's widgets.
 */

import React from "react";
import type { Widget } from "./ReportProvider";

interface WidgetGridProps {
  widgets: Widget[];
}

function WidgetValue({ value }: { value: unknown }) {
  if (value === true) return <span>✅</span>;
  if (value === false) return <span>❌</span>;
  if (value === null || value === undefined)
    return <span style={{ opacity: 0.5 }}>N/A</span>;
  return <span>{String(value)}</span>;
}

export function WidgetGrid({ widgets }: WidgetGridProps): React.JSX.Element {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 250px), 1fr))",
        gap: "0.75rem",
        marginBottom: "1.5rem",
      }}
    >
      {widgets.map((w, i) => {
        const content = (
          <div
            style={{
              padding: "1rem",
              background: "var(--ifm-card-background-color)",
              borderRadius: "8px",
              border: "1px solid var(--ifm-color-emphasis-200)",
              textAlign: (w.options?.align as string) ?? "left",
              height: "100%",
            }}
          >
            {w.options?.title && (
              <h6
                style={{
                  marginBottom: "0.5rem",
                  color: "var(--ifm-color-primary)",
                  fontSize: "0.85rem",
                }}
              >
                {String(w.options.title)}
              </h6>
            )}
            {w.icon && <span style={{ fontSize: "1.5rem" }}>{w.icon}</span>}
            <strong
              style={{
                fontSize: "0.8rem",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                opacity: 0.8,
                display: "block",
              }}
            >
              {w.label}
            </strong>
            <span
              style={{
                fontSize: "1.8rem",
                fontWeight: 700,
                lineHeight: 1,
                display: "block",
                marginTop: "0.25rem",
              }}
            >
              <WidgetValue value={w.resolved_value} />
            </span>
            {w.resolved_subvalue && (
              <small style={{ opacity: 0.7, fontSize: "0.85rem" }}>
                {w.resolved_subvalue}
              </small>
            )}
          </div>
        );

        if (w.resolved_url) {
          return (
            <a
              key={i}
              href={w.resolved_url}
              style={{ textDecoration: "none", color: "inherit" }}
              target="_blank"
              rel="noopener noreferrer"
            >
              {content}
            </a>
          );
        }

        return <div key={i}>{content}</div>;
      })}
    </div>
  );
}
