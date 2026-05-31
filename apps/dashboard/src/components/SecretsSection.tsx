/**
 * SecretsSection — renders trufflehog secret-detection results.
 */

import React from "react";
import { Card, Flex, Text, Metric, Badge } from "@tremor/react";

interface SecretFinding {
  DetectorName: string;
  Verified: boolean;
  Redacted?: string;
  layer?: string;
}

interface SecretsData {
  secrets_count: number;
  verified_count: number;
  findings?: SecretFinding[];
}

export function SecretsSection({
  data,
}: {
  data: SecretsData;
}): React.JSX.Element {
  const findings = data.findings ?? [];
  const color =
    data.verified_count > 0
      ? "rose"
      : data.secrets_count > 0
        ? "amber"
        : "emerald";
  return (
    <Card>
      <Flex justifyContent="between" alignItems="start">
        <Text className="font-medium">Secrets</Text>
        <Badge color={color} size="xs">
          {data.verified_count} verified
        </Badge>
      </Flex>
      <Metric className="mt-2">{data.secrets_count}</Metric>
      <Text className="mt-1 text-tremor-content">Detected by TruffleHog</Text>
      <ul className="mt-4 space-y-1">
        {findings.map((f, i) => (
          <li key={i} className="text-tremor-default">
            <span className="font-medium">{f.DetectorName}</span>
            {f.Verified ? " (verified)" : ""} — {f.Redacted ?? ""}
          </li>
        ))}
      </ul>
    </Card>
  );
}
