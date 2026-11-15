"""REST API Router for Discussion Lifecycle and Management."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos import (
    CreateDiscussionRequest,
    DiscussionControlResponse,
    DiscussionListItemDTO,
    DiscussionResponseDTO,
    GenerateRosterRequest,
    GenerateRosterResponse,
    SummaryResponseDTO,
    TurnResponseDTO,
)
from app.application.use_cases import (
    CreateDiscussionUseCase,
    GenerateRosterUseCase,
    GetDiscussionUseCase,
    GetSummaryUseCase,
    GetTranscriptUseCase,
    ListDiscussionsUseCase,
    PauseDiscussionUseCase,
    ResumeDiscussionUseCase,
    StartDiscussionUseCase,
    TerminateDiscussionUseCase,
)
from app.domain.exceptions import DomainInvariantError, DomainStateError
from app.infrastructure.database import get_db

router = APIRouter(prefix="/api/discussions", tags=["Discussions"])


@router.post("/roster/generate", response_model=GenerateRosterResponse)
async def generate_roster(request: GenerateRosterRequest) -> GenerateRosterResponse:
    """Generate candidate expert panel for a topic."""
    use_case = GenerateRosterUseCase()
    return await use_case.execute(request)


@router.post("", response_model=DiscussionResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_discussion(
    request: CreateDiscussionRequest,
    db: AsyncSession = Depends(get_db),
) -> DiscussionResponseDTO:
    """Create a new discussion session with confirmed panel."""
    try:
        use_case = CreateDiscussionUseCase(db)
        return await use_case.execute(request)
    except DomainInvariantError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except DomainStateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=List[DiscussionListItemDTO])
async def list_discussions(db: AsyncSession = Depends(get_db)) -> List[DiscussionListItemDTO]:
    """List all discussions ordered by creation time descending."""
    use_case = ListDiscussionsUseCase(db)
    return await use_case.execute()


@router.get("/{discussion_id}", response_model=DiscussionResponseDTO)
async def get_discussion(
    discussion_id: str,
    db: AsyncSession = Depends(get_db),
) -> DiscussionResponseDTO:
    """Get detailed state of a single discussion."""
    use_case = GetDiscussionUseCase(db)
    result = await use_case.execute(discussion_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discussion '{discussion_id}' not found.",
        )
    return result


@router.post("/{discussion_id}/start", response_model=DiscussionControlResponse)
async def start_discussion(
    discussion_id: str,
    db: AsyncSession = Depends(get_db),
) -> DiscussionControlResponse:
    """Start the autonomous debate execution loop."""
    try:
        use_case = StartDiscussionUseCase(db)
        result = await use_case.execute(discussion_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discussion '{discussion_id}' not found.",
            )
        return result
    except DomainStateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/{discussion_id}/pause", response_model=DiscussionControlResponse)
async def pause_discussion(
    discussion_id: str,
    db: AsyncSession = Depends(get_db),
) -> DiscussionControlResponse:
    """Pause the running debate execution loop."""
    try:
        use_case = PauseDiscussionUseCase(db)
        result = await use_case.execute(discussion_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discussion '{discussion_id}' not found.",
            )
        return result
    except DomainStateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/{discussion_id}/resume", response_model=DiscussionControlResponse)
async def resume_discussion(
    discussion_id: str,
    db: AsyncSession = Depends(get_db),
) -> DiscussionControlResponse:
    """Resume a paused debate execution loop."""
    try:
        use_case = ResumeDiscussionUseCase(db)
        result = await use_case.execute(discussion_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discussion '{discussion_id}' not found.",
            )
        return result
    except DomainStateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/{discussion_id}/terminate", response_model=DiscussionControlResponse)
async def terminate_discussion(
    discussion_id: str,
    db: AsyncSession = Depends(get_db),
) -> DiscussionControlResponse:
    """Terminate debate execution immediately."""
    try:
        use_case = TerminateDiscussionUseCase(db)
        result = await use_case.execute(discussion_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discussion '{discussion_id}' not found.",
            )
        return result
    except DomainStateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{discussion_id}/transcript", response_model=List[TurnResponseDTO])
async def get_transcript(
    discussion_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[TurnResponseDTO]:
    """Retrieve full chronological transcript of speeches."""
    use_case = GetTranscriptUseCase(db)
    result = await use_case.execute(discussion_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discussion '{discussion_id}' not found.",
        )
    return result


@router.get("/{discussion_id}/summary", response_model=SummaryResponseDTO)
async def get_summary(
    discussion_id: str,
    db: AsyncSession = Depends(get_db),
) -> SummaryResponseDTO:
    """Retrieve post-debate synthesis, consensus/divergence boards, and stance audit."""
    use_case = GetSummaryUseCase(db)
    result = await use_case.execute(discussion_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discussion '{discussion_id}' not found.",
        )
    return result
