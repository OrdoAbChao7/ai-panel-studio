"""Domain Events for AI Panel Studio."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.domain.entities import Turn
from app.domain.value_objects import AgentIntent, ConsensusItem, DivergenceItem, SessionStatus


class DomainEvent(BaseModel):
    """Abstract base domain event."""

    event_type: str
    discussion_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = Field(default_factory=dict)


class DiscussionCreatedEvent(DomainEvent):
    """Emitted upon discussion creation."""

    event_type: str = "discussion_created"


class SessionStatusChangedEvent(DomainEvent):
    """Emitted when discussion status transitions."""

    event_type: str = "session_status_changed"


class HandRaisedEvent(DomainEvent):
    """Emitted when candidate experts raise hands and submit intents."""

    event_type: str = "hand_raising"


class SpeakerSelectedEvent(DomainEvent):
    """Emitted when arbitrator selects winning speaker."""

    event_type: str = "speaker_selected"


class SpeechChunkProducedEvent(DomainEvent):
    """Emitted per streaming chunk during speech generation."""

    event_type: str = "speech_chunk"


class TurnCompletedEvent(DomainEvent):
    """Emitted when an expert's turn is fully generated and committed."""

    event_type: str = "speech_completed"


class ModeratorInterventionEvent(DomainEvent):
    """Emitted when moderator delivers an intervention."""

    event_type: str = "moderator_intervention"


class ConsensusUpdatedEvent(DomainEvent):
    """Emitted when consensus items are updated."""

    event_type: str = "consensus_updated"


class DivergenceUpdatedEvent(DomainEvent):
    """Emitted when divergence items are updated."""

    event_type: str = "divergence_updated"


class SessionConcludedEvent(DomainEvent):
    """Emitted when debate finishes with final synthesis."""

    event_type: str = "session_concluded"
