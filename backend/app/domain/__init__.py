"""Domain Layer for AI Panel Studio."""

from app.domain.arbitrator import (
    ArbitrationContext,
    ArbitrationResult,
    SpeakerArbitrator,
)
from app.domain.entities import (
    DiscussionAggregate,
    Participant,
    Turn,
)
from app.domain.events import (
    ConsensusUpdatedEvent,
    DiscussionCreatedEvent,
    DivergenceUpdatedEvent,
    DomainEvent,
    HandRaisedEvent,
    ModeratorInterventionEvent,
    SessionConcludedEvent,
    SessionStatusChangedEvent,
    SpeakerSelectedEvent,
    SpeechChunkProducedEvent,
    TurnCompletedEvent,
)
from app.domain.exceptions import (
    DomainError,
    DomainInvariantError,
    DomainStateError,
)
from app.domain.repositories import (
    IDiscussionRepository,
    IEventStreamRepository,
)
from app.domain.value_objects import (
    ActionType,
    AgentIntent,
    ConsensusItem,
    DivergenceItem,
    SessionStatus,
    SpeakerScore,
)

__all__ = [
    # Aggregate Root & Entities
    "DiscussionAggregate",
    "Participant",
    "Turn",
    # Value Objects & Enums
    "SessionStatus",
    "ActionType",
    "AgentIntent",
    "SpeakerScore",
    "ConsensusItem",
    "DivergenceItem",
    # Domain Events
    "DomainEvent",
    "DiscussionCreatedEvent",
    "SessionStatusChangedEvent",
    "HandRaisedEvent",
    "SpeakerSelectedEvent",
    "SpeechChunkProducedEvent",
    "TurnCompletedEvent",
    "ModeratorInterventionEvent",
    "ConsensusUpdatedEvent",
    "DivergenceUpdatedEvent",
    "SessionConcludedEvent",
    # Repository Interfaces
    "IDiscussionRepository",
    "IEventStreamRepository",
    # Domain Services
    "SpeakerArbitrator",
    "ArbitrationContext",
    "ArbitrationResult",
    # Domain Exceptions
    "DomainError",
    "DomainStateError",
    "DomainInvariantError",
]
