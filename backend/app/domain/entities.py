"""Domain Entities and Aggregate Root."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.domain.exceptions import DomainInvariantError, DomainStateError
from app.domain.value_objects import (
    ActionType,
    ConsensusItem,
    DivergenceItem,
    SessionStatus,
)


class Participant(BaseModel):
    """Participant entity representing an expert agent or moderator."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discussion_id: str
    name: str
    occupation: str
    stance: str
    perspective: str
    color_hex: str
    role: str = "expert"  # "expert" | "moderator"
    total_turns_spoken: int = 0
    last_spoken_turn: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def record_speech(self, turn_number: int) -> None:
        """Update turn statistics upon speech commitment."""
        self.total_turns_spoken += 1
        self.last_spoken_turn = turn_number


class Turn(BaseModel):
    """Immutable turn entity recorded in debate transcript."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discussion_id: str
    turn_number: int
    round_number: int
    speaker_id: str
    speaker_name: str
    action_type: ActionType
    content: str
    rationale: Optional[str] = None
    priority_score: float = 0.0
    target_speaker_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DiscussionAggregate(BaseModel):
    """Aggregate Root managing debate session invariants and collections."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    status: SessionStatus = SessionStatus.CREATED
    current_round: int = 0
    max_rounds: int = 5
    summary: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    participants: Dict[str, Participant] = Field(default_factory=dict)
    turns: List[Turn] = Field(default_factory=list)
    consensus_items: List[ConsensusItem] = Field(default_factory=list)
    divergence_items: List[DivergenceItem] = Field(default_factory=list)
    pending_events: List[Any] = Field(default_factory=list)

    def can_transition_to(self, target_status: SessionStatus) -> bool:
        """Check if target lifecycle status transition is valid."""
        valid_transitions = {
            SessionStatus.CREATED: [SessionStatus.RUNNING, SessionStatus.TERMINATED],
            SessionStatus.RUNNING: [
                SessionStatus.PAUSED,
                SessionStatus.COMPLETED,
                SessionStatus.TERMINATED,
            ],
            SessionStatus.PAUSED: [SessionStatus.RUNNING, SessionStatus.TERMINATED],
            SessionStatus.COMPLETED: [],
            SessionStatus.TERMINATED: [],
        }
        return target_status in valid_transitions.get(self.status, [])

    def transition_status(self, target_status: SessionStatus) -> None:
        """Transition lifecycle status and enqueue SessionStatusChangedEvent."""
        if not self.can_transition_to(target_status):
            raise DomainStateError(
                f"Invalid status transition from '{self.status.value}' to '{target_status.value}'"
            )
        old_status = self.status
        self.status = target_status
        self.updated_at = datetime.now(timezone.utc)

        from app.domain.events import SessionStatusChangedEvent

        self.pending_events.append(
            SessionStatusChangedEvent(
                discussion_id=self.id,
                old_status=old_status.value,
                new_status=target_status.value,
            )
        )

    # Backward compatibility alias
    transition_to = transition_status

    def add_participant(self, participant: Participant) -> None:
        """Register a participant before discussion starts."""
        if self.status != SessionStatus.CREATED:
            raise DomainStateError(
                "Cannot add participant to a discussion that is not in 'created' state."
            )
        if participant.id in self.participants:
            raise DomainInvariantError(
                f"Participant '{participant.id}' is already registered."
            )
        if participant.discussion_id != self.id:
            raise DomainInvariantError(
                f"Participant discussion_id '{participant.discussion_id}' does not match aggregate '{self.id}'."
            )
        self.participants[participant.id] = participant
        self.updated_at = datetime.now(timezone.utc)

    def add_turn(self, turn: Turn) -> None:
        """Commit an immutable speech turn and enforce domain invariants."""
        if self.status != SessionStatus.RUNNING:
            raise DomainStateError(
                f"Cannot add turn when discussion is in '{self.status.value}' state. Must be 'running'."
            )
        if turn.discussion_id != self.id:
            raise DomainInvariantError(
                f"Turn discussion_id '{turn.discussion_id}' does not match aggregate '{self.id}'."
            )
        if turn.speaker_id not in self.participants:
            raise DomainInvariantError(
                f"Speaker '{turn.speaker_id}' is not a registered participant in this discussion."
            )

        # Invariant: Consecutive Speaker Cooldown
        if len(self.turns) > 0 and self.turns[-1].speaker_id == turn.speaker_id:
            raise DomainInvariantError(
                f"Consecutive speaker invariant violated: participant '{turn.speaker_id}' cannot speak in two consecutive turns."
            )

        # Invariant: Turn Monotonicity & Monotonic Sequence
        expected_turn_number = len(self.turns) + 1
        if turn.turn_number != expected_turn_number:
            raise DomainInvariantError(
                f"Turn number must be strictly monotonic: expected {expected_turn_number}, got {turn.turn_number}."
            )

        # Invariant: Max Rounds Boundary
        if turn.round_number > self.max_rounds:
            raise DomainInvariantError(
                f"Turn round {turn.round_number} exceeds max_rounds {self.max_rounds}."
            )

        # Commit turn
        self.turns.append(turn)

        # Update participant statistics
        speaker = self.participants[turn.speaker_id]
        speaker.record_speech(turn.turn_number)

        # Advance current round
        self.current_round = max(self.current_round, turn.round_number)
        self.updated_at = datetime.now(timezone.utc)

        # Emit TurnCompletedEvent
        from app.domain.events import TurnCompletedEvent

        self.pending_events.append(
            TurnCompletedEvent(
                discussion_id=self.id,
                turn_id=turn.id,
                speaker_id=turn.speaker_id,
                turn_number=turn.turn_number,
                content=turn.content,
                action_type=(
                    turn.action_type.value
                    if hasattr(turn.action_type, "value")
                    else str(turn.action_type)
                ),
                round_number=turn.round_number,
            )
        )

    def update_consensus(self, items: List[ConsensusItem]) -> None:
        """Update consensus collection and enqueue ConsensusUpdatedEvent."""
        self.consensus_items = items
        self.updated_at = datetime.now(timezone.utc)

        from app.domain.events import ConsensusUpdatedEvent

        self.pending_events.append(
            ConsensusUpdatedEvent(
                discussion_id=self.id,
                consensus_items=items,
            )
        )

    def update_divergence(self, items: List[DivergenceItem]) -> None:
        """Update divergence collection and enqueue DivergenceUpdatedEvent."""
        self.divergence_items = items
        self.updated_at = datetime.now(timezone.utc)

        from app.domain.events import DivergenceUpdatedEvent

        self.pending_events.append(
            DivergenceUpdatedEvent(
                discussion_id=self.id,
                divergence_items=items,
            )
        )

    def conclude(
        self, summary: str, final_stances: Optional[Dict[str, Any]] = None
    ) -> None:
        """Conclude debate session with final synthesis and emit SessionConcludedEvent."""
        self.summary = summary
        self.transition_status(SessionStatus.COMPLETED)

        from app.domain.events import SessionConcludedEvent

        self.pending_events.append(
            SessionConcludedEvent(
                discussion_id=self.id,
                summary=summary,
                final_stances=final_stances or {},
            )
        )

    def collect_pending_events(self) -> List[Any]:
        """Atomically drain all accumulated pending domain events."""
        events = list(self.pending_events)
        self.pending_events.clear()
        return events
