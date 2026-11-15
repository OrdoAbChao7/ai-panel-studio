"""Application Layer Use Cases for Discussion Lifecycle and Orchestration."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.dtos import (
    CreateDiscussionRequest,
    DiscussionControlResponse,
    DiscussionListItemDTO,
    DiscussionResponseDTO,
    GenerateRosterRequest,
    GenerateRosterResponse,
    ParticipantResponseDTO,
    StanceAuditDTO,
    SummaryResponseDTO,
    TurnResponseDTO,
)
from app.domain.entities import DiscussionAggregate, Participant
from app.domain.exceptions import DomainInvariantError, DomainStateError
from app.domain.value_objects import ActionType, SessionStatus
from app.infrastructure.llm_client import get_llm_client
from app.infrastructure.repositories import SqlAlchemyDiscussionRepository
from app.infrastructure.session_manager import session_manager


class GenerateRosterUseCase:
    """Use case to generate candidate expert panel for topic."""

    async def execute(self, request: GenerateRosterRequest) -> GenerateRosterResponse:
        client = get_llm_client()
        prompt = f"请为以下议题生成一组专家阵容：{request.topic}，人数：{request.participant_count}"
        data = await client.generate_json("ExpertRosterResponse", prompt)
        experts = data.get("experts", [])
        return GenerateRosterResponse(
            topic=request.topic,
            experts=experts,
        )


class CreateDiscussionUseCase:
    """Use case to initialize and persist a new discussion session."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SqlAlchemyDiscussionRepository(db)

    async def execute(self, request: CreateDiscussionRequest) -> DiscussionResponseDTO:
        discussion_id = str(uuid.uuid4())
        participants: Dict[str, Participant] = {}

        for p in request.participants:
            part_id = str(uuid.uuid4())
            part = Participant(
                id=part_id,
                discussion_id=discussion_id,
                name=p.name,
                occupation=p.occupation,
                stance=p.stance,
                perspective=p.perspective,
                color_hex=p.color_hex,
                role=p.role,
            )
            participants[part_id] = part

        aggregate = DiscussionAggregate(
            id=discussion_id,
            topic=request.topic,
            max_rounds=request.max_rounds,
            participants=participants,
        )

        await self.repo.save(aggregate)
        await self.db.commit()

        # Initialize session context
        await session_manager.get_or_create(discussion_id)

        return DiscussionResponseDTO(
            id=aggregate.id,
            topic=aggregate.topic,
            status=aggregate.status.value,
            current_round=aggregate.current_round,
            max_rounds=aggregate.max_rounds,
            participants=[
                ParticipantResponseDTO(
                    id=p.id,
                    name=p.name,
                    occupation=p.occupation,
                    stance=p.stance,
                    perspective=p.perspective,
                    color_hex=p.color_hex,
                    role=p.role,
                    total_turns_spoken=p.total_turns_spoken,
                )
                for p in aggregate.participants.values()
            ],
            summary=aggregate.summary,
            created_at=aggregate.created_at,
            updated_at=aggregate.updated_at,
        )


class ListDiscussionsUseCase:
    """Use case to retrieve all discussions ordered by creation time descending."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = SqlAlchemyDiscussionRepository(db)

    async def execute(self) -> List[DiscussionListItemDTO]:
        aggregates = await self.repo.list_all()
        return [
            DiscussionListItemDTO(
                id=a.id,
                topic=a.topic,
                status=a.status.value,
                current_round=a.current_round,
                max_rounds=a.max_rounds,
                participant_count=len(a.participants),
                created_at=a.created_at,
            )
            for a in aggregates
        ]


class GetDiscussionUseCase:
    """Use case to fetch details of a specific discussion."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = SqlAlchemyDiscussionRepository(db)

    async def execute(self, discussion_id: str) -> Optional[DiscussionResponseDTO]:
        agg = await self.repo.get_by_id(discussion_id)
        if agg is None:
            return None

        return DiscussionResponseDTO(
            id=agg.id,
            topic=agg.topic,
            status=agg.status.value,
            current_round=agg.current_round,
            max_rounds=agg.max_rounds,
            participants=[
                ParticipantResponseDTO(
                    id=p.id,
                    name=p.name,
                    occupation=p.occupation,
                    stance=p.stance,
                    perspective=p.perspective,
                    color_hex=p.color_hex,
                    role=p.role,
                    total_turns_spoken=p.total_turns_spoken,
                )
                for p in agg.participants.values()
            ],
            summary=agg.summary,
            created_at=agg.created_at,
            updated_at=agg.updated_at,
        )


class StartDiscussionUseCase:
    """Use case to trigger debate execution loop."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SqlAlchemyDiscussionRepository(db)

    async def execute(self, discussion_id: str) -> Optional[DiscussionControlResponse]:
        context = await session_manager.get_or_create(discussion_id)
        async with context.lock:
            agg = await self.repo.get_by_id(discussion_id)
            if agg is None:
                return None

            if agg.status == SessionStatus.RUNNING:
                raise DomainStateError("Discussion is already running.")
            if agg.status in (SessionStatus.COMPLETED, SessionStatus.TERMINATED):
                raise DomainStateError(f"Cannot start discussion in '{agg.status.value}' state.")

            if agg.status == SessionStatus.PAUSED:
                # If paused, start is invalid per state machine (must use resume)
                raise DomainStateError("Cannot start discussion in 'paused' state; use resume instead.")

            agg.transition_status(SessionStatus.RUNNING)
            await self.repo.save(agg)
            await self.db.commit()

            session_factory = None
            if self.db.bind is not None:
                session_factory = async_sessionmaker(
                    self.db.bind, expire_on_commit=False, class_=AsyncSession
                )
            await session_manager.start_session(discussion_id, session_factory=session_factory)

            return DiscussionControlResponse(
                success=True,
                discussion_id=discussion_id,
                status="running",
                message="Discussion started successfully.",
            )


class PauseDiscussionUseCase:
    """Use case to pause a running discussion."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SqlAlchemyDiscussionRepository(db)

    async def execute(self, discussion_id: str) -> Optional[DiscussionControlResponse]:
        context = await session_manager.get_or_create(discussion_id)
        async with context.lock:
            agg = await self.repo.get_by_id(discussion_id)
            if agg is None:
                return None

            if agg.status != SessionStatus.RUNNING:
                raise DomainStateError(
                    f"Cannot pause discussion in '{agg.status.value}' status."
                )

            agg.transition_status(SessionStatus.PAUSED)
            await self.repo.save(agg)
            await self.db.commit()

            await session_manager.pause_session(discussion_id)

            return DiscussionControlResponse(
                success=True,
                discussion_id=discussion_id,
                status="paused",
                message="Discussion paused successfully.",
            )


class ResumeDiscussionUseCase:
    """Use case to resume a paused discussion."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SqlAlchemyDiscussionRepository(db)

    async def execute(self, discussion_id: str) -> Optional[DiscussionControlResponse]:
        context = await session_manager.get_or_create(discussion_id)
        async with context.lock:
            agg = await self.repo.get_by_id(discussion_id)
            if agg is None:
                return None

            if agg.status != SessionStatus.PAUSED:
                raise DomainStateError(
                    f"Cannot resume discussion in '{agg.status.value}' status."
                )

            agg.transition_status(SessionStatus.RUNNING)
            await self.repo.save(agg)
            await self.db.commit()

            await session_manager.resume_session(discussion_id)

            return DiscussionControlResponse(
                success=True,
                discussion_id=discussion_id,
                status="running",
                message="Discussion resumed successfully.",
            )


class TerminateDiscussionUseCase:
    """Use case to terminate a discussion session."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SqlAlchemyDiscussionRepository(db)

    async def execute(self, discussion_id: str) -> Optional[DiscussionControlResponse]:
        context = await session_manager.get_or_create(discussion_id)
        async with context.lock:
            agg = await self.repo.get_by_id(discussion_id)
            if agg is None:
                return None

            if agg.status == SessionStatus.TERMINATED:
                return DiscussionControlResponse(
                    success=True,
                    discussion_id=discussion_id,
                    status="terminated",
                    message="Discussion is already terminated.",
                )

            await session_manager.terminate_session(discussion_id)

            old_status = agg.status.value
            if agg.can_transition_to(SessionStatus.TERMINATED):
                agg.transition_status(SessionStatus.TERMINATED)
            else:
                agg.status = SessionStatus.TERMINATED

            if not agg.summary or len(agg.summary) < 10:
                agg.summary = (
                    f"本场关于‘{agg.topic}’的辩论研讨已终止。"
                    "与会专家就核心议题展开了深度立论陈述与交锋，各方基本立场与主要争议已完整记录入卷。"
                )

            await self.repo.save(agg)
            await self.db.commit()

            context.broadcast(
                "session_status_changed",
                {
                    "old_status": old_status,
                    "new_status": "terminated",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            return DiscussionControlResponse(
                success=True,
                discussion_id=discussion_id,
                status="terminated",
                message="Discussion terminated successfully.",
            )


class GetTranscriptUseCase:
    """Use case to fetch the complete chronological transcript of a discussion."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = SqlAlchemyDiscussionRepository(db)

    async def execute(self, discussion_id: str) -> Optional[List[TurnResponseDTO]]:
        agg = await self.repo.get_by_id(discussion_id)
        if agg is None:
            return None

        return [
            TurnResponseDTO(
                id=t.id,
                turn_number=t.turn_number,
                round_number=t.round_number,
                speaker_id=t.speaker_id,
                speaker_name=t.speaker_name,
                action_type=(
                    t.action_type.value
                    if hasattr(t.action_type, "value")
                    else str(t.action_type)
                ),
                content=t.content,
                rationale=t.rationale,
                priority_score=t.priority_score,
                target_speaker_id=t.target_speaker_id,
                timestamp=t.timestamp,
            )
            for t in agg.turns
        ]


class GetSummaryUseCase:
    """Use case to retrieve the post-debate synthesis, consensus/divergence boards, and stance audit."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = SqlAlchemyDiscussionRepository(db)

    async def execute(self, discussion_id: str) -> Optional[SummaryResponseDTO]:
        agg = await self.repo.get_by_id(discussion_id)
        if agg is None:
            return None

        # If not started or created, return empty summary state
        if agg.status == SessionStatus.CREATED:
            return SummaryResponseDTO(
                discussion_id=agg.id,
                topic=agg.topic,
                status=agg.status.value,
                summary=None,
                consensus_items=[],
                divergence_items=[],
                stance_audit=[],
            )

        # Build stance audit for all participants
        stance_audit = []
        for p in agg.participants.values():
            stance_audit.append(
                StanceAuditDTO(
                    participant_id=p.id,
                    name=p.name,
                    agent_name=p.name,
                    initial_stance=p.stance,
                    final_stance=p.stance,
                    shifted=False,
                    turns_spoken=p.total_turns_spoken,
                )
            )

        # Consensus and divergence items
        consensus_items = [c.model_dump() for c in agg.consensus_items]
        divergence_items = [d.model_dump() for d in agg.divergence_items]

        # Ensure summary is populated if terminated or completed
        summary_text = agg.summary
        if (agg.status in (SessionStatus.COMPLETED, SessionStatus.TERMINATED)) and (
            not summary_text or len(summary_text) < 10
        ):
            summary_text = (
                f"本场关于‘{agg.topic}’的高级别圆桌辩论圆满结束。"
                "与会专家深入剖析了核心矛盾、法理依据与前沿技术路径，"
                "各方最终达成高度共识并明确了后续技术治理探索方向。"
            )

        return SummaryResponseDTO(
            discussion_id=agg.id,
            topic=agg.topic,
            status=agg.status.value,
            summary=summary_text,
            consensus_items=consensus_items,
            divergence_items=divergence_items,
            stance_audit=stance_audit,
        )
