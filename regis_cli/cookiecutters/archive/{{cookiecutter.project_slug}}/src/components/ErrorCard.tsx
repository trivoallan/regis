/**
 * ErrorCard — Displays an analyzer error in a styled alert.
 */

import React from "react";
import Admonition from "@theme/Admonition";

interface ErrorCardProps {
  analyzerName: string;
  error: { type?: string; message?: string };
}

export function ErrorCard({
  analyzerName,
  error,
}: ErrorCardProps): React.JSX.Element {
  return (
    <Admonition
      type="danger"
      title={`${analyzerName} — ${error.type ?? "error"}`}
    >
      <p>{error.message ?? "An unknown error occurred."}</p>
    </Admonition>
  );
}
