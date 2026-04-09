"""GitLab API proxy routes for the regis dashboard server."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import gitlab
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

REGIS_LABEL_PREFIX = "regis::"


@dataclass
class GitLabConfig:
    """Configuration for the GitLab API proxy."""

    url: str
    token: str
    project_id: str | int


def _get_project(config: GitLabConfig) -> Any:
    """Get a python-gitlab project instance."""
    gl = gitlab.Gitlab(config.url, private_token=config.token)
    try:
        return gl.projects.get(config.project_id)
    except gitlab.GitlabGetError as exc:
        raise HTTPException(
            status_code=502, detail=f"Failed to access GitLab project: {exc}"
        ) from exc


def _extract_regis_labels(labels: list[str]) -> list[str]:
    """Extract regis-scoped labels from a label list."""
    return [lb for lb in labels if lb.startswith(REGIS_LABEL_PREFIX)]


def _serialize_mr(mr: Any) -> dict[str, Any]:
    """Serialize a MR object to a JSON-safe dict with regis-relevant fields."""
    attrs = mr.attributes if hasattr(mr, "attributes") else mr
    labels = attrs.get("labels", [])
    return {
        "iid": attrs["iid"],
        "title": attrs["title"],
        "state": attrs["state"],
        "web_url": attrs["web_url"],
        "source_branch": attrs["source_branch"],
        "author": attrs.get("author", {}).get("username"),
        "created_at": attrs["created_at"],
        "updated_at": attrs["updated_at"],
        "labels": labels,
        "regis_labels": _extract_regis_labels(labels),
        "has_report": "View Analysis Report" in (attrs.get("description") or ""),
    }


def _serialize_pipeline(pipeline: Any) -> dict[str, Any]:
    """Serialize a pipeline object to a JSON-safe dict."""
    attrs = pipeline.attributes if hasattr(pipeline, "attributes") else pipeline
    return {
        "id": attrs["id"],
        "status": attrs["status"],
        "ref": attrs["ref"],
        "sha": attrs.get("sha", "")[:8],
        "web_url": attrs["web_url"],
        "created_at": attrs["created_at"],
        "updated_at": attrs.get("updated_at"),
        "source": attrs.get("source"),
    }


def create_gitlab_router(config: GitLabConfig) -> APIRouter:
    """Create a FastAPI router with GitLab proxy endpoints.

    Args:
        config: GitLab connection configuration.
    """
    router = APIRouter(prefix="/api/gitlab", tags=["gitlab"])

    @router.get("/mrs")
    async def list_mrs(
        state: str = "opened",
        per_page: int = 20,
    ) -> dict[str, Any]:
        """List merge requests with regis analysis data."""
        project = _get_project(config)
        try:
            mrs = project.mergerequests.list(
                state=state,
                per_page=per_page,
                order_by="updated_at",
                sort="desc",
            )
        except gitlab.GitlabListError as exc:
            raise HTTPException(
                status_code=502, detail=f"Failed to list MRs: {exc}"
            ) from exc
        return {
            "merge_requests": [_serialize_mr(mr) for mr in mrs],
            "total": len(mrs),
        }

    @router.get("/mrs/{iid}")
    async def get_mr(iid: int) -> dict[str, Any]:
        """Get a single merge request with full details."""
        project = _get_project(config)
        try:
            mr = project.mergerequests.get(iid)
        except gitlab.GitlabGetError as exc:
            raise HTTPException(
                status_code=404, detail=f"MR !{iid} not found: {exc}"
            ) from exc

        data = _serialize_mr(mr)
        # Add extra detail fields
        attrs = mr.attributes
        data["description"] = attrs.get("description", "")
        data["merge_status"] = attrs.get("merge_status")
        data["pipeline"] = (
            _serialize_pipeline_summary(attrs["pipeline"])
            if attrs.get("pipeline")
            else None
        )
        return data

    @router.get("/pipelines")
    async def list_pipelines(
        per_page: int = 20,
        source: str | None = None,
    ) -> dict[str, Any]:
        """List recent pipelines."""
        project = _get_project(config)
        kwargs: dict[str, Any] = {
            "per_page": per_page,
            "order_by": "updated_at",
            "sort": "desc",
        }
        if source:
            kwargs["source"] = source
        try:
            pipelines = project.pipelines.list(**kwargs)
        except gitlab.GitlabListError as exc:
            raise HTTPException(
                status_code=502, detail=f"Failed to list pipelines: {exc}"
            ) from exc
        return {
            "pipelines": [_serialize_pipeline(p) for p in pipelines],
            "total": len(pipelines),
        }

    return router


def _serialize_pipeline_summary(pipeline_data: dict[str, Any]) -> dict[str, Any]:
    """Serialize an inline pipeline dict (from MR attributes)."""
    return {
        "id": pipeline_data.get("id"),
        "status": pipeline_data.get("status"),
        "web_url": pipeline_data.get("web_url"),
    }
