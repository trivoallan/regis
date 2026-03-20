/**
 * RequestTable — Displays the request parameters (registry, repository, tag, etc.)
 */

import React from "react";
import { useReport } from "./ReportProvider";

export function RequestTable(): React.JSX.Element {
  const { report } = useReport();
  if (!report?.request) return <p>No request metadata available.</p>;

  const req = report.request;
  const rows = [
    { label: "Registry", value: req.registry },
    { label: "Repository", value: req.repository },
    { label: "Tag", value: req.tag },
    { label: "Digest", value: req.digest },
    {
      label: "Timestamp",
      value: req.timestamp ? new Date(req.timestamp).toLocaleString() : "N/A",
    },
    { label: "Platform Override", value: req.platform || "Not specified" },
  ];

  return (
    <table>
      <thead>
        <tr>
          <th style={{ width: "200px" }}>Parameter</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>
            <td style={{ fontWeight: 600 }}>{row.label}</td>
            <td
              style={{
                fontFamily:
                  row.value && row.value.length > 20 ? "monospace" : "inherit",
                fontSize: "0.9rem",
              }}
            >
              {row.value || "—"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
