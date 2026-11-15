"""
Tier 2 Boundary & Corner Case E2E Test Suite for AI Panel Studio.

Verifies system robustness against invalid inputs, boundary values, malformed payloads,
illegal state transitions, race conditions, auth key fallbacks, credential isolation,
and 404 handling on non-existent resources across 8 domains (51 tests total):
- Domain 2.1: Min/Max Participant Counts (T2-PART, 6 tests)
- Domain 2.2: Topic String Boundaries (T2-TOPIC, 6 tests)
- Domain 2.3: Invalid Round Counts (T2-RND, 6 tests)
- Domain 2.4: Invalid Lifecycle State Transitions (T2-STATE, 7 tests)
- Domain 2.5: Malformed & Truncated Payloads (T2-PAYL, 6 tests)
- Domain 2.6: Rapid Repeated Controls & Concurrency Race (T2-RACE, 6 tests)
- Domain 2.7: Unconfigured vs Invalid API Key Handling (T2-KEY, 6 tests)
- Domain 2.8: Non-existent IDs 404 Handling (T2-ID, 8 tests)
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List
import uuid
import httpx
import pytest

# Ensure all tests in this module carry the tier2 marker
pytestmark = [pytest.mark.tier2, pytest.mark.asyncio]


@pytest.fixture
def client(async_client: httpx.AsyncClient) -> httpx.AsyncClient:
    """Convenience fixture mapping 'client' to 'async_client'."""
    return async_client


def make_valid_participants(count: int = 4) -> List[Dict[str, Any]]:
    """Helper returning a valid list of participant dictionaries adhering to PROJECT.md."""
    base_pool = [
        {"name": "林博", "occupation": "AI架构师", "stance": "技术赋能创作者", "color_hex": "#3B82F6", "role": "panelist"},
        {"name": "陈文", "occupation": "独立作家", "stance": "冲击原创精神", "color_hex": "#EF4444", "role": "panelist"},
        {"name": "张法", "occupation": "知识产权律师", "stance": "亟需确立版权界限", "color_hex": "#10B981", "role": "panelist"},
        {"name": "周经", "occupation": "文化投资人", "stance": "市场效率至上", "color_hex": "#F59E0B", "role": "panelist"},
        {"name": "赵社", "occupation": "社会学家", "stance": "关注技术失业风险", "color_hex": "#8B5CF6", "role": "panelist"},
        {"name": "孙政", "occupation": "公共政策研究员", "stance": "提倡审慎包容监管", "color_hex": "#EC4899", "role": "panelist"},
    ]
    return [dict(p) for p in base_pool[:count]]


async def create_helper_discussion(
    client: httpx.AsyncClient,
    topic: str = "科技伦理与人工智能",
    count: int = 4,
    max_rounds: int = 3,
) -> str:
    """Helper to create a discussion and return its ID."""
    payload = {
        "topic": topic,
        "participants": make_valid_participants(count),
        "max_rounds": max_rounds,
    }
    resp = await client.post("/api/discussions", json=payload)
    assert resp.status_code in (200, 201), f"Failed to create helper discussion: {resp.status_code} - {resp.text}"
    data = resp.json()
    assert "id" in data, f"Response missing id: {data}"
    return data["id"]


# ==============================================================================
# Domain 2.1: Min/Max Participant Counts (T2-PART, 6 tests)
# ==============================================================================

async def test_t2_part_01_participant_count_zero_rejected(client: httpx.AsyncClient):
    """T2-PART-01: Zero participants in roster generation must be rejected with 422."""
    resp = await client.post(
        "/api/discussions/roster/generate",
        json={"topic": "科技伦理与人工智能", "participant_count": 0},
    )
    assert resp.status_code == 422, f"Expected 422 for count=0, got {resp.status_code}"


async def test_t2_part_02_participant_count_single_rejected(client: httpx.AsyncClient):
    """T2-PART-02: Single participant in roster generation must be rejected with 422."""
    resp = await client.post(
        "/api/discussions/roster/generate",
        json={"topic": "科技伦理与人工智能", "participant_count": 1},
    )
    assert resp.status_code == 422, f"Expected 422 for count=1, got {resp.status_code}"


async def test_t2_part_03_participant_count_lower_bound_two(client: httpx.AsyncClient):
    """T2-PART-03: Lower boundary (exactly 2 participants) must succeed in roster generation and creation."""
    roster_resp = await client.post(
        "/api/discussions/roster/generate",
        json={"topic": "科技伦理与人工智能", "participant_count": 2},
    )
    assert roster_resp.status_code == 200, f"Expected 200 for count=2, got {roster_resp.status_code}"
    roster_data = roster_resp.json()
    assert len(roster_data.get("experts", [])) == 2

    # Create discussion with exactly 2 participants
    create_resp = await client.post(
        "/api/discussions",
        json={
            "topic": "科技伦理与人工智能",
            "participants": make_valid_participants(2),
            "max_rounds": 2,
        },
    )
    assert create_resp.status_code in (200, 201)
    create_data = create_resp.json()
    assert len(create_data.get("participants", [])) == 2
    assert create_data.get("status") == "created"


async def test_t2_part_04_participant_count_upper_bound_six(client: httpx.AsyncClient):
    """T2-PART-04: Upper boundary (exactly 6 participants) must succeed in roster generation and creation."""
    roster_resp = await client.post(
        "/api/discussions/roster/generate",
        json={"topic": "科技伦理与人工智能", "participant_count": 6},
    )
    assert roster_resp.status_code == 200, f"Expected 200 for count=6, got {roster_resp.status_code}"
    roster_data = roster_resp.json()
    assert len(roster_data.get("experts", [])) == 6

    # Create discussion with exactly 6 participants
    create_resp = await client.post(
        "/api/discussions",
        json={
            "topic": "科技伦理与人工智能",
            "participants": make_valid_participants(6),
            "max_rounds": 2,
        },
    )
    assert create_resp.status_code in (200, 201)
    create_data = create_resp.json()
    assert len(create_data.get("participants", [])) == 6
    assert create_data.get("status") == "created"


async def test_t2_part_05_participant_count_exceeds_upper_bound_seven(client: httpx.AsyncClient):
    """T2-PART-05: Exceeding upper limit (7 participants) in roster generation must be rejected with 422."""
    resp = await client.post(
        "/api/discussions/roster/generate",
        json={"topic": "科技伦理与人工智能", "participant_count": 7},
    )
    assert resp.status_code == 422, f"Expected 422 for count=7, got {resp.status_code}"


async def test_t2_part_06_direct_creation_illegal_participant_arrays(client: httpx.AsyncClient):
    """T2-PART-06: Direct creation with empty, 1, or 7+ participant lists must return 422."""
    # Subcase A: Empty array
    resp_empty = await client.post(
        "/api/discussions",
        json={"topic": "科技伦理", "participants": [], "max_rounds": 3},
    )
    assert resp_empty.status_code == 422, f"Expected 422 for empty participants, got {resp_empty.status_code}"

    # Subcase B: Only 1 participant
    resp_one = await client.post(
        "/api/discussions",
        json={"topic": "科技伦理", "participants": make_valid_participants(1), "max_rounds": 3},
    )
    assert resp_one.status_code == 422, f"Expected 422 for 1 participant, got {resp_one.status_code}"

    # Subcase C: 7 participants (exceeds max 6)
    seven_participants = make_valid_participants(6) + [
        {"name": "额外专家", "occupation": "独立观察员", "stance": "中立", "color_hex": "#6B7280", "role": "panelist"}
    ]
    resp_seven = await client.post(
        "/api/discussions",
        json={"topic": "科技伦理", "participants": seven_participants, "max_rounds": 3},
    )
    assert resp_seven.status_code == 422, f"Expected 422 for 7 participants, got {resp_seven.status_code}"


# ==============================================================================
# Domain 2.2: Topic String Boundaries (T2-TOPIC, 6 tests)
# ==============================================================================

async def test_t2_topic_01_empty_topic_rejected(client: httpx.AsyncClient):
    """T2-TOPIC-01: Empty topic string must return 422 in both roster generation and creation."""
    roster_resp = await client.post(
        "/api/discussions/roster/generate",
        json={"topic": "", "participant_count": 4},
    )
    assert roster_resp.status_code == 422, f"Expected 422 for empty topic in roster, got {roster_resp.status_code}"

    create_resp = await client.post(
        "/api/discussions",
        json={"topic": "", "participants": make_valid_participants(4), "max_rounds": 3},
    )
    assert create_resp.status_code == 422, f"Expected 422 for empty topic in creation, got {create_resp.status_code}"


async def test_t2_topic_02_whitespace_only_topic_rejected(client: httpx.AsyncClient):
    """T2-TOPIC-02: Whitespace-only topic string must return 422 in both roster generation and creation."""
    ws_topic = "   \n\t   "
    roster_resp = await client.post(
        "/api/discussions/roster/generate",
        json={"topic": ws_topic, "participant_count": 4},
    )
    assert roster_resp.status_code == 422, f"Expected 422 for whitespace topic in roster, got {roster_resp.status_code}"

    create_resp = await client.post(
        "/api/discussions",
        json={"topic": ws_topic, "participants": make_valid_participants(4), "max_rounds": 3},
    )
    assert create_resp.status_code == 422, f"Expected 422 for whitespace topic in creation, got {create_resp.status_code}"


async def test_t2_topic_03_ultra_long_topic_handled(client: httpx.AsyncClient):
    """T2-TOPIC-03: Ultra-long topic (5000+ chars) must be safely rejected with 422/400 without 500 error."""
    ultra_long = "超长议题测试" * 1000  # 6000 characters
    resp = await client.post(
        "/api/discussions",
        json={"topic": ultra_long, "participants": make_valid_participants(4), "max_rounds": 3},
    )
    assert resp.status_code in (400, 422), f"Expected 400 or 422 for ultra-long topic, got {resp.status_code}"
    assert resp.status_code != 500, "Server must not throw 500 on large payload"


async def test_t2_topic_04_xss_script_injection_handled_safely(client: httpx.AsyncClient):
    """T2-TOPIC-04: XSS injection strings in topic must be stored and served safely without execution."""
    xss_topic = "<script>alert('xss')</script><img src=x onerror=alert(1)>"
    resp = await client.post(
        "/api/discussions",
        json={"topic": xss_topic, "participants": make_valid_participants(4), "max_rounds": 2},
    )
    assert resp.status_code in (200, 201, 422), f"Unexpected status: {resp.status_code}"
    if resp.status_code in (200, 201):
        discussion_id = resp.json()["id"]
        detail = await client.get(f"/api/discussions/{discussion_id}")
        assert detail.status_code == 200
        content_type = detail.headers.get("content-type", "")
        assert "application/json" in content_type, f"Content-type should be JSON, got {content_type}"
        # Stored text should retain or safely represent input without corrupting JSON
        assert "<script>" in detail.json()["topic"]


async def test_t2_topic_05_sql_injection_handled_safely(client: httpx.AsyncClient):
    """T2-TOPIC-05: SQL injection payloads in topic must not compromise database integrity."""
    sqli_topic = "'; DROP TABLE discussions; --"
    resp = await client.post(
        "/api/discussions",
        json={"topic": sqli_topic, "participants": make_valid_participants(4), "max_rounds": 2},
    )
    assert resp.status_code in (200, 201), f"Creation failed: {resp.status_code}"

    # Verify table integrity: querying discussion list must succeed normally
    list_resp = await client.get("/api/discussions")
    assert list_resp.status_code == 200, "Discussions table was compromised by SQL injection!"
    assert isinstance(list_resp.json(), list)


async def test_t2_topic_06_unicode_emojis_multilingual_topic(client: httpx.AsyncClient):
    """T2-TOPIC-06: Unicode emojis and multilingual characters must be preserved verbatim."""
    unicode_topic = "🤖 AI Safety: 伦理与未来 (Éthique & Futur) 🚀 100% 繁体/简体"
    resp = await client.post(
        "/api/discussions",
        json={"topic": unicode_topic, "participants": make_valid_participants(4), "max_rounds": 2},
    )
    assert resp.status_code in (200, 201), f"Failed to create discussion: {resp.status_code}"
    discussion_id = resp.json()["id"]

    detail = await client.get(f"/api/discussions/{discussion_id}")
    assert detail.status_code == 200
    assert detail.json()["topic"] == unicode_topic


# ==============================================================================
# Domain 2.3: Invalid Round Counts (T2-RND, 6 tests)
# ==============================================================================

async def test_t2_rnd_01_zero_max_rounds_rejected(client: httpx.AsyncClient):
    """T2-RND-01: Zero max_rounds must be rejected with 422."""
    resp = await client.post(
        "/api/discussions",
        json={"topic": "有效议题", "participants": make_valid_participants(4), "max_rounds": 0},
    )
    assert resp.status_code == 422, f"Expected 422 for max_rounds=0, got {resp.status_code}"


async def test_t2_rnd_02_negative_max_rounds_rejected(client: httpx.AsyncClient):
    """T2-RND-02: Negative max_rounds must be rejected with 422."""
    resp = await client.post(
        "/api/discussions",
        json={"topic": "有效议题", "participants": make_valid_participants(4), "max_rounds": -3},
    )
    assert resp.status_code == 422, f"Expected 422 for negative max_rounds, got {resp.status_code}"


async def test_t2_rnd_03_floating_point_max_rounds_rejected(client: httpx.AsyncClient):
    """T2-RND-03: Floating-point max_rounds must be rejected with 422."""
    resp = await client.post(
        "/api/discussions",
        json={"topic": "有效议题", "participants": make_valid_participants(4), "max_rounds": 3.14},
    )
    assert resp.status_code == 422, f"Expected 422 for float max_rounds, got {resp.status_code}"


async def test_t2_rnd_04_string_max_rounds_rejected(client: httpx.AsyncClient):
    """T2-RND-04: String type for max_rounds must be rejected with 422."""
    resp = await client.post(
        "/api/discussions",
        json={"topic": "有效议题", "participants": make_valid_participants(4), "max_rounds": "five"},
    )
    assert resp.status_code == 422, f"Expected 422 for string max_rounds, got {resp.status_code}"


async def test_t2_rnd_05_excessive_max_rounds_rejected(client: httpx.AsyncClient):
    """T2-RND-05: Excessively high max_rounds (e.g. 10,000) must be rejected with 422."""
    resp = await client.post(
        "/api/discussions",
        json={"topic": "有效议题", "participants": make_valid_participants(4), "max_rounds": 10000},
    )
    assert resp.status_code == 422, f"Expected 422 for excessive rounds (>system cap), got {resp.status_code}"


async def test_t2_rnd_06_minimal_valid_round_accepted(client: httpx.AsyncClient):
    """T2-RND-06: Minimal valid round count (1 round) must succeed."""
    resp = await client.post(
        "/api/discussions",
        json={"topic": "有效议题", "participants": make_valid_participants(4), "max_rounds": 1},
    )
    assert resp.status_code in (200, 201), f"Expected 200/201 for max_rounds=1, got {resp.status_code}"
    assert resp.json()["max_rounds"] == 1


# ==============================================================================
# Domain 2.4: Invalid Lifecycle State Transitions (T2-STATE, 7 tests)
# ==============================================================================

async def test_t2_state_01_pause_on_created_session_rejected(client: httpx.AsyncClient):
    """T2-STATE-01: Pausing an unstarted discussion (status 'created') must return 400 or 409."""
    d_id = await create_helper_discussion(client)
    resp = await client.post(f"/api/discussions/{d_id}/pause")
    assert resp.status_code in (400, 409), f"Expected 400/409 pausing unstarted session, got {resp.status_code}"


async def test_t2_state_02_resume_on_created_session_rejected(client: httpx.AsyncClient):
    """T2-STATE-02: Resuming an unstarted discussion (status 'created') must return 400 or 409."""
    d_id = await create_helper_discussion(client)
    resp = await client.post(f"/api/discussions/{d_id}/resume")
    assert resp.status_code in (400, 409), f"Expected 400/409 resuming unstarted session, got {resp.status_code}"


async def test_t2_state_03_resume_on_running_session_rejected(client: httpx.AsyncClient):
    """T2-STATE-03: Resuming an already running discussion must return 400 or 409."""
    d_id = await create_helper_discussion(client)
    start_resp = await client.post(f"/api/discussions/{d_id}/start")
    assert start_resp.status_code in (200, 201)

    resume_resp = await client.post(f"/api/discussions/{d_id}/resume")
    assert resume_resp.status_code in (400, 409), f"Expected 400/409 resuming running session, got {resume_resp.status_code}"


async def test_t2_state_04_start_on_running_session_rejected(client: httpx.AsyncClient):
    """T2-STATE-04: Starting an already running discussion must return 400 or 409."""
    d_id = await create_helper_discussion(client)
    start1 = await client.post(f"/api/discussions/{d_id}/start")
    assert start1.status_code in (200, 201)

    start2 = await client.post(f"/api/discussions/{d_id}/start")
    assert start2.status_code in (400, 409), f"Expected 400/409 double start, got {start2.status_code}"


async def test_t2_state_05_pause_on_paused_session_rejected(client: httpx.AsyncClient):
    """T2-STATE-05: Pausing an already paused discussion must return 400 or 409."""
    d_id = await create_helper_discussion(client)
    await client.post(f"/api/discussions/{d_id}/start")
    pause1 = await client.post(f"/api/discussions/{d_id}/pause")
    assert pause1.status_code == 200

    pause2 = await client.post(f"/api/discussions/{d_id}/pause")
    assert pause2.status_code in (400, 409), f"Expected 400/409 double pause, got {pause2.status_code}"


async def test_t2_state_06_controls_on_terminated_session_rejected(client: httpx.AsyncClient):
    """T2-STATE-06: Control operations (start, pause, resume) on a terminated session must be rejected."""
    d_id = await create_helper_discussion(client)
    await client.post(f"/api/discussions/{d_id}/start")
    term = await client.post(f"/api/discussions/{d_id}/terminate")
    assert term.status_code == 200

    start_resp = await client.post(f"/api/discussions/{d_id}/start")
    assert start_resp.status_code in (400, 409)

    pause_resp = await client.post(f"/api/discussions/{d_id}/pause")
    assert pause_resp.status_code in (400, 409)

    resume_resp = await client.post(f"/api/discussions/{d_id}/resume")
    assert resume_resp.status_code in (400, 409)

    # Terminate again: either 400/409 or idempotent 200
    term2 = await client.post(f"/api/discussions/{d_id}/terminate")
    assert term2.status_code in (200, 400, 409)


async def test_t2_state_07_controls_on_completed_session_rejected(client: httpx.AsyncClient):
    """T2-STATE-07: Control operations on a completed/terminated discussion must return 400 or 409."""
    d_id = await create_helper_discussion(client, max_rounds=1)
    await client.post(f"/api/discussions/{d_id}/start")

    # Await natural completion or terminate to reach terminal state
    for _ in range(20):
        detail = await client.get(f"/api/discussions/{d_id}")
        if detail.json().get("status") in ("completed", "terminated"):
            break
        await asyncio.sleep(0.1)
    else:
        # Fallback to terminating if engine has not finished within time
        await client.post(f"/api/discussions/{d_id}/terminate")

    detail = await client.get(f"/api/discussions/{d_id}")
    assert detail.json()["status"] in ("completed", "terminated")

    # Post-completion controls should be rejected
    res_start = await client.post(f"/api/discussions/{d_id}/start")
    assert res_start.status_code in (400, 409)

    res_resume = await client.post(f"/api/discussions/{d_id}/resume")
    assert res_resume.status_code in (400, 409)


# ==============================================================================
# Domain 2.5: Malformed & Truncated Payloads (T2-PAYL, 6 tests)
# ==============================================================================

async def test_t2_payl_01_empty_json_body_rejected(client: httpx.AsyncClient):
    """T2-PAYL-01: Completely empty JSON body {} on creation must return 422."""
    resp = await client.post("/api/discussions", json={})
    assert resp.status_code == 422, f"Expected 422 for empty body, got {resp.status_code}"


async def test_t2_payl_02_missing_topic_in_roster_generation_rejected(client: httpx.AsyncClient):
    """T2-PAYL-02: Missing required topic in roster generation must return 422."""
    resp = await client.post("/api/discussions/roster/generate", json={"participant_count": 4})
    assert resp.status_code == 422, f"Expected 422 for missing topic, got {resp.status_code}"


async def test_t2_payl_03_invalid_field_data_types_rejected(client: httpx.AsyncClient):
    """T2-PAYL-03: Invalid field data types (e.g. topic as integer, participants as string) must return 422."""
    resp = await client.post(
        "/api/discussions",
        json={"topic": 99999, "participants": "not-a-list", "max_rounds": "three"},
    )
    assert resp.status_code == 422, f"Expected 422 for wrong field types, got {resp.status_code}"


async def test_t2_payl_04_malformed_participant_item_rejected(client: httpx.AsyncClient):
    """T2-PAYL-04: Participant item missing required fields or invalid color_hex must return 422."""
    # Subcase A: Missing 'name'
    bad_item = [{"occupation": "AI专家", "stance": "支持", "color_hex": "#3B82F6", "role": "panelist"}]
    resp_name = await client.post(
        "/api/discussions",
        json={"topic": "合法议题", "participants": bad_item, "max_rounds": 2},
    )
    assert resp_name.status_code == 422

    # Subcase B: Invalid color_hex format
    bad_color = [{"name": "张三", "occupation": "AI专家", "stance": "支持", "color_hex": "not-a-hex", "role": "panelist"}]
    resp_color = await client.post(
        "/api/discussions",
        json={"topic": "合法议题", "participants": bad_color, "max_rounds": 2},
    )
    assert resp_color.status_code == 422


async def test_t2_payl_05_unparseable_syntax_broken_json_rejected(client: httpx.AsyncClient):
    """T2-PAYL-05: Unparseable raw JSON syntax must return 400 or 422."""
    resp = await client.post(
        "/api/discussions",
        content=b"{topic: unquoted_key_and_broken_syntax",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code in (400, 422)


async def test_t2_payl_06_extra_unknown_payload_keys_accepted(client: httpx.AsyncClient):
    """T2-PAYL-06: Extra unknown payload keys must be ignored cleanly without 500 server error."""
    payload = {
        "topic": "合法测试议题",
        "participants": make_valid_participants(4),
        "max_rounds": 2,
        "unexpected_extra_key": "malicious_or_extra_content",
        "nested_unknown": {"foo": "bar"},
    }
    resp = await client.post("/api/discussions", json=payload)
    assert resp.status_code in (200, 201), f"Expected 200/201 ignoring extra keys, got {resp.status_code}"
    assert resp.status_code != 500


# ==============================================================================
# Domain 2.6: Rapid Repeated Controls & Concurrency Race (T2-RACE, 6 tests)
# ==============================================================================

async def test_t2_race_01_simultaneous_double_start_race(client: httpx.AsyncClient):
    """T2-RACE-01: Concurrent double start calls must not spawn duplicate loops or return 500."""
    d_id = await create_helper_discussion(client)
    res1, res2 = await asyncio.gather(
        client.post(f"/api/discussions/{d_id}/start"),
        client.post(f"/api/discussions/{d_id}/start"),
        return_exceptions=True,
    )
    responses = [r for r in (res1, res2) if isinstance(r, httpx.Response)]
    assert len(responses) == 2, f"Exceptions occurred during double start: {[res1, res2]}"
    statuses = [r.status_code for r in responses]
    assert all(s in (200, 400, 409) for s in statuses), f"Unexpected statuses: {statuses}"
    assert 200 in statuses, "At least one start call must succeed with 200"
    assert 500 not in statuses

    detail = await client.get(f"/api/discussions/{d_id}")
    assert detail.json()["status"] == "running"


async def test_t2_race_02_simultaneous_double_pause_race(client: httpx.AsyncClient):
    """T2-RACE-02: Concurrent double pause calls must cleanly settle to paused without deadlocks."""
    d_id = await create_helper_discussion(client)
    await client.post(f"/api/discussions/{d_id}/start")

    res1, res2 = await asyncio.gather(
        client.post(f"/api/discussions/{d_id}/pause"),
        client.post(f"/api/discussions/{d_id}/pause"),
        return_exceptions=True,
    )
    responses = [r for r in (res1, res2) if isinstance(r, httpx.Response)]
    statuses = [r.status_code for r in responses]
    assert all(s in (200, 400, 409) for s in statuses)
    assert 500 not in statuses

    detail = await client.get(f"/api/discussions/{d_id}")
    assert detail.json()["status"] == "paused"


async def test_t2_race_03_simultaneous_double_resume_race(client: httpx.AsyncClient):
    """T2-RACE-03: Concurrent double resume calls must cleanly settle to running."""
    d_id = await create_helper_discussion(client)
    await client.post(f"/api/discussions/{d_id}/start")
    await client.post(f"/api/discussions/{d_id}/pause")

    res1, res2 = await asyncio.gather(
        client.post(f"/api/discussions/{d_id}/resume"),
        client.post(f"/api/discussions/{d_id}/resume"),
        return_exceptions=True,
    )
    responses = [r for r in (res1, res2) if isinstance(r, httpx.Response)]
    statuses = [r.status_code for r in responses]
    assert all(s in (200, 400, 409) for s in statuses)
    assert 500 not in statuses

    detail = await client.get(f"/api/discussions/{d_id}")
    assert detail.json()["status"] == "running"


async def test_t2_race_04_start_immediately_followed_by_terminate(client: httpx.AsyncClient):
    """T2-RACE-04: Immediate termination right after start (<5ms) must cancel gracefully without crash."""
    d_id = await create_helper_discussion(client)
    task1 = asyncio.create_task(client.post(f"/api/discussions/{d_id}/start"))
    task2 = asyncio.create_task(client.post(f"/api/discussions/{d_id}/terminate"))

    r1, r2 = await asyncio.gather(task1, task2)
    assert r1.status_code in (200, 400, 409)
    assert r2.status_code in (200, 400, 409)
    assert r1.status_code != 500 and r2.status_code != 500

    await asyncio.sleep(0.05)
    detail = await client.get(f"/api/discussions/{d_id}")
    assert detail.json()["status"] == "terminated"


async def test_t2_race_05_rapid_alternating_pause_resume_spam(client: httpx.AsyncClient):
    """T2-RACE-05: Rapid alternating pause and resume calls must not cause deadlock or 500 errors."""
    d_id = await create_helper_discussion(client)
    await client.post(f"/api/discussions/{d_id}/start")

    for _ in range(3):
        p_resp = await client.post(f"/api/discussions/{d_id}/pause")
        assert p_resp.status_code in (200, 400, 409)
        assert p_resp.status_code != 500
        r_resp = await client.post(f"/api/discussions/{d_id}/resume")
        assert r_resp.status_code in (200, 400, 409)
        assert r_resp.status_code != 500

    detail = await client.get(f"/api/discussions/{d_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] in ("running", "paused")


async def test_t2_race_06_simultaneous_double_terminate_race(client: httpx.AsyncClient):
    """T2-RACE-06: Concurrent double terminate calls must terminate cleanly without 500."""
    d_id = await create_helper_discussion(client)
    await client.post(f"/api/discussions/{d_id}/start")

    res1, res2 = await asyncio.gather(
        client.post(f"/api/discussions/{d_id}/terminate"),
        client.post(f"/api/discussions/{d_id}/terminate"),
        return_exceptions=True,
    )
    responses = [r for r in (res1, res2) if isinstance(r, httpx.Response)]
    statuses = [r.status_code for r in responses]
    assert all(s in (200, 400, 409) for s in statuses)
    assert 200 in statuses
    assert 500 not in statuses

    detail = await client.get(f"/api/discussions/{d_id}")
    assert detail.json()["status"] == "terminated"


# ==============================================================================
# Domain 2.7: Unconfigured vs Invalid API Key Handling (T2-KEY, 6 tests)
# ==============================================================================

async def test_t2_key_01_empty_api_key_falls_back_to_mock(client: httpx.AsyncClient, monkeypatch):
    """T2-KEY-01: Empty LLM API key must seamlessly fall back to the offline mock engine."""
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("LLM_BASE_URL", "")
    monkeypatch.setenv("LLM_MODEL", "mock")

    resp = await client.post(
        "/api/discussions/roster/generate",
        json={"topic": "核聚变商业化路径探讨", "participant_count": 4},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data.get("experts", [])) == 4


async def test_t2_key_02_whitespace_api_key_falls_back_to_mock(client: httpx.AsyncClient, monkeypatch):
    """T2-KEY-02: Whitespace-only LLM API key must be treated as unconfigured and activate mock mode."""
    monkeypatch.setenv("LLM_API_KEY", "   \t  \n ")

    resp = await client.post(
        "/api/discussions/roster/generate",
        json={"topic": "生成式AI在医疗诊断中的边界", "participant_count": 4},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data.get("experts", [])) == 4


async def test_t2_key_03_invalid_api_key_error_containment(client: httpx.AsyncClient, monkeypatch):
    """T2-KEY-03: Invalid LLM API key returning upstream 401 must be contained gracefully without crash."""
    monkeypatch.setenv("LLM_API_KEY", "sk-invalid-fake-key-123456")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")

    resp = await client.post(
        "/api/discussions/roster/generate",
        json={"topic": "自动驾驶责任认定机制", "participant_count": 4},
    )
    # The backend should either fall back to mock (200) or return controlled error (502/503/401), not 500
    assert resp.status_code in (200, 502, 503, 504, 401)
    assert resp.status_code != 500
    assert "Traceback (most recent call last)" not in resp.text


async def test_t2_key_04_nonexistent_base_url_connection_refusal(client: httpx.AsyncClient, monkeypatch):
    """T2-KEY-04: Non-existent base URL connection refusal must not hang indefinitely or crash server."""
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:54321/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-dummy-key")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")

    resp = await client.post(
        "/api/discussions/roster/generate",
        json={"topic": "商业航天探索与星链发展", "participant_count": 4},
    )
    assert resp.status_code in (200, 502, 503, 504)
    assert resp.status_code != 500
    assert "Traceback (most recent call last)" not in resp.text


async def test_t2_key_05_credential_leakage_scanner_across_responses(client: httpx.AsyncClient, monkeypatch):
    """T2-KEY-05: Injected secret canary key must NEVER leak into response bodies, headers, or error details."""
    canary = "sk-canary-secret-value-abcdef-9988"
    monkeypatch.setenv("LLM_API_KEY", canary)

    endpoints_to_probe = []
    # 1. Roster generation
    endpoints_to_probe.append(
        await client.post("/api/discussions/roster/generate", json={"topic": "测试议题", "participant_count": 4})
    )
    # 2. Discussion creation
    create_resp = await client.post(
        "/api/discussions",
        json={"topic": "测试议题", "participants": make_valid_participants(4), "max_rounds": 2},
    )
    endpoints_to_probe.append(create_resp)

    d_id = create_resp.json().get("id", str(uuid.uuid4()))

    # 3. List
    endpoints_to_probe.append(await client.get("/api/discussions"))
    # 4. Detail
    endpoints_to_probe.append(await client.get(f"/api/discussions/{d_id}"))
    # 5. Start
    endpoints_to_probe.append(await client.post(f"/api/discussions/{d_id}/start"))
    # 6. Pause
    endpoints_to_probe.append(await client.post(f"/api/discussions/{d_id}/pause"))
    # 7. Transcript
    endpoints_to_probe.append(await client.get(f"/api/discussions/{d_id}/transcript"))
    # 8. Summary
    endpoints_to_probe.append(await client.get(f"/api/discussions/{d_id}/summary"))
    # 9. 404 response
    endpoints_to_probe.append(await client.get(f"/api/discussions/{uuid.uuid4()}"))
    # 10. 422 error response
    endpoints_to_probe.append(await client.post("/api/discussions", json={}))

    for i, resp in enumerate(endpoints_to_probe):
        assert canary not in resp.text, f"Secret canary leaked in response body of probe #{i}: {resp.url}"
        assert canary not in str(resp.headers), f"Secret canary leaked in headers of probe #{i}: {resp.url}"


async def test_t2_key_06_client_bundle_credential_isolation():
    """T2-KEY-06: Frontend source and client configs must not hardcode server API keys or secrets."""
    repo_root = Path(__file__).resolve().parents[3]
    frontend_src = repo_root / "frontend" / "src"

    if frontend_src.exists():
        for file_path in frontend_src.rglob("*"):
            if file_path.is_file() and file_path.suffix in (".ts", ".tsx", ".js", ".jsx", ".html"):
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                assert "LLM_API_KEY" not in content, (
                    f"Forbidden server secret 'LLM_API_KEY' found in frontend source: {file_path}"
                )
                assert "sk-" not in content or "task-" in content, (
                    f"Possible OpenAI secret key detected in frontend file: {file_path}"
                )

    # Verify root .env.example contains only dummy placeholders
    env_example = repo_root / ".env.example"
    if env_example.exists():
        content = env_example.read_text(encoding="utf-8", errors="ignore")
        # Ensure no active live OpenAI key was committed
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("LLM_API_KEY=") and not line.startswith("#"):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                assert val == "" or val.startswith("your_") or "example" in val or "placeholder" in val or "mock" in val, (
                    f"Real API key suspected in .env.example: {line}"
                )


# ==============================================================================
# Domain 2.8: Non-existent IDs (404 Error Handling) (T2-ID, 8 tests)
# ==============================================================================

NONEXISTENT_UUID = "00000000-0000-0000-0000-000000000000"


async def test_t2_id_01_get_discussion_nonexistent_id_404(client: httpx.AsyncClient):
    """T2-ID-01: GET /api/discussions/{id} with non-existent ID must return 404."""
    resp = await client.get(f"/api/discussions/{NONEXISTENT_UUID}")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


async def test_t2_id_02_start_discussion_nonexistent_id_404(client: httpx.AsyncClient):
    """T2-ID-02: POST /api/discussions/{id}/start with non-existent ID must return 404."""
    resp = await client.post(f"/api/discussions/{NONEXISTENT_UUID}/start")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


async def test_t2_id_03_pause_discussion_nonexistent_id_404(client: httpx.AsyncClient):
    """T2-ID-03: POST /api/discussions/{id}/pause with non-existent ID must return 404."""
    resp = await client.post(f"/api/discussions/{NONEXISTENT_UUID}/pause")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


async def test_t2_id_04_resume_discussion_nonexistent_id_404(client: httpx.AsyncClient):
    """T2-ID-04: POST /api/discussions/{id}/resume with non-existent ID must return 404."""
    resp = await client.post(f"/api/discussions/{NONEXISTENT_UUID}/resume")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


async def test_t2_id_05_terminate_discussion_nonexistent_id_404(client: httpx.AsyncClient):
    """T2-ID-05: POST /api/discussions/{id}/terminate with non-existent ID must return 404."""
    resp = await client.post(f"/api/discussions/{NONEXISTENT_UUID}/terminate")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


async def test_t2_id_06_get_transcript_nonexistent_id_404(client: httpx.AsyncClient):
    """T2-ID-06: GET /api/discussions/{id}/transcript with non-existent ID must return 404."""
    resp = await client.get(f"/api/discussions/{NONEXISTENT_UUID}/transcript")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


async def test_t2_id_07_get_summary_nonexistent_id_404(client: httpx.AsyncClient):
    """T2-ID-07: GET /api/discussions/{id}/summary with non-existent ID must return 404."""
    resp = await client.get(f"/api/discussions/{NONEXISTENT_UUID}/summary")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


async def test_t2_id_08_sse_events_nonexistent_id_404(client: httpx.AsyncClient):
    """T2-ID-08: GET /api/discussions/{id}/events with non-existent ID must return 404."""
    try:
        async with asyncio.timeout(5.0):
            async with client.stream("GET", f"/api/discussions/{NONEXISTENT_UUID}/events") as resp:
                assert resp.status_code == 404, f"Expected 404 for nonexistent SSE stream, got {resp.status_code}"
    except TimeoutError:
        pytest.fail(f"GET /api/discussions/{NONEXISTENT_UUID}/events did not return 404; streamed indefinitely and timed out.")
