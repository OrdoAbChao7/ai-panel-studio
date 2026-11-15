"""Server-Sent Events (SSE) Interface Router."""

import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter, Header, HTTPException, Query, Request
from sse_starlette.sse import EventSourceResponse

from app.infrastructure.session_manager import session_manager

router = APIRouter(prefix="/api/discussions", tags=["Streaming"])


@router.get("/{discussion_id}/events")
async def stream_discussion_events(
    discussion_id: str,
    request: Request,
    last_event_id: str = Header(None, alias="Last-Event-ID"),
    query_last_event_id: int = Query(None, alias="last_event_id"),
) -> EventSourceResponse:
    """Stream debate events in real time with monotonic sequence IDs and ring buffer replay."""
    context = await session_manager.get_or_create(discussion_id)

    # Resolve last event sequence ID
    last_id = None
    if last_event_id:
        try:
            last_id = int(last_event_id)
        except ValueError:
            pass
    elif query_last_event_id is not None:
        last_id = query_last_event_id

    async def event_generator() -> AsyncGenerator[dict, None]:
        queue = context.subscribe()
        try:
            # 1. Replay missed events from ring buffer if client reconnected
            if last_id is not None and last_id < context.ring_buffer.current_seq:
                if last_id >= context.ring_buffer.oldest_seq - 1:
                    replayed_events = context.ring_buffer.get_events_since(last_id)
                    for item in replayed_events:
                        yield {
                            "id": item["id"],
                            "event": item["event"],
                            "data": json.dumps(item["data"], ensure_ascii=False),
                        }
                else:
                    # Gap overflow: inform client to re-sync full state
                    yield {
                        "event": "sync_required",
                        "data": json.dumps({"reason": "ring_buffer_gap_overflow"}),
                    }

            # 2. Stream live events
            while True:
                if await request.is_disconnected():
                    break
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {
                        "id": item["id"],
                        "event": item["event"],
                        "data": json.dumps(item["data"], ensure_ascii=False),
                    }
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat ping
                    yield {"comment": "ping"}
        finally:
            context.unsubscribe(queue)

    return EventSourceResponse(event_generator())
