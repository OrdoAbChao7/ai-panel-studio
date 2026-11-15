"""Comprehensive Integration Tests for Persistence Layer and SQLite Database."""

import asyncio
from datetime import datetime, timezone
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import DiscussionAggregate, Participant, Turn
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
from app.domain.value_objects import (
    ActionType,
    AgentIntent,
    ConsensusItem,
    DivergenceItem,
    SessionStatus,
)
from app.infrastructure.models import (
    ConsensusItemModel,
    DiscussionModel,
    DivergenceItemModel,
    EventModel,
    ParticipantModel,
    TurnModel,
)
from app.infrastructure.repositories import (
    SqlAlchemyDiscussionRepository,
    SqlAlchemyEventStreamRepository,
)


@pytest.mark.asyncio
class TestSqliteForeignKeysAndCascades:
    """Tests for SQLite foreign key constraint enforcement and cascade deletions."""

    async def test_foreign_key_violation_raises_integrity_error(self, test_session: AsyncSession):
        """Inserting a participant with nonexistent discussion_id must fail."""
        p = ParticipantModel(
            id="orphan_p1",
            discussion_id="non_existent_disc",
            name="孤立专家",
            occupation="测试员",
            stance="无",
            perspective="无",
            color_hex="#3B82F6",
        )
        test_session.add(p)
        with pytest.raises(IntegrityError):
            await test_session.flush()

    async def test_cascade_delete_removes_all_child_records(self, test_session: AsyncSession):
        """Deleting discussion must cascade and purge all children without SAWarning."""
        disc = DiscussionModel(
            id="disc_cascade_test",
            topic="级联删除测试",
            status="created",
            max_rounds=3,
        )
        test_session.add(disc)
        await test_session.flush()

        p = ParticipantModel(
            id="p_casc_1",
            discussion_id=disc.id,
            name="专家1",
            occupation="专家",
            stance="立场",
            perspective="视角",
            color_hex="#3B82F6",
        )
        test_session.add(p)

        t = TurnModel(
            id="t_casc_1",
            discussion_id=disc.id,
            turn_number=1,
            round_number=1,
            speaker_id=p.id,
            speaker_name=p.name,
            action_type="statement",
            content="发言内容",
        )
        test_session.add(t)

        e = EventModel(
            discussion_id=disc.id,
            seq_id=1,
            event_type="test_event",
            payload="{}",
        )
        test_session.add(e)

        c = ConsensusItemModel(
            id="c_casc_1",
            discussion_id=disc.id,
            statement="共识点",
            supporting_agents="[]",
            confidence=0.9,
            resolved_turn=1,
        )
        test_session.add(c)

        d = DivergenceItemModel(
            id="d_casc_1",
            discussion_id=disc.id,
            tension="分歧点",
            opposing_stances="{}",
            intensity=0.8,
        )
        test_session.add(d)
        await test_session.flush()

        # Delete parent discussion
        await test_session.delete(disc)
        await test_session.flush()

        # Verify all child tables are purged
        res_p = await test_session.execute(select(ParticipantModel).where(ParticipantModel.discussion_id == disc.id))
        assert len(res_p.scalars().all()) == 0

        res_t = await test_session.execute(select(TurnModel).where(TurnModel.discussion_id == disc.id))
        assert len(res_t.scalars().all()) == 0

        res_e = await test_session.execute(select(EventModel).where(EventModel.discussion_id == disc.id))
        assert len(res_e.scalars().all()) == 0

        res_c = await test_session.execute(select(ConsensusItemModel).where(ConsensusItemModel.discussion_id == disc.id))
        assert len(res_c.scalars().all()) == 0

        res_d = await test_session.execute(select(DivergenceItemModel).where(DivergenceItemModel.discussion_id == disc.id))
        assert len(res_d.scalars().all()) == 0


@pytest.mark.asyncio
class TestEventStreamRepository:
    """Tests for monotonic sequence ID allocation and SSE replay recovery."""

    async def test_monotonic_seq_id_allocation(self, test_session: AsyncSession):
        repo = SqlAlchemyEventStreamRepository(test_session)
        disc_id = "disc_stream_test"

        # Pre-create parent discussion
        disc = DiscussionModel(id=disc_id, topic="流测试", status="created")
        test_session.add(disc)
        await test_session.flush()

        seq1 = await repo.append_event(
            disc_id,
            DomainEvent(event_type="event_1", discussion_id=disc_id, payload={"step": 1}),
        )
        seq2 = await repo.append_event(
            disc_id,
            DomainEvent(event_type="event_2", discussion_id=disc_id, payload={"step": 2}),
        )
        seq3 = await repo.append_event(
            disc_id,
            DomainEvent(event_type="event_3", discussion_id=disc_id, payload={"step": 3}),
        )

        assert seq1 == 1
        assert seq2 == 2
        assert seq3 == 3

    async def test_duplicate_seq_id_rejected_by_unique_index(self, test_session: AsyncSession):
        disc_id = "disc_uniq_seq"
        disc = DiscussionModel(id=disc_id, topic="唯一序号测试", status="created")
        test_session.add(disc)
        await test_session.flush()

        e1 = EventModel(discussion_id=disc_id, seq_id=1, event_type="test", payload="{}")
        e2 = EventModel(discussion_id=disc_id, seq_id=1, event_type="test", payload="{}")
        test_session.add(e1)
        await test_session.flush()

        test_session.add(e2)
        with pytest.raises(IntegrityError):
            await test_session.flush()

    async def test_get_events_since_filters_and_orders_ascending(self, test_session: AsyncSession):
        repo = SqlAlchemyEventStreamRepository(test_session)
        disc_id = "disc_replay_test"

        disc = DiscussionModel(id=disc_id, topic="重放测试", status="created")
        test_session.add(disc)
        await test_session.flush()

        for i in range(1, 6):
            await repo.append_event(
                disc_id,
                DomainEvent(event_type=f"evt_{i}", discussion_id=disc_id, payload={"val": i}),
            )

        # Query events since seq_id = 2
        events = await repo.get_events_since(disc_id, last_seq_id=2)
        assert len(events) == 3
        assert events[0].event_type == "evt_3"
        assert events[1].event_type == "evt_4"
        assert events[2].event_type == "evt_5"

    async def test_reconstitute_all_10_domain_event_types_without_kwarg_collision(
        self, test_session: AsyncSession
    ):
        """Verify appending and retrieving all 10 domain event subclasses causes zero TypeError."""
        repo = SqlAlchemyEventStreamRepository(test_session)
        disc_id = "disc_10_events_test"

        disc = DiscussionModel(id=disc_id, topic="全量事件类型重构测试", status="created")
        test_session.add(disc)
        await test_session.flush()

        # Construct all 10 domain event types
        events_to_test = [
            DiscussionCreatedEvent(
                discussion_id=disc_id,
                topic="全量事件类型重构测试",
                participant_count=4,
            ),
            SessionStatusChangedEvent(
                discussion_id=disc_id,
                old_status="created",
                new_status="running",
            ),
            HandRaisedEvent(
                discussion_id=disc_id,
                candidate_intents=[
                    AgentIntent(
                        agent_id="a1",
                        agent_name="沈清源",
                        action_type=ActionType.STATEMENT,
                        urgency=0.88,
                        conflict_intensity=0.45,
                        rationale="阐明AI治理伦理基石",
                    )
                ],
            ),
            SpeakerSelectedEvent(
                discussion_id=disc_id,
                speaker_id="a1",
                speaker_name="沈清源",
                score=0.91,
                score_breakdown={"urgency": 0.88, "conflict": 0.45},
            ),
            SpeechChunkProducedEvent(
                discussion_id=disc_id,
                turn_id="turn_1",
                speaker_id="a1",
                chunk="各位同仁，我们首先必须审视伦理对齐边界。",
                is_first=True,
            ),
            TurnCompletedEvent(
                discussion_id=disc_id,
                turn_id="turn_1",
                speaker_id="a1",
                turn_number=1,
                content="各位同仁，我们首先必须审视伦理对齐边界。盲目推进将带来不可逆的风险。",
                action_type="statement",
                round_number=1,
            ),
            ModeratorInterventionEvent(
                discussion_id=disc_id,
                intervention_type="probe",
                content="请问陆宏宇专家，技术自发演进能否有效覆盖系统性外部风险？",
                target_agent_id="a2",
                target_agent_name="陆宏宇",
            ),
            ConsensusUpdatedEvent(
                discussion_id=disc_id,
                consensus_items=[
                    ConsensusItem(
                        id="cons_1",
                        statement="技术自主创新与外部法理监管具有辩证协同关系",
                        supporting_agents=["沈清源", "陆宏宇"],
                        confidence=0.87,
                        resolved_turn=1,
                    )
                ],
            ),
            DivergenceUpdatedEvent(
                discussion_id=disc_id,
                divergence_items=[
                    DivergenceItem(
                        id="div_1",
                        tension="强监管前置介入 vs 开源自发演进的优先次序",
                        opposing_stances={"沈清源": "先监管对齐", "陆宏宇": "先开源演化"},
                        intensity=0.82,
                    )
                ],
            ),
            SessionConcludedEvent(
                discussion_id=disc_id,
                summary="辩论各方就前置底线与敏捷监管达成了多项共识，主要分歧聚焦于自适应对齐的技术路径选择。",
                final_stances={"沈清源": "坚持全生命周期强约束", "陆宏宇": "坚持开源与工程容错"},
            ),
        ]

        # Append all 10 events sequentially
        for ev in events_to_test:
            seq = await repo.append_event(disc_id, ev)
            assert seq > 0

        # Retrieve and verify all 10 events reconstructed into concrete domain subclasses
        retrieved = await repo.get_events_since(disc_id, last_seq_id=0)
        assert len(retrieved) == 10

        expected_classes = [
            DiscussionCreatedEvent,
            SessionStatusChangedEvent,
            HandRaisedEvent,
            SpeakerSelectedEvent,
            SpeechChunkProducedEvent,
            TurnCompletedEvent,
            ModeratorInterventionEvent,
            ConsensusUpdatedEvent,
            DivergenceUpdatedEvent,
            SessionConcludedEvent,
        ]

        for idx, (ev_obj, exp_cls) in enumerate(zip(retrieved, expected_classes)):
            assert isinstance(
                ev_obj, exp_cls
            ), f"Event index {idx} expected {exp_cls.__name__}, got {type(ev_obj).__name__}"
            assert ev_obj.discussion_id == disc_id
            assert ev_obj.event_type == events_to_test[idx].event_type

        # Verify specific payload values survived serialization and reconstitution
        speech_chunk = retrieved[4]
        assert isinstance(speech_chunk, SpeechChunkProducedEvent)
        assert speech_chunk.payload["chunk"] == "各位同仁，我们首先必须审视伦理对齐边界。"
        assert speech_chunk.payload["is_first"] is True

        concluded = retrieved[9]
        assert isinstance(concluded, SessionConcludedEvent)
        assert "全生命周期强约束" in str(concluded.payload["final_stances"])
        assert "辩论各方" in concluded.payload["summary"]


@pytest.mark.asyncio
class TestDiscussionRepositoryRoundtrip:
    """Tests for aggregate reconstitution, updates, and multi-session isolation."""

    async def test_aggregate_save_and_reconstitution(self, test_session: AsyncSession):
        repo = SqlAlchemyDiscussionRepository(test_session)

        agg = DiscussionAggregate(
            topic="人工智能与数字版权",
            status=SessionStatus.RUNNING,
            max_rounds=4,
        )
        p1 = Participant(
            id="p1",
            discussion_id=agg.id,
            name="沈清源",
            occupation="伦理学家",
            stance="支持监管",
            perspective="规范伦理学",
            color_hex="#3B82F6",
            total_turns_spoken=1,
            last_spoken_turn=1,
        )
        p2 = Participant(
            id="p2",
            discussion_id=agg.id,
            name="陆宏宇",
            occupation="开源架构师",
            stance="支持开源",
            perspective="系统演化论",
            color_hex="#10B981",
        )
        agg.participants[p1.id] = p1
        agg.participants[p2.id] = p2

        turn = Turn(
            id="t1",
            discussion_id=agg.id,
            turn_number=1,
            round_number=1,
            speaker_id="p1",
            speaker_name="沈清源",
            action_type=ActionType.STATEMENT,
            content="我方在此提出版权声明。",
            priority_score=0.88,
        )
        agg.turns.append(turn)

        agg.consensus_items.append(
            ConsensusItem(
                id="c1",
                statement="各方均认可著作权重要性",
                supporting_agents=["p1", "p2"],
                confidence=0.92,
                resolved_turn=1,
            )
        )
        agg.divergence_items.append(
            DivergenceItem(
                id="d1",
                tension="训练集是否属于合理使用",
                opposing_stances={"p1": "不属于", "p2": "属于"},
                intensity=0.85,
            )
        )

        # Save to database
        await repo.save(agg)

        # Reconstitute from database
        fetched = await repo.get_by_id(agg.id)
        assert fetched is not None
        assert fetched.id == agg.id
        assert fetched.topic == agg.topic
        assert fetched.status == SessionStatus.RUNNING
        assert len(fetched.participants) == 2
        assert fetched.participants["p1"].total_turns_spoken == 1
        assert fetched.participants["p1"].last_spoken_turn == 1
        assert len(fetched.turns) == 1
        assert fetched.turns[0].content == "我方在此提出版权声明。"
        assert fetched.turns[0].action_type == ActionType.STATEMENT
        assert len(fetched.consensus_items) == 1
        assert fetched.consensus_items[0].statement == "各方均认可著作权重要性"
        assert len(fetched.divergence_items) == 1
        assert fetched.divergence_items[0].tension == "训练集是否属于合理使用"

        # Verify UTC datetime normalization
        assert fetched.created_at.tzinfo == timezone.utc
        assert fetched.turns[0].timestamp.tzinfo == timezone.utc

    async def test_update_existing_aggregate_in_place(self, test_session: AsyncSession):
        repo = SqlAlchemyDiscussionRepository(test_session)

        agg = DiscussionAggregate(topic="更新测试", status=SessionStatus.RUNNING)
        p1 = Participant(
            id="p1",
            discussion_id=agg.id,
            name="专家A",
            occupation="职务",
            stance="立场",
            perspective="视角",
            color_hex="#3B82F6",
        )
        agg.participants[p1.id] = p1
        await repo.save(agg)

        # Append turn and update aggregate
        t = Turn(
            id="t1",
            discussion_id=agg.id,
            turn_number=1,
            round_number=1,
            speaker_id="p1",
            speaker_name="专家A",
            action_type=ActionType.STATEMENT,
            content="首轮发言更新",
        )
        agg.add_turn(t)
        await repo.save(agg)

        fetched = await repo.get_by_id(agg.id)
        assert fetched is not None
        assert len(fetched.turns) == 1
        assert fetched.participants["p1"].total_turns_spoken == 1

    async def test_delete_discussion_returns_expected_boolean(self, test_session: AsyncSession):
        repo = SqlAlchemyDiscussionRepository(test_session)

        agg = DiscussionAggregate(topic="删除测试")
        await repo.save(agg)

        deleted = await repo.delete(agg.id)
        assert deleted is True

        # Non-existent deletion
        deleted_again = await repo.delete("non_existent_id")
        assert deleted_again is False

    async def test_list_all_orders_by_created_at_desc(self, test_session: AsyncSession):
        repo = SqlAlchemyDiscussionRepository(test_session)

        agg1 = DiscussionAggregate(topic="先建讨论")
        await repo.save(agg1)
        await asyncio.sleep(0.01)

        agg2 = DiscussionAggregate(topic="后建讨论")
        await repo.save(agg2)

        all_discs = await repo.list_all()
        ids = [d.id for d in all_discs]
        assert ids.index(agg2.id) < ids.index(agg1.id)
