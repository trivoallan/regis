import React from "react";
import {
  Grid,
  Card,
  Text,
  Badge,
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
} from "@tremor/react";
import { StatCard } from "./StatCard";

interface Component {
  name: string;
  version?: string;
  type: string;
  licenses: string[];
}
interface SbomData {
  has_sbom: boolean;
  sbom_format: string;
  sbom_version: string;
  total_components: number;
  component_types: Record<string, number>;
  total_dependencies: number;
  licenses: string[];
  components: Component[];
}

export function SbomSection({ data }: { data: SbomData }): React.JSX.Element {
  if (!data.has_sbom) {
    return (
      <Card>
        <Badge color="amber" size="lg">
          No SBOM could be generated for this image.
        </Badge>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Grid numItemsSm={2} numItemsLg={4} className="gap-4">
        <StatCard label="Total Components" value={data.total_components} />
        <StatCard label="Dependencies" value={data.total_dependencies} />
        <StatCard label="Unique Licenses" value={data.licenses.length} />
        <StatCard
          label="Format"
          value={data.sbom_format}
          size="lg"
          badge={<Badge color="gray">v{data.sbom_version}</Badge>}
        />
      </Grid>

      {Object.keys(data.component_types).length > 0 && (
        <Card>
          <Text className="font-medium mb-4">Component Types</Text>
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Type</TableHeaderCell>
                <TableHeaderCell>Count</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(data.component_types)
                .sort(([, a], [, b]) => b - a)
                .map(([type, count]) => (
                  <TableRow key={type}>
                    <TableCell className="font-medium capitalize">
                      {type}
                    </TableCell>
                    <TableCell>{count}</TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </Card>
      )}

      {data.licenses.length > 0 && (
        <Card>
          <Text className="font-medium mb-3">Licenses</Text>
          <div className="flex flex-wrap gap-2">
            {data.licenses.map((l) => (
              <Badge key={l} color="blue">
                {l}
              </Badge>
            ))}
          </div>
        </Card>
      )}

      {data.components.length > 0 && (
        <Card>
          <Text className="font-medium mb-4">
            Components (top {Math.min(100, data.components.length)} of{" "}
            {data.total_components})
          </Text>
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Name</TableHeaderCell>
                <TableHeaderCell>Version</TableHeaderCell>
                <TableHeaderCell>Type</TableHeaderCell>
                <TableHeaderCell>Licenses</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.components.slice(0, 100).map((comp, i) => (
                <TableRow key={i}>
                  <TableCell className="font-semibold text-sm">
                    {comp.name}
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {comp.version ?? "—"}
                  </TableCell>
                  <TableCell>
                    <Badge color="gray">{comp.type}</Badge>
                  </TableCell>
                  <TableCell className="text-sm">
                    {comp.licenses.join(", ")}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
