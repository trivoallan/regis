import { useState, useEffect } from "react";
import type { Report } from "../types/report";

declare global {
  interface Window {
    __REPORT_DATA__?: Report;
  }
}

export type ReportSource =
  | { kind: "window" }
  | { kind: "prop"; data: Report }
  | { kind: "url"; url: string };

export interface UseReportResult {
  report: Report | null;
  loading: boolean;
  error: string | null;
}

/**
 * Charge le report depuis window.__REPORT_DATA__, une prop directe, ou une URL.
 * Ordre de priorité : prop > window > url
 */
export function useReport(
  source: ReportSource = { kind: "window" },
): UseReportResult {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        if (source.kind === "prop") {
          setReport(source.data);
          setLoading(false);
          return;
        }

        if (source.kind === "window") {
          const data = window.__REPORT_DATA__;
          if (!data) {
            throw new Error(
              "window.__REPORT_DATA__ is not defined. " +
                "Ensure the report shell HTML injects the report JSON.",
            );
          }
          setReport(data);
          setLoading(false);
          return;
        }

        if (source.kind === "url") {
          const res = await fetch(source.url);
          if (!res.ok) {
            throw new Error(
              `Failed to fetch report: ${res.status} ${res.statusText}`,
            );
          }
          const data: Report = await res.json();
          setReport(data);
          setLoading(false);
          return;
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        setLoading(false);
      }
    }

    load();
  }, []);

  return { report, loading, error };
}

// -----------------------------------------------------------
// Helpers dérivés du report
// -----------------------------------------------------------

/** Retourne le label d'une rule (title ou description selon le champ disponible) */
export function getRuleLabel(rule: import("../types/report").Rule): string {
  return rule.title ?? rule.description ?? rule.slug;
}

/** Vérifie si un analyzer a retourné une erreur */
export function hasAnalyzerError(result: unknown): boolean {
  return (
    result != null &&
    typeof result === "object" &&
    "error" in result &&
    result.error != null
  );
}

/** Formate un nombre avec séparateurs de milliers */
export function formatNumber(n: number | null | undefined): string {
  if (n == null) return "—";
  return n.toLocaleString();
}

/** Formate une date ISO en date locale courte */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

/** Retourne le score global du premier playbook, ou rules_summary.score */
export function getOverallScore(report: Report): number | null {
  return (
    report.playbook?.score ??
    report.playbooks?.[0]?.score ??
    report.rules_summary?.score ??
    null
  );
}
