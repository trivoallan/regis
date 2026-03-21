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

interface PlatformInfo {
  platform: string;
  compressed_human: string;
  layer_count: number;
}
interface SizeData {
  multi_arch: boolean;
  total_compressed_human: string;
  layer_count: number;
  platforms?: PlatformInfo[];
}

export function SizeSection({ data }: { data: SizeData }): React.JSX.Element {
  return (
    <div className="space-y-6">
      <Grid numItemsSm={2} numItemsLg={3} className="gap-4">
        <StatCard
          label="Compressed Size"
          value={data.total_compressed_human}
          size="lg"
        />
        <StatCard label="Layers" value={data.layer_count} />
        <StatCard
          label="Multi-arch"
          value={data.multi_arch ? "Yes" : "No"}
          size="lg"
          badge={
            <Badge color={data.multi_arch ? "emerald" : "gray"}>
              {data.multi_arch ? "Multi-arch" : "Single arch"}
            </Badge>
          }
        />
      </Grid>

      {data.platforms && data.platforms.length > 1 && (
        <Card>
          <Text className="font-medium mb-4">Platform Breakdown</Text>
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Platform</TableHeaderCell>
                <TableHeaderCell>Size</TableHeaderCell>
                <TableHeaderCell>Layers</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.platforms.map((p, i) => (
                <TableRow key={i}>
                  <TableCell className="font-mono">{p.platform}</TableCell>
                  <TableCell>{p.compressed_human}</TableCell>
                  <TableCell>{p.layer_count}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
