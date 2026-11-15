"""High-Fidelity Offline Mock LLM Engine."""

import asyncio
from typing import AsyncGenerator, Dict, List
from app.infrastructure.llm_client import ILLMClient


class MockLLMClient(ILLMClient):
    """Deterministic offline Mock LLM client providing zero-network execution."""

    def __init__(self, chunk_delay: float = 0.04) -> None:
        self.chunk_delay = chunk_delay

    async def generate_json(self, system_prompt: str, user_prompt: str) -> Dict:
        """Return deterministic JSON based on prompt keywords."""
        if "专家阵容" in user_prompt or "ExpertRosterResponse" in system_prompt:
            return {
                "topic": "通用人工智能的伦理与监管边界",
                "experts": [
                    {
                        "name": "沈清源",
                        "occupation": "认知AI伦理学家",
                        "stance": "主张立即实施强监管与对齐约束，优先预防不可逆的自主性失控风险",
                        "perspective": "规范伦理学、价值对齐理论与长期主义风险评估",
                        "color_hex": "#3B82F6",
                    },
                    {
                        "name": "陆宏宇",
                        "occupation": "前沿大模型总架构师",
                        "stance": "主张通过技术创新与开源生态自发演进解决安全问题，反对扼杀创新的过早强管制",
                        "perspective": "工程实用主义、系统演化论与计算博弈论",
                        "color_hex": "#10B981",
                    },
                    {
                        "name": "周思敏",
                        "occupation": "科技反垄断与数字法学专家",
                        "stance": "主张确立明确的算法法律追责机制，防止科技寡头借开源之名规避侵权与合规责任",
                        "perspective": "法经济学、主体责任法理与市场反垄断",
                        "color_hex": "#F59E0B",
                    },
                    {
                        "name": "韩立诚",
                        "occupation": "战略竞争与技术地缘政治学者",
                        "stance": "主张在国家科技主权与产业战略优势前提下审视监管节奏，避免单边自缚手脚",
                        "perspective": "结构现实主义、科技冷战博弈与产业安全",
                        "color_hex": "#8B5CF6",
                    },
                ],
            }

        if "AgentIntentResponse" in system_prompt or "发言意愿" in user_prompt:
            return {
                "desire_to_speak": True,
                "action_type": "rebuttal",
                "priority_score": 0.85,
                "target_speaker_name": "沈清源",
                "rationale": "针对开源安全风险提出反驳",
                "drafted_content": "指出开源社区众包审计在修复漏洞方面的速度优势",
            }

        if "ConsensusDivergenceResponse" in system_prompt or "共识看板" in user_prompt:
            return {
                "consensus_items": [
                    {
                        "id": "cons_1",
                        "statement": "同意对关键基础设施领域的基础模型进行安全日志与可追溯性审计",
                        "supporting_agents": ["沈清源", "陆宏宇", "周思敏"],
                        "confidence": 0.88,
                        "status": "established",
                    }
                ],
                "divergence_items": [
                    {
                        "id": "div_1",
                        "tension": "开源开发者责任穿透与豁免权界限",
                        "opposing_stances": {
                            "陆宏宇": "支持避风港豁免",
                            "周思敏": "主张开发者过错推定责任",
                        },
                        "intensity": 0.82,
                        "key_conflict": "在模型能力与攻击能力呈指数演进时，责任主体的归责逻辑",
                    }
                ],
            }

        return {}

    async def stream_speech(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncGenerator[str, None]:
        """Stream simulated speech chunks with typing cadence."""
        speech = (
            "[面色严肃，扶了扶眼镜] "
            "各位专家，刚才探讨的开源与闭源之争实质上直指技术民主化与生存性风险的博弈。"
            "如果我们彻底封锁底层模型权重，将把整个认知基础设施拱手让给少数科技寡头；"
            "但若完全放任无门槛扩散，生物与网络攻防失衡的系统性代价不可承受。"
            "因此，我们必须探索分级沙盒与开源红线准入相结合的第三条道路！"
        )
        chunks = [speech[i : i + 8] for i in range(0, len(speech), 8)]
        for chunk in chunks:
            yield chunk
            await asyncio.sleep(self.chunk_delay)
