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

interface PlatformDetail {
  architecture: string;
  os: string;
  variant?: string;
  digest?: string;
  created?: string;
  layers_count: number;
  size: number;
  user: string;
  exposed_ports: string[];
  env: string[];
  labels: Record<string, string>;
}
interface SkopeoData {
  platforms: PlatformDetail[];
  inspect: Record<string, unknown>;
  tags: string[];
}

export function SkopeoSection({
  data,
}: {
  data: SkopeoData;
}): React.JSX.Element {
  const platforms = (data?.platforms || []).filter(
    (p) => !(p.os === "unknown" && p.architecture === "unknown"),
  );

  const tags = data?.tags || [];

  return (
    <div className="space-y-6">
      <Grid
        numItemsSm={1}
        numItemsLg={platforms.length > 1 ? 2 : 1}
        className="gap-4"
      >
        {platforms.map((p, i) => (
          <Card key={i} className="flex flex-col">
            <Text className="font-medium mb-4">
              {p.os}/{p.architecture}
              {p.variant ? ` (${p.variant})` : ""}
            </Text>
            <Grid numItemsSm={2} numItemsLg={3} className="gap-3">
              <StatCard
                label="Size"
                value={
                  p.size != null
                    ? `${(p.size / 1024 / 1024).toFixed(1)} MB`
                    : "—"
                }
                size="md"
              />
              <StatCard
                label="Layers"
                value={p.layers_count ?? "—"}
                size="lg"
              />
              <StatCard label="User" value={p.user || "root"} size="sm" />
            </Grid>
            {(p.exposed_ports?.length ?? 0) > 0 && (
              <div className="mt-4">
                <Text className="mb-2">Exposed Ports</Text>
                <div className="flex flex-wrap gap-1">
                  {p.exposed_ports.map((port) => (
                    <Badge key={port} color="blue">
                      {port}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {p.created && (
              <div className="mt-3">
                <Text className="text-xs opacity-60">
                  Created: {new Date(p.created).toLocaleDateString()}
                </Text>
              </div>
            )}
            {p.digest && (
              <div className="mt-1">
                <Text className="text-xs opacity-40 break-all font-mono">
                  {p.digest}
                </Text>
              </div>
            )}
          </Card>
        ))}
      </Grid>

      {platforms.some((p) => p.labels && Object.keys(p.labels).length > 0) && (
        <Card>
          <Text className="font-medium mb-4">Labels</Text>
          {platforms.map(
            (p, i) =>
              p.labels &&
              Object.keys(p.labels).length > 0 && (
                <div key={i} className="mb-4">
                  {platforms.length > 1 && (
                    <Text className="mb-2 text-xs opacity-60">
                      {p.os}/{p.architecture}
                    </Text>
                  )}
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableHeaderCell>Key</TableHeaderCell>
                        <TableHeaderCell>Value</TableHeaderCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(p.labels).map(([k, v]) => (
                        <TableRow key={k}>
                          <TableCell className="font-mono text-sm font-semibold break-all">
                            {k}
                          </TableCell>
                          <TableCell className="text-sm break-all">
                            {v}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ),
          )}
        </Card>
      )}

      {tags.length > 0 && (
        <Card>
          <Text className="font-medium mb-3">
            Available Tags ({tags.length})
          </Text>
          <div className="flex flex-wrap gap-1.5">
            {tags.slice(0, 50).map((t) => (
              <Badge key={t} color="gray">
                {t}
              </Badge>
            ))}
            {tags.length > 50 && (
              <Badge color="gray">+{tags.length - 50} more</Badge>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
