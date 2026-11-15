"""Comprehensive Tests for Mock LLM Engine and LLMClient Protocol Compliance."""

import pytest
from app.application.dtos import GenerateRosterResponse
from app.domain.value_objects import ActionType, AgentIntent
from app.infrastructure.llm_client import LLMClient
from app.infrastructure.mock_engine import MockLLMClient, _match_domain


@pytest.mark.asyncio
class TestMockLLMClientProtocol:
    """Tests verifying MockLLMClient protocol conformance and core methods."""

    async def test_protocol_adherence(self):
        client = MockLLMClient()
        assert isinstance(client, LLMClient)

    async def test_generate_text_returns_valid_string_with_stage_direction(self):
        client = MockLLMClient()
        text = await client.generate_text(prompt="探讨人工智能发展")
        assert isinstance(text, str)
        assert len(text) > 20
        assert "[" in text and "]" in text  # Contains stage direction

    async def test_generate_structured_pydantic_validation(self):
        client = MockLLMClient()
        roster = await client.generate_structured(
            prompt="请为通用人工智能伦理生成专家阵容，人数：4",
            schema=GenerateRosterResponse,
        )
        assert isinstance(roster, GenerateRosterResponse)
        assert len(roster.experts) == 4
        for exp in roster.experts:
            assert exp.name and len(exp.name) > 0
            assert exp.color_hex.startswith("#")

    async def test_generate_structured_agent_intent(self):
        client = MockLLMClient()
        intent = await client.generate_structured(
            prompt="沈清源发言意愿评定",
            schema=AgentIntent,
        )
        assert isinstance(intent, AgentIntent)
        assert 0.0 <= intent.urgency <= 1.0
        assert 0.0 <= intent.conflict_intensity <= 1.0
        assert intent.desire_to_speak is True


@pytest.mark.asyncio
class Test5DomainsMockGeneration:
    """Tests covering the 5 distinct Chinese debate domains and persona fidelity."""

    DOMAINS_TOPICS = [
        ("AI伦理与安全", "通用人工智能的伦理与监管边界"),
        ("自动驾驶与智慧城市", "全无人自动驾驶的大规模城市准入与事故归责机制"),
        ("医疗AI与基因隐私", "生成式AI在临床诊断中的自主权与基因隐私红线"),
        ("金融科技与平台算法", "高频量化交易算法监管与数字平台内容推荐伦理"),
        ("未来教育与深空探索", "AI个性化导学对传统班级学校制的解构与太空探索公约"),
    ]

    async def test_5_domains_roster_generation(self):
        client = MockLLMClient()
        for domain_name, topic in self.DOMAINS_TOPICS:
            data = await client.generate_json(
                system_prompt="ExpertRosterResponse",
                user_prompt=f"请为以下议题生成一组专家阵容：{topic}，人数：4",
            )
            experts = data.get("experts", [])
            assert len(experts) == 4, f"Domain {domain_name} expected 4 experts, got {len(experts)}"

            # Assert distinct visual identities and personas
            names = [e["name"] for e in experts]
            colors = [e["color_hex"] for e in experts]
            assert len(set(names)) == len(names), f"Duplicate names in {domain_name}"
            assert len(set(colors)) == len(colors), f"Duplicate colors in {domain_name}"

            for exp in experts:
                assert len(exp["stance"]) >= 10, f"Stance too short in {domain_name}"
                assert len(exp["perspective"]) >= 5

    REPRESENTATIVE_TOPICS = [
        ("生成式AI在临床诊断中的自主权与基因隐私红线", "healthcare"),
        ("高频量化交易算法监管与数字平台内容推荐伦理", "fintech"),
        ("AI个性化导学对传统班级学校制的解构与太空探索公约", "education_space"),
        ("L4/L5级自动驾驶全域路测权责划分与智慧城市伦理", "smart_city"),
        ("AGI意识觉醒评估标准与多智能体系统行为对齐", "ai_ethics"),
    ]

    CROSSOVER_AND_PURE_TOPICS = [
        ("AI医疗诊断的伦理责任归属与患者隐私保护", "healthcare"),
        ("自动驾驶致命事故中的责任归属", "smart_city"),
        ("AI医疗伦理", "healthcare"),
        ("大模型价值对齐与人类主权", "ai_ethics"),
    ]

    async def test_domain_matching_representative_topics(self):
        """Verify _match_domain correctly classifies all 5 representative debate topics."""
        for topic, expected_domain in self.REPRESENTATIVE_TOPICS:
            matched = _match_domain(topic)
            assert (
                matched == expected_domain
            ), f"Topic '{topic}' misclassified: expected '{expected_domain}', got '{matched}'"

    async def test_domain_matching_crossover_topics(self):
        """Verify crossover topics with generic ethics/liability phrasing correctly resolve to vertical domains."""
        for topic, expected_domain in self.CROSSOVER_AND_PURE_TOPICS:
            matched = _match_domain(topic)
            assert (
                matched == expected_domain
            ), f"Crossover topic '{topic}' misclassified: expected '{expected_domain}', got '{matched}'"

    async def test_5_representative_topics_generate_distinct_domain_personas(self):
        """Verify the 5 representative debate topics generate distinct personas across domains."""
        client = MockLLMClient()
        rosters_by_domain = {}

        for topic, expected_domain in self.REPRESENTATIVE_TOPICS:
            data = await client.generate_json(
                system_prompt="ExpertRosterResponse",
                user_prompt=f"请为以下议题生成一组专家阵容：{topic}，人数：4",
            )
            experts = data.get("experts", [])
            assert len(experts) == 4
            rosters_by_domain[expected_domain] = [e["name"] for e in experts]

        # Verify that all 5 domains have mutually distinct personas
        domain_names = list(rosters_by_domain.keys())
        for i in range(len(domain_names)):
            for j in range(i + 1, len(domain_names)):
                d1, d2 = domain_names[i], domain_names[j]
                overlap = set(rosters_by_domain[d1]).intersection(set(rosters_by_domain[d2]))
                assert (
                    len(overlap) == 0
                ), f"Domains '{d1}' and '{d2}' share identical personas: {overlap}"

    async def test_variable_participant_counts(self):
        client = MockLLMClient()
        topic = "深空资源开采与星际治理公约"
        for count in [3, 4, 5, 6]:
            data = await client.generate_json(
                system_prompt="ExpertRosterResponse",
                user_prompt=f"议题：{topic}，人数：{count}",
            )
            experts = data.get("experts", [])
            assert len(experts) == count, f"Requested {count} experts, got {len(experts)}"


@pytest.mark.asyncio
class TestDynamicIntentsAndCooldown:
    """Tests verifying dynamic intent generation and cooldown detection."""

    async def test_dynamic_intent_factors_within_bounds(self):
        client = MockLLMClient()
        data = await client.generate_json(
            system_prompt="AgentIntentResponse",
            user_prompt="专家陆宏宇针对沈清源提出反驳发言意愿",
        )
        assert data["desire_to_speak"] is True
        assert data["action_type"] in [a.value for a in ActionType]
        assert 0.0 <= data["urgency"] <= 1.0
        assert 0.0 <= data["conflict_intensity"] <= 1.0
        assert data["target_speaker_name"] is not None

    async def test_cooldown_intent_suppression(self):
        client = MockLLMClient()
        data = await client.generate_json(
            system_prompt="AgentIntentResponse",
            user_prompt="专家沈清源刚刚发言完毕 last_speaker",
        )
        assert data["desire_to_speak"] is False
        assert data["action_type"] == "none"
        assert data["urgency"] == 0.0


@pytest.mark.asyncio
class TestTypewriterStreamingJitter:
    """Tests verifying typewriter streaming cadence, chunking, and non-blocking delays."""

    async def test_stream_text_yields_multiple_chunks(self):
        client = MockLLMClient(chunk_delay=0.005)
        chunks = []
        async for chunk in client.stream_text("关于自动驾驶测试议题"):
            chunks.append(chunk)

        # Must yield multiple chunks
        assert len(chunks) >= 5, f"Expected at least 5 chunks, got {len(chunks)}"

        # Reconstructed speech text must be coherent and contain stage direction
        full_text = "".join(chunks)
        assert len(full_text) >= 50
        assert "[" in full_text and "]" in full_text
