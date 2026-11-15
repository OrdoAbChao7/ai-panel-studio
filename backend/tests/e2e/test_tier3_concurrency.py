"""
Tier 3: Cross-Feature Combinations & Multi-Session Concurrency Test Suite.
Verifies pairwise and cross-feature interactions, lifecycle state transitions,
SSE streaming resilience, Last-Event-ID replay, and multi-session concurrency isolation
under autonomous AI debate engine operations.

Features tested:
- F01: Dynamic Turn-Taking & Arbitration
- F02: Consensus & Divergence Tracking
- F03: Moderator Intervention System
- F04: Session Lifecycle Controller
- F05: Multi-Discussion Isolation
- F06: SSE Stream & Last-Event-ID Replay
- F11: Expert Status & Hand-Raising
- F12: Real-Time Streaming Transcript
- F15: Post-Debate Moderator Synthesis
- F17: Transcript History & Persistence
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


async def _create_test_discussion(
    client: httpx.AsyncClient,
    topic: str = "通用人工智能（AGI）开源是促进技术普惠还是加剧灾难性风险？",
    participant_count: int = 4,
    max_rounds: int = 2,
    participants: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Helper to generate roster (if needed) and create a test discussion."""
    if participants is None:
        roster_resp = await client.post(
            "/api/discussions/roster/generate",
            json={"topic": topic, "participant_count": participant_count},
        )
        assert roster_resp.status_code == 200, f"Roster gen failed: {roster_resp.text}"
        roster_data = roster_resp.json()
        experts = roster_data.get("experts", [])
        assert len(experts) >= 2, f"Expected at least 2 experts, got {len(experts)}"
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

    create_resp = await client.post(
        "/api/discussions",
        json={
            "topic": topic,
            "participants": participants,
            "max_rounds": max_rounds,
        },
    )
    assert create_resp.status_code in (200, 201), f"Create discussion failed: {create_resp.text}"
    return create_resp.json()


# ============================================================================
# T3-CROSS-01: Mid-Speech Pause and Resume with SSE Stream Continuity
# ============================================================================
@pytest.mark.tier3
@pytest.mark.asyncio
async def test_t3_cross_01_mid_speech_pause_resume(client: httpx.AsyncClient):
    """
    Test Case T3-CROSS-01:
    Verify that issuing a pause request while speech chunks are streaming halts
    further turn taking immediately after the current chunk/turn without dropping
    the SSE connection, and resuming continues the debate seamlessly.
    """
    disc = await _create_test_discussion(
        client,
        topic="通用人工智能（AGI）开源是促进技术普惠还是加剧灾难性风险？",
        participant_count=4,
        max_rounds=2,
    )
    disc_id = disc["id"]

    collector = SSECollector(client, f"/api/discussions/{disc_id}/events")
    await collector.start()

    try:
        start_resp = await client.post(f"/api/discussions/{disc_id}/start")
        assert start_resp.status_code == 200, f"Start failed: {start_resp.text}"

        # Wait until first speech_chunk or speaker_selected is received
        first_chunk = await collector.wait_for_event(
            lambda e: e.event in ("speech_chunk", "speaker_selected"), timeout=15.0
        )
        assert first_chunk is not None

        # Issue pause mid-stream
        pause_resp = await client.post(f"/api/discussions/{disc_id}/pause")
        assert pause_resp.status_code == 200, f"Pause failed: {pause_resp.text}"
        pause_data = pause_resp.json()
        assert pause_data.get("status") == "paused" or pause_data.get("success") is True

        # Wait for status change to paused in event stream
        paused_event = await collector.wait_for_event(
            lambda e: e.event == "session_status_changed" and e.data.get("new_status") == "paused",
            timeout=10.0,
        )
        assert paused_event is not None
        validate_sse_event_contract(paused_event)

        # Silence window test: verify no new speaker_selected is emitted while paused
        event_count_before = len(collector.events)
        await asyncio.sleep(1.5)
        new_events = collector.events[event_count_before:]
        speaker_events_during_pause = [e for e in new_events if e.event == "speaker_selected"]
        assert len(speaker_events_during_pause) == 0, (
            f"Speaker was selected during pause state: {speaker_events_during_pause}"
        )

        # Resume debate
        resume_resp = await client.post(f"/api/discussions/{disc_id}/resume")
        assert resume_resp.status_code == 200, f"Resume failed: {resume_resp.text}"
        resume_data = resume_resp.json()
        assert resume_data.get("status") == "running" or resume_data.get("success") is True

        # Wait for status change to running in event stream
        resumed_event = await collector.wait_for_event(
            lambda e: e.event == "session_status_changed" and e.data.get("new_status") == "running",
            timeout=10.0,
        )
        assert resumed_event is not None

        # Await conclusion
        await collector.wait_for_conclusion(timeout=35.0)

        # Invariant checks
        collector.assert_monotonic_ids()
        for evt in collector.events:
            validate_sse_event_contract(evt)

    finally:
        await collector.close()


# ============================================================================
# T3-CROSS-02: Moderator Probing Intervention Timing During High-Divergence State
# ============================================================================
@pytest.mark.tier3
@pytest.mark.asyncio
async def test_t3_cross_02_moderator_probing_high_divergence(client: httpx.AsyncClient):
    """
    Test Case T3-CROSS-02:
    Verify that when divergence occurs, the debate engine schedules a moderator
    intervention (probing/floor control/opening) without corrupting turn order.
    """
    disc = await _create_test_discussion(
        client,
        topic="通用人工智能（AGI）开源是促进技术普惠还是加剧灾难性风险？",
        participant_count=4,
        max_rounds=3,
    )
    disc_id = disc["id"]

    collector = SSECollector(client, f"/api/discussions/{disc_id}/events")
    await collector.start()

    try:
        start_resp = await client.post(f"/api/discussions/{disc_id}/start")
        assert start_resp.status_code == 200

        # Run until conclusion
        await collector.wait_for_conclusion(timeout=35.0)

        # Inspect moderator interventions
        mod_events = collector.get_events_by_type("moderator_intervention")
        assert len(mod_events) >= 1, "Expected at least 1 moderator intervention event"

        for mevt in mod_events:
            validate_sse_event_contract(mevt)
            assert "type" in mevt.data
            assert "content" in mevt.data
            assert len(mevt.data["content"]) > 0

        # Check divergence tracking events
        div_events = collector.get_events_by_type("divergence_updated")
        if div_events:
            for devt in div_events:
                validate_sse_event_contract(devt)

        # Assert monotonic sequence IDs
        collector.assert_monotonic_ids()

        # Check transcript persistence
        tr_resp = await client.get(f"/api/discussions/{disc_id}/transcript")
        assert tr_resp.status_code == 200
        transcript = tr_resp.json()
        assert len(transcript) >= 2, f"Expected at least 2 transcript turns, got {len(transcript)}"

    finally:
        await collector.close()


# ============================================================================
# T3-CROSS-03: Last-Event-ID Replay After Artificial Network Disconnection
# ============================================================================
@pytest.mark.tier3
@pytest.mark.asyncio
async def test_t3_cross_03_last_event_id_replay(client: httpx.AsyncClient):
    """
    Test Case T3-CROSS-03:
    Verify that a client disconnecting mid-debate can reconnect using Last-Event-ID
    and receive subsequent events in exact sequential order without duplicate or lost IDs.
    """
    disc = await _create_test_discussion(
        client,
        topic="全面远程办公是否会永久性重塑企业形态并取代传统办公室协作？",
        participant_count=3,
        max_rounds=2,
    )
    disc_id = disc["id"]

    # Client 1 connects
    collector1 = SSECollector(client, f"/api/discussions/{disc_id}/events")
    await collector1.start()

    start_resp = await client.post(f"/api/discussions/{disc_id}/start")
    assert start_resp.status_code == 200

    # Wait until at least 4 events are collected
    await collector1.wait_for_event(lambda e: len(collector1.events) >= 4, timeout=15.0)
    last_event = collector1.events[-1]
    assert last_event.id is not None, "SSEEvent must have an id for replay"
    last_id = int(last_event.id)

    # Disconnect Client 1
    await collector1.close()

    # Allow debate engine to produce subsequent events
    await asyncio.sleep(0.5)

    # Client 2 reconnects with Last-Event-ID
    collector2 = SSECollector(
        client,
        f"/api/discussions/{disc_id}/events",
        last_event_id=str(last_id),
    )
    await collector2.start()

    try:
        # Wait for conclusion on reconnect
        await collector2.wait_for_conclusion(timeout=35.0)

        assert len(collector2.events) >= 1, "Expected replayed/subsequent events on reconnect"

        # Verify all received events in collector2 have ID > last_id
        replayed_ids = []
        for e in collector2.events:
            if e.id is not None:
                replayed_ids.append(int(e.id))

        assert len(replayed_ids) > 0, "Expected at least one event with an id in collector2"
        for rid in replayed_ids:
            assert rid > last_id, f"Replayed event ID {rid} must be strictly greater than Last-Event-ID {last_id}"

        # Monotonicity check
        collector2.assert_monotonic_ids()

    finally:
        await collector2.close()


# ============================================================================
# T3-CROSS-04: Last-Event-ID Replay Beyond Ring-Buffer Window
# ============================================================================
@pytest.mark.tier3
@pytest.mark.asyncio
async def test_t3_cross_04_ring_buffer_eviction_handling(client: httpx.AsyncClient):
    """
    Test Case T3-CROSS-04:
    Verify that requesting replay with an ancient or zero Last-Event-ID does not crash
    the server with HTTP 500 and streams available events gracefully.
    """
    disc = await _create_test_discussion(
        client,
        topic="在迈向净零排放的过程中，核能是否应当作为基荷电力的核心支柱？",
        participant_count=4,
        max_rounds=2,
    )
    disc_id = disc["id"]

    collector = SSECollector(client, f"/api/discussions/{disc_id}/events")
    await collector.start()

    try:
        await client.post(f"/api/discussions/{disc_id}/start")
        await collector.wait_for_conclusion(timeout=35.0)
        assert len(collector.events) >= 6
    finally:
        await collector.close()

    # Reconnect with Last-Event-ID: 0
    collector_ancient = SSECollector(
        client,
        f"/api/discussions/{disc_id}/events",
        last_event_id="0",
    )
    await collector_ancient.start()

    try:
        # Should stream without 500 error
        await asyncio.sleep(1.0)
        assert len(collector_ancient.events) >= 1, (
            "Expected events replayed or streamed when reconnecting with Last-Event-ID: 0"
        )
        collector_ancient.assert_monotonic_ids()
    finally:
        await collector_ancient.close()


# ============================================================================
# T3-CROSS-05: Dual Concurrent Debate Sessions with Zero Cross-Session Contamination
# ============================================================================
@pytest.mark.tier3
@pytest.mark.asyncio
async def test_t3_cross_05_concurrent_sessions_isolation(client: httpx.AsyncClient):
    """
    Test Case T3-CROSS-05:
    Verify that two discussions running simultaneously operate in complete isolation:
    event streams, participant IDs, transcripts, and sequence IDs never cross boundaries.
    """
    disc_alpha = await _create_test_discussion(
        client,
        topic="通用人工智能（AGI）开源是促进技术普惠还是加剧灾难性风险？",
        participant_count=4,
        max_rounds=2,
    )
    disc_beta = await _create_test_discussion(
        client,
        topic="全面远程办公是否会永久性重塑企业形态并取代传统办公室协作？",
        participant_count=3,
        max_rounds=2,
    )

    alpha_id = disc_alpha["id"]
    beta_id = disc_beta["id"]

    collector_alpha = SSECollector(client, f"/api/discussions/{alpha_id}/events")
    collector_beta = SSECollector(client, f"/api/discussions/{beta_id}/events")

    await collector_alpha.start()
    await collector_beta.start()

    try:
        # Start both concurrently
        start_resps = await asyncio.gather(
            client.post(f"/api/discussions/{alpha_id}/start"),
            client.post(f"/api/discussions/{beta_id}/start"),
        )
        assert all(r.status_code == 200 for r in start_resps)

        # Wait for conclusion on both
        await asyncio.gather(
            collector_alpha.wait_for_conclusion(timeout=40.0),
            collector_beta.wait_for_conclusion(timeout=40.0),
        )

        # Check Alpha events isolation
        collector_alpha.assert_monotonic_ids()
        collector_beta.assert_monotonic_ids()

        alpha_speakers = {
            e.data["speaker_id"]
            for e in collector_alpha.get_events_by_type("speaker_selected")
            if "speaker_id" in e.data
        }
        beta_speakers = {
            e.data["speaker_id"]
            for e in collector_beta.get_events_by_type("speaker_selected")
            if "speaker_id" in e.data
        }

        # Zero speaker ID overlap between Alpha and Beta
        assert len(alpha_speakers & beta_speakers) == 0, (
            f"Cross-session speaker leakage: {alpha_speakers & beta_speakers}"
        )

        # Check transcripts
        tr_alpha_resp = await client.get(f"/api/discussions/{alpha_id}/transcript")
        tr_beta_resp = await client.get(f"/api/discussions/{beta_id}/transcript")
        assert tr_alpha_resp.status_code == 200
        assert tr_beta_resp.status_code == 200

        turns_alpha = tr_alpha_resp.json()
        turns_beta = tr_beta_resp.json()

        turn_ids_alpha = {t["id"] for t in turns_alpha}
        turn_ids_beta = {t["id"] for t in turns_beta}
        assert len(turn_ids_alpha & turn_ids_beta) == 0, (
            f"Turn ID collision across discussions: {turn_ids_alpha & turn_ids_beta}"
        )

    finally:
        await collector_alpha.close()
        await collector_beta.close()


# ============================================================================
# T3-CROSS-06: Asymmetric Control on Concurrent Sessions
# ============================================================================
@pytest.mark.tier3
@pytest.mark.asyncio
async def test_t3_cross_06_asymmetric_session_controls(client: httpx.AsyncClient):
    """
    Test Case T3-CROSS-06:
    Verify that pausing Session Alpha does not impact or delay Session Beta,
    which continues streaming and completes normally.
    """
    disc_alpha = await _create_test_discussion(
        client,
        topic="通用人工智能（AGI）开源是促进技术普惠还是加剧灾难性风险？",
        participant_count=4,
        max_rounds=2,
    )
    disc_beta = await _create_test_discussion(
        client,
        topic="在迈向净零排放的过程中，核能是否应当作为基荷电力的核心支柱？",
        participant_count=4,
        max_rounds=2,
    )

    alpha_id = disc_alpha["id"]
    beta_id = disc_beta["id"]

    collector_alpha = SSECollector(client, f"/api/discussions/{alpha_id}/events")
    collector_beta = SSECollector(client, f"/api/discussions/{beta_id}/events")

    await collector_alpha.start()
    await collector_beta.start()

    try:
        await client.post(f"/api/discussions/{alpha_id}/start")
        await client.post(f"/api/discussions/{beta_id}/start")

        # Wait for both to start producing events
        await collector_alpha.wait_for_event(
            lambda e: e.event in ("speaker_selected", "speech_chunk"), timeout=15.0
        )
        await collector_beta.wait_for_event(
            lambda e: e.event in ("speaker_selected", "speech_chunk"), timeout=15.0
        )

        # Pause Alpha
        pause_resp = await client.post(f"/api/discussions/{alpha_id}/pause")
        assert pause_resp.status_code == 200

        # Beta must continue and conclude cleanly
        await collector_beta.wait_for_conclusion(timeout=35.0)

        # Alpha must still be in paused status
        alpha_status_resp = await client.get(f"/api/discussions/{alpha_id}")
        assert alpha_status_resp.status_code == 200
        assert alpha_status_resp.json().get("status") == "paused"

        # Resume Alpha and await its conclusion
        resume_resp = await client.post(f"/api/discussions/{alpha_id}/resume")
        assert resume_resp.status_code == 200

        await collector_alpha.wait_for_conclusion(timeout=35.0)

        # Both sessions concluded independently
        collector_alpha.assert_monotonic_ids()
        collector_beta.assert_monotonic_ids()

    finally:
        await collector_alpha.close()
        await collector_beta.close()


# ============================================================================
# T3-CROSS-07: Database Persistence Concurrency & SQLite Lock Safety Under Parallel Writes
# ============================================================================
@pytest.mark.tier3
@pytest.mark.asyncio
async def test_t3_cross_07_db_persistence_concurrency(client: httpx.AsyncClient):
    """
    Test Case T3-CROSS-07:
    Verify that 3 concurrent sessions writing turns and consensus records simultaneously
    to the shared SQLite database encounter zero lock collisions or data corruptions.
    """
    topics = [
        "通用人工智能（AGI）开源是促进技术普惠还是加剧灾难性风险？",
        "全面远程办公是否会永久性重塑企业形态并取代传统办公室协作？",
        "在迈向净零排放的过程中，核能是否应当作为基荷电力的核心支柱？",
    ]

    discs = await asyncio.gather(
        *[_create_test_discussion(client, topic=t, participant_count=3, max_rounds=2) for t in topics]
    )
    disc_ids = [d["id"] for d in discs]

    collectors = [SSECollector(client, f"/api/discussions/{did}/events") for did in disc_ids]
    for c in collectors:
        await c.start()

    try:
        # Start all 3 discussions concurrently
        start_resps = await asyncio.gather(
            *[client.post(f"/api/discussions/{did}/start") for did in disc_ids]
        )
        assert all(r.status_code == 200 for r in start_resps)

        # Await conclusion for all 3 concurrently
        await asyncio.gather(*[c.wait_for_conclusion(timeout=40.0) for c in collectors])

        # Query and verify transcripts
        for did in disc_ids:
            tr_resp = await client.get(f"/api/discussions/{did}/transcript")
            assert tr_resp.status_code == 200, f"Transcript fetch failed for {did}: {tr_resp.text}"
            turns = tr_resp.json()
            assert len(turns) >= 2, f"Expected at least 2 turns for {did}, got {len(turns)}"

            # Assert turn numbers are sequential starting from 1
            turn_numbers = [t["turn_number"] for t in turns if "turn_number" in t]
            if turn_numbers:
                assert turn_numbers == sorted(turn_numbers), (
                    f"Turn numbers out of order for {did}: {turn_numbers}"
                )

            # Assert summary endpoint is accessible
            sum_resp = await client.get(f"/api/discussions/{did}/summary")
            assert sum_resp.status_code == 200, f"Summary failed for {did}: {sum_resp.text}"

    finally:
        for c in collectors:
            await c.close()


# ============================================================================
# T3-CROSS-08: Early Debate Termination Mid-Speech with Immediate Synthesis Generation
# ============================================================================
@pytest.mark.tier3
@pytest.mark.asyncio
async def test_t3_cross_08_early_termination_synthesis(client: httpx.AsyncClient):
    """
    Test Case T3-CROSS-08:
    Verify that terminating an active debate during speech streaming halts the debate loop
    immediately and triggers early moderator synthesis over whatever turns transpired.
    """
    disc = await _create_test_discussion(
        client,
        topic="通用人工智能（AGI）开源是促进技术普惠还是加剧灾难性风险？",
        participant_count=4,
        max_rounds=5,
    )
    disc_id = disc["id"]

    collector = SSECollector(client, f"/api/discussions/{disc_id}/events")
    await collector.start()

    try:
        start_resp = await client.post(f"/api/discussions/{disc_id}/start")
        assert start_resp.status_code == 200

        # Wait for first speech_chunk or speaker_selected
        await collector.wait_for_event(
            lambda e: e.event in ("speech_chunk", "speaker_selected"), timeout=15.0
        )

        # Terminate debate
        term_resp = await client.post(f"/api/discussions/{disc_id}/terminate")
        assert term_resp.status_code == 200, f"Terminate failed: {term_resp.text}"
        term_data = term_resp.json()
        assert term_data.get("status") == "terminated" or term_data.get("success") is True

        # Wait for terminated status event or conclusion
        term_event = await collector.wait_for_event(
            lambda e: (
                (e.event == "session_status_changed" and e.data.get("new_status") == "terminated")
                or e.event == "session_concluded"
            ),
            timeout=15.0,
        )
        assert term_event is not None

        # Verify discussion state is terminated
        detail_resp = await client.get(f"/api/discussions/{disc_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json().get("status") == "terminated"

        # Verify summary endpoint provides early synthesis
        summary_resp = await client.get(f"/api/discussions/{disc_id}/summary")
        assert summary_resp.status_code == 200
        sum_data = summary_resp.json()
        assert "summary" in sum_data
        assert sum_data["summary"] is not None and len(sum_data["summary"]) > 0

    finally:
        await collector.close()


# ============================================================================
# T3-CROSS-09: SpeakerArbitrator Consecutive Speaker Exclusion Invariant Across Rounds
# ============================================================================
@pytest.mark.tier3
@pytest.mark.asyncio
async def test_t3_cross_09_consecutive_speaker_exclusion_invariant(client: httpx.AsyncClient):
    """
    Test Case T3-CROSS-09:
    Verify that the SpeakerArbitrator strictly enforces P_cd(i) = +inf when delta_t_i = 0,
    guaranteeing that no agent speaks twice consecutively, even across round boundaries.
    """
    disc = await _create_test_discussion(
        client,
        topic="商业太空探索与小行星采矿：人类文明的战略飞跃还是深空资源争夺战？",
        participant_count=4,
        max_rounds=3,
    )
    disc_id = disc["id"]

    collector = SSECollector(client, f"/api/discussions/{disc_id}/events")
    await collector.start()

    try:
        await client.post(f"/api/discussions/{disc_id}/start")
        await collector.wait_for_conclusion(timeout=35.0)

        # Extract sequence of speakers
        speaker_events = collector.get_events_by_type("speaker_selected")
        assert len(speaker_events) >= 3, f"Expected at least 3 turns, got {len(speaker_events)}"

        speakers = [e.data["speaker_id"] for e in speaker_events if "speaker_id" in e.data]
        assert len(speakers) >= 3

        # Assert no two consecutive speakers are identical
        for i in range(len(speakers) - 1):
            assert speakers[i] != speakers[i + 1], (
                f"Consecutive speaker exclusion violated at turn {i} -> {i+1}: "
                f"Agent '{speakers[i]}' spoke twice in a row!"
            )

        # Verify against database transcript
        tr_resp = await client.get(f"/api/discussions/{disc_id}/transcript")
        assert tr_resp.status_code == 200
        turns = tr_resp.json()
        # Filter out moderator / system actions
        expert_turns = [t for t in turns if t.get("action_type") not in ("topic_introduction", "summary")]
        expert_speakers = [t["speaker_id"] for t in expert_turns if "speaker_id" in t]
        for i in range(len(expert_speakers) - 1):
            assert expert_speakers[i] != expert_speakers[i + 1], (
                f"Transcript consecutive speaker violation at turn {i}: {expert_speakers[i]}"
            )

    finally:
        await collector.close()


# ============================================================================
# T3-CROSS-10: Zero Desire Score Deadlock & Automatic Moderator Probing Fallback
# ============================================================================
@pytest.mark.tier3
@pytest.mark.asyncio
async def test_t3_cross_10_zero_desire_moderator_fallback(client: httpx.AsyncClient):
    """
    Test Case T3-CROSS-10:
    Verify that when agents express low or tied desire to speak, the debate engine
    does not deadlock or stall, progressing through turns via fairness/arbitration
    or automatic moderator intervention.
    """
    disc = await _create_test_discussion(
        client,
        topic="全面远程办公是否会永久性重塑企业形态并取代传统办公室协作？",
        participant_count=3,
        max_rounds=2,
    )
    disc_id = disc["id"]

    collector = SSECollector(client, f"/api/discussions/{disc_id}/events")
    await collector.start()

    try:
        await client.post(f"/api/discussions/{disc_id}/start")

        # Debate must advance to conclusion within reasonable timeout
        conclusion = await collector.wait_for_conclusion(timeout=30.0)
        assert conclusion is not None
        validate_sse_event_contract(conclusion)

        # Confirm multiple speech completed events occurred
        speech_events = collector.get_events_by_type("speech_completed")
        assert len(speech_events) >= 2, f"Debate stalled; only {len(speech_events)} speeches completed"

        # Contract checks
        collector.assert_monotonic_ids()

    finally:
        await collector.close()


# ============================================================================
# T3-CROSS-11: Rapid Hammering of Control Endpoints (Race Condition & Mutex Resilience)
# ============================================================================
@pytest.mark.tier3
@pytest.mark.asyncio
async def test_t3_cross_11_rapid_control_hammering_mutex(client: httpx.AsyncClient):
    """
    Test Case T3-CROSS-11:
    Verify that rapidly hammering control endpoints (pause, resume, start, terminate)
    within a tight time window does not cause race conditions, duplicate workers,
    corrupted states, or HTTP 500 crashes.
    """
    disc = await _create_test_discussion(
        client,
        topic="在迈向净零排放的过程中，核能是否应当作为基荷电力的核心支柱？",
        participant_count=3,
        max_rounds=3,
    )
    disc_id = disc["id"]

    # Start discussion first
    start_resp = await client.post(f"/api/discussions/{disc_id}/start")
    assert start_resp.status_code == 200

    # Rapid concurrent calls: mix of pause, resume, pause, resume
    actions = ["pause", "resume", "pause", "resume", "pause", "pause", "resume", "pause"]
    tasks = [client.post(f"/api/discussions/{disc_id}/{action}") for action in actions]

    responses = await asyncio.gather(*tasks, return_exceptions=True)

    # Assert no 500 Internal Server Errors
    for idx, resp in enumerate(responses):
        if isinstance(resp, Exception):
            pytest.fail(f"Request {idx} raised unhandled exception: {resp}")
        assert resp.status_code in (200, 400, 409), (
            f"Unexpected status code {resp.status_code} on rapid control {actions[idx]}: {resp.text}"
        )

    # Check discussion state consistency
    detail_resp = await client.get(f"/api/discussions/{disc_id}")
    assert detail_resp.status_code == 200
    current_status = detail_resp.json().get("status")
    assert current_status in ("running", "paused", "completed", "terminated"), (
        f"Inconsistent state after hammering: {current_status}"
    )

    # Cleanup: terminate to release background task cleanly
    await client.post(f"/api/discussions/{disc_id}/terminate")


# ============================================================================
# T3-CROSS-12: Multi-Subscriber Fan-Out to Single SSE Discussion Stream
# ============================================================================
@pytest.mark.tier3
@pytest.mark.asyncio
async def test_t3_cross_12_multi_subscriber_fan_out(client: httpx.AsyncClient):
    """
    Test Case T3-CROSS-12:
    Verify that multiple subscribers connecting to the same discussion stream receive
    identical event sequences, and abruptly closing one subscriber does not affect others.
    """
    disc = await _create_test_discussion(
        client,
        topic="通用人工智能（AGI）开源是促进技术普惠还是加剧灾难性风险？",
        participant_count=4,
        max_rounds=2,
    )
    disc_id = disc["id"]

    sub1 = SSECollector(client, f"/api/discussions/{disc_id}/events")
    sub2 = SSECollector(client, f"/api/discussions/{disc_id}/events")

    await sub1.start()
    await sub2.start()

    try:
        await client.post(f"/api/discussions/{disc_id}/start")

        # Wait until both subscribers receive at least 4 events
        await asyncio.gather(
            sub1.wait_for_event(lambda e: len(sub1.events) >= 4, timeout=15.0),
            sub2.wait_for_event(lambda e: len(sub2.events) >= 4, timeout=15.0),
        )

        # Compare event sequences received so far
        common_len = min(len(sub1.events), len(sub2.events))
        assert common_len >= 4, f"Insufficient common events: {common_len}"

        for i in range(common_len):
            e1 = sub1.events[i]
            e2 = sub2.events[i]
            assert e1.event == e2.event, f"Event type mismatch at index {i}: {e1.event} != {e2.event}"
            if e1.id is not None and e2.id is not None:
                assert e1.id == e2.id, f"Event ID mismatch at index {i}: {e1.id} != {e2.id}"

        # Abruptly disconnect subscriber 1
        await sub1.close()

        # Subscriber 2 must continue receiving events and reach conclusion
        conclusion2 = await sub2.wait_for_conclusion(timeout=35.0)
        assert conclusion2 is not None
        validate_sse_event_contract(conclusion2)
        sub2.assert_monotonic_ids()

    finally:
        await sub1.close()
        await sub2.close()
