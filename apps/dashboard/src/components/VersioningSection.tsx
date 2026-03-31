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

interface TagPattern {
  pattern: string;
  count: number;
  percentage: number;
  examples: string[];
}
interface TagVariant {
  name: string;
  count: number;
  percentage: number;
  examples: string[];
}
interface VersioningData {
  total_tags: number;
  dominant_pattern?: string;
  semver_compliant_percentage?: number;
  patterns?: TagPattern[];
  variants?: TagVariant[];
  aliases?: string[];
}

export function VersioningSection({
  data,
}: {
  data: VersioningData;
}): React.JSX.Element {
  return (
    <div className="space-y-6">
      <Grid numItemsSm={2} numItemsLg={3} className="gap-4">
        <StatCard label="Total Tags" value={data.total_tags} />
        <StatCard
          label="SemVer Compliance"
          value={
            <>
              {data.semver_compliant_percentage?.toFixed(1) ?? "—"}
              <span
                style={{ fontSize: "0.5em", fontWeight: 400, opacity: 0.6 }}
              >
                %
              </span>
            </>
          }
        />
        <StatCard
          label="Dominant Pattern"
          value={data.dominant_pattern ?? "N/A"}
          size="md"
        />
      </Grid>

      {data.patterns && data.patterns.length > 0 && (
        <Card>
          <Text className="font-medium mb-4">Tag Patterns</Text>
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Pattern</TableHeaderCell>
                <TableHeaderCell>Count</TableHeaderCell>
                <TableHeaderCell>Share</TableHeaderCell>
                <TableHeaderCell>Examples</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.patterns.map((p) => (
                <TableRow key={p.pattern}>
                  <TableCell className="font-mono font-semibold">
                    {p.pattern}
                  </TableCell>
                  <TableCell>{p.count}</TableCell>
                  <TableCell>
                    <Badge color="blue">{p.percentage.toFixed(1)}%</Badge>
                  </TableCell>
                  <TableCell className="text-sm font-mono">
                    {p.examples.slice(0, 3).join(", ")}
                    {p.examples.length > 3 && "…"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      {data.aliases && data.aliases.length > 0 && (
        <Card>
          <Text className="font-medium mb-3">
            Aliases — other tags pointing to this digest ({data.aliases.length})
          </Text>
          <div className="flex flex-wrap gap-1.5">
            {data.aliases.map((a) => (
              <Badge key={a} color="gray">
                {a}
              </Badge>
            ))}
          </div>
        </Card>
      )}

      {data.variants && data.variants.length > 0 && (
        <Card>
          <Text className="font-medium mb-4">Detected Variants</Text>
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Variant</TableHeaderCell>
                <TableHeaderCell>Count</TableHeaderCell>
                <TableHeaderCell>Share</TableHeaderCell>
                <TableHeaderCell>Examples</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.variants.map((v) => (
                <TableRow key={v.name}>
                  <TableCell className="font-mono font-semibold">
                    {v.name}
                  </TableCell>
                  <TableCell>{v.count}</TableCell>
                  <TableCell>
                    <Badge color="indigo">{v.percentage.toFixed(1)}%</Badge>
                  </TableCell>
                  <TableCell className="text-sm font-mono">
                    {v.examples.slice(0, 3).join(", ")}
                    {v.examples.length > 3 && "…"}
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
