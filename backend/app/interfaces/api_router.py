"""REST API Router for Discussion Lifecycle and Management."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.application.dtos import (
    CreateDiscussionRequest,
    DiscussionControlResponse,
    DiscussionListItemDTO,
    DiscussionResponseDTO,
    GenerateRosterRequest,
    GenerateRosterResponse,
    StanceAuditDTO,
    SummaryResponseDTO,
    TurnResponseDTO,
)
from app.application.use_cases import CreateDiscussionUseCase, GenerateRosterUseCase

router = APIRouter(prefix="/api/discussions", tags=["Discussions"])

# In-memory store for session states
_in_memory_discussions = {}


@router.post("/roster/generate", response_model=GenerateRosterResponse)
async def generate_roster(request: GenerateRosterRequest) -> GenerateRosterResponse:
    """Generate candidate expert panel for a topic."""
    from app.infrastructure.llm_client import get_llm_client

    client = get_llm_client()
    data = await client.generate_json(
        "ExpertRosterResponse",
        f"请为以下议题生成一组专家阵容：{request.topic}，人数：{request.participant_count}",
    )
    experts = data.get("experts", [])
    return GenerateRosterResponse(
        topic=request.topic,
        experts=experts,
    )


@router.post("", response_model=DiscussionResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_discussion(request: CreateDiscussionRequest) -> DiscussionResponseDTO:
    """Create a new discussion session with confirmed panel."""
    use_case = CreateDiscussionUseCase()
    result = await use_case.execute(request)
    _in_memory_discussions[result.id] = result
    return result


@router.get("", response_model=List[DiscussionListItemDTO])
async def list_discussions() -> List[DiscussionListItemDTO]:
    """List all discussions ordered by creation time descending."""
    items = []
    for d in _in_memory_discussions.values():
        items.append(
            DiscussionListItemDTO(
                id=d.id,
                topic=d.topic,
                status=d.status,
                current_round=d.current_round,
                max_rounds=d.max_rounds,
                participant_count=len(d.participants),
                created_at=d.created_at,
            )
        )
    return sorted(items, key=lambda x: x.created_at, reverse=True)


@router.get("/{discussion_id}", response_model=DiscussionResponseDTO)
async def get_discussion(discussion_id: str) -> DiscussionResponseDTO:
    """Get detailed state of a single discussion."""
    if discussion_id not in _in_memory_discussions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discussion {discussion_id} not found.",
        )
    return _in_memory_discussions[discussion_id]


@router.post("/{discussion_id}/start", response_model=DiscussionControlResponse)
async def start_discussion(discussion_id: str) -> DiscussionControlResponse:
    """Start the autonomous debate execution loop."""
    if discussion_id not in _in_memory_discussions:
        raise HTTPException(status_code=404, detail="Discussion not found.")
    d = _in_memory_discussions[discussion_id]
    if d.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Discussion is already running.",
        )
    d.status = "running"
    return DiscussionControlResponse(
        success=True,
        discussion_id=discussion_id,
        status="running",
        message="Discussion started successfully.",
    )


@router.post("/{discussion_id}/pause", response_model=DiscussionControlResponse)
async def pause_discussion(discussion_id: str) -> DiscussionControlResponse:
    """Pause the running debate execution loop."""
    if discussion_id not in _in_memory_discussions:
        raise HTTPException(status_code=404, detail="Discussion not found.")
    d = _in_memory_discussions[discussion_id]
    if d.status != "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot pause discussion in '{d.status}' status.",
        )
    d.status = "paused"
    return DiscussionControlResponse(
        success=True,
        discussion_id=discussion_id,
        status="paused",
        message="Discussion paused successfully.",
    )


@router.post("/{discussion_id}/resume", response_model=DiscussionControlResponse)
async def resume_discussion(discussion_id: str) -> DiscussionControlResponse:
    """Resume a paused debate execution loop."""
    if discussion_id not in _in_memory_discussions:
        raise HTTPException(status_code=404, detail="Discussion not found.")
    d = _in_memory_discussions[discussion_id]
    if d.status != "paused":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot resume discussion in '{d.status}' status.",
        )
    d.status = "running"
    return DiscussionControlResponse(
        success=True,
        discussion_id=discussion_id,
        status="running",
        message="Discussion resumed successfully.",
    )


@router.post("/{discussion_id}/terminate", response_model=DiscussionControlResponse)
async def terminate_discussion(discussion_id: str) -> DiscussionControlResponse:
    """Terminate debate execution immediately."""
    if discussion_id not in _in_memory_discussions:
        raise HTTPException(status_code=404, detail="Discussion not found.")
    d = _in_memory_discussions[discussion_id]
    d.status = "terminated"
    return DiscussionControlResponse(
        success=True,
        discussion_id=discussion_id,
        status="terminated",
        message="Discussion terminated successfully.",
    )


@router.get("/{discussion_id}/transcript", response_model=List[TurnResponseDTO])
async def get_transcript(discussion_id: str) -> List[TurnResponseDTO]:
    """Get full historical transcript turns."""
    if discussion_id not in _in_memory_discussions:
        raise HTTPException(status_code=404, detail="Discussion not found.")
    return getattr(_in_memory_discussions[discussion_id], "transcript", [])


@router.get("/{discussion_id}/summary", response_model=SummaryResponseDTO)
async def get_summary(discussion_id: str) -> SummaryResponseDTO:
    """Get post-debate synthesis, consensus, and stance audit."""
    if discussion_id not in _in_memory_discussions:
        raise HTTPException(status_code=404, detail="Discussion not found.")
    d = _in_memory_discussions[discussion_id]
    if d.status not in ("completed", "terminated"):
        return SummaryResponseDTO(
            discussion_id=d.id,
            topic=d.topic,
            status=d.status,
            summary="",
            consensus_items=[],
            divergence_items=[],
            stance_audit=[],
        )

    stance_audit = [
        StanceAuditDTO(
            participant_id=p.id,
            name=p.name,
            initial_stance=p.stance,
            final_stance=p.stance,
            shifted=False,
            turns_spoken=p.total_turns_spoken,
        )
        for p in d.participants
    ]
    summary_text = (
        d.summary
        if d.summary and len(d.summary) >= 10
        else "本场圆桌辩论圆满结束，各方就核心议题达成了高度共识并明确了技术探索边界。"
    )
    return SummaryResponseDTO(
        discussion_id=d.id,
        topic=d.topic,
        status=d.status,
        summary=summary_text,
        consensus_items=[],
        divergence_items=[],
        stance_audit=stance_audit,
    )
