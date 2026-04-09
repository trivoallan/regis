/**
 * MRComparison — Compare analysis results between two merge requests.
 * Fetches individual MR details from /api/gitlab/mrs/{iid}.
 */

import React, { useEffect, useState } from "react";
import {
  Badge,
  Card,
  Grid,
  Text,
  TextInput,
  Title,
  Button,
} from "@tremor/react";

interface MRDetail {
  iid: number;
  title: string;
  state: string;
  web_url: string;
  regis_labels: string[];
  has_report: boolean;
  description: string;
  merge_status: string | null;
  pipeline: { id: number; status: string; web_url: string } | null;
}

function MRCard({ mr }: { mr: MRDetail }): React.JSX.Element {
  return (
    <Card>
      <div className="flex items-center gap-2 mb-2">
        <Title>
          <a href={mr.web_url} target="_blank" rel="noopener noreferrer">
            !{mr.iid}
          </a>
        </Title>
        <Badge color={mr.state === "opened" ? "emerald" : "blue"}>
          {mr.state}
        </Badge>
      </div>
      <Text className="font-medium mb-3">{mr.title}</Text>

      <div className="flex flex-col gap-2">
        <div>
          <Text className="text-xs font-medium uppercase">Regis Labels</Text>
          <div className="flex flex-wrap gap-1 mt-1">
            {mr.regis_labels.length > 0 ? (
              mr.regis_labels.map((lb) => (
                <Badge key={lb} size="xs">
                  {lb.replace("regis::", "")}
                </Badge>
              ))
            ) : (
              <Text>None</Text>
            )}
          </div>
        </div>

        <div>
          <Text className="text-xs font-medium uppercase">Report</Text>
          <Text>
            {mr.has_report ? (
              <Badge color="emerald" size="xs">
                Available
              </Badge>
            ) : (
              "Not available"
            )}
          </Text>
        </div>

        {mr.pipeline && (
          <div>
            <Text className="text-xs font-medium uppercase">Pipeline</Text>
            <div className="flex items-center gap-2">
              <Badge
                color={mr.pipeline.status === "success" ? "emerald" : "yellow"}
                size="xs"
              >
                {mr.pipeline.status}
              </Badge>
              <a
                href={mr.pipeline.web_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-600 hover:underline"
              >
                #{mr.pipeline.id}
              </a>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

export function MRComparison(): React.JSX.Element {
  const [leftIid, setLeftIid] = useState("");
  const [rightIid, setRightIid] = useState("");
  const [leftMR, setLeftMR] = useState<MRDetail | null>(null);
  const [rightMR, setRightMR] = useState<MRDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function fetchMR(iid: string): Promise<MRDetail> {
    const resp = await fetch(`/api/gitlab/mrs/${iid}`);
    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}));
      throw new Error(data.detail ?? `MR !${iid}: HTTP ${resp.status}`);
    }
    return resp.json();
  }

  async function handleCompare() {
    if (!leftIid.trim() || !rightIid.trim()) return;
    setLoading(true);
    setError(null);
    setLeftMR(null);
    setRightMR(null);

    try {
      const [left, right] = await Promise.all([
        fetchMR(leftIid),
        fetchMR(rightIid),
      ]);
      setLeftMR(left);
      setRightMR(right);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mt-4">
      <Title>Compare Merge Requests</Title>
      <Text className="mb-4">
        Enter two MR IIDs to compare their analysis results side by side.
      </Text>

      <div className="flex items-end gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium mb-1">Left MR</label>
          <TextInput
            placeholder="e.g. 42"
            value={leftIid}
            onValueChange={setLeftIid}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Right MR</label>
          <TextInput
            placeholder="e.g. 43"
            value={rightIid}
            onValueChange={setRightIid}
          />
        </div>
        <Button
          onClick={handleCompare}
          loading={loading}
          disabled={!leftIid.trim() || !rightIid.trim() || loading}
        >
          Compare
        </Button>
      </div>

      {error && (
        <Card className="mb-4">
          <Text className="text-red-500">{error}</Text>
        </Card>
      )}

      {leftMR && rightMR && (
        <Grid numItems={1} numItemsMd={2} className="gap-4">
          <MRCard mr={leftMR} />
          <MRCard mr={rightMR} />
        </Grid>
      )}
    </div>
  );
}
