"""Comprehensive Unit Tests for Domain Layer Aggregates, Invariants, and Services."""

import pytest
from pydantic import ValidationError

from app.domain.arbitrator import ArbitrationContext, SpeakerArbitrator
from app.domain.entities import DiscussionAggregate, Participant, Turn
from app.domain.events import (
    ConsensusUpdatedEvent,
    DivergenceUpdatedEvent,
    SessionConcludedEvent,
    SessionStatusChangedEvent,
    TurnCompletedEvent,
)
from app.domain.exceptions import DomainInvariantError, DomainStateError
from app.domain.value_objects import (
    ActionType,
    AgentIntent,
    ConsensusItem,
    DivergenceItem,
    SessionStatus,
)


def create_sample_aggregate(topic: str = "人工智能伦理与监管", max_rounds: int = 3) -> DiscussionAggregate:
    """Helper creating a standard debate aggregate with 4 participants."""
    disc = DiscussionAggregate(topic=topic, max_rounds=max_rounds)
    experts_data = [
        ("p1", "沈清源", "认知AI伦理学家", "强监管", "规范伦理学", "#3B82F6"),
        ("p2", "陆宏宇", "大模型架构师", "开源自愈", "工程实用主义", "#10B981"),
        ("p3", "周思敏", "数字法学专家", "法律追责", "法经济学", "#F59E0B"),
        ("p4", "韩立诚", "地缘政治学者", "国家主权", "结构现实主义", "#8B5CF6"),
    ]
    for pid, name, occ, st, persp, color in experts_data:
        disc.add_participant(
            Participant(
                id=pid,
                discussion_id=disc.id,
                name=name,
                occupation=occ,
                stance=st,
                perspective=persp,
                color_hex=color,
            )
        )
    return disc


class TestDiscussionLifecycleFSM:
    """Tests for DiscussionAggregate state machine transitions."""

    def test_initial_state_invariants(self):
        disc = DiscussionAggregate(topic="测试议题")
        assert disc.status == SessionStatus.CREATED
        assert disc.current_round == 0
        assert disc.max_rounds == 5
        assert len(disc.turns) == 0
        assert len(disc.participants) == 0
        assert disc.summary is None

    def test_valid_status_transitions(self):
        disc = create_sample_aggregate()
        # CREATED -> RUNNING
        disc.transition_status(SessionStatus.RUNNING)
        assert disc.status == SessionStatus.RUNNING

        # RUNNING -> PAUSED
        disc.transition_status(SessionStatus.PAUSED)
        assert disc.status == SessionStatus.PAUSED

        # PAUSED -> RUNNING
        disc.transition_status(SessionStatus.RUNNING)
        assert disc.status == SessionStatus.RUNNING

        # RUNNING -> COMPLETED
        disc.transition_status(SessionStatus.COMPLETED)
        assert disc.status == SessionStatus.COMPLETED

    def test_direct_termination(self):
        disc = create_sample_aggregate()
        disc.transition_status(SessionStatus.TERMINATED)
        assert disc.status == SessionStatus.TERMINATED

    def test_invalid_transition_from_created_to_paused(self):
        disc = create_sample_aggregate()
        with pytest.raises(DomainStateError) as exc_info:
            disc.transition_status(SessionStatus.PAUSED)
        assert "Invalid status transition" in str(exc_info.value)

    def test_invalid_transition_from_completed_terminal(self):
        disc = create_sample_aggregate()
        disc.transition_status(SessionStatus.RUNNING)
        disc.transition_status(SessionStatus.COMPLETED)
        with pytest.raises(DomainStateError):
            disc.transition_status(SessionStatus.RUNNING)

    def test_invalid_transition_from_terminated_terminal(self):
        disc = create_sample_aggregate()
        disc.transition_status(SessionStatus.TERMINATED)
        with pytest.raises(DomainStateError):
            disc.transition_status(SessionStatus.RUNNING)


class TestParticipantRegistration:
    """Tests for participant enrollment and validation."""

    def test_successful_participant_enrollment(self):
        disc = DiscussionAggregate(topic="测试议题")
        p = Participant(
            id="agent_1",
            discussion_id=disc.id,
            name="沈清源",
            occupation="伦理学家",
            stance="支持监管",
            perspective="伦理学",
            color_hex="#3B82F6",
        )
        disc.add_participant(p)
        assert "agent_1" in disc.participants
        assert disc.participants["agent_1"].name == "沈清源"

    def test_duplicate_participant_id_raises_invariant_error(self):
        disc = DiscussionAggregate(topic="测试议题")
        p1 = Participant(
            id="dup_id",
            discussion_id=disc.id,
            name="专家A",
            occupation="学者",
            stance="立场A",
            perspective="视角A",
            color_hex="#3B82F6",
        )
        p2 = Participant(
            id="dup_id",
            discussion_id=disc.id,
            name="专家B",
            occupation="学者",
            stance="立场B",
            perspective="视角B",
            color_hex="#10B981",
        )
        disc.add_participant(p1)
        with pytest.raises(DomainInvariantError) as exc_info:
            disc.add_participant(p2)
        assert "already registered" in str(exc_info.value)

    def test_participant_discussion_id_mismatch_raises_error(self):
        disc = DiscussionAggregate(topic="测试议题")
        p = Participant(
            id="agent_1",
            discussion_id="different_disc_id",
            name="沈清源",
            occupation="伦理学家",
            stance="支持监管",
            perspective="伦理学",
            color_hex="#3B82F6",
        )
        with pytest.raises(DomainInvariantError) as exc_info:
            disc.add_participant(p)
        assert "does not match aggregate" in str(exc_info.value)

    def test_add_participant_after_discussion_started_raises_error(self):
        disc = create_sample_aggregate()
        disc.transition_status(SessionStatus.RUNNING)
        p_late = Participant(
            id="p_late",
            discussion_id=disc.id,
            name="迟到专家",
            occupation="学者",
            stance="中立",
            perspective="观察",
            color_hex="#EC4899",
        )
        with pytest.raises(DomainStateError) as exc_info:
            disc.add_participant(p_late)
        assert "Cannot add participant" in str(exc_info.value)


class TestTurnInvariants:
    """Tests for turn addition, consecutive speaker prohibition, and monotonicity."""

    def test_successful_turn_addition(self):
        disc = create_sample_aggregate(max_rounds=3)
        disc.transition_status(SessionStatus.RUNNING)

        turn = Turn(
            id="t1",
            discussion_id=disc.id,
            turn_number=1,
            round_number=1,
            speaker_id="p1",
            speaker_name="沈清源",
            action_type=ActionType.STATEMENT,
            content="我方主张对前沿AI实施严格对齐监管。",
            priority_score=0.85,
        )
        disc.add_turn(turn)

        assert len(disc.turns) == 1
        assert disc.current_round == 1
        assert disc.participants["p1"].total_turns_spoken == 1
        assert disc.participants["p1"].last_spoken_turn == 1

    def test_consecutive_speaker_cooldown_invariant(self):
        disc = create_sample_aggregate(max_rounds=3)
        disc.transition_status(SessionStatus.RUNNING)

        turn1 = Turn(
            id="t1",
            discussion_id=disc.id,
            turn_number=1,
            round_number=1,
            speaker_id="p1",
            speaker_name="沈清源",
            action_type=ActionType.STATEMENT,
            content="首轮立论发言。",
        )
        disc.add_turn(turn1)

        # Same speaker immediately following
        turn2 = Turn(
            id="t2",
            discussion_id=disc.id,
            turn_number=2,
            round_number=1,
            speaker_id="p1",
            speaker_name="沈清源",
            action_type=ActionType.REBUTTAL,
            content="连续发言尝试。",
        )
        with pytest.raises(DomainInvariantError) as exc_info:
            disc.add_turn(turn2)
        assert "Consecutive speaker invariant violated" in str(exc_info.value)

    def test_non_monotonic_turn_number_raises_invariant_error(self):
        disc = create_sample_aggregate(max_rounds=3)
        disc.transition_status(SessionStatus.RUNNING)

        turn = Turn(
            id="t1",
            discussion_id=disc.id,
            turn_number=5,  # Expected 1
            round_number=1,
            speaker_id="p1",
            speaker_name="沈清源",
            action_type=ActionType.STATEMENT,
            content="跳跃轮次发言。",
        )
        with pytest.raises(DomainInvariantError) as exc_info:
            disc.add_turn(turn)
        assert "Turn number must be strictly monotonic" in str(exc_info.value)

    def test_turn_round_exceeding_max_rounds_raises_error(self):
        disc = create_sample_aggregate(max_rounds=2)
        disc.transition_status(SessionStatus.RUNNING)

        turn = Turn(
            id="t1",
            discussion_id=disc.id,
            turn_number=1,
            round_number=3,  # max_rounds is 2
            speaker_id="p1",
            speaker_name="沈清源",
            action_type=ActionType.STATEMENT,
            content="超出最大轮次发言。",
        )
        with pytest.raises(DomainInvariantError) as exc_info:
            disc.add_turn(turn)
        assert "exceeds max_rounds" in str(exc_info.value)

    def test_unregistered_speaker_raises_invariant_error(self):
        disc = create_sample_aggregate()
        disc.transition_status(SessionStatus.RUNNING)

        turn = Turn(
            id="t1",
            discussion_id=disc.id,
            turn_number=1,
            round_number=1,
            speaker_id="unknown_agent",
            speaker_name="未注册嘉宾",
            action_type=ActionType.STATEMENT,
            content="未注册嘉宾发言。",
        )
        with pytest.raises(DomainInvariantError) as exc_info:
            disc.add_turn(turn)
        assert "not a registered participant" in str(exc_info.value)

    def test_turn_immutability(self):
        turn = Turn(
            id="t1",
            discussion_id="disc_1",
            turn_number=1,
            round_number=1,
            speaker_id="p1",
            speaker_name="沈清源",
            action_type=ActionType.STATEMENT,
            content="不可变发言文本。",
        )
        with pytest.raises(ValidationError):
            turn.content = "试图篡改文本"


class TestDomainEventsAndSummary:
    """Tests for event emission, collection, and debate conclusion."""

    def test_event_staging_and_drainage(self):
        disc = create_sample_aggregate()
        disc.transition_status(SessionStatus.RUNNING)

        turn = Turn(
            id="t1",
            discussion_id=disc.id,
            turn_number=1,
            round_number=1,
            speaker_id="p1",
            speaker_name="沈清源",
            action_type=ActionType.STATEMENT,
            content="发言记录。",
        )
        disc.add_turn(turn)

        events = disc.collect_pending_events()
        assert len(events) == 2  # SessionStatusChangedEvent, TurnCompletedEvent
        assert isinstance(events[0], SessionStatusChangedEvent)
        assert isinstance(events[1], TurnCompletedEvent)

        # Pending events buffer should now be empty
        assert len(disc.collect_pending_events()) == 0

    def test_consensus_and_divergence_updates(self):
        disc = create_sample_aggregate()
        disc.transition_status(SessionStatus.RUNNING)

        cons = [
            ConsensusItem(
                id="c1",
                statement="全体验证通过",
                supporting_agents=["p1", "p2"],
                confidence=0.9,
                resolved_turn=1,
            )
        ]
        div = [
            DivergenceItem(
                id="d1",
                tension="开源分歧",
                opposing_stances={"p1": "管制", "p2": "自由"},
                intensity=0.85,
            )
        ]

        disc.update_consensus(cons)
        disc.update_divergence(div)

        assert len(disc.consensus_items) == 1
        assert len(disc.divergence_items) == 1

        events = disc.collect_pending_events()
        event_types = [e.event_type for e in events]
        assert "consensus_updated" in event_types
        assert "divergence_updated" in event_types

    def test_conclude_session_sets_summary_and_completed_status(self):
        disc = create_sample_aggregate()
        disc.transition_status(SessionStatus.RUNNING)

        disc.conclude(
            summary="辩论总结：双方就多项关键议题达成建设性共识。",
            final_stances={"p1": "微调立场", "p2": "坚持开源"},
        )
        assert disc.status == SessionStatus.COMPLETED
        assert disc.summary is not None
        assert "达成建设性共识" in disc.summary

        events = disc.collect_pending_events()
        assert any(isinstance(e, SessionConcludedEvent) for e in events)


class TestSpeakerArbitratorFormula:
    """Tests for SpeakerArbitrator 8-factor mathematical scoring and tie-breaking."""

    def test_immediate_last_speaker_disqualified(self):
        arbitrator = SpeakerArbitrator()
        p1 = Participant(id="p1", discussion_id="d1", name="A", occupation="X", stance="S", perspective="P", color_hex="#1")
        p2 = Participant(id="p2", discussion_id="d1", name="B", occupation="Y", stance="S", perspective="P", color_hex="#2")

        context = ArbitrationContext(
            current_turn=2,
            last_speaker_id="p1",
            participants={"p1": p1, "p2": p2},
        )

        candidates = [
            AgentIntent(agent_id="p1", agent_name="A", desire_to_speak=True, urgency=1.0),
            AgentIntent(agent_id="p2", agent_name="B", desire_to_speak=True, urgency=0.5),
        ]

        result = arbitrator.arbitrate(candidates, context)
        assert result.winner is not None
        assert result.winner.agent_id == "p2"  # p1 is disqualified by cooldown
        assert result.all_scores["p1"] == float("-inf")
