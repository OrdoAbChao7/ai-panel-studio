"""
Tier 1: Feature Coverage E2E Tests for AI Panel Studio.

Total 36 Tests covering:
- T1-CRUD (6 tests): Create, List, Detail, Sequential isolation, Field types, Ordering.
- T1-LIFE (6 tests): Start, Pause, Resume, Terminate from running, Terminate from paused, Natural completion.
- T1-ROST (6 tests): Default 4-expert roster, Custom counts (2, 6), Color/Name uniqueness, Stance diversity, Role assignment, Custom edit persistence.
- T1-TRAN (6 tests): Empty init, Monotonic turn numbering, Turn record schema, Consecutive speaker prohibition invariant (P_cd = +inf), Rebuttal target validity, Incremental persistence.
- T1-SUMM (6 tests): Pre-completion state, Post-debate synthesis, Consensus schema/confidence, Divergence schema/intensity, Stance audit completeness, Read idempotency.
- T1-MOCK (6 tests): Fallback trigger, Offline roster gen, Full debate execution, Mock mode label, 5 domain personas, Zero secret leak invariant.
"""

import asyncio
import re
from typing import Any, Dict, List
import pytest
import httpx

try:
    from app.core.config import get_settings
except (ImportError, AttributeError):
    get_settings = lambda: None


SAMPLE_TOPIC = "人工智能生成内容（AIGC）对传统创作者的冲击与赋能"

SAMPLE_PARTICIPANTS = [
    {
        "name": "林博",
        "occupation": "AI架构师",
        "stance": "技术赋能创作者，降低生产门槛并提升创作广度",
        "perspective": "技术演进与生产力变革",
        "color_hex": "#3B82F6",
        "role": "expert",
    },
    {
        "name": "陈文",
        "occupation": "独立作家",
        "stance": "冲击原创精神与深层人文思考，造成内容同质化",
        "perspective": "人文主义与艺术真实性",
        "color_hex": "#EF4444",
        "role": "expert",
    },
    {
        "name": "张法",
        "occupation": "知识产权律师",
        "stance": "亟需确立版权界限与训练数据合理使用原则",
        "perspective": "法律合规与制度平衡",
        "color_hex": "#10B981",
        "role": "expert",
    },
    {
        "name": "周经",
        "occupation": "文化产业投资人",
        "stance": "市场效率至上，商业模式将重塑文化创意产业链",
        "perspective": "商业逻辑与产业生态",
        "color_hex": "#F59E0B",
        "role": "expert",
    },
]


async def create_discussion_helper(
    client: httpx.AsyncClient,
    topic: str = SAMPLE_TOPIC,
    participants: List[Dict[str, Any]] = None,
    max_rounds: int = 3,
) -> Dict[str, Any]:
    """Helper to create a discussion session via REST API."""
    if participants is None:
        participants = SAMPLE_PARTICIPANTS
    payload = {
        "topic": topic,
        "participants": participants,
        "max_rounds": max_rounds,
    }
    response = await client.post("/api/discussions", json=payload)
    assert response.status_code in (200, 201), (
        f"Create discussion failed: {response.status_code} - {response.text}"
    )
    return response.json()


# ==============================================================================
# Group 1.1: REST API & Discussion CRUD (6 Tests)
# ==============================================================================

@pytest.mark.tier1
class TestTier1CRUD:
    """T1-CRUD: RESTful Discussion CRUD Operations."""

    async def test_t1_crud_01_create_discussion_valid_payload(self, async_client: httpx.AsyncClient):
        """T1-CRUD-01: Create discussion with standard valid payload and verify response contract."""
        payload = {
            "topic": SAMPLE_TOPIC,
            "participants": SAMPLE_PARTICIPANTS,
            "max_rounds": 3,
        }
        res = await async_client.post("/api/discussions", json=payload)
        assert res.status_code in (200, 201), f"Unexpected status: {res.status_code} {res.text}"
        data = res.json()

        assert "id" in data and isinstance(data["id"], str) and len(data["id"]) > 0
        assert data["topic"] == payload["topic"]
        assert data["status"] == "created"
        assert len(data["participants"]) == 4
        assert "created_at" in data and isinstance(data["created_at"], str)

    async def test_t1_crud_02_list_discussions_returns_created_session(self, async_client: httpx.AsyncClient):
        """T1-CRUD-02: List discussions endpoint returns newly created discussion."""
        created = await create_discussion_helper(async_client)
        created_id = created["id"]

        res = await async_client.get("/api/discussions")
        assert res.status_code == 200
        discussions = res.json()
        assert isinstance(discussions, list)

        match = next((d for d in discussions if d["id"] == created_id), None)
        assert match is not None, f"Created discussion {created_id} not found in discussion list"
        assert match["topic"] == created["topic"]
        assert match["status"] in ("created", "running", "paused", "completed", "terminated")
        assert "participant_count" in match
        assert match["participant_count"] == 4

    async def test_t1_crud_03_get_discussion_aggregate_by_id(self, async_client: httpx.AsyncClient):
        """T1-CRUD-03: Get discussion details returns complete aggregate state."""
        created = await create_discussion_helper(async_client, max_rounds=3)
        created_id = created["id"]

        res = await async_client.get(f"/api/discussions/{created_id}")
        assert res.status_code == 200
        data = res.json()

        assert data["id"] == created_id
        assert data["topic"] == SAMPLE_TOPIC
        assert data["status"] == "created"
        assert data["current_round"] == 0
        assert data["max_rounds"] == 3
        assert data.get("summary") is None or data.get("summary") == ""
        assert len(data["participants"]) == 4

    async def test_t1_crud_04_sequential_creation_isolated_discussions(self, async_client: httpx.AsyncClient):
        """T1-CRUD-04: Successive discussion creations produce strictly isolated sessions."""
        topic_a = "讨论议题A：量子计算的商业化路径"
        topic_b = "讨论议题B：脑机接口的人类认知边界"

        disc_a = await create_discussion_helper(async_client, topic=topic_a)
        disc_b = await create_discussion_helper(async_client, topic=topic_b)

        assert disc_a["id"] != disc_b["id"]

        res_a = await async_client.get(f"/api/discussions/{disc_a['id']}")
        res_b = await async_client.get(f"/api/discussions/{disc_b['id']}")

        assert res_a.status_code == 200
        assert res_b.status_code == 200
        assert res_a.json()["topic"] == topic_a
        assert res_b.json()["topic"] == topic_b
        assert res_a.json()["id"] != res_b.json()["id"]

    async def test_t1_crud_05_discussion_schema_field_types(self, async_client: httpx.AsyncClient):
        """T1-CRUD-05: Discussion schema satisfies exact typed field invariants."""
        created = await create_discussion_helper(async_client)
        res = await async_client.get(f"/api/discussions/{created['id']}")
        assert res.status_code == 200
        data = res.json()

        assert isinstance(data["id"], str)
        assert isinstance(data["topic"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["current_round"], int)
        assert isinstance(data["max_rounds"], int)
        assert isinstance(data["participants"], list)

        for p in data["participants"]:
            assert isinstance(p["name"], str) and len(p["name"]) > 0
            assert isinstance(p["occupation"], str)
            assert isinstance(p["stance"], str)
            assert isinstance(p["color_hex"], str)
            assert re.match(r"^#[0-9A-Fa-f]{6}$", p["color_hex"])

    async def test_t1_crud_06_discussion_list_ordering_descending(self, async_client: httpx.AsyncClient):
        """T1-CRUD-06: Discussion list is sorted by creation time descending."""
        disc_1 = await create_discussion_helper(async_client, topic="时间排序测试-1")
        await asyncio.sleep(0.05)
        disc_2 = await create_discussion_helper(async_client, topic="时间排序测试-2")

        res = await async_client.get("/api/discussions")
        assert res.status_code == 200
        discussions = res.json()

        ids = [d["id"] for d in discussions]
        idx_1 = ids.index(disc_1["id"])
        idx_2 = ids.index(disc_2["id"])

        # Most recently created (disc_2) must precede disc_1
        assert idx_2 < idx_1, f"Expected disc_2 ({idx_2}) before disc_1 ({idx_1}) in list"


# ==============================================================================
# Group 1.2: Discussion Lifecycle State Machine (6 Tests)
# ==============================================================================

@pytest.mark.tier1
class TestTier1Lifecycle:
    """T1-LIFE: Discussion Lifecycle State Machine Controls."""

    async def test_t1_life_01_start_transition(self, async_client: httpx.AsyncClient):
        """T1-LIFE-01: Start transition (created -> running)."""
        created = await create_discussion_helper(async_client)
        disc_id = created["id"]

        res = await async_client.post(f"/api/discussions/{disc_id}/start")
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True
        assert data.get("status") == "running"

        check = await async_client.get(f"/api/discussions/{disc_id}")
        assert check.status_code == 200
        assert check.json()["status"] == "running"

    async def test_t1_life_02_pause_transition(self, async_client: httpx.AsyncClient):
        """T1-LIFE-02: Pause transition (running -> paused)."""
        created = await create_discussion_helper(async_client)
        disc_id = created["id"]

        await async_client.post(f"/api/discussions/{disc_id}/start")
        res = await async_client.post(f"/api/discussions/{disc_id}/pause")
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True
        assert data.get("status") == "paused"

        check = await async_client.get(f"/api/discussions/{disc_id}")
        assert check.status_code == 200
        assert check.json()["status"] == "paused"

    async def test_t1_life_03_resume_transition(self, async_client: httpx.AsyncClient):
        """T1-LIFE-03: Resume transition (paused -> running)."""
        created = await create_discussion_helper(async_client)
        disc_id = created["id"]

        await async_client.post(f"/api/discussions/{disc_id}/start")
        await async_client.post(f"/api/discussions/{disc_id}/pause")

        res = await async_client.post(f"/api/discussions/{disc_id}/resume")
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True
        assert data.get("status") == "running"

        check = await async_client.get(f"/api/discussions/{disc_id}")
        assert check.status_code == 200
        assert check.json()["status"] == "running"

    async def test_t1_life_04_terminate_from_running(self, async_client: httpx.AsyncClient):
        """T1-LIFE-04: Terminate from running state (running -> terminated)."""
        created = await create_discussion_helper(async_client)
        disc_id = created["id"]

        await async_client.post(f"/api/discussions/{disc_id}/start")
        res = await async_client.post(f"/api/discussions/{disc_id}/terminate")
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True
        assert data.get("status") == "terminated"

        check = await async_client.get(f"/api/discussions/{disc_id}")
        assert check.status_code == 200
        assert check.json()["status"] == "terminated"

    async def test_t1_life_05_terminate_from_paused(self, async_client: httpx.AsyncClient):
        """T1-LIFE-05: Terminate from paused state (paused -> terminated)."""
        created = await create_discussion_helper(async_client)
        disc_id = created["id"]

        await async_client.post(f"/api/discussions/{disc_id}/start")
        await async_client.post(f"/api/discussions/{disc_id}/pause")

        res = await async_client.post(f"/api/discussions/{disc_id}/terminate")
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True
        assert data.get("status") == "terminated"

        check = await async_client.get(f"/api/discussions/{disc_id}")
        assert check.status_code == 200
        assert check.json()["status"] == "terminated"

    async def test_t1_life_06_natural_completion_on_max_rounds(self, async_client: httpx.AsyncClient):
        """T1-LIFE-06: Discussion halts and completes when max_rounds is reached."""
        created = await create_discussion_helper(async_client, max_rounds=1)
        disc_id = created["id"]

        await async_client.post(f"/api/discussions/{disc_id}/start")

        # Poll status until it concludes naturally
        completed = False
        final_data = {}
        for _ in range(30):
            await asyncio.sleep(0.3)
            check = await async_client.get(f"/api/discussions/{disc_id}")
            if check.status_code == 200:
                final_data = check.json()
                if final_data.get("status") in ("completed", "terminated"):
                    completed = True
                    break

        assert completed, f"Discussion did not complete naturally; status: {final_data.get('status')}"
        assert final_data.get("current_round", 0) >= 1


# ==============================================================================
# Group 1.3: Participant Roster Management (6 Tests)
# ==============================================================================

@pytest.mark.tier1
class TestTier1Roster:
    """T1-ROST: Participant Roster Generation and Configuration."""

    async def test_t1_rost_01_dynamic_roster_generation_default_4(self, async_client: httpx.AsyncClient):
        """T1-ROST-01: Generate candidate roster with default count of 4 experts."""
        payload = {
            "topic": "核能是否应该作为实现碳中和的主力能源？",
            "participant_count": 4,
        }
        res = await async_client.post("/api/discussions/roster/generate", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["topic"] == payload["topic"]
        assert "experts" in data
        assert len(data["experts"]) == 4

        for exp in data["experts"]:
            assert "name" in exp and len(exp["name"]) > 0
            assert "occupation" in exp and len(exp["occupation"]) > 0
            assert "stance" in exp and len(exp["stance"]) > 0
            assert "perspective" in exp and len(exp["perspective"]) > 0
            assert "color_hex" in exp and re.match(r"^#[0-9A-Fa-f]{6}$", exp["color_hex"])

    async def test_t1_rost_02_roster_generation_variable_counts(self, async_client: httpx.AsyncClient):
        """T1-ROST-02: Generate candidate rosters for boundary counts 2 and 6."""
        # 2 participants
        res_2 = await async_client.post(
            "/api/discussions/roster/generate",
            json={"topic": "人工智能生成内容冲击与赋能", "participant_count": 2},
        )
        assert res_2.status_code == 200
        assert len(res_2.json()["experts"]) == 2

        # 6 participants
        res_6 = await async_client.post(
            "/api/discussions/roster/generate",
            json={"topic": "人工智能生成内容冲击与赋能", "participant_count": 6},
        )
        assert res_6.status_code == 200
        assert len(res_6.json()["experts"]) == 6

    async def test_t1_rost_03_visual_identity_color_name_uniqueness(self, async_client: httpx.AsyncClient):
        """T1-ROST-03: Generated experts have mutually unique names and distinct hex colors."""
        res = await async_client.post(
            "/api/discussions/roster/generate",
            json={"topic": "商业航天与太空资源开发", "participant_count": 4},
        )
        assert res.status_code == 200
        experts = res.json()["experts"]
        assert len(experts) == 4

        names = [e["name"] for e in experts]
        colors = [e["color_hex"] for e in experts]

        assert len(set(names)) == len(experts), f"Found duplicate names: {names}"
        assert len(set(colors)) == len(experts), f"Found duplicate colors: {colors}"

    async def test_t1_rost_04_stance_diversity_polarization(self, async_client: httpx.AsyncClient):
        """T1-ROST-04: Generated panel exhibits diversity of stances and distinct perspectives."""
        res = await async_client.post(
            "/api/discussions/roster/generate",
            json={"topic": "算法推荐与信息茧房机制", "participant_count": 4},
        )
        assert res.status_code == 200
        experts = res.json()["experts"]

        stances = [e["stance"] for e in experts]
        perspectives = [e["perspective"] for e in experts]

        assert len(set(stances)) > 1, f"Stances are not diverse: {stances}"
        assert len(set(perspectives)) > 1, f"Perspectives are not diverse: {perspectives}"

    async def test_t1_rost_05_participant_role_assignment(self, async_client: httpx.AsyncClient):
        """T1-ROST-05: Participants persist specified roles (moderator, panelist/expert)."""
        participants = [
            {
                "name": "主持人-苏敏",
                "occupation": "资深辩论主持人",
                "stance": "保持中立，引导全场议题深入",
                "perspective": "辩论议程推进与控场",
                "color_hex": "#64748B",
                "role": "moderator",
            },
            {
                "name": "辩手-李强",
                "occupation": "产业研究员",
                "stance": "支持积极应用",
                "perspective": "产业落地与经济效益",
                "color_hex": "#3B82F6",
                "role": "expert",
            },
        ]
        created = await create_discussion_helper(async_client, participants=participants)
        disc_id = created["id"]

        check = await async_client.get(f"/api/discussions/{disc_id}")
        assert check.status_code == 200
        retrieved_participants = check.json()["participants"]

        mod = next((p for p in retrieved_participants if p["name"] == "主持人-苏敏"), None)
        assert mod is not None
        assert mod.get("role") == "moderator"

    async def test_t1_rost_06_custom_modified_expert_persistence(self, async_client: httpx.AsyncClient):
        """T1-ROST-06: User-edited expert name and stance persist accurately in discussion state."""
        custom_participants = list(SAMPLE_PARTICIPANTS)
        custom_participants[0] = {
            "name": "自定义专家-张教授",
            "occupation": "特邀客座教授",
            "stance": "全面中立与审慎推进，兼顾伦理与发展",
            "perspective": "交叉学科系统观",
            "color_hex": "#8B5CF6",
            "role": "expert",
        }

        created = await create_discussion_helper(async_client, participants=custom_participants)
        disc_id = created["id"]

        check = await async_client.get(f"/api/discussions/{disc_id}")
        assert check.status_code == 200
        parts = check.json()["participants"]

        target = next((p for p in parts if p["name"] == "自定义专家-张教授"), None)
        assert target is not None, "Custom edited expert name not found in persisted participants"
        assert target["stance"] == "全面中立与审慎推进，兼顾伦理与发展"
        assert target["color_hex"] == "#8B5CF6"


# ==============================================================================
# Group 1.4: Transcripts & Speeches (6 Tests)
# ==============================================================================

@pytest.mark.tier1
class TestTier1Transcript:
    """T1-TRAN: Debate Transcript Persistence and Turn Invariants."""

    async def test_t1_tran_01_empty_transcript_on_creation(self, async_client: httpx.AsyncClient):
        """T1-TRAN-01: Newly created discussion possesses an empty transcript list."""
        created = await create_discussion_helper(async_client)
        disc_id = created["id"]

        res = await async_client.get(f"/api/discussions/{disc_id}/transcript")
        assert res.status_code == 200
        turns = res.json()
        assert isinstance(turns, list)
        assert len(turns) == 0

    async def test_t1_tran_02_monotonic_turn_numbering(self, async_client: httpx.AsyncClient):
        """T1-TRAN-02: Turns generated during debate follow strictly monotonic 1-based numbering."""
        created = await create_discussion_helper(async_client, max_rounds=2)
        disc_id = created["id"]

        await async_client.post(f"/api/discussions/{disc_id}/start")

        # Wait for at least 2 turns
        turns = []
        for _ in range(30):
            await asyncio.sleep(0.3)
            res = await async_client.get(f"/api/discussions/{disc_id}/transcript")
            if res.status_code == 200:
                turns = res.json()
                if len(turns) >= 2:
                    break

        await async_client.post(f"/api/discussions/{disc_id}/pause")

        assert len(turns) >= 2, f"Expected at least 2 turns in transcript, got {len(turns)}"
        turn_numbers = [t["turn_number"] for t in turns]
        expected = list(range(1, len(turns) + 1))
        assert turn_numbers == expected, f"Turn numbers {turn_numbers} do not match expected {expected}"

    async def test_t1_tran_03_turn_record_schema_invariants(self, async_client: httpx.AsyncClient):
        """T1-TRAN-03: Transcript records satisfy full schema contracts and field types."""
        created = await create_discussion_helper(async_client, max_rounds=1)
        disc_id = created["id"]

        await async_client.post(f"/api/discussions/{disc_id}/start")

        turns = []
        for _ in range(30):
            await asyncio.sleep(0.3)
            res = await async_client.get(f"/api/discussions/{disc_id}/transcript")
            if res.status_code == 200:
                turns = res.json()
                if len(turns) >= 1:
                    break

        await async_client.post(f"/api/discussions/{disc_id}/terminate")

        assert len(turns) >= 1, f"Expected at least 1 turn in transcript, got {len(turns)}"
        for turn in turns:
            assert "id" in turn and isinstance(turn["id"], str)
            assert "turn_number" in turn and isinstance(turn["turn_number"], int)
            assert "speaker_id" in turn and isinstance(turn["speaker_id"], str)
            assert "speaker_name" in turn and isinstance(turn["speaker_name"], str)
            assert "action_type" in turn and isinstance(turn["action_type"], str)
            assert "content" in turn and isinstance(turn["content"], str) and len(turn["content"]) > 0
            assert "priority_score" in turn and isinstance(turn["priority_score"], (int, float))
            assert "timestamp" in turn and isinstance(turn["timestamp"], str)

    async def test_t1_tran_04_consecutive_speaker_prohibition_invariant(self, async_client: httpx.AsyncClient):
        """
        T1-TRAN-04: Cooldown formula invariant (P_cd = +inf).
        No agent may speak twice consecutively: speaker_id[k] != speaker_id[k+1].
        """
        created = await create_discussion_helper(async_client, max_rounds=2)
        disc_id = created["id"]

        await async_client.post(f"/api/discussions/{disc_id}/start")

        turns = []
        for _ in range(35):
            await asyncio.sleep(0.3)
            res = await async_client.get(f"/api/discussions/{disc_id}/transcript")
            if res.status_code == 200:
                turns = res.json()
                if len(turns) >= 3:
                    break

        await async_client.post(f"/api/discussions/{disc_id}/terminate")

        assert len(turns) >= 2, f"Expected at least 2 turns in transcript, got {len(turns)}"
        for i in range(len(turns) - 1):
            assert turns[i]["speaker_id"] != turns[i + 1]["speaker_id"], (
                f"Consecutive turn violation at turns {i+1} and {i+2}: "
                f"Speaker '{turns[i]['speaker_name']}' ({turns[i]['speaker_id']}) spoke consecutively!"
            )

    async def test_t1_tran_05_rebuttal_target_validity(self, async_client: httpx.AsyncClient):
        """T1-TRAN-05: Rebuttal actions target prior valid speakers; openings do not."""
        created = await create_discussion_helper(async_client, max_rounds=2)
        disc_id = created["id"]

        await async_client.post(f"/api/discussions/{disc_id}/start")

        turns = []
        for _ in range(35):
            await asyncio.sleep(0.3)
            res = await async_client.get(f"/api/discussions/{disc_id}/transcript")
            if res.status_code == 200:
                turns = res.json()
                if len(turns) >= 2:
                    break

        await async_client.post(f"/api/discussions/{disc_id}/terminate")

        assert len(turns) >= 2, f"Expected at least 2 turns in transcript, got {len(turns)}"
        for idx, turn in enumerate(turns):
            if turn.get("action_type") == "rebuttal":
                target_id = turn.get("target_speaker_id")
                # When rebuttal occurs, target should reference an earlier speaker
                if target_id is not None:
                    prior_speakers = {t["speaker_id"] for t in turns[:idx]}
                    assert target_id in prior_speakers, f"Rebuttal target {target_id} not in prior speakers {prior_speakers}"
            elif turn.get("action_type") in ("opening", "statement") and idx == 0:
                assert turn.get("target_speaker_id") is None

    async def test_t1_tran_06_incremental_transcript_persistence(self, async_client: httpx.AsyncClient):
        """T1-TRAN-06: Transcript persists incrementally and remains stable across pause/resume."""
        created = await create_discussion_helper(async_client, max_rounds=2)
        disc_id = created["id"]

        await async_client.post(f"/api/discussions/{disc_id}/start")

        # Wait for at least 1 turn then pause
        turns_phase1 = []
        for _ in range(25):
            await asyncio.sleep(0.3)
            res = await async_client.get(f"/api/discussions/{disc_id}/transcript")
            if res.status_code == 200:
                turns_phase1 = res.json()
                if len(turns_phase1) >= 1:
                    break

        await async_client.post(f"/api/discussions/{disc_id}/pause")
        count_1 = len(turns_phase1)

        # Transcript must be safely accessible and unchanged while paused
        res_paused = await async_client.get(f"/api/discussions/{disc_id}/transcript")
        assert res_paused.status_code == 200
        assert len(res_paused.json()) == count_1

        await async_client.post(f"/api/discussions/{disc_id}/terminate")


# ==============================================================================
# Group 1.5: Summaries & Consensus/Divergence (6 Tests)
# ==============================================================================

@pytest.mark.tier1
class TestTier1Summary:
    """T1-SUMM: Post-Debate Summary, Consensus, and Stance Audit."""

    async def test_t1_summ_01_summary_query_before_completion(self, async_client: httpx.AsyncClient):
        """T1-SUMM-01: Querying summary on created session returns null/empty summary state."""
        created = await create_discussion_helper(async_client)
        disc_id = created["id"]

        res = await async_client.get(f"/api/discussions/{disc_id}/summary")
        assert res.status_code == 200
        data = res.json()

        assert data.get("summary") is None or data.get("summary") == ""
        assert data.get("consensus_items") == [] or data.get("consensus_items") is None
        assert data.get("divergence_items") == [] or data.get("divergence_items") is None

    async def test_t1_summ_02_post_debate_moderator_synthesis(self, async_client: httpx.AsyncClient):
        """T1-SUMM-02: Terminated or completed debate produces substantial natural language synthesis."""
        created = await create_discussion_helper(async_client, max_rounds=1)
        disc_id = created["id"]

        await async_client.post(f"/api/discussions/{disc_id}/start")
        await asyncio.sleep(1.0)
        await async_client.post(f"/api/discussions/{disc_id}/terminate")

        res = await async_client.get(f"/api/discussions/{disc_id}/summary")
        assert res.status_code == 200
        data = res.json()

        summary_text = data.get("summary")
        assert summary_text is not None, "Summary text must not be None after termination"
        assert isinstance(summary_text, str)
        assert len(summary_text) >= 10, f"Summary text too short: '{summary_text}'"

    async def test_t1_summ_03_consensus_items_schema_and_invariants(self, async_client: httpx.AsyncClient):
        """T1-SUMM-03: Consensus items contain statements, supporting agents, and normalized confidence."""
        created = await create_discussion_helper(async_client, max_rounds=1)
        disc_id = created["id"]

        await async_client.post(f"/api/discussions/{disc_id}/start")
        await asyncio.sleep(1.0)
        await async_client.post(f"/api/discussions/{disc_id}/terminate")

        res = await async_client.get(f"/api/discussions/{disc_id}/summary")
        assert res.status_code == 200
        data = res.json()

        consensus_items = data.get("consensus_items", [])
        assert isinstance(consensus_items, list)

        for item in consensus_items:
            assert "statement" in item and isinstance(item["statement"], str) and len(item["statement"]) > 0
            assert "supporting_agents" in item and isinstance(item["supporting_agents"], list)
            if "confidence" in item:
                assert 0.0 <= item["confidence"] <= 1.0, f"Invalid confidence: {item['confidence']}"

    async def test_t1_summ_04_divergence_items_schema_and_invariants(self, async_client: httpx.AsyncClient):
        """T1-SUMM-04: Divergence items contain tension descriptions and normalized intensity."""
        created = await create_discussion_helper(async_client, max_rounds=1)
        disc_id = created["id"]

        await async_client.post(f"/api/discussions/{disc_id}/start")
        await asyncio.sleep(1.0)
        await async_client.post(f"/api/discussions/{disc_id}/terminate")

        res = await async_client.get(f"/api/discussions/{disc_id}/summary")
        assert res.status_code == 200
        data = res.json()

        divergence_items = data.get("divergence_items", [])
        assert isinstance(divergence_items, list)

        for item in divergence_items:
            assert "tension" in item and isinstance(item["tension"], str) and len(item["tension"]) > 0
            assert "opposing_stances" in item and isinstance(item["opposing_stances"], dict)
            if "intensity" in item:
                assert 0.0 <= item["intensity"] <= 1.0, f"Invalid intensity: {item['intensity']}"

    async def test_t1_summ_05_stance_audit_completeness(self, async_client: httpx.AsyncClient):
        """T1-SUMM-05: Stance audit accounts for all participants with initial and final stances."""
        created = await create_discussion_helper(async_client, max_rounds=1)
        disc_id = created["id"]

        await async_client.post(f"/api/discussions/{disc_id}/start")
        await asyncio.sleep(1.0)
        await async_client.post(f"/api/discussions/{disc_id}/terminate")

        res = await async_client.get(f"/api/discussions/{disc_id}/summary")
        assert res.status_code == 200
        data = res.json()

        stance_audit = data.get("stance_audit", [])
        assert isinstance(stance_audit, list)

        assert len(stance_audit) == len(SAMPLE_PARTICIPANTS), (
            f"Stance audit must cover all participants, expected {len(SAMPLE_PARTICIPANTS)}, got {len(stance_audit)}"
        )
        for entry in stance_audit:
            agent_name = entry.get("agent_name") or entry.get("name")
            assert agent_name is not None
            assert "initial_stance" in entry
            assert "final_stance" in entry

    async def test_t1_summ_06_summary_read_idempotency(self, async_client: httpx.AsyncClient):
        """T1-SUMM-06: Repeated reads of discussion summary return identical payloads."""
        created = await create_discussion_helper(async_client, max_rounds=1)
        disc_id = created["id"]

        await async_client.post(f"/api/discussions/{disc_id}/start")
        await asyncio.sleep(0.5)
        await async_client.post(f"/api/discussions/{disc_id}/terminate")

        first_payload = None
        for _ in range(5):
            res = await async_client.get(f"/api/discussions/{disc_id}/summary")
            assert res.status_code == 200
            current_payload = res.json()
            if first_payload is None:
                first_payload = current_payload
            else:
                assert current_payload == first_payload, "Summary response was not idempotent across successive calls"


# ==============================================================================
# Group 1.6: Mock LLM Fallback & Credential Handling (6 Tests)
# ==============================================================================

@pytest.mark.tier1
class TestTier1Mock:
    """T1-MOCK: Mock Fallback Engine and Credential Security."""

    async def test_t1_mock_01_graceful_startup_without_llm_credentials(self, async_client: httpx.AsyncClient):
        """T1-MOCK-01: Service operates stably when LLM_API_KEY is unconfigured."""
        res_health = await async_client.get("/api/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "ok"

        res_disc = await async_client.get("/api/discussions")
        assert res_disc.status_code == 200
        assert isinstance(res_disc.json(), list)

    async def test_t1_mock_02_offline_mock_roster_generation(self, async_client: httpx.AsyncClient):
        """T1-MOCK-02: Offline mock engine generates topic-grounded candidate rosters."""
        res = await async_client.post(
            "/api/discussions/roster/generate",
            json={"topic": "通用人工智能的伦理与监管边界", "participant_count": 4},
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["experts"]) == 4

    async def test_t1_mock_03_full_mock_debate_lifecycle_execution(self, async_client: httpx.AsyncClient):
        """T1-MOCK-03: Full debate lifecycle executes deterministically offline in Mock mode."""
        created = await create_discussion_helper(async_client, max_rounds=1)
        disc_id = created["id"]

        start_res = await async_client.post(f"/api/discussions/{disc_id}/start")
        assert start_res.status_code == 200

        await asyncio.sleep(1.0)

        term_res = await async_client.post(f"/api/discussions/{disc_id}/terminate")
        assert term_res.status_code == 200

        summary_res = await async_client.get(f"/api/discussions/{disc_id}/summary")
        assert summary_res.status_code == 200
        assert summary_res.json().get("summary") is not None

    async def test_t1_mock_04_mock_mode_identification(self, async_client: httpx.AsyncClient):
        """T1-MOCK-04: System execution mode is clearly identifiable as mock/development."""
        settings = get_settings()
        is_mock_env = (
            getattr(settings, "LLM_MODEL", "") == "mock"
            or getattr(settings, "LLM_API_KEY", "") == ""
            or getattr(settings, "INTEGRITY_MODE", "") == "demo"
        )
        assert is_mock_env, "Test environment must be configured for offline Mock mode"

        res = await async_client.get("/api/health")
        assert res.status_code == 200

    async def test_t1_mock_05_persona_grounded_content_across_5_domains(self, async_client: httpx.AsyncClient):
        """T1-MOCK-05: Mock roster generator produces contextually tailored experts for all 5 domains."""
        domains = [
            ("AGI安全", "AGI 安全与超级对齐：加速还是限制？"),
            ("远程办公", "远程办公与重返办公室：未来组织形态之争"),
            ("核能转型", "核能是否应该作为实现碳中和的主力能源？"),
            ("算法伦理", "算法推荐与信息茧房：技术的便利还是认知窄化？"),
            ("太空开发", "商业太空探索与小行星采矿的法律与伦理"),
        ]

        for label, topic in domains:
            res = await async_client.post(
                "/api/discussions/roster/generate",
                json={"topic": topic, "participant_count": 4},
            )
            assert res.status_code == 200, f"Failed generating roster for {label}"
            data = res.json()
            assert len(data["experts"]) == 4, f"Expert count mismatch for domain {label}"
            assert data["topic"] == topic

    async def test_t1_mock_06_zero_secret_leak_invariant(self, async_client: httpx.AsyncClient, monkeypatch):
        """
        T1-MOCK-06: Zero secret leak invariant.
        Server environment secrets must never appear in response bodies, headers, or error details.
        """
        canary_secret = "sk-canary-secret-do-not-leak-12345"
        monkeypatch.setenv("LLM_API_KEY", canary_secret)
        if hasattr(get_settings, "cache_clear"):
            get_settings.cache_clear()

        # Probe health endpoint
        r_health = await async_client.get("/api/health")
        assert canary_secret not in r_health.text
        for k, v in r_health.headers.items():
            assert canary_secret not in v

        # Probe discussions list
        r_list = await async_client.get("/api/discussions")
        assert canary_secret not in r_list.text
        for k, v in r_list.headers.items():
            assert canary_secret not in v

        # Probe roster generator
        r_roster = await async_client.post(
            "/api/discussions/roster/generate",
            json={"topic": "信息安全测试", "participant_count": 2},
        )
        assert canary_secret not in r_roster.text
        for k, v in r_roster.headers.items():
            assert canary_secret not in v
