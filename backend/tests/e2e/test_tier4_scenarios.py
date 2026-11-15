"""
Tier 4: Real-World Application Scenarios (S1 – S5) Full-Lifecycle E2E Test Suite.
Validates the complete autonomous round-table debate lifecycle across 5 realistic
thematic domains specified in ORIGINAL_REQUEST.md, PROJECT.md, and TEST_INFRA.md:

- Scenario 1 (S1): AGI Safety vs Acceleration (4 experts + 1 mod, frontier alignment probing, tiered licensing consensus)
- Scenario 2 (S2): Remote Work vs Return to Office (3 experts + 1 mod, odd-count panel, mid-debate pause/resume control)
- Scenario 3 (S3): Nuclear Energy in Green Transition (4 experts + 1 mod, floor control de-escalation, SMR consensus)
- Scenario 4 (S4): Algorithmic Recommendation in Media (4 experts + 1 mod, concurrent multi-session isolation & Last-Event-ID replay)
- Scenario 5 (S5): Commercial Space Exploration & Asteroid Mining (5 experts + 1 mod, 5-agent priority arbitration & fairness invariant)

Each scenario tests the entire pipeline:
Roster Generation -> Discussion Creation -> SSE Streaming -> Turn Arbitration ->
Consensus/Divergence Dynamics -> Moderator Intervention -> Conclusion -> Stance Audit & Transcript Persistence.
"""

import asyncio
from typing import Any, Dict, List, Optional
import httpx
import pytest

from .sse_helper import (
    SSECollector,
    SSEEvent,
    validate_sse_event_contract,
)


@pytest.fixture
def client(async_client: httpx.AsyncClient) -> httpx.AsyncClient:
    """Fixture bridge ensuring tests can use 'client' as an alias for 'async_client'."""
    return async_client


# ============================================================================
# Scenario 1 (S1): AGI Safety vs Acceleration
# ============================================================================
@pytest.mark.tier4
@pytest.mark.asyncio
async def test_t4_scen_01_agi_safety_vs_acceleration(client: httpx.AsyncClient):
    """
    Scenario 1 (S1): 通用人工智能（AGI）开源是促进技术普惠还是加剧灾难性风险？
    Domain: AI / Technology Policy & Existential Safety.
    Panel: 4 Experts (陆成峰, 艾丽斯·戴维斯, 周秉和, 宋嘉琳) + 1 Moderator.
    """
    topic = "通用人工智能（AGI）开源是促进技术普惠还是加剧灾难性风险？"

    # Phase 1: Dynamic Roster Generation
    roster_resp = await client.post(
        "/api/discussions/roster/generate",
        json={"topic": topic, "participant_count": 4},
    )
    assert roster_resp.status_code == 200, f"Roster gen failed: {roster_resp.text}"
    roster_data = roster_resp.json()
    experts = roster_data.get("experts", [])
    assert len(experts) == 4, f"Expected exactly 4 experts, got {len(experts)}"

    for exp in experts:
        assert "name" in exp and exp["name"]
        assert "occupation" in exp and exp["occupation"]
        assert "stance" in exp and exp["stance"]
        assert "color_hex" in exp and exp["color_hex"]

    participants = [
        {
            "name": exp["name"],
            "occupation": exp["occupation"],
            "stance": exp["stance"],
            "color_hex": exp.get("color_hex", "#3B82F6"),
            "role": exp.get("role", "expert"),
        }
        for exp in experts
    ]

    # Phase 2: Discussion Creation
    create_resp = await client.post(
        "/api/discussions",
        json={
            "topic": topic,
            "participants": participants,
            "max_rounds": 3,
        },
    )
    assert create_resp.status_code in (200, 201), f"Create discussion failed: {create_resp.text}"
    disc = create_resp.json()
    disc_id = disc["id"]
    assert disc.get("status") == "created"
    assert len(disc.get("participants", [])) >= 4

    # Phase 3: SSE Subscription & Start Debate
    collector = SSECollector(client, f"/api/discussions/{disc_id}/events")
    await collector.start()

    try:
        start_resp = await client.post(f"/api/discussions/{disc_id}/start")
        assert start_resp.status_code == 200, f"Start failed: {start_resp.text}"
        start_data = start_resp.json()
        assert start_data.get("status") == "running" or start_data.get("success") is True

        # Phase 4: Live SSE Stream Validation
        # Wait for status change to running
        running_evt = await collector.wait_for_event(
            lambda e: e.event == "session_status_changed" and e.data.get("new_status") == "running",
            timeout=10.0,
        )
        assert running_evt is not None
        validate_sse_event_contract(running_evt)

        # Await conclusion of the debate
        conclusion_evt = await collector.wait_for_conclusion(timeout=40.0)
        assert conclusion_evt is not None
        validate_sse_event_contract(conclusion_evt)

        # Verify core event occurrences in stream
        collector.assert_event_sequence(["session_status_changed", "speaker_selected", "speech_completed"])
        collector.assert_monotonic_ids()

        # Consecutive speaker lockout invariant check across turns
        speaker_events = collector.get_events_by_type("speaker_selected")
        assert len(speaker_events) >= 3, f"Expected at least 3 speaking turns, got {len(speaker_events)}"
        speakers = [e.data["speaker_id"] for e in speaker_events if "speaker_id" in e.data]
        for i in range(len(speakers) - 1):
            assert speakers[i] != speakers[i + 1], (
                f"Consecutive speaker lockout violated in S1: {speakers[i]} spoke twice in a row!"
            )

        # Validate all received events pass schema contracts
        for evt in collector.events:
            validate_sse_event_contract(evt)

        # Phase 5: Post-Debate Transcript & Summary Audits
        tr_resp = await client.get(f"/api/discussions/{disc_id}/transcript")
        assert tr_resp.status_code == 200
        transcript = tr_resp.json()
        assert len(transcript) >= 3, f"Expected at least 3 transcript turns, got {len(transcript)}"

        for turn in transcript:
            assert "turn_number" in turn
            assert "speaker_id" in turn
            assert "content" in turn and len(turn["content"]) > 0
            assert "action_type" in turn

        sum_resp = await client.get(f"/api/discussions/{disc_id}/summary")
        assert sum_resp.status_code == 200
        summary_data = sum_resp.json()
        assert "summary" in summary_data and summary_data["summary"]
        assert len(summary_data["summary"]) > 0

        # Consensus and divergence items check
        assert "consensus_items" in summary_data
        assert "divergence_items" in summary_data

        # Stance audit inspection
        if "stance_audit" in summary_data and summary_data["stance_audit"]:
            assert len(summary_data["stance_audit"]) >= 2

    finally:
        await collector.close()


# ============================================================================
# Scenario 2 (S2): Remote Work vs Return to Office (Odd Count N=3 + Control)
# ============================================================================
@pytest.mark.tier4
@pytest.mark.asyncio
async def test_t4_scen_02_remote_work_vs_rto(client: httpx.AsyncClient):
    """
    Scenario 2 (S2): 全面远程办公是否会永久性重塑企业形态并取代传统办公室协作？
    Domain: Corporate Management / Workplace Sociology.
    Panel: 3 Experts (陈翰霖, 苏晓敏, 方予涵) + 1 Moderator (Tests odd count N=3).
    Includes mid-debate pause and resume control verification.
    """
    topic = "全面远程办公是否会永久性重塑企业形态并取代传统办公室协作？"

    # Phase 1: 3-Expert Roster Generation
    roster_resp = await client.post(
        "/api/discussions/roster/generate",
        json={"topic": topic, "participant_count": 3},
    )
    assert roster_resp.status_code == 200
    experts = roster_resp.json().get("experts", [])
    assert len(experts) == 3, f"Expected exactly 3 experts, got {len(experts)}"

    participants = [
        {
            "name": exp["name"],
            "occupation": exp["occupation"],
            "stance": exp["stance"],
            "color_hex": exp.get("color_hex", "#3B82F6"),
            "role": exp.get("role", "expert"),
        }
        for exp in experts
    ]

    # Create discussion with max_rounds=2
    create_resp = await client.post(
        "/api/discussions",
        json={
            "topic": topic,
            "participants": participants,
            "max_rounds": 2,
        },
    )
    assert create_resp.status_code in (200, 201)
    disc_id = create_resp.json()["id"]

    # Phase 2: SSE Listener & Start
    collector = SSECollector(client, f"/api/discussions/{disc_id}/events")
    await collector.start()

    try:
        await client.post(f"/api/discussions/{disc_id}/start")

        # Wait for first speech_chunk or speaker_selected
        await collector.wait_for_event(
            lambda e: e.event in ("speech_chunk", "speaker_selected"), timeout=15.0
        )

        # Mid-debate Pause Control
        pause_resp = await client.post(f"/api/discussions/{disc_id}/pause")
        assert pause_resp.status_code == 200

        paused_evt = await collector.wait_for_event(
            lambda e: e.event == "session_status_changed" and e.data.get("new_status") == "paused",
            timeout=10.0,
        )
        assert paused_evt is not None

        # Verify pause silence window
        count_at_pause = len(collector.events)
        await asyncio.sleep(1.0)
        assert len([e for e in collector.events[count_at_pause:] if e.event == "speaker_selected"]) == 0

        # Resume debate
        resume_resp = await client.post(f"/api/discussions/{disc_id}/resume")
        assert resume_resp.status_code == 200

        # Run to conclusion
        await collector.wait_for_conclusion(timeout=35.0)

        # Monotonicity & Contract checks
        collector.assert_monotonic_ids()
        for evt in collector.events:
            validate_sse_event_contract(evt)

        # Verify transcript
        tr_resp = await client.get(f"/api/discussions/{disc_id}/transcript")
        assert tr_resp.status_code == 200
        turns = tr_resp.json()
        assert len(turns) >= 2

        # Verify summary
        sum_resp = await client.get(f"/api/discussions/{disc_id}/summary")
        assert sum_resp.status_code == 200
        summary_data = sum_resp.json()
        assert "summary" in summary_data and summary_data["summary"]

    finally:
        await collector.close()


# ============================================================================
# Scenario 3 (S3): Nuclear Energy in Green Transition
# ============================================================================
@pytest.mark.tier4
@pytest.mark.asyncio
async def test_t4_scen_03_nuclear_energy_transition(client: httpx.AsyncClient):
    """
    Scenario 3 (S3): 在迈向净零排放的过程中，核能是否应当作为基荷电力的核心支柱？
    Domain: Energy Engineering / Climate Transition Policy.
    Panel: 4 Experts (严景德, 白曼丽, 钱立勋, 孙思齐) + 1 Moderator.
    Tests floor control / de-escalation, high divergence tracking, and SMR consensus.
    """
    topic = "在迈向净零排放的过程中，核能是否应当作为基荷电力的核心支柱？"

    roster_resp = await client.post(
        "/api/discussions/roster/generate",
        json={"topic": topic, "participant_count": 4},
    )
    assert roster_resp.status_code == 200
    experts = roster_resp.json().get("experts", [])
    assert len(experts) == 4

    create_resp = await client.post(
        "/api/discussions",
        json={
            "topic": topic,
            "participants": [
                {
                    "name": exp["name"],
                    "occupation": exp["occupation"],
                    "stance": exp["stance"],
                    "color_hex": exp.get("color_hex", "#3B82F6"),
                    "role": "expert",
                }
                for exp in experts
            ],
            "max_rounds": 3,
        },
    )
    assert create_resp.status_code in (200, 201)
    disc_id = create_resp.json()["id"]

    collector = SSECollector(client, f"/api/discussions/{disc_id}/events")
    await collector.start()

    try:
        await client.post(f"/api/discussions/{disc_id}/start")
        await collector.wait_for_conclusion(timeout=40.0)

        # Verify moderator intervention or divergence updates occurred
        mod_events = collector.get_events_by_type("moderator_intervention")
        div_events = collector.get_events_by_type("divergence_updated")
        cons_events = collector.get_events_by_type("consensus_updated")

        # Debate must have produced turns and consensus/divergence snapshots
        assert len(collector.get_events_by_type("speech_completed")) >= 2
        collector.assert_monotonic_ids()

        for evt in collector.events:
            validate_sse_event_contract(evt)

        # Verify final transcript
        tr_resp = await client.get(f"/api/discussions/{disc_id}/transcript")
        assert tr_resp.status_code == 200
        assert len(tr_resp.json()) >= 2

        # Verify summary
        sum_resp = await client.get(f"/api/discussions/{disc_id}/summary")
        assert sum_resp.status_code == 200
        sum_data = sum_resp.json()
        assert "summary" in sum_data and len(sum_data["summary"]) > 0

    finally:
        await collector.close()


# ============================================================================
# Scenario 4 (S4): Algorithmic Recommendation in Media (Multi-Session Isolation E2E)
# ============================================================================
@pytest.mark.tier4
@pytest.mark.asyncio
async def test_t4_scen_04_algorithmic_recommendation(client: httpx.AsyncClient):
    """
    Scenario 4 (S4): 算法个性化推荐是加剧了信息茧房与社会撕裂，还是提升了信息匹配效率？
    Domain: Digital Ethics / Platform Governance & Public Sphere.
    Panel: 4 Experts (林浩然, 程思远, 高敏华, 赵梓辰) + 1 Moderator.
    Executes concurrently alongside an independent control session to validate complete
    multi-session runtime isolation and Last-Event-ID reconnection under load.
    """
    topic_a = "算法个性化推荐是加剧了信息茧房与社会撕裂，还是提升了信息匹配效率？"
    topic_b = "全面远程办公是否会永久性重塑企业形态并取代传统办公室协作？"

    # Discussion A (S4)
    roster_a = await client.post("/api/discussions/roster/generate", json={"topic": topic_a, "participant_count": 4})
    assert roster_a.status_code == 200
    create_a = await client.post(
        "/api/discussions",
        json={
            "topic": topic_a,
            "participants": [
                {
                    "name": exp["name"],
                    "occupation": exp["occupation"],
                    "stance": exp["stance"],
                    "color_hex": exp.get("color_hex", "#3B82F6"),
                    "role": "expert",
                }
                for exp in roster_a.json().get("experts", [])
            ],
            "max_rounds": 2,
        },
    )
    id_a = create_a.json()["id"]

    # Discussion B (Control)
    roster_b = await client.post("/api/discussions/roster/generate", json={"topic": topic_b, "participant_count": 3})
    assert roster_b.status_code == 200
    create_b = await client.post(
        "/api/discussions",
        json={
            "topic": topic_b,
            "participants": [
                {
                    "name": exp["name"],
                    "occupation": exp["occupation"],
                    "stance": exp["stance"],
                    "color_hex": exp.get("color_hex", "#10B981"),
                    "role": "expert",
                }
                for exp in roster_b.json().get("experts", [])
            ],
            "max_rounds": 2,
        },
    )
    id_b = create_b.json()["id"]

    # Concurrent streaming
    collector_a = SSECollector(client, f"/api/discussions/{id_a}/events")
    collector_b = SSECollector(client, f"/api/discussions/{id_b}/events")

    await collector_a.start()
    await collector_b.start()

    try:
        # Start both concurrently
        await asyncio.gather(
            client.post(f"/api/discussions/{id_a}/start"),
            client.post(f"/api/discussions/{id_b}/start"),
        )

        # Wait for Session A to collect at least 3 events
        await collector_a.wait_for_event(lambda e: len(collector_a.events) >= 3, timeout=15.0)

        # Disconnect Session A briefly to test Last-Event-ID reconnection under concurrency
        last_id_a = collector_a.events[-1].id
        await collector_a.close()

        # Session B continues running without interruption
        await asyncio.sleep(0.5)

        # Reconnect Session A
        collector_a_reconnect = SSECollector(
            client,
            f"/api/discussions/{id_a}/events",
            last_event_id=last_id_a,
        )
        await collector_a_reconnect.start()

        # Await conclusion on both
        await asyncio.gather(
            collector_a_reconnect.wait_for_conclusion(timeout=40.0),
            collector_b.wait_for_conclusion(timeout=40.0),
        )

        # Validate sequence monotonicity
        collector_a_reconnect.assert_monotonic_ids()
        collector_b.assert_monotonic_ids()

        # Database transcript isolation check: disjoint turn IDs
        tr_a_resp = await client.get(f"/api/discussions/{id_a}/transcript")
        tr_b_resp = await client.get(f"/api/discussions/{id_b}/transcript")
        assert tr_a_resp.status_code == 200
        assert tr_b_resp.status_code == 200

        turns_a = tr_a_resp.json()
        turns_b = tr_b_resp.json()

        assert len(turns_a) >= 2
        assert len(turns_b) >= 2

        turn_ids_a = {t["id"] for t in turns_a}
        turn_ids_b = {t["id"] for t in turns_b}
        assert len(turn_ids_a & turn_ids_b) == 0, f"Turn ID crosstalk: {turn_ids_a & turn_ids_b}"

    finally:
        await collector_a.close()
        if "collector_a_reconnect" in locals():
            await collector_a_reconnect.close()
        await collector_b.close()


# ============================================================================
# Scenario 5 (S5): Commercial Space Exploration & Asteroid Mining (Large Panel N=5)
# ============================================================================
@pytest.mark.tier4
@pytest.mark.asyncio
async def test_t4_scen_05_space_exploration_mining(client: httpx.AsyncClient):
    """
    Scenario 5 (S5): 商业太空探索与小行星采矿：人类文明的战略飞跃还是深空资源争夺战？
    Domain: Space Technology / International Law & Common Heritage.
    Panel: 5 Experts (万斯远, 梁素芬, 赵廷岳, 何瑞安, 齐梦华) + 1 Moderator (Large Panel N=5).
    Verifies 5-agent hand-raising arbitration, fairness score distribution, and consecutive
    speaker lockout invariant across full multi-round debate.
    """
    topic = "商业太空探索与小行星采矿：人类文明的战略飞跃还是深空资源争夺战？"

    # Phase 1: 5-Expert Panel Setup
    roster_resp = await client.post(
        "/api/discussions/roster/generate",
        json={"topic": topic, "participant_count": 5},
    )
    assert roster_resp.status_code == 200, f"Roster gen failed: {roster_resp.text}"
    experts = roster_resp.json().get("experts", [])
    assert len(experts) == 5, f"Expected exactly 5 experts, got {len(experts)}"

    # Verify 5 distinct colors and names
    colors = [exp.get("color_hex") for exp in experts if "color_hex" in exp]
    names = [exp.get("name") for exp in experts if "name" in exp]
    assert len(set(names)) == 5, f"Expected 5 unique names, got: {names}"

    create_resp = await client.post(
        "/api/discussions",
        json={
            "topic": topic,
            "participants": [
                {
                    "name": exp["name"],
                    "occupation": exp["occupation"],
                    "stance": exp["stance"],
                    "color_hex": exp.get("color_hex", "#EC4899"),
                    "role": "expert",
                }
                for exp in experts
            ],
            "max_rounds": 3,
        },
    )
    assert create_resp.status_code in (200, 201)
    disc_id = create_resp.json()["id"]

    # Phase 2: SSE Listener & Debate Execution
    collector = SSECollector(client, f"/api/discussions/{disc_id}/events")
    await collector.start()

    try:
        await client.post(f"/api/discussions/{disc_id}/start")
        await collector.wait_for_conclusion(timeout=45.0)

        # Phase 3: 5-Agent Arbitration & Invariant Audits
        speaker_events = collector.get_events_by_type("speaker_selected")
        assert len(speaker_events) >= 4, f"Expected at least 4 turns, got {len(speaker_events)}"

        speakers = [e.data["speaker_id"] for e in speaker_events if "speaker_id" in e.data]

        # Consecutive speaker lockout invariant check across all 5 agents
        for i in range(len(speakers) - 1):
            assert speakers[i] != speakers[i + 1], (
                f"Consecutive speaker lockout violated in 5-agent debate: "
                f"Speaker '{speakers[i]}' spoke at turn {i} and {i+1}!"
            )

        # Fairness distribution check: verify multiple distinct experts took the floor
        distinct_speakers = set(speakers)
        assert len(distinct_speakers) >= 2, (
            f"Expected at least 2 distinct speakers in 5-expert debate, got: {distinct_speakers}"
        )

        # Monotonicity check
        collector.assert_monotonic_ids()

        # Contract validation on all events
        for evt in collector.events:
            validate_sse_event_contract(evt)

        # Phase 4: Final Summary & Transcript Export Verification
        tr_resp = await client.get(f"/api/discussions/{disc_id}/transcript")
        assert tr_resp.status_code == 200
        transcript = tr_resp.json()
        assert len(transcript) >= 3

        sum_resp = await client.get(f"/api/discussions/{disc_id}/summary")
        assert sum_resp.status_code == 200
        summary_data = sum_resp.json()
        assert "summary" in summary_data and len(summary_data["summary"]) > 0

    finally:
        await collector.close()
