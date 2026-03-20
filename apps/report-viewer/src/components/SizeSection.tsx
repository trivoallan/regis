/**
 * SizeSection — Displays image size and layer breakdown.
 */

import React from "react";

interface PlatformInfo {
  platform: string;
  compressed_bytes: number;
  compressed_human: string;
  layer_count: number;
}

interface SizeData {
  analyzer: string;
  repository: string;
  tag: string;
  multi_arch: boolean;
  total_compressed_bytes: number;
  total_compressed_human: string;
  layer_count: number;
  config_size_bytes?: number;
  platforms?: PlatformInfo[];
}

interface SizeSectionProps {
  data: SizeData;
}

export function SizeSection({ data }: SizeSectionProps): React.JSX.Element {
  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: "0.75rem",
          marginBottom: "1rem",
        }}
      >
        <div className="stat-card">
          <div className="stat-card__label">Compressed Size</div>
          <div className="stat-card__value">{data.total_compressed_human}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Layers</div>
          <div className="stat-card__value">{data.layer_count}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Multi-arch</div>
          <div className="stat-card__value">
            {data.multi_arch ? "✅ Yes" : "No"}
          </div>
        </div>
      </div>

      {data.platforms && data.platforms.length > 0 && (
        <div>
          <h5>Platform Breakdown</h5>
          <table>
            <thead>
              <tr>
                <th>Platform</th>
                <th>Size</th>
                <th>Layers</th>
              </tr>
            </thead>
            <tbody>
              {data.platforms.map((p, i) => (
                <tr key={i}>
                  <td>
                    <code>{p.platform}</code>
                  </td>
                  <td>{p.compressed_human}</td>
                  <td>{p.layer_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
