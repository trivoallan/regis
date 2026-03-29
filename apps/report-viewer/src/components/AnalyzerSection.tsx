/**
 * AnalyzerSection — Smart dispatcher that routes to specialized components
 * based on analyzer name, falling back to raw JSON for unknown analyzers.
 */

import React from "react";
import CodeBlock from "@theme/CodeBlock";
import { TrivySection } from "./TrivySection";
import { FreshnessSection } from "./FreshnessSection";
import { SizeSection } from "./SizeSection";
import { HadolintSection } from "./HadolintSection";
import { PopularitySection } from "./PopularitySection";
import { EndOfLifeSection } from "./EndOfLifeSection";
import { ProvenanceSection } from "./ProvenanceSection";
import { ScorecardSection } from "./ScorecardSection";
import { VersioningSection } from "./VersioningSection";
import { SkopeoSection } from "./SkopeoSection";
import { SbomSection } from "./SbomSection";
import { DockleSection } from "./DockleSection";

import { ErrorCard } from "./ErrorCard";

interface AnalyzerSectionProps {
  name: string;
  data: Record<string, unknown>;
}

/** Maps analyzer names to their specialized component. */
function renderAnalyzer(
  name: string,
  data: Record<string, unknown>,
): React.ReactNode {
  // Global error handling for analyzers
  if (data && "analysis_error" in data) {
    return (
      <ErrorCard
        analyzerName={name}
        error={{
          type: "Analysis Error",
          message: String(data.analysis_error),
        }}
      />
    );
  }

  switch (name) {
    case "trivy":
      return <TrivySection data={data as never} />;
    case "freshness":
      return <FreshnessSection data={data as never} />;
    case "size":
      return <SizeSection data={data as never} />;
    case "hadolint":
      return <HadolintSection data={data as never} />;
    case "popularity":
      return <PopularitySection data={data as never} />;
    case "endoflife":
      return <EndOfLifeSection data={data as never} />;
    case "provenance":
      return <ProvenanceSection data={data as never} />;
    case "scorecarddev":
      return <ScorecardSection data={data as never} />;
    case "versioning":
      return <VersioningSection data={data as never} />;
    case "skopeo":
      return <SkopeoSection data={data as never} />;
    case "sbom":
      return <SbomSection data={data as never} />;
    case "dockle":
      return <DockleSection data={data as never} />;
    default:
      return (
        <CodeBlock language="json" title={`${name} (raw)`}>
          {JSON.stringify(data, null, 2)}
        </CodeBlock>
      );
  }
}

export function AnalyzerSection({
  name,
  data,
}: AnalyzerSectionProps): React.JSX.Element {
  return <>{renderAnalyzer(name, data)}</>;
}
