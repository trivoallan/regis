import React from "react";
import { Card, Flex, Text, DonutChart, Legend } from "@tremor/react";

interface ComplianceData {
  name: string;
  value: number;
}

interface ComplianceDonutProps {
  data: ComplianceData[];
}

export function ComplianceDonut({ data }: ComplianceDonutProps) {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  const passed = data.find((d) => d.name === "Passed")?.value ?? 0;
  const score = total > 0 ? Math.round((passed / total) * 100) : 0;

  return (
    <Card>
      <Text className="font-medium">Compliance Breakdown</Text>
      <Text className="mt-1 text-tremor-default text-tremor-content">
        Pass/fail distribution of all scorecards
      </Text>
      <DonutChart
        className="mt-6 h-48"
        data={data}
        category="value"
        index="name"
        colors={["emerald", "rose"]}
        label={`${score}%`}
        variant="donut"
      />
      <Flex className="mt-4" justifyContent="center">
        <Legend
          categories={data.map((d) => `${d.name} (${d.value})`)}
          colors={["emerald", "rose"]}
        />
      </Flex>
    </Card>
  );
}
