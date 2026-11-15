"""Server-Sent Events (SSE) Interface Router."""

import asyncio
import json
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.infrastructure.database import get_db
from app.infrastructure.repositories import SqlAlchemyDiscussionRepository
from app.infrastructure.session_manager import session_manager

router = APIRouter(prefix="/api/discussions", tags=["Streaming"])


@router.get("/{discussion_id}/events")
async def stream_discussion_events(
    discussion_id: str,
    request: Request,
    last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
    query_last_event_id: Optional[int] = Query(None, alias="last_event_id"),
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    """Stream debate events in real time with monotonic sequence IDs and ring buffer replay."""
    # 1. Enforce existence check in database (returns 404 if missing)
    repo = SqlAlchemyDiscussionRepository(db)
    agg = await repo.get_by_id(discussion_id)
    if agg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discussion '{discussion_id}' not found.",
        )

    context = await session_manager.get_or_create(discussion_id)

    # 2. Resolve last event sequence ID
    last_id: Optional[int] = None
    if last_event_id is not None:
        try:
            last_id = int(last_event_id)
        except ValueError:
            last_id = None
    elif query_last_event_id is not None:
        last_id = query_last_event_id

    async def event_generator() -> AsyncGenerator[dict, None]:
        queue = context.subscribe()
        max_delivered_id = last_id if last_id is not None else 0

        # Immediately flush SSE connection headers to ensure client handshake completes
        yield {"comment": "connected"}

        try:
            # 3. Replay missed events from ring buffer if client reconnected
            if last_id is not None and last_id < context.ring_buffer.current_seq:
                if last_id >= context.ring_buffer.oldest_seq - 1:
                    replayed_events = context.ring_buffer.get_events_since(last_id)
                    for item in replayed_events:
                        max_delivered_id = max(max_delivered_id, item["id"])
                        yield {
                            "id": str(item["id"]),
                            "event": item["event"],
                            "data": json.dumps(item["data"], ensure_ascii=False),
                        }
                else:
                    # Gap overflow: emit sync_required notification
                    yield {
                        "event": "sync_required",
                        "data": json.dumps({"reason": "ring_buffer_gap_overflow"}),
                    }
                    # Also stream currently retained events
                    for item in context.ring_buffer.get_events_since(last_id):
                        max_delivered_id = max(max_delivered_id, item["id"])
                        yield {
                            "id": str(item["id"]),
                            "event": item["event"],
                            "data": json.dumps(item["data"], ensure_ascii=False),
                        }

            # 4. Stream live events with de-duplication
            while True:
                if await request.is_disconnected():
                    break
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=15.0)
                    if item.get("id") is not None and item["id"] <= max_delivered_id:
                        continue
                    if item.get("id") is not None:
                        max_delivered_id = max(max_delivered_id, item["id"])

                    yield {
                        "id": str(item["id"]),
                        "event": item["event"],
                        "data": json.dumps(item["data"], ensure_ascii=False),
                    }
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat ping comment
                    yield {"comment": "ping"}
        finally:
            context.unsubscribe(queue)

    return EventSourceResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
