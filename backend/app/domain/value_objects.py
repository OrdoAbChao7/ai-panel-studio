"""Domain Value Objects and Enums."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Lifecycle status of a debate session."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class ActionType(str, Enum):
    """Categorized speech actions in the debate."""

    STATEMENT = "statement"
    REBUTTAL = "rebuttal"
    SUPPLEMENT = "supplement"
    QUESTION = "question"
    CLARIFICATION = "clarification"
    CONSENSUS_PROPOSAL = "consensus_proposal"
    CONCESSION = "concession"
    NONE = "none"


class AgentIntent(BaseModel):
    """Evaluated desire and intended contribution of an expert."""

    agent_id: str
    agent_name: str
    desire_to_speak: bool = True
    action_type: ActionType = ActionType.STATEMENT
    urgency: float = Field(default=0.5, ge=0.0, le=1.0)
    conflict_intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    topical_relevance: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_depth: float = Field(default=0.5, ge=0.0, le=1.0)
    novelty: float = Field(default=0.5, ge=0.0, le=1.0)
    target_speaker_id: Optional[str] = None
    target_speaker_name: Optional[str] = None
    rationale: str = ""
    drafted_content: str = ""


class SpeakerScore(BaseModel):
    """Detailed mathematical breakdown of arbitration scoring."""

    urgency: float
    conflict: float
    topical: float
    evidence: float
    novelty: float
    fairness: float
    cooldown_penalty: float
    jitter: float
    final_score: float


class ConsensusItem(BaseModel):
    """Synthesized point of mutual agreement across experts."""

    id: str
    statement: str
    supporting_agents: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    resolved_turn: int = 0


class DivergenceItem(BaseModel):
    """Active point of philosophical, technical or ethical disagreement."""

    id: str
    tension: str
    opposing_stances: Dict[str, str] = Field(default_factory=dict)
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    is_active: bool = True
