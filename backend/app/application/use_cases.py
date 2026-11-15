"""Application Use Cases for Discussion Lifecycle and Orchestration."""

from typing import List, Optional
import uuid

from app.application.dtos import (
    CreateDiscussionRequest,
    DiscussionResponseDTO,
    GenerateRosterRequest,
    GenerateRosterResponse,
    ParticipantResponseDTO,
)
from app.domain.entities import DiscussionAggregate, Participant
from app.domain.value_objects import SessionStatus


class GenerateRosterUseCase:
    """Use case to generate candidate expert panel for topic."""

    async def execute(self, request: GenerateRosterRequest) -> GenerateRosterResponse:
        # Placeholder skeleton implemented in M2/M3
        return GenerateRosterResponse(
            topic=request.topic,
            experts=[],
        )


class CreateDiscussionUseCase:
    """Use case to initialize and persist a new discussion session."""

    async def execute(self, request: CreateDiscussionRequest) -> DiscussionResponseDTO:
        discussion_id = str(uuid.uuid4())
        participants = []
        for p in request.participants:
            part = Participant(
                id=str(uuid.uuid4()),
                discussion_id=discussion_id,
                name=p.name,
                occupation=p.occupation,
                stance=p.stance,
                perspective=p.perspective,
                color_hex=p.color_hex,
                role=p.role,
            )
            participants.append(part)

        aggregate = DiscussionAggregate(
            id=discussion_id,
            topic=request.topic,
            max_rounds=request.max_rounds,
            participants={p.id: p for p in participants},
        )

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
                for p in participants
            ],
            summary=aggregate.summary,
            created_at=aggregate.created_at,
        )


class StartDiscussionUseCase:
    """Use case to trigger debate execution loop."""

    async def execute(self, discussion_id: str) -> bool:
        return True


class ControlDiscussionUseCase:
    """Use case to execute lifecycle actions (pause, resume, terminate)."""

    async def execute(self, discussion_id: str, action: str) -> bool:
        return True


class GetSummaryUseCase:
    """Use case to compile final synthesis and audit."""

    async def execute(self, discussion_id: str) -> Optional[dict]:
        return None
