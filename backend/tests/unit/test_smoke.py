"""Smoke test verifying test infrastructure, backend scaffolding, and core health."""

import pytest
from app.domain.entities import DiscussionAggregate, Participant
from app.domain.value_objects import SessionStatus


@pytest.mark.asyncio
async def test_health_check(async_client):
    """Verify that the health check endpoint returns status ok."""
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "AI Panel Studio"
    assert data["version"] == "0.1.0"


def test_domain_entity_instantiation():
    """Verify that domain aggregate and participant instantiate with valid invariants."""
    participant = Participant(
        discussion_id="disc-test-1",
        name="沈清源",
        occupation="AI伦理学家",
        stance="主张强监管",
        perspective="对齐理论",
        color_hex="#3B82F6",
    )
    assert participant.name == "沈清源"
    assert participant.total_turns_spoken == 0

    aggregate = DiscussionAggregate(
        topic="通用人工智能监管边界",
        participants={participant.id: participant},
    )
    assert aggregate.status == SessionStatus.CREATED
    assert aggregate.current_round == 0
    assert aggregate.can_transition_to(SessionStatus.RUNNING) is True
    assert aggregate.can_transition_to(SessionStatus.COMPLETED) is False
