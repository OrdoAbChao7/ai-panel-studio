"""Discussion Session Manager and In-Memory Event Ring Buffer."""

import asyncio
from collections import deque
from typing import Dict, List, Optional, Set
from pydantic import BaseModel


class EventRingBuffer:
    """Fixed-capacity circular buffer preserving monotonic sequence events for SSE replay."""

    def __init__(self, capacity: int = 500) -> None:
        self.capacity = capacity
        self.buffer: deque = deque(maxlen=capacity)
        self.current_seq: int = 0

    def append(self, event_type: str, payload: dict) -> dict:
        """Assign next monotonic sequence ID and store in buffer."""
        self.current_seq += 1
        event_item = {
            "id": self.current_seq,
            "event": event_type,
            "data": payload,
        }
        self.buffer.append(event_item)
        return event_item

    def get_events_since(self, last_event_id: int) -> List[dict]:
        """Fetch all buffered events with sequence ID strictly greater than last_event_id."""
        return [e for e in self.buffer if e["id"] > last_event_id]

    @property
    def oldest_seq(self) -> int:
        if not self.buffer:
            return 0
        return self.buffer[0]["id"]


class DiscussionSessionContext:
    """Isolated runtime execution context for an active debate session."""

    def __init__(self, discussion_id: str) -> None:
        self.discussion_id = discussion_id
        self.lock = asyncio.Lock()
        self.pause_event = asyncio.Event()
        self.pause_event.set()  # Initially running
        self.task: Optional[asyncio.Task] = None
        self.ring_buffer = EventRingBuffer(capacity=500)
        self.subscribers: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        """Register a new SSE client subscriber queue."""
        queue: asyncio.Queue = asyncio.Queue()
        self.subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Remove an SSE client subscriber queue."""
        self.subscribers.discard(queue)

    def broadcast(self, event_type: str, payload: dict) -> dict:
        """Store in ring buffer and fan out to all active subscriber queues."""
        event_item = self.ring_buffer.append(event_type, payload)
        for queue in list(self.subscribers):
            try:
                queue.put_nowait(event_item)
            except asyncio.QueueFull:
                pass
        return event_item


class SessionManager:
    """Registry managing concurrent discussion session contexts."""

    def __init__(self) -> None:
        self.sessions: Dict[str, DiscussionSessionContext] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, discussion_id: str) -> DiscussionSessionContext:
        """Retrieve existing context or create a new one."""
        async with self._lock:
            if discussion_id not in self.sessions:
                self.sessions[discussion_id] = DiscussionSessionContext(discussion_id)
            return self.sessions[discussion_id]

    async def get(self, discussion_id: str) -> Optional[DiscussionSessionContext]:
        """Retrieve session context if present."""
        return self.sessions.get(discussion_id)

    async def remove(self, discussion_id: str) -> None:
        """Clean up and remove session context."""
        async with self._lock:
            context = self.sessions.pop(discussion_id, None)
            if context and context.task and not context.task.done():
                context.task.cancel()


session_manager = SessionManager()
