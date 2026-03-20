/**
 * SbomSection — Displays the Software Bill of Materials (SBOM) overview.
 */

import React from "react";

interface Component {
  name: string;
  version?: string;
  type: string;
  purl?: string;
  licenses: string[];
}

interface SbomData {
  analyzer: string;
  repository: string;
  tag: string;
  has_sbom: boolean;
  sbom_format: string;
  sbom_version: string;
  total_components: number;
  component_types: Record<string, number>;
  total_dependencies: number;
  licenses: string[];
  components: Component[];
}

interface SbomSectionProps {
  data: SbomData;
}

export function SbomSection({ data }: SbomSectionProps): React.JSX.Element {
  if (!data.has_sbom) {
    return (
      <div className="alert alert--warning">
        No SBOM could be generated for this image.
      </div>
    );
  }

  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: "0.75rem",
          marginBottom: "1.5rem",
        }}
      >
        <div className="stat-card">
          <div className="stat-card__label">Total Components</div>
          <div className="stat-card__value">{data.total_components}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Unique Licenses</div>
          <div className="stat-card__value">{data.licenses.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Format</div>
          <div
            className="stat-card__value"
            style={{ fontSize: "1.2rem", paddingTop: "0.5rem" }}
          >
            {data.sbom_format} {data.sbom_version}
          </div>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "2rem",
          marginBottom: "1.5rem",
        }}
      >
        {data.component_types && (
          <div>
            <h5>Component Types</h5>
            <ul style={{ fontSize: "0.9rem" }}>
              {Object.entries(data.component_types).map(([type, count]) => (
                <li key={type}>
                  <strong>{type}</strong>: {count}
                </li>
              ))}
            </ul>
          </div>
        )}
        {data.licenses && data.licenses.length > 0 && (
          <div>
            <h5>Top Licenses</h5>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
              {data.licenses.slice(0, 15).map((l) => (
                <span
                  key={l}
                  style={{
                    padding: "2px 8px",
                    background: "var(--ifm-color-emphasis-200)",
                    borderRadius: "4px",
                    fontSize: "0.8rem",
                  }}
                >
                  {l}
                </span>
              ))}
              {data.licenses.length > 15 && (
                <span style={{ opacity: 0.5 }}>...</span>
              )}
            </div>
          </div>
        )}
      </div>

      <details>
        <summary style={{ cursor: "pointer", fontWeight: 600 }}>
          Component List (Top 100)
        </summary>
        <table style={{ marginTop: "1rem" }}>
          <thead>
            <tr>
              <th>Name</th>
              <th>Version</th>
              <th>Type</th>
              <th>Licenses</th>
            </tr>
          </thead>
          <tbody>
            {data.components.slice(0, 100).map((comp, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 600, fontSize: "0.85rem" }}>
                  {comp.name}
                </td>
                <td style={{ fontFamily: "monospace", fontSize: "0.85rem" }}>
                  {comp.version}
                </td>
                <td>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      opacity: 0.7,
                      textTransform: "uppercase",
                    }}
                  >
                    {comp.type}
                  </span>
                </td>
                <td style={{ fontSize: "0.8rem" }}>
                  {comp.licenses.join(", ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}
