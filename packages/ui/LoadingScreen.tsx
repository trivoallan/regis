import React from "react";

export function LoadingScreen() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "var(--regis-text-muted)",
        fontSize: "0.9rem",
        gap: "0.75rem",
      }}
    >
      <Spinner />
      Loading report…
    </div>
  );
}

export function ErrorScreen({ message }: { message: string }) {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
      }}
    >
      <div
        style={{
          maxWidth: "480px",
          padding: "1.5rem",
          borderRadius: "0.75rem",
          border: "1px solid var(--regis-danger)",
          background: "var(--regis-danger-bg)",
        }}
      >
        <div
          style={{
            fontWeight: 600,
            color: "var(--regis-danger)",
            marginBottom: "0.5rem",
          }}
        >
          Failed to load report
        </div>
        <div
          style={{
            fontSize: "0.85rem",
            color: "var(--regis-text)",
            opacity: 0.8,
          }}
        >
          {message}
        </div>
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      style={{ animation: "regis-spin 0.8s linear infinite" }}
    >
      <style>{`@keyframes regis-spin { to { transform: rotate(360deg); } }`}</style>
      <circle cx="12" cy="12" r="10" opacity="0.25" />
      <path d="M12 2a10 10 0 0 1 10 10" />
    </svg>
  );
}
