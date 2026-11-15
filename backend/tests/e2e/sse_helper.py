"""
Server-Sent Events (SSE) Test Helper for AI Panel Studio E2E Tests.
Provides:
- SSEEvent data model with JSON decoding and schema contracts
- SSEStreamReader for direct line-by-line async stream reading
- SSECollector for asynchronous background event buffering and predicate waiting
- Comprehensive assertion helpers for event sequences, monotonic IDs, and payloads
"""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Union
import httpx


@dataclass
class SSEEvent:
    """Represents a single parsed Server-Sent Event."""
    id: Optional[str]
    event: str
    data: Any  # Parsed dict/list if valid JSON, otherwise raw str
    raw_data: str
    retry: Optional[int] = None

    @property
    def is_json(self) -> bool:
        return isinstance(self.data, (dict, list))

    def get(self, key: str, default: Any = None) -> Any:
        if isinstance(self.data, dict):
            return self.data.get(key, default)
        return default

    def __repr__(self) -> str:
        snippet = str(self.data)[:60] + "..." if len(str(self.data)) > 60 else str(self.data)
        return f"<SSEEvent id={self.id} event={self.event} data={snippet}>"


def parse_sse_block(lines: List[str]) -> Optional[SSEEvent]:
    """
    Parses a block of SSE lines into an SSEEvent object.
    Complies with W3C Server-Sent Events specification.
    """
    event_type = "message"
    event_id = None
    retry_ms = None
    data_lines = []

    for line in lines:
        line = line.rstrip("\r\n")
        if not line or line.startswith(":"):
            continue  # Comment or ping line

        if ":" in line:
            field_name, val = line.split(":", 1)
            if val.startswith(" "):
                val = val[1:]  # Strip single leading space per W3C spec
            
            if field_name == "event":
                event_type = val
            elif field_name == "id":
                event_id = val
            elif field_name == "data":
                data_lines.append(val)
            elif field_name == "retry":
                try:
                    retry_ms = int(val)
                except ValueError:
                    pass
        else:
            field_name = line
            if field_name == "data":
                data_lines.append("")

    if not data_lines and not event_id and event_type == "message":
        return None

    raw_data = "\n".join(data_lines)
    try:
        data = json.loads(raw_data) if raw_data else None
    except json.JSONDecodeError:
        data = raw_data

    return SSEEvent(id=event_id, event=event_type, data=data, raw_data=raw_data, retry=retry_ms)


class SSEStreamReader:
    """
    Direct asynchronous iterator for SSE streams using httpx.
    Usage:
        async with SSEStreamReader(client, "/api/discussions/1/events") as stream:
            async for event in stream.iter_events():
                if event.event == "session_concluded":
                    break
    """
    def __init__(
        self,
        client: httpx.AsyncClient,
        url: str,
        last_event_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ):
        self.client = client
        self.url = url
        self.last_event_id = last_event_id
        self.headers = headers or {}
        self.timeout = timeout
        self._cm = None
        self._response: Optional[httpx.Response] = None

    async def __aenter__(self):
        req_headers = {"Accept": "text/event-stream"}
        req_headers.update(self.headers)
        if self.last_event_id is not None:
            req_headers["Last-Event-ID"] = str(self.last_event_id)

        self._cm = self.client.stream("GET", self.url, headers=req_headers, timeout=self.timeout)
        self._response = await self._cm.__aenter__()
        if self._response.status_code != 200:
            content = await self._response.aread()
            raise AssertionError(f"SSE stream connection failed: HTTP {self._response.status_code}: {content.decode('utf-8', errors='ignore')}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._cm:
            await self._cm.__aexit__(exc_type, exc_val, exc_tb)

    async def iter_events(self) -> AsyncIterator[SSEEvent]:
        """Yields SSEEvent instances as they arrive from the server."""
        current_block: List[str] = []
        async for line in self._response.aiter_lines():
            line = line.rstrip("\r\n")
            if not line:
                if current_block:
                    evt = parse_sse_block(current_block)
                    current_block = []
                    if evt:
                        yield evt
            else:
                current_block.append(line)
        if current_block:
            evt = parse_sse_block(current_block)
            if evt:
                yield evt

    async def collect_until(
        self,
        predicate: Union[str, Callable[[SSEEvent], bool]],
        timeout: float = 30.0,
        max_events: Optional[int] = None,
    ) -> List[SSEEvent]:
        """Collects events until predicate evaluates to True or max_events reached."""
        events = []
        check_fn = (lambda e: e.event == predicate) if isinstance(predicate, str) else predicate

        async def _consumer():
            async for evt in self.iter_events():
                events.append(evt)
                if check_fn(evt):
                    break
                if max_events and len(events) >= max_events:
                    break

        await asyncio.wait_for(_consumer(), timeout=timeout)
        return events


class SSECollector:
    """
    Background SSE event accumulator.
    Solves the test race condition by connecting BEFORE triggering REST actions,
    buffering events in an async-safe list, and notifying waiters.
    
    Usage:
        async with SSECollector(client, "/api/discussions/d1/events") as collector:
            await client.post("/api/discussions/d1/start")
            evt = await collector.wait_for_event("speaker_selected", timeout=10.0)
            assert evt.data["speaker_id"] is not None
            
            await collector.wait_for_event("session_concluded", timeout=20.0)
            collector.assert_monotonic_ids()
    """
    def __init__(
        self,
        client: httpx.AsyncClient,
        url: str,
        last_event_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ):
        self.client = client
        self.url = url
        self.last_event_id = last_event_id
        self.headers = headers or {}
        self.timeout = timeout
        self.events: List[SSEEvent] = []
        self._cond = asyncio.Condition()
        self._new_event_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        self._closed = False
        self._exception: Optional[Exception] = None
        self._connected = asyncio.Event()

    async def start(self) -> "SSECollector":
        """Spawns background listener task and waits for HTTP connection handshake."""
        self._task = asyncio.create_task(self._listener_loop())
        # Wait up to 5s for connection handshake
        try:
            await asyncio.wait_for(self._connected.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            # If not connected yet, proceed anyway; listener continues
            pass
        return self

    async def _listener_loop(self):
        req_headers = {"Accept": "text/event-stream"}
        req_headers.update(self.headers)
        if self.last_event_id is not None:
            req_headers["Last-Event-ID"] = str(self.last_event_id)

        try:
            async with self.client.stream("GET", self.url, headers=req_headers, timeout=self.timeout) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise RuntimeError(f"SSE stream failed HTTP {resp.status_code}: {body.decode('utf-8', errors='ignore')}")

                self._connected.set()

                current_block: List[str] = []
                async for line in resp.aiter_lines():
                    if self._closed:
                        break
                    line = line.rstrip("\r\n")
                    if not line:
                        if current_block:
                            evt = parse_sse_block(current_block)
                            current_block = []
                            if evt:
                                async with self._cond:
                                    self.events.append(evt)
                                    self._new_event_event.set()
                                    self._cond.notify_all()
                    else:
                        current_block.append(line)
        except asyncio.CancelledError:
            async with self._cond:
                self._cond.notify_all()
        except Exception as e:
            self._exception = e
            self._connected.set()
            async with self._cond:
                self._cond.notify_all()
        finally:
            self._connected.set()
            async with self._cond:
                self._cond.notify_all()

    async def wait_for_event(
        self,
        predicate: Union[str, Callable[[SSEEvent], bool]],
        timeout: float = 15.0,
    ) -> SSEEvent:
        """
        Awaits an event satisfying the predicate.
        If already received, returns immediately.
        Otherwise suspends until the matching event arrives or timeout elapses.
        """
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        check_fn = (lambda e: e.event == predicate) if isinstance(predicate, str) else predicate

        async with self._cond:
            while True:
                if self._exception:
                    raise RuntimeError(f"Background SSE stream encountered exception: {self._exception}")

                for e in self.events:
                    if check_fn(e):
                        return e

                elapsed = loop.time() - start_time
                remaining = timeout - elapsed
                if remaining <= 0:
                    event_summary = [f"{e.id}:{e.event}" for e in self.events]
                    raise TimeoutError(
                        f"Timed out after {timeout}s waiting for matching SSE event. "
                        f"Buffered events ({len(self.events)}): {event_summary}"
                    )

                try:
                    await asyncio.wait_for(self._cond.wait(), timeout=remaining)
                except asyncio.TimeoutError:
                    event_summary = [f"{e.id}:{e.event}" for e in self.events]
                    raise TimeoutError(
                        f"Timed out after {timeout}s waiting for matching SSE event. "
                        f"Buffered events ({len(self.events)}): {event_summary}"
                    )

    async def wait_for_conclusion(self, timeout: float = 30.0) -> SSEEvent:
        """Convenience method to await session_concluded event."""
        return await self.wait_for_event("session_concluded", timeout=timeout)

    def get_events_by_type(self, event_type: str) -> List[SSEEvent]:
        """Returns all received events of a given type in arrival order."""
        return [e for e in self.events if e.event == event_type]

    def assert_monotonic_ids(self) -> None:
        """Verifies that all received events have strictly non-decreasing integer sequence IDs."""
        numeric_ids = []
        for e in self.events:
            if e.id is not None:
                try:
                    numeric_ids.append(int(e.id))
                except ValueError:
                    pass
        if len(numeric_ids) > 1:
            for i in range(len(numeric_ids) - 1):
                assert numeric_ids[i] <= numeric_ids[i + 1], (
                    f"SSE sequence IDs violated monotonicity: {numeric_ids[i]} > {numeric_ids[i+1]}"
                )

    def assert_event_sequence(self, expected_types: List[str]) -> None:
        """Verifies that the sequence of event types appears as a subsequence in buffered events."""
        actual_types = [e.event for e in self.events]
        it = iter(actual_types)
        for expected in expected_types:
            assert any(actual == expected for actual in it), (
                f"Expected event '{expected}' in sequence, but not found in remaining actual events: {actual_types}"
            )

    async def close(self):
        """Cleanly terminates the background listener."""
        self._closed = True
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


def validate_sse_event_contract(event: SSEEvent) -> bool:
    """
    Validates that an SSEEvent satisfies the payload contracts specified in PROJECT.md.
    Throws AssertionError with detailed diagnostics upon contract mismatch.
    """
    t = event.event
    d = event.data

    if t == "session_status_changed":
        assert isinstance(d, dict), f"{t} payload must be a dict"
        assert "old_status" in d and "new_status" in d, f"{t} missing old_status/new_status: {d}"

    elif t == "hand_raising":
        assert isinstance(d, list), f"{t} payload must be a list of intent objects"
        for item in d:
            assert "agent_id" in item or "speaker_id" in item, f"hand_raising item missing agent_id: {item}"
            assert "priority_score" in item, f"hand_raising item missing priority_score: {item}"

    elif t == "speaker_selected":
        assert isinstance(d, dict), f"{t} payload must be a dict"
        assert "speaker_id" in d, f"{t} missing speaker_id: {d}"
        assert "score" in d or "priority_score" in d, f"{t} missing score: {d}"

    elif t == "speech_chunk":
        assert isinstance(d, dict), f"{t} payload must be a dict"
        assert "turn_id" in d and "chunk" in d, f"{t} missing fields: {d}"

    elif t == "speech_completed":
        assert isinstance(d, dict), f"{t} payload must be a dict"
        assert "turn_id" in d and "content" in d and "action_type" in d, f"{t} missing fields: {d}"

    elif t == "moderator_intervention":
        assert isinstance(d, dict), f"{t} payload must be a dict"
        assert "type" in d and "content" in d, f"{t} missing type/content: {d}"

    elif t == "consensus_updated":
        assert isinstance(d, list), f"{t} payload must be a list of consensus items"

    elif t == "divergence_updated":
        assert isinstance(d, list), f"{t} payload must be a list of divergence items"

    elif t == "session_concluded":
        assert isinstance(d, dict), f"{t} payload must be a dict"
        assert "summary" in d, f"{t} missing summary: {d}"

    return True
