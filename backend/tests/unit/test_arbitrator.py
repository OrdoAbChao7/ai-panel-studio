"""Unit tests for SpeakerArbitrator mathematical formula and invariants."""

import pytest
from app.domain.arbitrator import ArbitrationContext, SpeakerArbitrator
from app.domain.entities import Participant
from app.domain.value_objects import ActionType, AgentIntent


def test_cooldown_invariant():
    """Verify that an agent who spoke in turn T-1 receives S_i = -inf and cannot speak."""
    arbitrator = SpeakerArbitrator()

    p1 = Participant(
        id="p1",
        discussion_id="disc-1",
        name="沈清源",
        occupation="AI伦理学家",
        stance="强监管",
        perspective="对齐",
        color_hex="#3B82F6",
        total_turns_spoken=1,
        last_spoken_turn=1,
    )
    p2 = Participant(
        id="p2",
        discussion_id="disc-1",
        name="陆宏宇",
        occupation="大模型总架构师",
        stance="开源自由",
        perspective="工程实用主义",
        color_hex="#10B981",
        total_turns_spoken=0,
        last_spoken_turn=None,
    )

    context = ArbitrationContext(
        current_turn=2,
        last_speaker_id="p1",  # p1 just spoke in turn 1
        participants={"p1": p1, "p2": p2},
    )

    intent_p1 = AgentIntent(
        agent_id="p1",
        agent_name="沈清源",
        desire_to_speak=True,
        action_type=ActionType.REBUTTAL,
        urgency=1.0,  # Max urgency
        conflict_intensity=1.0,
    )
    intent_p2 = AgentIntent(
        agent_id="p2",
        agent_name="陆宏宇",
        desire_to_speak=True,
        action_type=ActionType.STATEMENT,
        urgency=0.5,
        conflict_intensity=0.5,
    )

    result = arbitrator.arbitrate([intent_p1, intent_p2], context)

    # Invariant: p1 cannot be selected because they spoke in the immediate preceding turn
    assert result.winner is not None
    assert result.winner.agent_id == "p2"
    assert result.all_scores["p1"] == float("-inf")
    assert result.all_scores["p2"] > 0.0
