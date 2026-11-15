"""Application Data Transfer Objects (DTOs) for API Requests and Responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Roster Generation DTOs ---

class GenerateRosterRequest(BaseModel):
    """Request payload to dynamically generate expert candidate roster."""

    topic: str = Field(..., min_length=3, description="Debate topic or question")
    participant_count: int = Field(default=4, ge=2, le=6, description="Number of experts (2-6)")


class ExpertRosterItem(BaseModel):
    """A single candidate expert persona generated for inspection."""

    name: str
    occupation: str
    stance: str
    perspective: str
    color_hex: str


class GenerateRosterResponse(BaseModel):
    """Response payload containing generated expert roster."""

    topic: str
    experts: List[ExpertRosterItem]


# --- Discussion Creation & Inspection DTOs ---

class ParticipantCreateDTO(BaseModel):
    """Input DTO for confirming an expert in a discussion."""

    name: str
    occupation: str
    stance: str
    perspective: str = ""
    color_hex: str = "#3B82F6"
    role: str = "expert"


class CreateDiscussionRequest(BaseModel):
    """Request payload to create and persist a new discussion session."""

    topic: str = Field(..., min_length=3)
    max_rounds: int = Field(default=5, ge=1, le=20)
    participants: List[ParticipantCreateDTO] = Field(default_factory=list)


class ParticipantResponseDTO(BaseModel):
    """DTO for a participant in an active or historical discussion."""

    id: str
    name: str
    occupation: str
    stance: str
    perspective: str
    color_hex: str
    role: str
    total_turns_spoken: int = 0


class DiscussionResponseDTO(BaseModel):
    """Detailed view of a discussion aggregate."""

    id: str
    topic: str
    status: str
    current_round: int
    max_rounds: int
    participants: List[ParticipantResponseDTO]
    summary: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class DiscussionListItemDTO(BaseModel):
    """Summary item for listing discussions."""

    id: str
    topic: str
    status: str
    current_round: int
    max_rounds: int
    participant_count: int
    created_at: datetime


# --- Discussion Control DTOs ---

class DiscussionControlResponse(BaseModel):
    """Generic response for discussion lifecycle commands."""

    success: bool
    discussion_id: str
    status: str
    message: str


# --- Transcript & Summary DTOs ---

class TurnResponseDTO(BaseModel):
    """DTO for a single turn in the discussion transcript."""

    id: str
    turn_number: int
    round_number: int
    speaker_id: str
    speaker_name: str
    action_type: str
    content: str
    rationale: Optional[str] = None
    priority_score: float = 0.0
    target_speaker_id: Optional[str] = None
    timestamp: datetime


class StanceAuditDTO(BaseModel):
    """Audit of participant initial vs final stance shifts."""

    participant_id: str
    name: str
    initial_stance: str
    final_stance: str
    shifted: bool
    turns_spoken: int


class SummaryResponseDTO(BaseModel):
    """Comprehensive post-debate summary, consensus items, and stance audit."""

    discussion_id: str
    topic: str
    status: str
    summary: Optional[str] = ""
    consensus_items: List[Dict[str, Any]] = Field(default_factory=list)
    divergence_items: List[Dict[str, Any]] = Field(default_factory=list)
    stance_audit: List[StanceAuditDTO] = Field(default_factory=list)
