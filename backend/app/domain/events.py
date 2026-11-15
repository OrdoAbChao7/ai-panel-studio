"""Domain Events for AI Panel Studio."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.domain.value_objects import AgentIntent, ConsensusItem, DivergenceItem


class DomainEvent(BaseModel):
    """Abstract base domain event for state notifications and event streams."""

    event_type: str
    discussion_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = Field(default_factory=dict)

    def to_sse_dict(self) -> Dict[str, Any]:
        """Convert domain event to SSE dictionary format."""
        return {
            "event": self.event_type,
            "data": {
                "event_type": self.event_type,
                "discussion_id": self.discussion_id,
                "timestamp": self.timestamp.isoformat(),
                **self.payload,
            },
        }


class DiscussionCreatedEvent(DomainEvent):
    """Emitted upon discussion aggregate initialization."""

    event_type: str = "discussion_created"

    def __init__(
        self,
        discussion_id: str,
        topic: Optional[str] = None,
        participant_count: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        p = payload.copy() if payload else {}
        if topic is not None:
            p["topic"] = topic
        if participant_count is not None:
            p["participant_count"] = participant_count
        p.setdefault("discussion_id", discussion_id)
        kwargs.pop("event_type", None)
        super().__init__(
            event_type="discussion_created",
            discussion_id=discussion_id,
            payload=p,
            **kwargs,
        )


class SessionStatusChangedEvent(DomainEvent):
    """Emitted when discussion status transitions."""

    event_type: str = "session_status_changed"

    def __init__(
        self,
        discussion_id: str,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        p = payload.copy() if payload else {}
        if old_status is not None:
            p["old_status"] = old_status
        if new_status is not None:
            p["new_status"] = new_status
        p.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        kwargs.pop("event_type", None)
        super().__init__(
            event_type="session_status_changed",
            discussion_id=discussion_id,
            payload=p,
            **kwargs,
        )


class HandRaisedEvent(DomainEvent):
    """Emitted when candidate experts raise hands and submit intents."""

    event_type: str = "hand_raising"

    def __init__(
        self,
        discussion_id: str,
        candidate_intents: Optional[List[AgentIntent]] = None,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        p = payload.copy() if payload else {}
        if candidate_intents is not None:
            p["candidates"] = [
                {
                    "agent_id": intent.agent_id,
                    "agent_name": intent.agent_name,
                    "action_type": (
                        intent.action_type.value
                        if hasattr(intent.action_type, "value")
                        else str(intent.action_type)
                    ),
                    "priority_score": intent.urgency,
                    "target_speaker_id": intent.target_speaker_id,
                    "target_speaker_name": intent.target_speaker_name,
                    "rationale": intent.rationale,
                }
                for intent in candidate_intents
            ]
        kwargs.pop("event_type", None)
        super().__init__(
            event_type="hand_raising",
            discussion_id=discussion_id,
            payload=p,
            **kwargs,
        )


class SpeakerSelectedEvent(DomainEvent):
    """Emitted when arbitrator selects winning speaker."""

    event_type: str = "speaker_selected"

    def __init__(
        self,
        discussion_id: str,
        speaker_id: Optional[str] = None,
        speaker_name: Optional[str] = None,
        score: Optional[float] = None,
        score_breakdown: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        p = payload.copy() if payload else {}
        if speaker_id is not None:
            p["speaker_id"] = speaker_id
        if speaker_name is not None:
            p["speaker_name"] = speaker_name
        if score is not None:
            p["score"] = score
        if score_breakdown is not None:
            p["score_breakdown"] = score_breakdown
        kwargs.pop("event_type", None)
        super().__init__(
            event_type="speaker_selected",
            discussion_id=discussion_id,
            payload=p,
            **kwargs,
        )


class SpeechChunkProducedEvent(DomainEvent):
    """Emitted per streaming chunk during speech generation."""

    event_type: str = "speech_chunk"

    def __init__(
        self,
        discussion_id: str,
        turn_id: Optional[str] = None,
        speaker_id: Optional[str] = None,
        chunk: Optional[str] = None,
        is_first: Optional[bool] = None,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        p = payload.copy() if payload else {}
        if turn_id is not None:
            p["turn_id"] = turn_id
        if speaker_id is not None:
            p["speaker_id"] = speaker_id
        if chunk is not None:
            p["chunk"] = chunk
        if is_first is not None:
            p["is_first"] = is_first
        else:
            p.setdefault("is_first", False)
        kwargs.pop("event_type", None)
        super().__init__(
            event_type="speech_chunk",
            discussion_id=discussion_id,
            payload=p,
            **kwargs,
        )


class TurnCompletedEvent(DomainEvent):
    """Emitted when an expert's turn is fully generated and committed."""

    event_type: str = "speech_completed"

    def __init__(
        self,
        discussion_id: str,
        turn_id: Optional[str] = None,
        speaker_id: Optional[str] = None,
        turn_number: Optional[int] = None,
        content: Optional[str] = None,
        action_type: Optional[str] = None,
        round_number: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        p = payload.copy() if payload else {}
        if turn_id is not None:
            p["turn_id"] = turn_id
        if speaker_id is not None:
            p["speaker_id"] = speaker_id
        if turn_number is not None:
            p["turn_number"] = turn_number
        if content is not None:
            p["content"] = content
        if action_type is not None:
            p["action_type"] = action_type
        if round_number is not None:
            p["round_number"] = round_number
        kwargs.pop("event_type", None)
        super().__init__(
            event_type="speech_completed",
            discussion_id=discussion_id,
            payload=p,
            **kwargs,
        )


class ModeratorInterventionEvent(DomainEvent):
    """Emitted when moderator delivers an intervention."""

    event_type: str = "moderator_intervention"

    def __init__(
        self,
        discussion_id: str,
        intervention_type: Optional[str] = None,
        content: Optional[str] = None,
        target_agent_id: Optional[str] = None,
        target_agent_name: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        p = payload.copy() if payload else {}
        if intervention_type is not None:
            p["type"] = intervention_type
        if content is not None:
            p["content"] = content
        if target_agent_id is not None:
            p["target_agent_id"] = target_agent_id
        if target_agent_name is not None:
            p["target_agent_name"] = target_agent_name
        kwargs.pop("event_type", None)
        super().__init__(
            event_type="moderator_intervention",
            discussion_id=discussion_id,
            payload=p,
            **kwargs,
        )


class ConsensusUpdatedEvent(DomainEvent):
    """Emitted when consensus items are updated."""

    event_type: str = "consensus_updated"

    def __init__(
        self,
        discussion_id: str,
        consensus_items: Optional[List[ConsensusItem]] = None,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        p = payload.copy() if payload else {}
        if consensus_items is not None:
            p["consensus_items"] = [
                item.model_dump() if hasattr(item, "model_dump") else item
                for item in consensus_items
            ]
        kwargs.pop("event_type", None)
        super().__init__(
            event_type="consensus_updated",
            discussion_id=discussion_id,
            payload=p,
            **kwargs,
        )


class DivergenceUpdatedEvent(DomainEvent):
    """Emitted when divergence items are updated."""

    event_type: str = "divergence_updated"

    def __init__(
        self,
        discussion_id: str,
        divergence_items: Optional[List[DivergenceItem]] = None,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        p = payload.copy() if payload else {}
        if divergence_items is not None:
            p["divergence_items"] = [
                item.model_dump() if hasattr(item, "model_dump") else item
                for item in divergence_items
            ]
        kwargs.pop("event_type", None)
        super().__init__(
            event_type="divergence_updated",
            discussion_id=discussion_id,
            payload=p,
            **kwargs,
        )


class SessionConcludedEvent(DomainEvent):
    """Emitted when debate finishes with final synthesis."""

    event_type: str = "session_concluded"

    def __init__(
        self,
        discussion_id: str,
        summary: Optional[str] = None,
        final_stances: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        p = payload.copy() if payload else {}
        if summary is not None:
            p["summary"] = summary
        if final_stances is not None:
            p["final_stances"] = final_stances
        p.setdefault("final_stances", {})
        kwargs.pop("event_type", None)
        super().__init__(
            event_type="session_concluded",
            discussion_id=discussion_id,
            payload=p,
            **kwargs,
        )
