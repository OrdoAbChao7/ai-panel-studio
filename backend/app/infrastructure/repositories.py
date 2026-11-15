"""Concrete SQLAlchemy 2.0 Repositories Implementing Domain Interfaces."""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
from app.domain.repositories import IDiscussionRepository, IEventStreamRepository
from app.domain.value_objects import (
    ActionType,
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


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Attach timezone.utc to naive datetimes returned by SQLite."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class SqlAlchemyDiscussionRepository(IDiscussionRepository):
    """SQLAlchemy 2.0 implementation of IDiscussionRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_domain(self, m: DiscussionModel) -> DiscussionAggregate:
        """Convert ORM model to pure Domain DiscussionAggregate."""
        participants: Dict[str, Participant] = {
            p.id: Participant(
                id=p.id,
                discussion_id=p.discussion_id,
                name=p.name,
                occupation=p.occupation,
                stance=p.stance,
                perspective=p.perspective,
                color_hex=p.color_hex,
                role=p.role,
                total_turns_spoken=p.total_turns_spoken,
                last_spoken_turn=p.last_spoken_turn,
                created_at=_ensure_utc(p.created_at) or datetime.now(timezone.utc),
            )
            for p in m.participants
        }

        turns: List[Turn] = [
            Turn(
                id=t.id,
                discussion_id=t.discussion_id,
                turn_number=t.turn_number,
                round_number=t.round_number,
                speaker_id=t.speaker_id,
                speaker_name=t.speaker_name,
                action_type=ActionType(t.action_type),
                content=t.content,
                rationale=t.rationale,
                priority_score=t.priority_score,
                target_speaker_id=t.target_speaker_id,
                timestamp=_ensure_utc(t.timestamp) or datetime.now(timezone.utc),
            )
            for t in m.turns
        ]

        consensus_items: List[ConsensusItem] = []
        for c in m.consensus_items:
            try:
                agents = (
                    json.loads(c.supporting_agents)
                    if isinstance(c.supporting_agents, str)
                    else c.supporting_agents
                )
            except Exception:
                agents = []
            consensus_items.append(
                ConsensusItem(
                    id=c.id,
                    statement=c.statement,
                    supporting_agents=agents,
                    confidence=c.confidence,
                    resolved_turn=c.resolved_turn,
                )
            )

        divergence_items: List[DivergenceItem] = []
        for d in m.divergence_items:
            try:
                stances = (
                    json.loads(d.opposing_stances)
                    if isinstance(d.opposing_stances, str)
                    else d.opposing_stances
                )
            except Exception:
                stances = {}
            divergence_items.append(
                DivergenceItem(
                    id=d.id,
                    tension=d.tension,
                    opposing_stances=stances,
                    intensity=d.intensity,
                    is_active=d.is_active,
                )
            )

        return DiscussionAggregate(
            id=m.id,
            topic=m.topic,
            status=SessionStatus(m.status),
            current_round=m.current_round,
            max_rounds=m.max_rounds,
            summary=m.summary,
            created_at=_ensure_utc(m.created_at) or datetime.now(timezone.utc),
            updated_at=_ensure_utc(m.updated_at) or datetime.now(timezone.utc),
            participants=participants,
            turns=turns,
            consensus_items=consensus_items,
            divergence_items=divergence_items,
        )

    async def get_by_id(self, discussion_id: str) -> Optional[DiscussionAggregate]:
        stmt = (
            select(DiscussionModel)
            .where(DiscussionModel.id == discussion_id)
            .options(
                selectinload(DiscussionModel.participants),
                selectinload(DiscussionModel.turns),
                selectinload(DiscussionModel.consensus_items),
                selectinload(DiscussionModel.divergence_items),
            )
        )
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, agg: DiscussionAggregate) -> None:
        stmt = (
            select(DiscussionModel)
            .where(DiscussionModel.id == agg.id)
            .options(
                selectinload(DiscussionModel.participants),
                selectinload(DiscussionModel.turns),
                selectinload(DiscussionModel.consensus_items),
                selectinload(DiscussionModel.divergence_items),
            )
        )
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = DiscussionModel(
                id=agg.id,
                topic=agg.topic,
                status=agg.status.value,
                current_round=agg.current_round,
                max_rounds=agg.max_rounds,
                summary=agg.summary,
                created_at=agg.created_at,
                updated_at=agg.updated_at,
            )
            self.session.add(m)

            for p in agg.participants.values():
                m.participants.append(
                    ParticipantModel(
                        id=p.id,
                        discussion_id=agg.id,
                        name=p.name,
                        occupation=p.occupation,
                        stance=p.stance,
                        perspective=p.perspective,
                        color_hex=p.color_hex,
                        role=p.role,
                        total_turns_spoken=p.total_turns_spoken,
                        last_spoken_turn=p.last_spoken_turn,
                        created_at=p.created_at,
                    )
                )

            for t in agg.turns:
                m.turns.append(
                    TurnModel(
                        id=t.id,
                        discussion_id=agg.id,
                        turn_number=t.turn_number,
                        round_number=t.round_number,
                        speaker_id=t.speaker_id,
                        speaker_name=t.speaker_name,
                        action_type=t.action_type.value,
                        content=t.content,
                        rationale=t.rationale,
                        priority_score=t.priority_score,
                        target_speaker_id=t.target_speaker_id,
                        timestamp=t.timestamp,
                    )
                )

            for c in agg.consensus_items:
                m.consensus_items.append(
                    ConsensusItemModel(
                        id=c.id,
                        discussion_id=agg.id,
                        statement=c.statement,
                        supporting_agents=json.dumps(
                            c.supporting_agents, ensure_ascii=False
                        ),
                        confidence=c.confidence,
                        resolved_turn=c.resolved_turn,
                        created_at=datetime.now(timezone.utc),
                    )
                )

            for d in agg.divergence_items:
                m.divergence_items.append(
                    DivergenceItemModel(
                        id=d.id,
                        discussion_id=agg.id,
                        tension=d.tension,
                        opposing_stances=json.dumps(
                            d.opposing_stances, ensure_ascii=False
                        ),
                        intensity=d.intensity,
                        is_active=d.is_active,
                        created_at=datetime.now(timezone.utc),
                    )
                )
        else:
            m.topic = agg.topic
            m.status = agg.status.value
            m.current_round = agg.current_round
            m.max_rounds = agg.max_rounds
            m.summary = agg.summary
            m.updated_at = agg.updated_at

            # Reconcile participants
            existing_p = {p.id: p for p in m.participants}
            for p_id, p in agg.participants.items():
                if p_id in existing_p:
                    ep = existing_p[p_id]
                    ep.name = p.name
                    ep.occupation = p.occupation
                    ep.stance = p.stance
                    ep.perspective = p.perspective
                    ep.color_hex = p.color_hex
                    ep.role = p.role
                    ep.total_turns_spoken = p.total_turns_spoken
                    ep.last_spoken_turn = p.last_spoken_turn
                else:
                    m.participants.append(
                        ParticipantModel(
                            id=p.id,
                            discussion_id=agg.id,
                            name=p.name,
                            occupation=p.occupation,
                            stance=p.stance,
                            perspective=p.perspective,
                            color_hex=p.color_hex,
                            role=p.role,
                            total_turns_spoken=p.total_turns_spoken,
                            last_spoken_turn=p.last_spoken_turn,
                            created_at=p.created_at,
                        )
                    )

            # Reconcile turns (turns are immutable; only append new ones)
            existing_turn_ids = {t.id for t in m.turns}
            for t in agg.turns:
                if t.id not in existing_turn_ids:
                    m.turns.append(
                        TurnModel(
                            id=t.id,
                            discussion_id=agg.id,
                            turn_number=t.turn_number,
                            round_number=t.round_number,
                            speaker_id=t.speaker_id,
                            speaker_name=t.speaker_name,
                            action_type=t.action_type.value,
                            content=t.content,
                            rationale=t.rationale,
                            priority_score=t.priority_score,
                            target_speaker_id=t.target_speaker_id,
                            timestamp=t.timestamp,
                        )
                    )

            # Reconcile consensus items
            existing_c = {c.id: c for c in m.consensus_items}
            for c in agg.consensus_items:
                if c.id in existing_c:
                    ec = existing_c[c.id]
                    ec.statement = c.statement
                    ec.supporting_agents = json.dumps(
                        c.supporting_agents, ensure_ascii=False
                    )
                    ec.confidence = c.confidence
                    ec.resolved_turn = c.resolved_turn
                else:
                    m.consensus_items.append(
                        ConsensusItemModel(
                            id=c.id,
                            discussion_id=agg.id,
                            statement=c.statement,
                            supporting_agents=json.dumps(
                                c.supporting_agents, ensure_ascii=False
                            ),
                            confidence=c.confidence,
                            resolved_turn=c.resolved_turn,
                            created_at=datetime.now(timezone.utc),
                        )
                    )

            # Reconcile divergence items
            existing_d = {d.id: d for d in m.divergence_items}
            for d in agg.divergence_items:
                if d.id in existing_d:
                    ed = existing_d[d.id]
                    ed.tension = d.tension
                    ed.opposing_stances = json.dumps(
                        d.opposing_stances, ensure_ascii=False
                    )
                    ed.intensity = d.intensity
                    ed.is_active = d.is_active
                else:
                    m.divergence_items.append(
                        DivergenceItemModel(
                            id=d.id,
                            discussion_id=agg.id,
                            tension=d.tension,
                            opposing_stances=json.dumps(
                                d.opposing_stances, ensure_ascii=False
                            ),
                            intensity=d.intensity,
                            is_active=d.is_active,
                            created_at=datetime.now(timezone.utc),
                        )
                    )

        await self.session.flush()

    async def list_all(self) -> List[DiscussionAggregate]:
        stmt = (
            select(DiscussionModel)
            .options(
                selectinload(DiscussionModel.participants),
                selectinload(DiscussionModel.turns),
                selectinload(DiscussionModel.consensus_items),
                selectinload(DiscussionModel.divergence_items),
            )
            .order_by(DiscussionModel.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return [self._to_domain(m) for m in res.scalars().all()]

    async def delete(self, discussion_id: str) -> bool:
        stmt = select(DiscussionModel).where(DiscussionModel.id == discussion_id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if model is None:
            return False
        await self.session.delete(model)
        await self.session.flush()
        return True


class SqlAlchemyEventStreamRepository(IEventStreamRepository):
    """SQLAlchemy 2.0 implementation of IEventStreamRepository."""

    EVENT_TYPE_MAP = {
        "discussion_created": DiscussionCreatedEvent,
        "session_status_changed": SessionStatusChangedEvent,
        "hand_raising": HandRaisedEvent,
        "speaker_selected": SpeakerSelectedEvent,
        "speech_chunk": SpeechChunkProducedEvent,
        "speech_completed": TurnCompletedEvent,
        "moderator_intervention": ModeratorInterventionEvent,
        "consensus_updated": ConsensusUpdatedEvent,
        "divergence_updated": DivergenceUpdatedEvent,
        "session_concluded": SessionConcludedEvent,
    }

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def append_event(self, discussion_id: str, event: DomainEvent) -> int:
        stmt = select(
            func.coalesce(func.max(EventModel.seq_id), 0) + 1
        ).where(EventModel.discussion_id == discussion_id)
        res = await self.session.execute(stmt)
        next_seq = res.scalar() or 1

        payload_str = json.dumps(event.payload, ensure_ascii=False)
        model = EventModel(
            discussion_id=discussion_id,
            seq_id=next_seq,
            event_type=event.event_type,
            payload=payload_str,
            created_at=event.timestamp,
        )
        self.session.add(model)
        await self.session.flush()
        return next_seq

    async def get_events_since(
        self, discussion_id: str, last_seq_id: int
    ) -> List[DomainEvent]:
        stmt = (
            select(EventModel)
            .where(
                EventModel.discussion_id == discussion_id,
                EventModel.seq_id > last_seq_id,
            )
            .order_by(EventModel.seq_id.asc())
        )
        res = await self.session.execute(stmt)
        events: List[DomainEvent] = []
        for row in res.scalars().all():
            try:
                payload = json.loads(row.payload)
            except Exception:
                payload = {}

            event_cls = self.EVENT_TYPE_MAP.get(row.event_type, DomainEvent)
            ts = _ensure_utc(row.created_at) or datetime.now(timezone.utc)
            if event_cls is DomainEvent:
                events.append(
                    DomainEvent(
                        event_type=row.event_type,
                        discussion_id=row.discussion_id,
                        timestamp=ts,
                        payload=payload,
                    )
                )
            else:
                events.append(
                    event_cls(
                        discussion_id=row.discussion_id,
                        timestamp=ts,
                        payload=payload,
                    )
                )
        return events
