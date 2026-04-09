"""GitLab webhook receiver for the regis dashboard server."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

MAX_EVENTS = 100


class EventBus:
    """In-memory event bus for SSE broadcasting."""

    def __init__(self) -> None:
        self._events: deque[dict[str, Any]] = deque(maxlen=MAX_EVENTS)
        self._subscribers: list[asyncio.Queue[dict[str, Any]]] = []

    def publish(self, event: dict[str, Any]) -> None:
        """Publish an event to all subscribers and store it."""
        self._events.append(event)
        for queue in self._subscribers:
            queue.put_nowait(event)

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        """Create a new subscriber queue."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        """Remove a subscriber queue."""
        try:
            self._subscribers.remove(queue)
        except ValueError:
            pass

    @property
    def recent_events(self) -> list[dict[str, Any]]:
        """Return recent events (newest first)."""
        return list(reversed(self._events))


def create_webhooks_router(
    *, webhook_secret: str | None = None
) -> tuple[APIRouter, EventBus]:
    """Create a FastAPI router for GitLab webhook handling.

    Args:
        webhook_secret: Optional secret token to validate webhook requests.

    Returns:
        Tuple of (router, event_bus) so the app can access the bus.
    """
    router = APIRouter(tags=["webhooks"])
    event_bus = EventBus()

    @router.post("/api/webhooks/gitlab")
    async def receive_webhook(request: Request) -> dict[str, str]:
        """Receive GitLab webhook events (merge_request, pipeline)."""
        if webhook_secret:
            token = request.headers.get("X-Gitlab-Token")
            if token != webhook_secret:
                raise HTTPException(status_code=403, detail="Invalid webhook token")

        try:
            payload = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc

        object_kind = payload.get("object_kind")
        if object_kind not in ("merge_request", "pipeline"):
            return {"status": "ignored", "reason": f"Unhandled event: {object_kind}"}

        event = _extract_event(object_kind, payload)
        event_bus.publish(event)
        logger.info("Webhook received: %s %s", object_kind, event.get("id", ""))

        return {"status": "accepted", "event": object_kind}

    @router.get("/api/events")
    async def event_stream() -> StreamingResponse:
        """SSE endpoint for real-time dashboard updates."""
        queue = event_bus.subscribe()

        async def generate():
            try:
                while True:
                    event = await queue.get()
                    import json

                    data = json.dumps(event)
                    yield f"event: {event.get('type', 'update')}\ndata: {data}\n\n"
            except asyncio.CancelledError:
                pass
            finally:
                event_bus.unsubscribe(queue)

        return StreamingResponse(generate(), media_type="text/event-stream")

    @router.get("/api/events/recent")
    async def recent_events() -> dict[str, Any]:
        """Return recent webhook events."""
        return {
            "events": event_bus.recent_events,
            "total": len(event_bus.recent_events),
        }

    return router, event_bus


def _extract_event(object_kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Extract a normalized event from a GitLab webhook payload."""
    if object_kind == "merge_request":
        mr = payload.get("object_attributes", {})
        return {
            "type": "merge_request",
            "action": mr.get("action"),
            "id": mr.get("iid"),
            "title": mr.get("title"),
            "state": mr.get("state"),
            "url": mr.get("url"),
            "source_branch": mr.get("source_branch"),
            "labels": [lb.get("title") for lb in payload.get("labels", [])],
        }
    elif object_kind == "pipeline":
        attrs = payload.get("object_attributes", {})
        return {
            "type": "pipeline",
            "id": attrs.get("id"),
            "status": attrs.get("status"),
            "ref": attrs.get("ref"),
            "source": attrs.get("source"),
            "url": payload.get("project", {}).get("web_url", "")
            + "/-/pipelines/"
            + str(attrs.get("id", "")),
        }
    return {"type": object_kind, "raw": payload}
