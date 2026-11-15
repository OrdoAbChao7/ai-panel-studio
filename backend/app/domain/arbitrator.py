"""SpeakerArbitrator Domain Service — 8-Factor Mathematical Priority Arbitration."""

import math
import random
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.domain.entities import Participant
from app.domain.value_objects import AgentIntent, SpeakerScore


class ArbitrationContext(BaseModel):
    """Contextual information needed to evaluate candidate priorities."""

    current_turn: int
    last_speaker_id: Optional[str]
    participants: Dict[str, Participant]


class ArbitrationResult(BaseModel):
    """Result of arbitration containing chosen winner and all score breakdowns."""

    winner: Optional[AgentIntent]
    winner_score: float
    all_scores: Dict[str, float]
    breakdown: Dict[str, SpeakerScore]


class SpeakerArbitrator:
    """Programmatic 8-factor mathematical priority arbitrator."""

    def __init__(
        self,
        weight_urgency: float = 0.20,
        weight_conflict: float = 0.25,
        weight_topical: float = 0.15,
        weight_evidence: float = 0.15,
        weight_novelty: float = 0.10,
        weight_fairness: float = 0.15,
    ) -> None:
        self.w_u = weight_urgency
        self.w_c = weight_conflict
        self.w_t = weight_topical
        self.w_e = weight_evidence
        self.w_n = weight_novelty
        self.w_f = weight_fairness

    def arbitrate(
        self,
        candidates: List[AgentIntent],
        context: ArbitrationContext,
    ) -> ArbitrationResult:
        """Arbitrate between candidate expert intents using 8-factor formula."""
        if not candidates:
            return ArbitrationResult(
                winner=None,
                winner_score=float("-inf"),
                all_scores={},
                breakdown={},
            )

        total_turns = max(1, sum(p.total_turns_spoken for p in context.participants.values()))
        all_scores: Dict[str, float] = {}
        breakdown: Dict[str, SpeakerScore] = {}

        for intent in candidates:
            p = context.participants.get(intent.agent_id)
            turns_spoken = p.total_turns_spoken if p else 0

            # 1. Fairness: F_i = 1.0 - (turns_spoken / total_turns)
            fairness = max(0.0, min(1.0, 1.0 - (turns_spoken / total_turns)))

            # 2. Cooldown calculation
            # Invariant: If agent spoke in immediately preceding turn, P_cd = +inf -> S_i = -inf
            is_immediate_last_speaker = (
                context.last_speaker_id is not None
                and context.last_speaker_id == intent.agent_id
            )

            if is_immediate_last_speaker:
                cooldown_penalty = float("inf")
            elif p and p.last_spoken_turn is not None:
                delta_t = context.current_turn - p.last_spoken_turn
                if delta_t <= 1:
                    cooldown_penalty = 0.4
                else:
                    cooldown_penalty = 0.0
            else:
                cooldown_penalty = 0.0

            # 3. Micro-jitter epsilon in [-0.005, 0.005] for tie-breaking
            jitter = random.uniform(-0.005, 0.005)

            # 4. Final Score S_i
            if cooldown_penalty == float("inf") or not intent.desire_to_speak:
                final_score = float("-inf")
            else:
                raw_score = (
                    self.w_u * intent.urgency
                    + self.w_c * intent.conflict_intensity
                    + self.w_t * intent.topical_relevance
                    + self.w_e * intent.evidence_depth
                    + self.w_n * intent.novelty
                    + self.w_f * fairness
                    - cooldown_penalty
                    + jitter
                )
                final_score = raw_score

            all_scores[intent.agent_id] = final_score
            breakdown[intent.agent_id] = SpeakerScore(
                urgency=intent.urgency,
                conflict=intent.conflict_intensity,
                topical=intent.topical_relevance,
                evidence=intent.evidence_depth,
                novelty=intent.novelty,
                fairness=fairness,
                cooldown_penalty=cooldown_penalty if cooldown_penalty != float("inf") else 999.0,
                jitter=jitter,
                final_score=final_score if final_score != float("-inf") else -999.0,
            )

        # Select candidate with highest score (with secondary fairness and tertiary deterministic tie-breaker)
        valid_candidates = [
            c for c in candidates if all_scores[c.agent_id] != float("-inf")
        ]

        if not valid_candidates:
            return ArbitrationResult(
                winner=None,
                winner_score=float("-inf"),
                all_scores=all_scores,
                breakdown=breakdown,
            )

        def candidate_sort_key(c: AgentIntent) -> tuple[float, float, str]:
            score = all_scores[c.agent_id]
            fairness = breakdown[c.agent_id].fairness
            return (score, fairness, c.agent_id)

        winner = max(valid_candidates, key=candidate_sort_key)
        return ArbitrationResult(
            winner=winner,
            winner_score=all_scores[winner.agent_id],
            all_scores=all_scores,
            breakdown=breakdown,
        )
