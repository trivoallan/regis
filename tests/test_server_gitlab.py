"""Tests for regis/server/routes/gitlab.py."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from regis.server.app import create_app


@pytest.fixture()
def assets_dir(tmp_path: Path) -> Path:
    d = tmp_path / "assets"
    d.mkdir()
    (d / "index.html").write_text("<html><body>Dashboard</body></html>")
    return d


def _make_mr(**overrides: Any) -> MagicMock:
    """Create a mock MR object with sane defaults."""
    defaults = {
        "iid": 42,
        "title": "Regis Analysis: alpine:latest",
        "state": "opened",
        "web_url": "https://gitlab.com/org/proj/-/merge_requests/42",
        "source_branch": "regis/analyze/20260409",
        "author": {"username": "analyst"},
        "created_at": "2026-04-09T10:00:00Z",
        "updated_at": "2026-04-09T12:00:00Z",
        "labels": ["regis::score-Silver", "regis::cve-ok"],
        "description": "📝 **[View Analysis Report](https://example.com/report)**",
        "merge_status": "can_be_merged",
        "pipeline": {
            "id": 100,
            "status": "success",
            "web_url": "https://gitlab.com/pipelines/100",
        },
    }
    defaults.update(overrides)
    mr = MagicMock()
    mr.attributes = defaults
    return mr


def _make_pipeline(**overrides: Any) -> MagicMock:
    """Create a mock pipeline object."""
    defaults = {
        "id": 100,
        "status": "success",
        "ref": "main",
        "sha": "abc12345deadbeef",
        "web_url": "https://gitlab.com/pipelines/100",
        "created_at": "2026-04-09T10:00:00Z",
        "updated_at": "2026-04-09T10:05:00Z",
        "source": "web",
    }
    defaults.update(overrides)
    p = MagicMock()
    p.attributes = defaults
    return p


def _create_client(assets_dir: Path, mock_project: MagicMock) -> TestClient:
    """Create a TestClient with GitLab integration enabled."""
    with patch("regis.server.routes.gitlab.gitlab") as mock_gl_mod:
        mock_gl_instance = MagicMock()
        mock_gl_instance.projects.get.return_value = mock_project
        mock_gl_mod.Gitlab.return_value = mock_gl_instance
        mock_gl_mod.GitlabGetError = Exception
        mock_gl_mod.GitlabListError = Exception

        app = create_app(
            assets_dir=assets_dir,
            gitlab_url="https://gitlab.com",
            gitlab_token="test-token",
            gitlab_project="123",
        )
        # Re-patch for request time since _get_project is called per-request
        with patch(
            "regis.server.routes.gitlab._get_project", return_value=mock_project
        ):
            yield TestClient(app)


@pytest.fixture()
def mock_project() -> MagicMock:
    project = MagicMock()
    return project


@pytest.fixture()
def client(assets_dir: Path, mock_project: MagicMock):
    with patch("regis.server.routes.gitlab._get_project", return_value=mock_project):
        app = create_app(
            assets_dir=assets_dir,
            gitlab_url="https://gitlab.com",
            gitlab_token="test-token",
            gitlab_project="123",
        )
        with patch(
            "regis.server.routes.gitlab._get_project", return_value=mock_project
        ):
            yield TestClient(app), mock_project


class TestListMRs:
    def test_list_mrs_returns_serialized_data(self, client) -> None:
        test_client, mock_project = client
        mock_project.mergerequests.list.return_value = [_make_mr(), _make_mr(iid=43)]

        with patch(
            "regis.server.routes.gitlab._get_project", return_value=mock_project
        ):
            resp = test_client.get("/api/gitlab/mrs")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["merge_requests"][0]["iid"] == 42
        assert data["merge_requests"][0]["regis_labels"] == [
            "regis::score-Silver",
            "regis::cve-ok",
        ]
        assert data["merge_requests"][0]["has_report"] is True

    def test_list_mrs_with_state_filter(self, client) -> None:
        test_client, mock_project = client
        mock_project.mergerequests.list.return_value = []

        with patch(
            "regis.server.routes.gitlab._get_project", return_value=mock_project
        ):
            resp = test_client.get("/api/gitlab/mrs?state=merged")

        assert resp.status_code == 200
        mock_project.mergerequests.list.assert_called_with(
            state="merged", per_page=20, order_by="updated_at", sort="desc"
        )


class TestGetMR:
    def test_get_mr_returns_full_details(self, client) -> None:
        test_client, mock_project = client
        mock_project.mergerequests.get.return_value = _make_mr()

        with patch(
            "regis.server.routes.gitlab._get_project", return_value=mock_project
        ):
            resp = test_client.get("/api/gitlab/mrs/42")

        assert resp.status_code == 200
        data = resp.json()
        assert data["iid"] == 42
        assert "description" in data
        assert data["merge_status"] == "can_be_merged"
        assert data["pipeline"]["id"] == 100

    def test_get_mr_without_report(self, client) -> None:
        test_client, mock_project = client
        mock_project.mergerequests.get.return_value = _make_mr(
            description="No report here", labels=[]
        )

        with patch(
            "regis.server.routes.gitlab._get_project", return_value=mock_project
        ):
            resp = test_client.get("/api/gitlab/mrs/99")

        data = resp.json()
        assert data["has_report"] is False
        assert data["regis_labels"] == []


class TestListPipelines:
    def test_list_pipelines(self, client) -> None:
        test_client, mock_project = client
        mock_project.pipelines.list.return_value = [
            _make_pipeline(),
            _make_pipeline(id=101, status="running"),
        ]

        with patch(
            "regis.server.routes.gitlab._get_project", return_value=mock_project
        ):
            resp = test_client.get("/api/gitlab/pipelines")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["pipelines"][0]["id"] == 100
        assert data["pipelines"][0]["sha"] == "abc12345"

    def test_list_pipelines_with_source_filter(self, client) -> None:
        test_client, mock_project = client
        mock_project.pipelines.list.return_value = []

        with patch(
            "regis.server.routes.gitlab._get_project", return_value=mock_project
        ):
            test_client.get("/api/gitlab/pipelines?source=web")

        mock_project.pipelines.list.assert_called_with(
            per_page=20, order_by="updated_at", sort="desc", source="web"
        )


class TestNoGitLabConfig:
    def test_gitlab_routes_not_mounted_without_config(self, assets_dir: Path) -> None:
        app = create_app(assets_dir=assets_dir)
        client = TestClient(app)
        resp = client.get("/api/gitlab/mrs")
        # SPA fallback returns index.html, not a 404 JSON
        assert resp.status_code == 200
        assert "Dashboard" in resp.text

    def test_health_still_works(self, assets_dir: Path) -> None:
        app = create_app(assets_dir=assets_dir)
        client = TestClient(app)
        resp = client.get("/api/health")
        assert resp.status_code == 200
