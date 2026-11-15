"""Core Event Dispatcher & Base Event Definitions."""

from datetime import datetime, timezone
from typing import Any, Dict
from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """Base event model with timestamp and serialization."""

    event_type: str
    discussion_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = Field(default_factory=dict)

    def to_sse_dict(self, seq_id: int) -> Dict[str, Any]:
        """Convert event to SSE wire structure."""
        return {
            "id": seq_id,
            "event": self.event_type,
            "data": self.payload,
        }
