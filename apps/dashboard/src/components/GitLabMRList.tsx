/**
 * GitLabMRList — Displays merge requests with regis labels and scores.
 * Fetches from /api/gitlab/mrs (served by the FastAPI backend).
 */

import React, { useEffect, useState } from "react";
import {
  Badge,
  Card,
  Select,
  SelectItem,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  Text,
  Title,
} from "@tremor/react";

interface MR {
  iid: number;
  title: string;
  state: string;
  web_url: string;
  source_branch: string;
  author: string | null;
  created_at: string;
  updated_at: string;
  labels: string[];
  regis_labels: string[];
  has_report: boolean;
}

const STATE_COLORS: Record<string, string> = {
  opened: "emerald",
  merged: "blue",
  closed: "red",
};

export function GitLabMRList(): React.JSX.Element {
  const [mrs, setMrs] = useState<MR[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stateFilter, setStateFilter] = useState("opened");

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`/api/gitlab/mrs?state=${stateFilter}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => setMrs(data.merge_requests ?? []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [stateFilter]);

  if (error) {
    return (
      <Card className="mt-4">
        <Text className="text-red-500">
          Failed to load merge requests: {error}
        </Text>
        <Text className="mt-2">
          Make sure the server was started with <code>--gitlab-url</code>,{" "}
          <code>--gitlab-token</code>, and <code>--gitlab-project</code>.
        </Text>
      </Card>
    );
  }

  return (
    <div className="mt-4">
      <div className="flex items-center gap-4 mb-4">
        <Title>Merge Requests</Title>
        <Select
          value={stateFilter}
          onValueChange={setStateFilter}
          className="max-w-xs"
        >
          <SelectItem value="opened">Open</SelectItem>
          <SelectItem value="merged">Merged</SelectItem>
          <SelectItem value="closed">Closed</SelectItem>
          <SelectItem value="all">All</SelectItem>
        </Select>
      </div>

      <Card>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>MR</TableHeaderCell>
              <TableHeaderCell>Title</TableHeaderCell>
              <TableHeaderCell>Author</TableHeaderCell>
              <TableHeaderCell>State</TableHeaderCell>
              <TableHeaderCell>Regis Labels</TableHeaderCell>
              <TableHeaderCell>Report</TableHeaderCell>
              <TableHeaderCell>Updated</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7}>
                  <Text className="text-center">Loading...</Text>
                </TableCell>
              </TableRow>
            ) : mrs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7}>
                  <Text className="text-center">No merge requests found.</Text>
                </TableCell>
              </TableRow>
            ) : (
              mrs.map((mr) => (
                <TableRow key={mr.iid}>
                  <TableCell>
                    <a
                      href={mr.web_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      !{mr.iid}
                    </a>
                  </TableCell>
                  <TableCell>
                    <Text className="font-medium">{mr.title}</Text>
                  </TableCell>
                  <TableCell>
                    <Text>{mr.author ?? "—"}</Text>
                  </TableCell>
                  <TableCell>
                    <Badge color={STATE_COLORS[mr.state] ?? "gray"}>
                      {mr.state}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {mr.regis_labels.length > 0
                        ? mr.regis_labels.map((lb) => (
                            <Badge key={lb} size="xs">
                              {lb.replace("regis::", "")}
                            </Badge>
                          ))
                        : "—"}
                    </div>
                  </TableCell>
                  <TableCell>
                    {mr.has_report ? (
                      <Badge color="emerald" size="xs">
                        Available
                      </Badge>
                    ) : (
                      <Text>—</Text>
                    )}
                  </TableCell>
                  <TableCell>
                    <Text>{new Date(mr.updated_at).toLocaleDateString()}</Text>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
