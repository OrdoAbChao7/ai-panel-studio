"""Domain Entities and Aggregate Root."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import uuid

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


class Turn(BaseModel):
    """Immutable turn entity recorded in debate transcript."""

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

    def can_transition_to(self, target_status: SessionStatus) -> bool:
        """Enforce domain aggregate status transition rules."""
        valid_transitions = {
            SessionStatus.CREATED: [SessionStatus.RUNNING, SessionStatus.TERMINATED],
            SessionStatus.RUNNING: [SessionStatus.PAUSED, SessionStatus.COMPLETED, SessionStatus.TERMINATED],
            SessionStatus.PAUSED: [SessionStatus.RUNNING, SessionStatus.TERMINATED],
            SessionStatus.COMPLETED: [],
            SessionStatus.TERMINATED: [],
        }
        return target_status in valid_transitions.get(self.status, [])

    def transition_to(self, target_status: SessionStatus) -> None:
        """Execute state transition or raise ValueError."""
        if not self.can_transition_to(target_status):
            raise ValueError(
                f"Invalid status transition from {self.status.value} to {target_status.value}"
            )
        self.status = target_status
        self.updated_at = datetime.now(timezone.utc)
