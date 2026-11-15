"""High-Fidelity Offline Mock LLM Engine for AI Panel Studio.

Provides authentic Chinese multi-perspective personas across 5 debate domains,
dynamic intent arbitration simulation, stage-directed speeches, and typewriter
jitter streaming.
"""

import asyncio
import hashlib
import json
import random
import re
from typing import (
    Any,
    AsyncIterator,
    Dict,
    List,
    Optional,
    TypeVar,
)
from pydantic import BaseModel

from app.core.config import settings
from app.domain.value_objects import ActionType, AgentIntent

T = TypeVar("T", bound=BaseModel)

# ==============================================================================
# Domain Catalogs (5 Standard Multi-Perspective Debate Domains)
# ==============================================================================

DOMAIN_CATALOGS = {
    # 1. AI Ethics, Safety & Governance
    "ai_ethics": {
        "keywords": [
            "伦理",
            "对齐",
            "安全边界",
            "偏见",
            "人类主权",
            "责任归属",
            "agi",
            "意识觉醒",
            "通用人工智能",
            "智能体",
            "大模型",
        ],
        "default_topic": "通用人工智能的伦理与监管边界",
        "experts": [
            {
                "name": "沈清源",
                "occupation": "认知AI伦理学家",
                "stance": "主张立即实施强监管与对齐约束，优先预防不可逆的自主性失控风险",
                "perspective": "规范伦理学、价值对齐理论与长期主义风险评估",
                "color_hex": "#3B82F6",
                "role": "expert",
            },
            {
                "name": "陆宏宇",
                "occupation": "前沿大模型总架构师",
                "stance": "主张通过技术创新与开源生态自发演进解决安全问题，反对扼杀创新的过早强管制",
                "perspective": "工程实用主义、系统演化论与计算博弈论",
                "color_hex": "#10B981",
                "role": "expert",
            },
            {
                "name": "周思敏",
                "occupation": "科技反垄断与数字法学专家",
                "stance": "主张确立明确的算法法律追责机制，防止科技寡头借开源之名规避侵权与合规责任",
                "perspective": "法经济学、主体责任法理与市场反垄断",
                "color_hex": "#F59E0B",
                "role": "expert",
            },
            {
                "name": "韩立诚",
                "occupation": "战略竞争与技术地缘政治学者",
                "stance": "主张在国家科技主权与产业战略优势前提下审视监管节奏，避免单边自缚手脚",
                "perspective": "结构现实主义、科技冷战博弈与产业安全",
                "color_hex": "#8B5CF6",
                "role": "expert",
            },
            {
                "name": "艾琳·陈",
                "occupation": "人机共生社会学家",
                "stance": "强调关注底层劳工受AI冲击的代际公平，建立全民技术红利补偿基金",
                "perspective": "技术社会学、分配正义与数字包容性",
                "color_hex": "#EC4899",
                "role": "expert",
            },
            {
                "name": "赵天成",
                "occupation": "软硬件算力系统院士",
                "stance": "从能耗瓶颈与热力学极限论证算力红线，主张以绿色能耗配额自然限制模型规模",
                "perspective": "计算物理学、绿色计算与可持续算力",
                "color_hex": "#06B6D4",
                "role": "expert",
            },
        ],
    },
    # 2. Smart City & Autonomous Driving / Future of Work
    "smart_city": {
        "keywords": [
            "自动驾驶",
            "车路协同",
            "智慧交通",
            "智慧城市",
            "路测",
            "全域路测",
            "交通",
            "远程办公",
            "城市治理",
            "机器人",
            "无人驾驶",
        ],
        "default_topic": "全无人自动驾驶的大规模城市准入与事故归责机制",
        "experts": [
            {
                "name": "程凯",
                "occupation": "车路协同系统总工",
                "stance": "主张V2X车路协同基础设施先行，建立全域路网统一调度实现零事故",
                "perspective": "系统工程、分布式控制与路侧智能",
                "color_hex": "#3B82F6",
                "role": "expert",
            },
            {
                "name": "许明哲",
                "occupation": "侵权责任法与智能网联立法专家",
                "stance": "坚持严格无过错责任归属于车辆制造方与软件开发方，设立强制事故先行赔付基金",
                "perspective": "侵权法理、风险分配理论与受害者优先保护",
                "color_hex": "#10B981",
                "role": "expert",
            },
            {
                "name": "顾思源",
                "occupation": "整车主机厂智能研发副总裁",
                "stance": "呼吁明确界定责任边界与驾驶员接管合理期，避免过度担责摧毁整车产业创新动力",
                "perspective": "产业落地、商业可行性与软硬件工程容错",
                "color_hex": "#F59E0B",
                "role": "expert",
            },
            {
                "name": "林晓岚",
                "occupation": "城市社会学与公共政策教授",
                "stance": "关注网约车与出租车司机转型就业，防止无人化交通导致大规模社会排斥",
                "perspective": "劳工社会学、包容性发展与公众感知",
                "color_hex": "#8B5CF6",
                "role": "expert",
            },
            {
                "name": "孙宏达",
                "occupation": "保险科技精算精算师",
                "stance": "主张以实时动态驾驶数据驱动精准车险定价，实现风险与保费毫秒级对冲",
                "perspective": "精算数学、大数定律与行为风险量化",
                "color_hex": "#EC4899",
                "role": "expert",
            },
            {
                "name": "冯子衿",
                "occupation": "认知人机工程学首席科学家",
                "stance": "强调人类在复杂路况下的应急直觉不可完全被纯算法替代，主张混合增强驾驶模式",
                "perspective": "人机混合交互、认知负荷与反应时延",
                "color_hex": "#06B6D4",
                "role": "expert",
            },
        ],
    },
    # 3. Healthcare AI, Gene Privacy & Clean Energy
    "healthcare": {
        "keywords": [
            "医疗",
            "临床",
            "基因",
            "隐私",
            "诊断",
            "合成生物",
            "健康",
            "医药",
            "双碳",
            "能源",
            "清洁能源",
            "生物",
        ],
        "default_topic": "生成式AI在临床诊断中的自主权与基因隐私红线",
        "experts": [
            {
                "name": "何秋明",
                "occupation": "计算生物学国家重点实验室主任",
                "stance": "主张全面开放临床多模态脱敏数据库，依靠端到端大模型突破罕见病诊断瓶颈",
                "perspective": "转化医学、蛋白质折叠算法与数据驱动发现",
                "color_hex": "#3B82F6",
                "role": "expert",
            },
            {
                "name": "章若虚",
                "occupation": "生命医学伦理委员会资深委员",
                "stance": "强调生命不可测度，坚决反对将终局诊断与处方权交给不可解释的黑盒模型",
                "perspective": "临床医学伦理、知情同意原则与医生不可替代性",
                "color_hex": "#10B981",
                "role": "expert",
            },
            {
                "name": "白映雪",
                "occupation": "智慧医疗与数字健康创投合伙人",
                "stance": "主张通过市场化医保准入激发AI医疗器械落地，以效率提升基层医疗均质化",
                "perspective": "卫生经济学、商业模式闭环与医疗普惠",
                "color_hex": "#F59E0B",
                "role": "expert",
            },
            {
                "name": "郭海宁",
                "occupation": "公共卫生流行病学首席专家",
                "stance": "主张强化全国跨区域传染病AI监测网，平衡个人隐私保护与群体公共卫生安全",
                "perspective": "流行病学模型、群体免疫动力学与疫情预警",
                "color_hex": "#8B5CF6",
                "role": "expert",
            },
            {
                "name": "钟文韬",
                "occupation": "基因隐私与生物信息安全学者",
                "stance": "主张建立国家级基因主权防火墙，禁止任何商业机构将个人全基因组数据出境或跨境训练",
                "perspective": "国家生物安全、多方安全计算与同态加密",
                "color_hex": "#EC4899",
                "role": "expert",
            },
            {
                "name": "梁静宜",
                "occupation": "三甲医院重症医学科主任医师",
                "stance": "从临床一线出发主张AI应始终定位为辅助诊断助手，决策签字终生追责必须由医生承担",
                "perspective": "床旁诊断实践、医患信任纽带与医疗实务风险",
                "color_hex": "#06B6D4",
                "role": "expert",
            },
        ],
    },
    # 4. FinTech, Algorithmic Ethics & Platform Governance
    "fintech": {
        "keywords": [
            "金融",
            "量化",
            "交易",
            "风控",
            "高频量化",
            "算法",
            "平台",
            "垄断",
            "信息茧房",
            "区块链",
            "数字货币",
            "创作",
        ],
        "default_topic": "高频量化交易算法监管与数字平台内容推荐伦理",
        "experts": [
            {
                "name": "赵立峰",
                "occupation": "量化金融与风险控制科学家",
                "stance": "主张高频算法为市场提供了充沛流动性与价格发现效率，反对一刀切交易限制",
                "perspective": "微观市场结构、非线性动力学与资产定价",
                "color_hex": "#3B82F6",
                "role": "expert",
            },
            {
                "name": "王语嫣",
                "occupation": "金融消费者保护与反垄断法学者",
                "stance": "主张穿透式审查推荐算法与价格歧视模型，坚决打击算法操纵与掠夺性流动性抽离",
                "perspective": "金融法理、消费者剩余与穿透式监管",
                "color_hex": "#10B981",
                "role": "expert",
            },
            {
                "name": "陈思远",
                "occupation": "头部互联网内容平台首席运营官",
                "stance": "认为推荐算法反映了用户真实注意力的自发选择，平台自律与用户意图微调优于强行政干预",
                "perspective": "产品生态、用户行为心理学与流量商业化",
                "color_hex": "#F59E0B",
                "role": "expert",
            },
            {
                "name": "孙宏雷",
                "occupation": "金融社会学与认知科学研究员",
                "stance": "警惕算法同质化推荐对公众极化思潮与群体盲从的放大效应，主张引入信息异质度强制配额",
                "perspective": "信息生态学、认知偏差与社会网络分化",
                "color_hex": "#8B5CF6",
                "role": "expert",
            },
            {
                "name": "姜一舟",
                "occupation": "中央银行数字货币架构设计师",
                "stance": "主张将算法清算与智能合约纳入央行穿透式可编程宏观审慎框架",
                "perspective": "货币经济学、可编程金融与系统性风险防范",
                "color_hex": "#EC4899",
                "role": "expert",
            },
            {
                "name": "杜兰若",
                "occupation": "独立创作者权益联盟理事长",
                "stance": "要求平台透明化流量分发机制，反对算法剥削腰尾部创作者收益与版权挤压",
                "perspective": "文化创意产业、版权正义与创作者经济",
                "color_hex": "#06B6D4",
                "role": "expert",
            },
        ],
    },
    # 5. Future of Education & Space Exploration
    "education_space": {
        "keywords": [
            "教育",
            "导学",
            "学校",
            "太空",
            "深空",
            "航天",
            "个性化导学",
            "班级",
            "高考",
            "自适应",
            "元宇宙",
            "行星",
            "外层空间",
        ],
        "default_topic": "AI个性化导学对传统班级学校制的解构与太空探索公约",
        "experts": [
            {
                "name": "顾一鸣",
                "occupation": "个性化自适应教育实验室主任",
                "stance": "主张打破传统千人一面的班级学校制度，由AI大模型构建万人万相的终生认知脚手架",
                "perspective": "认知科学、知识图谱与自适应学习",
                "color_hex": "#3B82F6",
                "role": "expert",
            },
            {
                "name": "秦曼文",
                "occupation": "发展心理学与教育人类学教授",
                "stance": "强调学校不仅是知识灌输场所，更是同伴社会化与集体人格塑型的关键场域，AI不可替代",
                "perspective": "儿童社会化发展、情感共情与社会情感学习（SEL）",
                "color_hex": "#10B981",
                "role": "expert",
            },
            {
                "name": "严正德",
                "occupation": "教育科技产业创新协会会长",
                "stance": "主张大力发展人机协同双师课堂，将教师从重复性批改中解放，转型为育人导师",
                "perspective": "教育技术经济学、双师模式与教育信息化落地",
                "color_hex": "#F59E0B",
                "role": "expert",
            },
            {
                "name": "任晓梦",
                "occupation": "偏远地区教育均衡发展公益学者",
                "stance": "警惕AI教育应用扩大城乡数字认知鸿沟，呼吁国家免费统配底层教育AI算力与优质终端",
                "perspective": "教育社会公平、数字鸿沟与公益教育资源均等化",
                "color_hex": "#8B5CF6",
                "role": "expert",
            },
            {
                "name": "萧逸飞",
                "occupation": "深空探测与行星资源开发总指挥",
                "stance": "主张面向星际文明重塑全人类教育体系，将深空生存技能与太空探索纳入基础通识",
                "perspective": "星际人类学、极端环境工程与深空战略",
                "color_hex": "#EC4899",
                "role": "expert",
            },
            {
                "name": "楚怀安",
                "occupation": "外层空间法与国际空间治理专家",
                "stance": "坚持月球与小行星资源属于人类共同继承财产，坚决反对太空圈地与军事化垄断",
                "perspective": "外层空间条约法理、全人类共同财产与太空非军事化",
                "color_hex": "#06B6D4",
                "role": "expert",
            },
        ],
    },
}


PRIORITY_DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "healthcare": [
        "医疗",
        "临床",
        "基因",
        "隐私",
        "诊断",
        "医疗责任",
        "知情同意",
    ],
    "fintech": ["金融", "量化", "交易", "风控"],
    "smart_city": [
        "自动驾驶",
        "车路协同",
        "智慧交通",
        "智慧城市",
        "路测",
        "事故责任",
        "权责划分",
        "事故归责",
    ],
    "education_space": ["教育", "导学", "学校", "太空", "深空"],
    "ai_ethics": [
        "对齐",
        "价值对齐",
        "安全边界",
        "偏见",
        "人类主权",
        "意识觉醒",
        "agi",
        "通用人工智能",
        "大模型伦理",
    ],
}


def _match_domain(topic: str) -> str:
    """Identify best matching domain from topic keywords using prioritized scoring."""
    topic_lower = topic.lower()
    scores: Dict[str, float] = {k: 0.0 for k in DOMAIN_CATALOGS.keys()}

    for domain_key in DOMAIN_CATALOGS.keys():
        # Priority domain-specific terms have higher weight
        for kw in PRIORITY_DOMAIN_KEYWORDS.get(domain_key, []):
            if kw.lower() in topic_lower:
                scores[domain_key] += 5.0 * len(kw)

        # Standard domain catalog keywords
        for kw in DOMAIN_CATALOGS[domain_key]["keywords"]:
            if kw.lower() in topic_lower:
                scores[domain_key] += 2.0 * len(kw)

    best_domain = max(scores, key=lambda k: (scores[k], 0 if k == "ai_ethics" else 1))
    if scores[best_domain] > 0.0:
        return best_domain
    return "ai_ethics"


def _generate_generic_experts(topic: str, count: int) -> List[Dict[str, Any]]:
    """Synthesize authentic balanced expert personas for arbitrary custom topic."""
    colors = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#06B6D4"]
    archetypes = [
        ("技术演进与工程首席", "主张以技术持续突破与工程迭代为核心，在实践中解决发展中的矛盾", "技术实用主义与系统工程论"),
        ("法学与合规治理学者", "主张确立明确的法律制度规范与责任追溯机制，守住合规底线", "法理学、制度经济学与权益保护"),
        ("产业生态与商业领袖", "强调产业经济规律与市场机制调节，促进生态协同与可持续价值闭环", "商业生态学与产业竞争战略"),
        ("社会福祉与伦理观察家", "关注公共利益、人文价值与脆弱群体权益，预防技术异化风险", "应用伦理学与人文社会关怀"),
        ("战略决策与政策智库专家", "从长远国家战略与全球治理格局审视顶层设计，平衡发展与安全", "公共政策学与地缘战略分析"),
        ("一线实务与用户代表", "立足真实场景实操体验与痛点诉求，反馈第一手实证检验", "实证研究与敏捷用户洞察"),
    ]
    family_names = ["林", "陈", "张", "周", "赵", "孙", "李", "王", "吴", "黄"]
    given_names = ["博", "文", "法", "经", "成", "远", "岚", "凯", "源", "辉"]

    experts = []
    for i in range(count):
        idx = i % len(archetypes)
        occ, st, persp = archetypes[idx]
        name = f"{family_names[(i * 3 + len(topic)) % len(family_names)]}{given_names[i % len(given_names)]}"
        experts.append(
            {
                "name": name,
                "occupation": occ,
                "stance": f"针对议题‘{topic}’，{st}",
                "perspective": persp,
                "color_hex": colors[i % len(colors)],
                "role": "expert",
            }
        )
    return experts


STAGE_DIRECTIONS = [
    "[面色严肃，扶了扶眼镜]",
    "[微微前倾，语气沉稳而坚定]",
    "[翻开手边的白皮书与实证数据]",
    "[注视着对方，从容不迫地阐述]",
    "[轻扣桌面，语调提高了几分]",
    "[温和而敏锐地微笑着回应]",
    "[凝视全场，语气厚重且具穿透力]",
    "[深吸一口气，直击核心问题]",
]


class MockLLMClient:
    """High-fidelity zero-network Mock LLM Client implementing the LLMClient protocol."""

    def __init__(self, chunk_delay: float = 0.035) -> None:
        self.chunk_delay = chunk_delay

    def __repr__(self) -> str:
        return "MockLLMClient(mode='offline_high_fidelity_zero_network')"

    def __str__(self) -> str:
        return self.__repr__()

    # --------------------------------------------------------------------------
    # Protocol Implementation: generate_text
    # --------------------------------------------------------------------------
    async def generate_text(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate high-fidelity Chinese debate speech or analysis."""
        stage = random.choice(STAGE_DIRECTIONS)
        return (
            f"{stage} 各位同仁，就当前论题而言，我们必须从结构化矛盾与实证机理切入。"
            f"单向度的激进推进或过早的全面封堵都将导致系统性反噬。"
            f"真正的破局之道在于在开放博弈与红线准入之间建立可量化的动态缓冲带。"
        )

    # --------------------------------------------------------------------------
    # Protocol Implementation: generate_structured
    # --------------------------------------------------------------------------
    async def generate_structured(
        self, prompt: str, schema: type[T], system_prompt: Optional[str] = None
    ) -> T:
        """Generate validated Pydantic model for roster, intents, consensus or summary."""
        raw_dict = await self.generate_json(system_prompt or "", prompt)
        return schema.model_validate(raw_dict)

    # --------------------------------------------------------------------------
    # Protocol Implementation: stream_text
    # --------------------------------------------------------------------------
    async def stream_text(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        """Stream simulated speech chunks with typing jitter."""
        async for chunk in self.stream_speech(system_prompt or "", prompt):
            yield chunk

    # --------------------------------------------------------------------------
    # Core JSON Generation
    # --------------------------------------------------------------------------
    async def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Generate deterministic and contextual JSON response."""
        combined = f"{system_prompt} {user_prompt}"

        # 1. Expert Roster Generation
        if "专家阵容" in combined or "ExpertRosterResponse" in combined or "GenerateRosterRequest" in combined:
            # Parse participant count if present
            participant_count = 4
            match = re.search(r"人数[：:]\s*(\d+)", combined)
            if match:
                participant_count = int(match.group(1))

            domain = _match_domain(user_prompt)
            cat = DOMAIN_CATALOGS[domain]
            all_experts = cat["experts"]

            if participant_count <= len(all_experts):
                selected = all_experts[:participant_count]
            else:
                extra = _generate_generic_experts(user_prompt, participant_count)
                selected = extra[:participant_count]

            return {
                "topic": user_prompt.strip(),
                "experts": selected,
            }

        # 2. Agent Intent Generation (Hand-raising)
        if "AgentIntentResponse" in combined or "发言意愿" in combined or "intent" in combined.lower():
            # Check if agent was last speaker (cooldown)
            is_cooldown = "last_speaker" in combined.lower() or "刚刚发言" in combined
            if is_cooldown:
                return {
                    "agent_id": "mock_agent",
                    "agent_name": "沈清源",
                    "desire_to_speak": False,
                    "action_type": "none",
                    "urgency": 0.0,
                    "conflict_intensity": 0.0,
                    "topical_relevance": 0.5,
                    "evidence_depth": 0.5,
                    "novelty": 0.3,
                    "target_speaker_id": None,
                    "target_speaker_name": None,
                    "rationale": "刚结束发言，进入静默冷却周期",
                    "drafted_content": "",
                }

            # Generate dynamic intent variation based on prompt keywords
            action = "rebuttal" if ("反驳" in combined or "争议" in combined) else "statement"
            if "补充" in combined:
                action = "supplement"
            elif "提问" in combined:
                action = "question"

            urgency = round(random.uniform(0.72, 0.96) if action == "rebuttal" else random.uniform(0.55, 0.82), 2)
            conflict = round(random.uniform(0.70, 0.95) if action == "rebuttal" else random.uniform(0.20, 0.45), 2)
            novelty = round(random.uniform(0.60, 0.88), 2)

            return {
                "agent_id": "mock_agent_winner",
                "agent_name": "陆宏宇",
                "desire_to_speak": True,
                "action_type": action,
                "urgency": urgency,
                "conflict_intensity": conflict,
                "topical_relevance": 0.92,
                "evidence_depth": 0.85,
                "novelty": novelty,
                "target_speaker_id": "target_peer_1",
                "target_speaker_name": "沈清源",
                "rationale": "针对对方关于强管制的论据提出基于开源自适应审计的关键反驳",
                "drafted_content": "指出开源社区的漏洞自愈与红蓝攻防远比封闭官僚审查高效",
            }

        # 3. Consensus and Divergence Tracking
        if "ConsensusDivergenceResponse" in combined or "共识看板" in combined or "consensus" in combined.lower():
            return {
                "consensus_items": [
                    {
                        "id": "cons_1",
                        "statement": "全体专家一致赞同对关系公共生命安全的关键AI系统实施前置安全验证与日志全生命周期可追溯",
                        "supporting_agents": ["沈清源", "陆宏宇", "周思敏", "韩立诚"],
                        "confidence": 0.94,
                        "resolved_turn": 3,
                        "status": "established",
                    },
                    {
                        "id": "cons_2",
                        "statement": "认同必须设立国家与产业双层应急熔断机制以防御对抗性提示词与级联注入风险",
                        "supporting_agents": ["沈清源", "周思敏"],
                        "confidence": 0.82,
                        "resolved_turn": 4,
                        "status": "forming",
                    },
                ],
                "divergence_items": [
                    {
                        "id": "div_1",
                        "tension": "前沿模型底层权重开源对安全防线的利弊权衡",
                        "opposing_stances": {
                            "陆宏宇": "强调开源众包攻防与自发对齐速度超越中心化机构",
                            "沈清源": "坚持不可逆能力扩散一旦越过临界点将造成毁灭性灾难",
                        },
                        "intensity": 0.88,
                        "is_active": True,
                        "key_conflict": "在攻击者与防御者技术不对称时，代码公开是否加剧零日漏洞利用",
                    },
                    {
                        "id": "div_2",
                        "tension": "科技反垄断规制与国际产业地缘竞争优势的优先次序",
                        "opposing_stances": {
                            "周思敏": "坚决拆解科技巨头闭环垄断，防范侵蚀中小创新主体",
                            "韩立诚": "主张优先维护本国科技龙头战略算力集群以应对外部地缘压力",
                        },
                        "intensity": 0.79,
                        "is_active": True,
                        "key_conflict": "内部反垄断公平性与外部国家战略竞争力之间的政策权衡",
                    },
                ],
            }

        # 4. Summary & Synthesis
        if "SummaryResponseDTO" in combined or "总结" in combined or "summary" in combined.lower():
            return {
                "discussion_id": "disc_summary_mock",
                "topic": "通用人工智能的伦理与监管边界",
                "status": "completed",
                "summary": (
                    "本场关于人工智能伦理与监管边界的高级别圆桌辩论圆满结束。"
                    "与会专家深入剖析了技术创新演进、开源社区自愈能力、主体法律追责与国家战略主权等多维议题。"
                    "各方最终达成高度共识：必须坚持技术透明度与关键系统安全日志溯源，同时防范无序过度管制扼杀本土前沿创新活力。"
                    "针对开源权重分发与反垄断规制的未决分歧，将为后续产业白皮书提供关键审议依据。"
                ),
                "consensus_items": [
                    {
                        "id": "cons_1",
                        "statement": "同意对关键基础设施领域的基础模型进行安全日志与可追溯性审计",
                        "supporting_agents": ["沈清源", "陆宏宇", "周思敏", "韩立诚"],
                        "confidence": 0.94,
                        "resolved_turn": 3,
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
                        "intensity": 0.88,
                        "is_active": True,
                    }
                ],
                "stance_audit": [
                    {
                        "agent_id": "p1",
                        "agent_name": "沈清源",
                        "initial_stance": "主张立即实施强监管与对齐约束",
                        "final_stance": "坚持前置防范，但认可分级沙盒的渐进试验空间",
                        "stance_shift": "从绝对全面管制转向支持分级分类差异化沙盒",
                    },
                    {
                        "agent_id": "p2",
                        "agent_name": "陆宏宇",
                        "initial_stance": "主张通过技术创新与开源生态自发演进解决安全问题",
                        "final_stance": "支持开源生态自愈，但接纳关键公共安全领域的审计备案",
                        "stance_shift": "从完全反管制转向支持敏感红线场景的透明审计",
                    },
                    {
                        "agent_id": "p3",
                        "agent_name": "周思敏",
                        "initial_stance": "主张确立明确的算法法律追责机制",
                        "final_stance": "坚持法律底线追责，主张建立开发者合规免责抗辩通道",
                        "stance_shift": "从严格连带责任转向引入过错推定与合规抗辩机制",
                    },
                    {
                        "agent_id": "p4",
                        "agent_name": "韩立诚",
                        "initial_stance": "主张在国家科技主权与战略优势前提下审视监管",
                        "final_stance": "立足国家战略，认可高标准治理规则有助于提升国际话语权",
                        "stance_shift": "将国内合规治理升华为全球科技博弈的标准制定优势",
                    },
                ],
            }

        return {}

    # --------------------------------------------------------------------------
    # Speech Streaming with Typewriter Jitter
    # --------------------------------------------------------------------------
    async def stream_speech(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncIterator[str]:
        """Stream simulated speech chunks with typing cadence and punctuation pause."""
        stage = random.choice(STAGE_DIRECTIONS)
        domain = _match_domain(user_prompt)

        speeches = {
            "ai_ethics": (
                f"{stage} 各位专家，刚才探讨的开源与闭源之争实质上直指技术民主化与生存性风险的深刻博弈。"
                "沈清源先生谈到的生存性风险警示振聋发聩，但如果我们在模型迭代初期就彻底封死开源权重，"
                "只会将技术认知基础设施拱手让给跨国寡头，削弱全球学术共同体的众包审计效能；"
                "真正的解法并非一刀切关停，而是构建‘动态能力红线准入’与‘多方密态沙盒验证’相结合的敏捷机制！"
            ),
            "smart_city": (
                f"{stage} 针对自动驾驶全无人路权准入这一议题，我们必须清醒认识到纯单车智能在长尾边缘工况下的物理感知极限。"
                "许明哲教授提出的严格制造方责任确实为受害公众提供了制度兜底，但如果不辅以高精车路协同基建，"
                "整车算力冗余与制造成本将呈指数级跃升，最终阻断规模化普惠交通的落地前景！"
            ),
            "healthcare": (
                f"{stage} 在临床多模态辅助诊疗的场景下，任何算法模型的输出都直接关乎生命权与身体权。"
                "章若虚委员强调的医学伦理与知情同意是绝不可退让的基石，但面对罕见病诊断的漫长延迟，"
                "联邦学习与隐私计算恰恰为我们提供了在数据可用不可见前提下攻克医学孤岛的破局钥匙！"
            ),
            "fintech": (
                f"{stage} 谈及金融高频量化与推荐算法治理，流动性创造与市场操纵往往仅有一线之隔。"
                "赵立峰首席强调的微观流动性价值在平静市况下成立，然而在极端流动性抽离与雪崩踩踏发生时，"
                "黑天鹅放大效应要求我们必须在撮合引擎中预置穿透式宏观审慎防爆阀！"
            ),
            "education_space": (
                f"{stage} 关于AI个性化教育重构学校制的设想，知识灌输效率的倍增绝不能以牺牲集体社会化场域为代价。"
                "秦曼文教授指出的同伴互助与共情培育是人之所以为人的灵魂所在，"
                "未来的智慧教育绝非冰冷的人机单对单孤岛，而是以AI解除琐碎负荷、让人类教师真正回归传道授业的融合升华！"
            ),
        }

        full_speech = speeches.get(domain, speeches["ai_ethics"])

        # Split into variable 2 to 5 character fragments with variable sleep
        idx = 0
        while idx < len(full_speech):
            chunk_size = random.randint(2, 5)
            chunk = full_speech[idx : idx + chunk_size]
            idx += chunk_size
            yield chunk

            # Realistic typing jitter
            delay = self.chunk_delay + random.uniform(-0.01, 0.015)
            if any(p in chunk for p in "，。！？；"):
                delay += 0.035
            await asyncio.sleep(max(0.01, delay))
