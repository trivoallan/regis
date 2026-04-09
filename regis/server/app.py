"""FastAPI application factory for the regis dashboard server."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)


def create_app(
    *,
    assets_dir: Path,
    report: Path | None = None,
    archives: list[dict[str, str]] | None = None,
    gitlab_url: str | None = None,
    gitlab_token: str | None = None,
    gitlab_project: str | None = None,
    webhook_secret: str | None = None,
) -> FastAPI:
    """Create and configure the dashboard FastAPI application.

    Args:
        assets_dir: Path to the bundled dashboard static assets.
        report: Optional path to a report.json file to serve.
        archives: Optional list of archive dicts (name/path) for archives.json.
        gitlab_url: GitLab instance URL (e.g. https://gitlab.com).
        gitlab_token: GitLab private token for API access.
        gitlab_project: GitLab project ID or path.
    """
    app = FastAPI(title="Regis Dashboard", docs_url=None, redoc_url=None)

    archives_payload: bytes | None = None
    if archives:
        archives_payload = json.dumps({"archives": archives}, indent=2).encode()

    @app.get("/report.json")
    async def serve_report() -> Response:
        if report and report.exists():
            return FileResponse(report, media_type="application/json")
        return JSONResponse({"error": "No report loaded"}, status_code=404)

    @app.get("/archives.json")
    async def serve_archives() -> Response:
        if archives_payload is not None:
            return Response(content=archives_payload, media_type="application/json")
        return JSONResponse({"error": "No archives configured"}, status_code=404)

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    # Mount GitLab API proxy if configured
    if gitlab_url and gitlab_token and gitlab_project:
        from regis.server.routes.gitlab import GitLabConfig, create_gitlab_router

        gitlab_config = GitLabConfig(
            url=gitlab_url, token=gitlab_token, project_id=gitlab_project
        )
        app.include_router(create_gitlab_router(gitlab_config))

        from regis.server.routes.trigger import create_trigger_router

        app.include_router(create_trigger_router(gitlab_config))

    # Webhook receiver (works with or without GitLab config)
    from regis.server.routes.webhooks import create_webhooks_router

    webhooks_router, event_bus = create_webhooks_router(webhook_secret=webhook_secret)
    app.include_router(webhooks_router)
    app.state.event_bus = event_bus

    # Static files + SPA fallback must be mounted last
    app.mount("/", _SPAStaticFiles(directory=str(assets_dir), html=True), name="spa")

    return app


class _SPAStaticFiles(StaticFiles):
    """StaticFiles subclass that falls back to index.html for SPA routing."""

    async def get_response(self, path: str, scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except Exception:
            # SPA fallback: return index.html for any unmatched route
            return await super().get_response("index.html", scope)
