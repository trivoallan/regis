/**
 * SkopeoSection — Displays detailed image metadata and platform configuration.
 */

import React from "react";

interface PlatformDetail {
  architecture: string;
  os: string;
  variant?: string;
  digest?: string;
  created?: string;
  layers_count: number;
  size: number;
  user: string;
  exposed_ports: string[];
  env: string[];
  labels: Record<string, string>;
}

interface SkopeoData {
  analyzer: string;
  repository: string;
  tag: string;
  platforms: PlatformDetail[];
  inspect: Record<string, unknown>;
  tags: string[];
}

interface SkopeoSectionProps {
  data: SkopeoData;
}

export function SkopeoSection({ data }: SkopeoSectionProps): React.JSX.Element {
  return (
    <div>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "1rem",
          marginBottom: "1.5rem",
        }}
      >
        {data.platforms.map((p, i) => (
          <div
            key={i}
            className="stat-card"
            style={{ flex: "1 1 300px", textAlign: "left" }}
          >
            <div className="stat-card__label">
              Platform: {p.os}/{p.architecture}{" "}
              {p.variant ? `(${p.variant})` : ""}
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "0.5rem",
                marginTop: "0.5rem",
                fontSize: "0.9rem",
              }}
            >
              <div>
                <strong>User:</strong> <code>{p.user || "root (default)"}</code>
              </div>
              <div>
                <strong>Layers:</strong> {p.layers_count}
              </div>
              <div>
                <strong>Size:</strong> {(p.size / 1024 / 1024).toFixed(1)} MB
              </div>
            </div>

            {p.exposed_ports && p.exposed_ports.length > 0 && (
              <div style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
                <strong>Exposed Ports:</strong>
                <div
                  style={{
                    display: "flex",
                    gap: "0.4rem",
                    flexWrap: "wrap",
                    marginTop: "0.2rem",
                  }}
                >
                  {p.exposed_ports.map((port) => (
                    <span
                      key={port}
                      style={{
                        padding: "1px 6px",
                        background: "var(--ifm-color-primary-lightest)",
                        color: "var(--ifm-color-primary-darkest)",
                        borderRadius: "4px",
                        fontSize: "0.75rem",
                      }}
                    >
                      {port}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {p.labels && Object.keys(p.labels).length > 0 && (
              <details style={{ marginTop: "0.5rem", fontSize: "0.8rem" }}>
                <summary style={{ cursor: "pointer", opacity: 0.7 }}>
                  Labels ({Object.keys(p.labels).length})
                </summary>
                <div
                  style={{
                    padding: "0.5rem",
                    background: "var(--ifm-color-emphasis-100)",
                    borderRadius: "4px",
                    marginTop: "0.2rem",
                    maxHeight: "150px",
                    overflowY: "auto",
                  }}
                >
                  {Object.entries(p.labels).map(([k, v]) => (
                    <div
                      key={k}
                      style={{ marginBottom: "2px", wordBreak: "break-all" }}
                    >
                      <strong style={{ opacity: 0.8 }}>{k}:</strong> {v}
                    </div>
                  ))}
                </div>
              </details>
            )}

            <div
              style={{
                marginTop: "0.5rem",
                fontSize: "0.75rem",
                opacity: 0.5,
                wordBreak: "break-all",
              }}
            >
              Digest: <code>{p.digest}</code>
            </div>
          </div>
        ))}
      </div>

      {data.tags && data.tags.length > 0 && (
        <details>
          <summary style={{ cursor: "pointer", fontWeight: 600 }}>
            Available Tags ({data.tags.length})
          </summary>
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "0.4rem",
              padding: "1rem 0",
            }}
          >
            {data.tags.slice(0, 50).map((t) => (
              <span
                key={t}
                style={{
                  padding: "2px 8px",
                  background: "var(--ifm-color-emphasis-200)",
                  borderRadius: "4px",
                  fontSize: "0.8rem",
                }}
              >
                {t}
              </span>
            ))}
            {data.tags.length > 50 && (
              <span style={{ opacity: 0.5 }}>
                ... and {data.tags.length - 50} more
              </span>
            )}
          </div>
        </details>
      )}
    </div>
  );
}
