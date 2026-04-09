"""Tests for regis/server/routes/webhooks.py."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from regis.server.app import create_app


@pytest.fixture()
def assets_dir(tmp_path: Path) -> Path:
    d = tmp_path / "assets"
    d.mkdir()
    (d / "index.html").write_text("<html><body>Dashboard</body></html>")
    return d


@pytest.fixture()
def client(assets_dir: Path):
    app = create_app(assets_dir=assets_dir)
    return TestClient(app)


@pytest.fixture()
def client_with_secret(assets_dir: Path):
    app = create_app(assets_dir=assets_dir, webhook_secret="my-secret")
    return TestClient(app)


class TestWebhookReceiver:
    def test_merge_request_event(self, client: TestClient) -> None:
        payload = {
            "object_kind": "merge_request",
            "object_attributes": {
                "action": "open",
                "iid": 42,
                "title": "Regis Analysis: alpine:latest",
                "state": "opened",
                "url": "https://gitlab.com/org/proj/-/merge_requests/42",
                "source_branch": "regis/analyze/20260409",
            },
            "labels": [{"title": "regis::score-Silver"}],
        }
        resp = client.post("/api/webhooks/gitlab", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"
        assert resp.json()["event"] == "merge_request"

    def test_pipeline_event(self, client: TestClient) -> None:
        payload = {
            "object_kind": "pipeline",
            "object_attributes": {
                "id": 500,
                "status": "success",
                "ref": "main",
                "source": "web",
            },
            "project": {"web_url": "https://gitlab.com/org/proj"},
        }
        resp = client.post("/api/webhooks/gitlab", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"

    def test_unknown_event_ignored(self, client: TestClient) -> None:
        payload = {"object_kind": "push"}
        resp = client.post("/api/webhooks/gitlab", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"

    def test_invalid_json_returns_400(self, client: TestClient) -> None:
        resp = client.post(
            "/api/webhooks/gitlab",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400


class TestWebhookSecret:
    def test_valid_secret_accepted(self, client_with_secret: TestClient) -> None:
        payload = {
            "object_kind": "merge_request",
            "object_attributes": {
                "action": "open",
                "iid": 1,
                "title": "Test",
                "state": "opened",
                "url": "https://gitlab.com/mr/1",
                "source_branch": "test",
            },
            "labels": [],
        }
        resp = client_with_secret.post(
            "/api/webhooks/gitlab",
            json=payload,
            headers={"X-Gitlab-Token": "my-secret"},
        )
        assert resp.status_code == 200

    def test_invalid_secret_rejected(self, client_with_secret: TestClient) -> None:
        payload = {"object_kind": "merge_request", "object_attributes": {}}
        resp = client_with_secret.post(
            "/api/webhooks/gitlab",
            json=payload,
            headers={"X-Gitlab-Token": "wrong"},
        )
        assert resp.status_code == 403

    def test_missing_secret_rejected(self, client_with_secret: TestClient) -> None:
        payload = {"object_kind": "merge_request", "object_attributes": {}}
        resp = client_with_secret.post("/api/webhooks/gitlab", json=payload)
        assert resp.status_code == 403


class TestRecentEvents:
    def test_recent_events_empty(self, client: TestClient) -> None:
        resp = client.get("/api/events/recent")
        assert resp.status_code == 200
        assert resp.json()["events"] == []

    def test_recent_events_after_webhook(self, client: TestClient) -> None:
        payload = {
            "object_kind": "pipeline",
            "object_attributes": {
                "id": 600,
                "status": "success",
                "ref": "main",
                "source": "web",
            },
            "project": {"web_url": "https://gitlab.com/org/proj"},
        }
        client.post("/api/webhooks/gitlab", json=payload)

        resp = client.get("/api/events/recent")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["events"][0]["type"] == "pipeline"
        assert data["events"][0]["id"] == 600
