/**
 * TriggerAnalysis — Form to trigger a GitLab pipeline analysis.
 * Posts to /api/gitlab/trigger (served by the FastAPI backend).
 */

import React, { useState } from "react";
import { Button, Card, Text, TextInput, Title } from "@tremor/react";

interface TriggerResult {
  pipeline_id: number;
  status: string;
  web_url: string;
}

export function TriggerAnalysis(): React.JSX.Element {
  const [imageUrl, setImageUrl] = useState("");
  const [ref, setRef] = useState("main");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TriggerResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!imageUrl.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const resp = await fetch("/api/gitlab/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_url: imageUrl, ref }),
      });
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.detail ?? `HTTP ${resp.status}`);
      }
      setResult(await resp.json());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mt-4" style={{ maxWidth: 600 }}>
      <Title>Trigger Analysis</Title>
      <Text className="mb-4">
        Start a GitLab pipeline to analyze a container image.
      </Text>

      <Card>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Image URL</label>
            <TextInput
              placeholder="e.g. alpine:latest, nginx:1.25, ghcr.io/org/app:v2"
              value={imageUrl}
              onValueChange={setImageUrl}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Branch (ref)
            </label>
            <TextInput placeholder="main" value={ref} onValueChange={setRef} />
          </div>
          <Button
            type="submit"
            loading={loading}
            disabled={!imageUrl.trim() || loading}
          >
            {loading ? "Triggering..." : "Run Analysis"}
          </Button>
        </form>
      </Card>

      {result && (
        <Card className="mt-4">
          <Text className="font-medium text-emerald-600">
            Pipeline triggered successfully
          </Text>
          <div className="mt-2 flex flex-col gap-1">
            <Text>
              Pipeline ID: <strong>#{result.pipeline_id}</strong>
            </Text>
            <Text>
              Status: <strong>{result.status}</strong>
            </Text>
            <a
              href={result.web_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              View pipeline on GitLab
            </a>
          </div>
        </Card>
      )}

      {error && (
        <Card className="mt-4">
          <Text className="text-red-500">Failed to trigger: {error}</Text>
          <Text className="mt-2">
            Make sure the server was started with GitLab options and the token
            has pipeline trigger permissions.
          </Text>
        </Card>
      )}
    </div>
  );
}
