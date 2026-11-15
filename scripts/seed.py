"""AI Panel Studio — Database Seeding Script.

Populates the SQLite database with 5 complete, rich, multi-perspective sample
discussions across diverse technology and societal debate topics:
1. AI 是否会取代大部分初级程序员？
2. 中国大学生应该优先就业还是读研？
3. 自动驾驶技术距离全面普及还有多远？
4. AI Agent 是否会改变传统 SaaS 商业模式？
5. 大学生是否应该在本科阶段创业？
"""

import asyncio
from datetime import datetime, timezone, timedelta
import json
import os
import sys
import uuid

# Ensure backend package is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.config import settings
from app.infrastructure.database import AsyncSessionLocal, init_db
from app.infrastructure.models import (
    ConsensusItemModel,
    DiscussionModel,
    DivergenceItemModel,
    EventModel,
    ParticipantModel,
    TurnModel,
)


def gen_id(name: str) -> str:
    """Generate deterministic UUID from seed key."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"seed.aipanelstudio.{name}"))


SAMPLE_DISCUSSIONS = [
    # -------------------------------------------------------------------------
    # 1. AI 是否会取代大部分初级程序员？
    # -------------------------------------------------------------------------
    {
        "key": "ai_junior_dev",
        "topic": "AI 是否会取代大部分初级程序员？",
        "status": "completed",
        "current_round": 3,
        "max_rounds": 4,
        "summary": """### 辩题总结：AI 是否会取代大部分初级程序员？

**核心共识：**
1. 传统单纯从事重复性 CRUD 代码搬运、机械编写模板的“初级体力型”编码岗位确实正在被快速压缩。
2. 初级开发者的定义正在发生本质跃迁——从“代码编写者”升级为“AI 协同编排者与系统验证者”。

**持续分歧：**
1. **晋升阶梯断裂风险**：学术与劳动力学者担忧如果企业取消初级招聘，未来高级工程师将失去成长土壤；而产业方认为初级开发者借助大模型能在 1-2 年内达到过去 3-5 年的工程全局视野。
2. **重度依赖与代码劣质化**：AI 生成代码的隐性安全漏洞与架构技术债由谁最终兜底。

**未来展望：**
开发者生态的门槛在降低，但上限在提高。真正具有系统设计思维、业务洞察与审查能力的年轻工程师将迎来生产力倍增的黄金时代。""",
        "moderator": {
            "name": "林知远",
            "occupation": "圆桌主持人 / 科技智库观察员",
            "stance": "保持中立，客观引导技术、产业与劳动力各方深入交锋与共识收敛",
            "perspective": "中立主持、议程推进与论点提炼",
            "color_hex": "#64748B",
        },
        "experts": [
            {
                "key": "exp_1",
                "name": "赵子恒",
                "occupation": "头部云原生架构师 / 资深技术总监",
                "stance": "AI重塑的是工作流而非抹杀岗位，初级开发者将进化为拥有架构思维的编排者",
                "perspective": "工程架构、业务落地与全生命周期协同",
                "color_hex": "#3B82F6",
            },
            {
                "key": "exp_2",
                "name": "孙雨萌",
                "occupation": "通用大模型研究院高级研究员",
                "stance": "代码合成与自愈技术迅速迭代，企业初级HC缩减已成定局，必须正视剧烈阵痛",
                "perspective": "前沿模型评测、自动化软件工程与算法极限",
                "color_hex": "#10B981",
            },
            {
                "key": "exp_3",
                "name": "陈思远",
                "occupation": "科技劳动力经济学者 / 智库研究员",
                "stance": "关注技术替代对青年就业的结构性冲击，呼吁防止工程人才培养梯队断层",
                "perspective": "劳动力经济学、职场阶梯演变与技能溢价",
                "color_hex": "#F59E0B",
            },
            {
                "key": "exp_4",
                "name": "李博瀚",
                "occupation": "全球开源社区核心布道师",
                "stance": "开源协作范式正在剧变，未来优秀的初级开发者是能用Agent驱动百万级调用的个体极客",
                "perspective": "开源生态、极客文化与去中心化工程创新",
                "color_hex": "#8B5CF6",
            },
        ],
        "turns": [
            {
                "speaker": "moderator",
                "action_type": "statement",
                "content": "各位专家好，欢迎来到本期圆桌讨论。大语言模型在代码生成与重构上的能力日新月异，许多科技公司开始缩减校招初级开发岗位。究竟 AI 是取代初级程序员，还是正在重新定义这一角色？请各位专家表达核心判断。",
                "priority_score": 90.0,
                "target": None,
                "rationale": "主持人开场界定辩题核心争议点",
            },
            {
                "speaker": "exp_2",
                "action_type": "statement",
                "content": "从我们实验室的最新评测来看，前沿大模型在自动化代码生成、单元测试覆盖和常规缺陷修复上的准确率已经超过拥有1年经验的普通初级程序员。更关键的是边际成本接近零。企业追求投入产出比，取消大量简单代码录入的初级岗位是不可逆转的客观经济规律。",
                "priority_score": 88.0,
                "target": None,
                "rationale": "摆出模型性能实证数据，建立替代方论点",
            },
            {
                "speaker": "exp_1",
                "action_type": "rebuttal",
                "content": "雨萌老师的数据确实属实，但把软件工程等同于写单体函数是一个经典的认知偏差。真实企业生产环境涉及复杂的上下游契约、业务领域边界、并发一致性与运维灾备。大模型可以帮初级程序员秒级生成代码，但审查、集成、联调和对齐业务仍然需要人。初级程序员不是被取代，而是直接跃升到了‘初级架构师’的位置！",
                "priority_score": 92.0,
                "target": "exp_2",
                "rationale": "反驳将编码等同于软件工程的窄化视角",
            },
            {
                "speaker": "exp_3",
                "action_type": "argument",
                "content": "子恒提到了‘初级架构师’，这在理论上很美好，但在劳动力经济学上存在严重断层。如果初级开发者不再有机会在基础编码中犯错、踩坑、调试并建立直觉，他们如何凭空拥有辨别大模型代码陷阱的能力？如果企业连初级工位都不提供，5年后的高级工程师从哪里来？这种‘学徒期蒸发’是极其危险的。",
                "priority_score": 85.0,
                "target": "exp_1",
                "rationale": "从工程人才培养梯队与代际传承切入论证",
            },
            {
                "speaker": "exp_4",
                "action_type": "synthesis",
                "content": "陈老师提的培养断层很深刻，但答案可能不在传统的‘大厂学徒工’模式里。在开源社区，我们看到大量大一、大二的年轻开发者，借助 Cursor 和 Claude Code 独自完成了过去需要一个5人团队才能交付的开源框架。新一代程序员的踩坑场已经转移到了更高维度的开源全栈实践中。",
                "priority_score": 84.0,
                "target": "exp_3",
                "rationale": "引入开源生态实际案例证明新培养路径的诞生",
            },
            {
                "speaker": "exp_1",
                "action_type": "agreement",
                "content": "博瀚的观察和我团队的现实完全吻合。我们现在招聘初级工程师，根本不看会不会手写快速排序，而是看他能不能驾驭 AI 工具迅速跑通完整原型，并且指出 AI 生成方案中的安全缺陷。综合素质高的初级开发者比以往任何时候都更加稀缺。",
                "priority_score": 82.0,
                "target": "exp_4",
                "rationale": "赞同开源生态视角并补充产业界最新筛选标准",
            },
            {
                "speaker": "moderator",
                "action_type": "summary",
                "content": "非常精彩的交锋。大家逐渐形成了一个关键共识：被取代的不是‘初级工程师’这一生命周期阶段，而是仅掌握‘机械模板翻译’的技能形态。接下来请各位专家对高校计算机教育转型与企业新型岗位标准给出建议。",
                "priority_score": 90.0,
                "target": None,
                "rationale": "主持人阶段性总结并引导至教育应对方案",
            },
        ],
        "consensus": [
            {
                "statement": "纯粹机械性的简单模板代码编写岗位正面临被自动化工具替代的不可逆趋势。",
                "supporting": ["孙雨萌", "赵子恒", "李博瀚", "陈思远"],
                "confidence": 0.94,
                "resolved_turn": 5,
            },
            {
                "statement": "新一代初级程序员的核心竞争力转向提示词工程编排、业务契约理解与AI输出代码的安全审查。",
                "supporting": ["赵子恒", "李博瀚"],
                "confidence": 0.88,
                "resolved_turn": 6,
            },
        ],
        "divergence": [
            {
                "tension": "AI时代初级开发岗位的断层是否会摧毁高级工程技术人才的培养梯队",
                "opposing": {
                    "陈思远": "初级招聘萎缩导致年轻工程师缺乏实践踩坑机会，造成代际人才断层",
                    "赵子恒/李博瀚": "高阶AI辅助将缩短成长周期，开源协同与综合实践创造更敏捷的高阶人才孵化模式",
                },
                "intensity": 0.82,
            },
        ],
    },
    # -------------------------------------------------------------------------
    # 2. 中国大学生应该优先就业还是读研？
    # -------------------------------------------------------------------------
    {
        "key": "career_vs_grad",
        "topic": "中国大学生应该优先就业还是读研？",
        "status": "completed",
        "current_round": 3,
        "max_rounds": 4,
        "summary": """### 辩题总结：中国大学生应该优先就业还是读研？

**核心共识：**
1. 彻底打破“唯学历论”盲目从众考研的思维惯性，学历贬值背景下硕士文凭已非通用求职护身符。
2. 决策必须依据“学科性质（学术探索型 vs 强产业实践型）”与“个人经济抗风险耐受力”进行精准分类。

**持续分歧：**
1. **硬科技门槛 vs 产业敏捷度**：前沿硬核研发（算力/芯片/生物）坚定需要高学历研究训练，而广泛的应用层开发与运营管理更看重早期在市场中积累的生存敏锐度。
2. **延缓就业的时间成本**：读研三年所耗费的机会成本是否能被毕业时的薪酬溢价充分弥补。

**指导建议：**
若目标为前沿理论突破或具有明确学术导师资源，读研是高质量投资；若仅为逃避就业压力盲从二战三战，尽早入局积累真实业务成果是更稳健的职业策略。""",
        "moderator": {
            "name": "林知远",
            "occupation": "圆桌主持人 / 科技智库观察员",
            "stance": "引导各位专家从宏观就业数据、高校教育规律与青年生涯发展多维度客观剖析",
            "perspective": "中立主持、客观量化分析与务实解题",
            "color_hex": "#64748B",
        },
        "experts": [
            {
                "key": "exp_1",
                "name": "张宏伟",
                "occupation": "重点高校学生就业指导中心主任",
                "stance": "反对把考研当成延缓就业的避风港，建议有合理就业机会时果断入职积累实战经验",
                "perspective": "宏观就业统计、高校指导实务与学生心理预期管理",
                "color_hex": "#3B82F6",
            },
            {
                "key": "exp_2",
                "name": "陆晓芸",
                "occupation": "985高校智能科学系博导 / 国家青年拔尖人才",
                "stance": "在人工智能与硬科技领域，本科通识远远不够，读研是从事核心研发的必经之路",
                "perspective": "高水平科研训练、国际学术前沿与战略新兴产业需求",
                "color_hex": "#10B981",
            },
            {
                "key": "exp_3",
                "name": "郭振宇",
                "occupation": "跨国科技企业全球人力资源副总裁",
                "stance": "企业招聘早已转向‘交付结果导向’，很多岗位3年高强度实战经验胜过3年泛泛论文",
                "perspective": "人才投资回报率、组织敏捷度与企业用人标准",
                "color_hex": "#F59E0B",
            },
            {
                "key": "exp_4",
                "name": "梁沛林",
                "occupation": "青年职业发展研究学者 / 畅销书作者",
                "stance": "反对一刀切，主张根据家庭财务安全垫和个人认知觉醒程度制定差异化路线",
                "perspective": "社会分层、家庭抗风险能力与个人综合效用最大化",
                "color_hex": "#8B5CF6",
            },
        ],
        "turns": [
            {
                "speaker": "moderator",
                "action_type": "statement",
                "content": "近年来考研报名人数出现波动，但考研热依然存在。同时应届生就业市场结构性分化明显。中国大学生毕业后究竟应该优先抢占就业身位，还是通过读研提升学历？请各位专家开宗明义。",
                "priority_score": 90.0,
                "target": None,
                "rationale": "主持人点明当前考研与就业两难抉择的现实背景",
            },
            {
                "speaker": "exp_1",
                "action_type": "statement",
                "content": "我们指导中心跟踪了近五年毕业生的追踪数据。很多学生选择考研并非真正热爱科研，而是‘被动避险’。但现实是三年后专硕毕业面临的求职竞争甚至比本科阶段更激烈。遇到契合的产业机会，尽早进入职场建立行业认知、人脉和现金流，抗风险能力更强。",
                "priority_score": 87.0,
                "target": None,
                "rationale": "用追踪数据揭示被动考研带来的时间陷阱",
            },
            {
                "speaker": "exp_2",
                "action_type": "rebuttal",
                "content": "宏伟老师讲的情况在某些传统文商科可能存在，但在我们硬核技术领域绝非如此。本科毕业生连前沿Transformer的底层微调和分布式算力集群都未能深入实操，怎么去应聘高端算法岗？国家要突破‘卡脖子’关键技术，核心研发骨干几乎百分之百需要研究生阶段的严格学术与工程洗礼。",
                "priority_score": 89.0,
                "target": "exp_1",
                "rationale": "从硬核科技研发壁垒与战略需求进行有力反驳",
            },
            {
                "speaker": "exp_3",
                "action_type": "argument",
                "content": "陆教授讲的顶尖科研岗确实需要高学历，但全社会这种岗位的占比只有不到5%。绝大部分企业的绝大多数岗位是应用层开发、交付运维、运营管理和商业化拓展。在这些岗位上，一个有三年真实商业项目交付经验的本科生，业务嗅觉和自驱力普遍显著优于刚出象牙塔的应届硕士。",
                "priority_score": 86.0,
                "target": "exp_2",
                "rationale": "指出顶尖研发岗位的有限比例，强调市场主体对交付能力的需求",
            },
            {
                "speaker": "exp_4",
                "action_type": "synthesis",
                "content": "大家争论的根源在于把不同维度的赛道混为一谈了。我认为必须建立决策矩阵：第一看专业硬度——是‘深水区研发’还是‘应用层技能’；第二看家庭现金流——家庭能否支撑学生再脱产学习三年。盲从考研是对自己的不负责，盲目鄙视学历也是反智。",
                "priority_score": 91.0,
                "target": "exp_3",
                "rationale": "提出清晰的决策矩阵将争论从对立转向多维度权衡",
            },
            {
                "speaker": "moderator",
                "action_type": "summary",
                "content": "沛林老师的分类框架非常清晰实用。大家一致认同：没有适合所有人的标准答案，关键在于摆脱羊群效应，看清目标领域的硬性门槛与自身优势。感谢各位专家的洞见。",
                "priority_score": 90.0,
                "target": None,
                "rationale": "主持人归纳共识，完成讨论闭环",
            },
        ],
        "consensus": [
            {
                "statement": "考研不应作为逃避求职竞争的普遍避风港，盲目考研面临三年后更严峻的机会成本与学历通胀。",
                "supporting": ["张宏伟", "郭振宇", "梁沛林"],
                "confidence": 0.91,
                "resolved_turn": 4,
            },
            {
                "statement": "基础科学与高端硬科技核心岗位仍高度依赖研究生阶段的深度科研训练。",
                "supporting": ["陆晓芸", "张宏伟", "梁沛林"],
                "confidence": 0.89,
                "resolved_turn": 5,
            },
        ],
        "divergence": [
            {
                "tension": "对于非理论基础学科，三年全职工作经验是否系统性优于三年硕士研究生学历",
                "opposing": {
                    "郭振宇/张宏伟": "在应用型岗位中，三年实操商业经验与团队协作能力的溢价显著高于硕士文凭",
                    "陆晓芸": "系统性的学术研究方法论和独立解决未知问题的能力是长期职业天花板的根本支撑",
                },
                "intensity": 0.78,
            },
        ],
    },
    # -------------------------------------------------------------------------
    # 3. 自动驾驶技术距离全面普及还有多远？
    # -------------------------------------------------------------------------
    {
        "key": "autonomous_driving",
        "topic": "自动驾驶技术距离全面普及还有多远？",
        "status": "completed",
        "current_round": 3,
        "max_rounds": 4,
        "summary": """### 辩题总结：自动驾驶技术距离全面普及还有多远？

**核心共识：**
1. 封闭园区、固定路线无人接驳及特定区域 Robotaxi 商业闭环已经进入成熟期。
2. 全域无安全员全天候 L4/L5 级全场景普及仍需 5-10 年，主要瓶颈已从单纯感知算力拓展至极端物理长尾（Corner Cases）、法律权责与公众心理接受度。

**持续分歧：**
1. **纯视觉单车智能 vs 车路协同基础设施**：是依靠特斯拉式端到端大模型泛化解决一切，还是依靠国家级 V2X 智能路侧传感器与高精地图协同。
2. **事故法律责任穿透**：无驾驶员状态下的致命交通事故，赔偿与刑事过错应由主机厂、算法开发商还是车主共同承担。

**未来展望：**
普及不会以“一夜质变”的方式到来，而是通过特定场景由点到面渗透。保险精算创新与立法先行将成为技术释放商业价值的加速器。""",
        "moderator": {
            "name": "林知远",
            "occupation": "圆桌主持人 / 科技智库观察员",
            "stance": "聚焦工程技术、商业落地、交通伦理与法律法规的综合审视",
            "perspective": "中立主持、客观技术评估与监管维度整合",
            "color_hex": "#64748B",
        },
        "experts": [
            {
                "key": "exp_1",
                "name": "程凯",
                "occupation": "国家智能网联汽车创新中心首席科学家",
                "stance": "单车智能存在物理感知极限，唯有V2X车路协同基础设施全域覆盖才能实现零伤亡普及",
                "perspective": "车路协同、智能路侧网联与宏观交通系统控制",
                "color_hex": "#3B82F6",
            },
            {
                "key": "exp_2",
                "name": "顾思源",
                "occupation": "头部造车新势力智能驾驶研发副总裁",
                "stance": "端到端大模型改写了自动驾驶技术天花板，海量量产车影子数据将在3-5年内解决大部分长尾",
                "perspective": "单车智能端到端网络、量产数据飞轮与计算落地",
                "color_hex": "#10B981",
            },
            {
                "key": "exp_3",
                "name": "许明哲",
                "occupation": "侵权责任法与人工智能伦理学者",
                "stance": "立法与责任认定滞后是最大拦路虎，没有确定的责任主体与兜底保险，全无人商用寸步难行",
                "perspective": "侵权法理、产品责任归属与制度信任构建",
                "color_hex": "#F59E0B",
            },
            {
                "key": "exp_4",
                "name": "林晓岚",
                "occupation": "城市社会学与公共出行政策专家",
                "stance": "普及不仅是技术指标，更关乎上千万网约车与货运司机群体的转型平稳度",
                "perspective": "劳工社会学、公共交通包容性与社会总成本核算",
                "color_hex": "#8B5CF6",
            },
        ],
        "turns": [
            {
                "speaker": "moderator",
                "action_type": "statement",
                "content": "近年来，各大城市的自动驾驶示范区不断扩容，端到端大模型也为智驾带来了革命性突破。然而关于长尾场景和安全事故的讨论也从未停歇。自动驾驶距离全面普及究竟还有多远？",
                "priority_score": 90.0,
                "target": None,
                "rationale": "界定技术普及的时间维度与社会预期",
            },
            {
                "speaker": "exp_2",
                "action_type": "statement",
                "content": "我认为公众对自动驾驶的普及速度低估了。过去基于规则的感知与规划算法容易陷入死胡同，但现在端到端神经网络完全模拟老司机的直觉驾驶，通过数十亿公里影子数据持续进化。未来3到5年内，主流城市的高阶NOA体验就会像今天的自动挡汽车一样普及。",
                "priority_score": 89.0,
                "target": None,
                "rationale": "依托端到端大模型技术进步给出乐观时间表",
            },
            {
                "speaker": "exp_1",
                "action_type": "rebuttal",
                "content": "思源总对大模型的信心令人赞赏，但不能忽视物理限制。暴雪大雾天车载摄像头的盲区、暴雨逆光下激光雷达的散射，单靠车端传感器在物理上就存在不可逆丢失。不建车路协同路侧感知，单车智能永远跨不过99.9999%的安全冗余门槛。普及至少需要十年，且必须基础设施先行。",
                "priority_score": 87.0,
                "target": "exp_2",
                "rationale": "从传感器物理极限与极端工况挑战单车智能论点",
            },
            {
                "speaker": "exp_3",
                "action_type": "argument",
                "content": "两位工程师从技术层面争论，但现实中踩刹车的往往是法律。目前世界各国立法均以‘人类驾驶员为责任中心’。一旦去掉方向盘和安全员，发生致命交通事故究竟由软件厂商、整车厂还是零部件供应商担责？如果这个问题没有清晰的法定赔付机制，任何市长都不敢批准全域开放。",
                "priority_score": 86.0,
                "target": "exp_1",
                "rationale": "提出法律伦理与制度准入才是商业落地的核心前提",
            },
            {
                "speaker": "exp_4",
                "action_type": "synthesis",
                "content": "除了法律，还有巨大的社会成本。全国有上千万网约车司机、出租车司机和卡车司机。自动驾驶如果在两三年内瞬间爆发，社会将承受巨大的再就业压力。我赞同技术分阶段、分区域逐步演进，让社会治理和产业生态有足够的自愈与适应时间。",
                "priority_score": 84.0,
                "target": "exp_3",
                "rationale": "引入劳动力就业与社会转型平稳度视角",
            },
            {
                "speaker": "moderator",
                "action_type": "summary",
                "content": "各位专家的讨论非常发人深省。我们看到‘普及’不是一个单纯的算法达标问题，它包含‘技术可靠性、路网基础设施、法律责任框架、社会就业吸纳’四位一体的系统工程。谢谢各位！",
                "priority_score": 90.0,
                "target": None,
                "rationale": "总结技术、基建、法律、社会四个维度的综合结论",
            },
        ],
        "consensus": [
            {
                "statement": "限定区域（ODD）的高可靠性Robotaxi和干线物流有望在未来3-5年内实现规模化商业化运营。",
                "supporting": ["顾思源", "程凯", "许明哲"],
                "confidence": 0.92,
                "resolved_turn": 4,
            },
            {
                "statement": "全天候无死角的终极无人驾驶普及需要法律法规重塑、责任穿透机制及路网智能化的共同支撑。",
                "supporting": ["程凯", "许明哲", "林晓岚"],
                "confidence": 0.95,
                "resolved_turn": 5,
            },
        ],
        "divergence": [
            {
                "tension": "单车纯视觉/多传感器端到端路线能否彻底脱离车路协同实现全域普及",
                "opposing": {
                    "顾思源": "端到端大模型泛化与大规模影子数据能够在单车侧跨越绝大多数长尾难题",
                    "程凯": "单车物理极限无法突破，缺乏智能路侧全域感知与超视距调度无法达成绝对安全标准",
                },
                "intensity": 0.85,
            },
        ],
    },
    # -------------------------------------------------------------------------
    # 4. AI Agent 是否会改变传统 SaaS 商业模式？
    # -------------------------------------------------------------------------
    {
        "key": "saas_vs_agent",
        "topic": "AI Agent 是否会改变传统 SaaS 商业模式？",
        "status": "completed",
        "current_round": 3,
        "max_rounds": 4,
        "summary": """### 辩题总结：AI Agent 是否会改变传统 SaaS 商业模式？

**核心共识：**
1. 传统按席位付费（Per-Seat Pricing）的收费逻辑遭遇重创，按价值结果交付（Work Done / Outcome-Based）已成大势所趋。
2. 传统 SaaS 的表单 UI 前端被弱化，具备专业业务流编排能力与私有沉淀数据的后端将构筑全新护城河。

**持续分歧：**
1. **SaaS 颠覆 vs 赋能**：通用智能体平台是否会把传统 CRM/ERP 沦落为纯粹的“底层哑管道（Dumb Pipe）”，还是成熟 SaaS 能凭借数据重力与合规壁垒反向吞并 Agent。
2. **确定性与幻觉治理**：企业级严谨事务与金融审计是否允许 Agent 自主做决策，抑或必须保留传统审批工作流。

**未来展望：**
SaaS 不会死亡，但“软件即服务”正在真正回归“服务”本质——从向客户售卖工具软件，演变为直接售卖具备劳动技能的数字员工。""",
        "moderator": {
            "name": "林知远",
            "occupation": "圆桌主持人 / 科技智库观察员",
            "stance": "引导软件工程、商业模式演变与企业数字化落地三方展开务实推演",
            "perspective": "中立主持、商业模式解构与企业软件价值链梳理",
            "color_hex": "#64748B",
        },
        "experts": [
            {
                "key": "exp_1",
                "name": "何振东",
                "occupation": "资深企业级SaaS产品副总裁",
                "stance": "按人头付费模式即将终结，SaaS企业必须转型为提供交付结果的AI数字雇员平台",
                "perspective": "SaaS商业化模型、席位计费解构与成果交付型产品设计",
                "color_hex": "#3B82F6",
            },
            {
                "key": "exp_2",
                "name": "范文婷",
                "occupation": "大型跨国集团全球首席信息官（CIO）",
                "stance": "企业软件的核心基石是权限管控、可审计性与数据确定性，Agent的不可靠幻觉难以攻破核心ERP",
                "perspective": "企业治理架构、合规内控、系统集成与生产稳定性",
                "color_hex": "#10B981",
            },
            {
                "key": "exp_3",
                "name": "萧云天",
                "occupation": "前沿企业软件早期投资合伙人",
                "stance": "传统UI表单SaaS将大面积死亡，Agent将直接调用API闭环操作，拥有私有领域知识的工作流是新蓝海",
                "perspective": "风险投资视角、商业护城河转移与资本定价范式",
                "color_hex": "#F59E0B",
            },
            {
                "key": "exp_4",
                "name": "谭景华",
                "occupation": "企业系统安全与分布式系统首席架构师",
                "stance": "Agent需要极度严密的沙箱与确定性执行环境，传统SaaS的状态机与关系模型恰好是Agent的最佳宿主",
                "perspective": "系统安全边界、零信任架构与确定性状态机",
                "color_hex": "#8B5CF6",
            },
        ],
        "turns": [
            {
                "speaker": "moderator",
                "action_type": "statement",
                "content": "过去十年，企业软件的黄金法则一直是基于席位订阅（SaaS Subscription）。但随着具备自主思考、工具调用与任务规划的 AI Agent 爆发，传统的‘卖工具人头费’面临严峻挑战。AI Agent 到底会重构还是彻底颠覆传统 SaaS？",
                "priority_score": 90.0,
                "target": None,
                "rationale": "剖析席位制 SaaS 商业模式面临的底层挑战",
            },
            {
                "speaker": "exp_1",
                "action_type": "statement",
                "content": "传统 SaaS 的商业逻辑是‘每个员工一个账号，每月收取 50 美元’。但当 AI Agent 能顶替 80% 的日常客服或表单填报工作，企业员工数减半，SaaS 厂商的人头收入立刻腰斩。唯有将收费锚点从‘卖账号使用权’转向‘按成功完成的任务计费’，SaaS 才能生存。",
                "priority_score": 88.0,
                "target": None,
                "rationale": "直击席位费逻辑的数学漏洞，提出价值交付计费",
            },
            {
                "speaker": "exp_2",
                "action_type": "rebuttal",
                "content": "振东总把商业化逻辑讲得很透，但作为买单的 CIO，我更关心业务系统崩不崩溃。大模型存在偶发幻觉，财务核算、供应链调度容不得万分之一的差错。传统 ERP 的复杂表单虽然难看，但它保证了强类型校验、多级审批链与审计回溯。Agent 怎么解决幻觉和合规风险？",
                "priority_score": 91.0,
                "target": "exp_1",
                "rationale": "从企业 IT 严密合规与确定性角度提出尖锐质疑",
            },
            {
                "speaker": "exp_4",
                "action_type": "argument",
                "content": "范总的顾虑非常击中要害。我们目前的架构方案是将 Agent 限制在‘只读推理与方案起草层’，真正的状态变更必须通过传统 SaaS 预设的严格 API 契约和确定性状态机执行。这说明什么？说明传统 SaaS 不仅不会死，反而成为了约束 Agent 行为的最稳固沙箱！",
                "priority_score": 86.0,
                "target": "exp_2",
                "rationale": "从工程安全沙箱与确定性状态机视角提出共存机制",
            },
            {
                "speaker": "exp_3",
                "action_type": "synthesis",
                "content": "景华指出了关键：数据与系统记录（System of Record）不会死，死的是那些仅仅套了一层 Web UI、没有核心数据壁垒的薄层流程 SaaS。资本市场现在看企业软件，核心看两点：第一是否拥有不可替代的私有行业闭环数据；第二能否将复杂人类流程直接用 Agent 封装成端到端交付结果。",
                "priority_score": 87.0,
                "target": "exp_4",
                "rationale": "从资本与产业演进角度区分薄层包装与核心记录系统的命运",
            },
            {
                "speaker": "moderator",
                "action_type": "summary",
                "content": "总结得非常深刻。AI Agent 并非简单杀死 SaaS，而是倒逼 SaaS 卸下繁琐笨重的前端交互，蜕变为深藏幕后的‘业务数据底座与执行沙箱’，商业模式也从按人头订阅进化为按价值交付结算。",
                "priority_score": 90.0,
                "target": None,
                "rationale": "主持人系统化总结 SaaS 转型新形态",
            },
        ],
        "consensus": [
            {
                "statement": "传统按席位付费模式将向按任务产出（Work Done）与效果分润的定价范式迁移。",
                "supporting": ["何振东", "萧云天", "范文婷"],
                "confidence": 0.93,
                "resolved_turn": 4,
            },
            {
                "statement": "企业级核心业务系统（System of Record）的数据确定性与合规控制层仍然是不可替代的基石。",
                "supporting": ["范文婷", "谭景华", "萧云天"],
                "confidence": 0.96,
                "resolved_turn": 5,
            },
        ],
        "divergence": [
            {
                "tension": "通用多模态Agent是否会直接瓦解垂直SaaS的数据护城河与客户关系主导权",
                "opposing": {
                    "萧云天": "跨应用通用Agent能自主跨越各个SaaS孤岛，传统垂直厂商的入口地位将被彻底降级",
                    "何振东/范文婷": "垂直行业业务流包含大量隐性规则与强监管契约，通用Agent难以击穿垂直深水区",
                },
                "intensity": 0.79,
            },
        ],
    },
    # -------------------------------------------------------------------------
    # 5. 大学生是否应该在本科阶段创业？
    # -------------------------------------------------------------------------
    {
        "key": "college_startup",
        "topic": "大学生是否应该在本科阶段创业？",
        "status": "completed",
        "current_round": 3,
        "max_rounds": 4,
        "summary": """### 辩题总结：大学生是否应该在本科阶段创业？

**核心共识：**
1. 强烈反对以高负债、重资产模式投入传统商业博弈；鼓励以技术验证、轻量级独立出海开发、开源产品化为载体的敏捷创业实验。
2. 创业是最高效的通识实践教育，无论最终商业成功与否，所历练的综合逆商、领导力与资源协调能力均属宝贵财富。

**持续分歧：**
1. **学业深度与精力冲突**：本科阶段是扎实掌握高等数学、算法原理等基础理论的关键窗口期，过早被商务运作分散精力可能导致后劲不足。
2. **资本泡沫与投机心态**：高校过度渲染创业神话是否会诱导缺乏成熟心智的学生盲从，甚至耽误正常学业生涯。

**最终建议：**
鼓励“带着问题意识的探索型微创业”，警惕“脱离自身认知边界的盲目重资产跟风”。本科生应守住学业基本盘，把创业作为认知世界的加速器而非赌注。""",
        "moderator": {
            "name": "林知远",
            "occupation": "圆桌主持人 / 科技智库观察员",
            "stance": "平衡创新驱动与高等教育育人本位，促成务实理性的观点碰撞",
            "perspective": "中立主持、青年成长关怀与理性决策引导",
            "color_hex": "#64748B",
        },
        "experts": [
            {
                "key": "exp_1",
                "name": "王瀚明",
                "occupation": "国家级高校创业创新孵化基地主任",
                "stance": "大学是唯一允许以极低成本试错并重来的庇护所，本科创业是培养拔尖创新人才的最佳熔炉",
                "perspective": "孵化器运营、政策扶持体系与企业家精神早期培育",
                "color_hex": "#3B82F6",
            },
            {
                "key": "exp_2",
                "name": "郑嘉欣",
                "occupation": "硬科技与早期消费创投基金合伙人",
                "stance": "本科生普遍缺乏产业纵深认知与现金流管控能力，99%的大学生创业项目缺乏商业价值",
                "perspective": "硬核商业回报、现金流纪律与市场残酷生存法则",
                "color_hex": "#10B981",
            },
            {
                "key": "exp_3",
                "name": "穆青云",
                "occupation": "24岁连续创业者 / AI工具出海独立开发者",
                "stance": "生成式AI让个人生产力爆发，大学生完全可以依靠低成本甚至零成本做全球微型SaaS",
                "perspective": "个体极客实践、AI赋能开发与全球化微型商业",
                "color_hex": "#F59E0B",
            },
            {
                "key": "exp_4",
                "name": "杜明礼",
                "occupation": "高等教育发展研究所特聘教授",
                "stance": "大学本科的根本使命是心智塑型与基础学科筑基，过早商业化容易助长短期投机主义",
                "perspective": "高等教育哲学、青年认知发展心理与基础学科沉淀",
                "color_hex": "#8B5CF6",
            },
        ],
        "turns": [
            {
                "speaker": "moderator",
                "action_type": "statement",
                "content": "社会各界对大学生创业褒贬不一。有人视其为极低试错成本的青年英雄主义，也有人批评其缺乏沉淀、成功率极低。在 AI 生产力爆发的今天，大学生是否应该在本科阶段开启创业？请各位嘉宾发表见解。",
                "priority_score": 90.0,
                "target": None,
                "rationale": "开篇引入本科创业在低试错成本与成功率低下之间的张力",
            },
            {
                "speaker": "exp_1",
                "action_type": "statement",
                "content": "如果用商业回报率这把尺子去量，很多早期尝试都不划算。但大学创业的真正价值在于‘认知觉醒’。一个自己做过产品、对接客户、发过工资的学生，哪怕项目没成，毕业进入任何企业都是极具担当的骨干。大学有免费工位和导师指导，这是人生中试错成本最低的黄金期。",
                "priority_score": 87.0,
                "target": None,
                "rationale": "从试错成本与综合能力培养角度论证创业价值",
            },
            {
                "speaker": "exp_2",
                "action_type": "rebuttal",
                "content": "瀚明老师情怀很满，但市场是极其冷血的。我看过成千上万份大学生商业计划书，普遍存在‘伪需求自嗨’、‘不懂供应链’、‘现金流一个月断裂’的致命问题。很多学生因为创业连本科最基础的期末考试都挂科，这种沉没成本不是一句‘认知觉醒’就能弥补的。",
                "priority_score": 90.0,
                "target": "exp_1",
                "rationale": "以投资人视角揭示市场残酷规律与学业受损代价",
            },
            {
                "speaker": "exp_3",
                "action_type": "argument",
                "content": "嘉欣老师讲的是上一代烧钱做地推、做O2O的创业模式。而在今天的大模型时代，我和我的两个本科同学，零外部融资，靠着 Cursor 和海外支付接口，三个月就做出一款面向欧美创作者的 AI 剪辑插件，现在每月稳健产生两万美元现金流。今天的创业已经是‘一人公司’的技术敏捷实验，根本不需要高额负债！",
                "priority_score": 92.0,
                "target": "exp_2",
                "rationale": "用真实的AI原生独立开发案例反驳传统高风险创业观点",
            },
            {
                "speaker": "exp_4",
                "action_type": "synthesis",
                "content": "青云同学的案例非常激动人心，这恰恰证明了我们需要重新界定‘创业’两个字。我们反对的是好高骛远、借贷投机的盲目创业，但完全赞同以技术好奇心驱动的创造性探索。不过我还是要提醒：本科阶段的高等数学和算法底座如果不扎实，走得再快也会遇到天花板。",
                "priority_score": 85.0,
                "target": "exp_3",
                "rationale": "肯定AI赋能创造的同时强调基础理论学习的底座价值",
            },
            {
                "speaker": "moderator",
                "action_type": "summary",
                "content": "今天的讨论为青年大学生点亮了一盏明灯：守住学业与基础学科的基本盘，勇敢利用前沿工具开展零负债、重验证的微创业实践。感谢四位嘉宾带来的真实声音！",
                "priority_score": 90.0,
                "target": None,
                "rationale": "主持人完成整体总结，收束全场核心建议",
            },
        ],
        "consensus": [
            {
                "statement": "坚决反对借贷、重资产的投机式大学生创业，鼓励以低成本敏捷开发和轻资产验证为特征的技术实践。",
                "supporting": ["王瀚明", "郑嘉欣", "穆青云", "杜明礼"],
                "confidence": 0.96,
                "resolved_turn": 4,
            },
            {
                "statement": "创业体验对青年学生的沟通领导力、风险意识和商业闭环思维具有不可替代的锻炼效能。",
                "supporting": ["王瀚明", "穆青云", "杜明礼"],
                "confidence": 0.90,
                "resolved_turn": 5,
            },
        ],
        "divergence": [
            {
                "tension": "本科阶段应优先全力夯实基础学科理论，还是应当尽早将精力投入真实商业与产品闭环",
                "opposing": {
                    "杜明礼/郑嘉欣": "大学本科是构筑一生学术底座的唯一黄金期，分散精力容易导致知识结构脆弱",
                    "王瀚明/穆青云": "实战是最深刻的自驱力来源，在真实解决用户需求中学习理论往往事半功倍",
                },
                "intensity": 0.81,
            },
        ],
    },
]


async def seed_database() -> None:
    """Execute asynchronous database seeding for all 5 sample discussions."""
    print("🌱 Initializing database schema...")
    await init_db()

    async with AsyncSessionLocal() as session:
        base_time = datetime.now(timezone.utc) - timedelta(hours=24)

        for idx, sample in enumerate(SAMPLE_DISCUSSIONS):
            disc_id = gen_id(sample["key"])
            print(f"📦 Seeding [{idx + 1}/5]: '{sample['topic']}' (ID: {disc_id})")

            # Check if discussion already exists
            existing = await session.get(DiscussionModel, disc_id)
            if existing:
                print(f"   ℹ️ Discussion {disc_id} exists, deleting old record for clean seed...")
                await session.delete(existing)
                await session.flush()

            disc_created_at = base_time + timedelta(hours=idx * 4)
            disc_updated_at = disc_created_at + timedelta(minutes=45)

            discussion = DiscussionModel(
                id=disc_id,
                topic=sample["topic"],
                status=sample["status"],
                current_round=sample["current_round"],
                max_rounds=sample["max_rounds"],
                summary=sample["summary"],
                created_at=disc_created_at,
                updated_at=disc_updated_at,
            )
            session.add(discussion)

            # Participants map: key -> id
            participant_id_map = {}

            # Moderator
            mod_data = sample["moderator"]
            mod_id = gen_id(f"{sample['key']}_moderator")
            participant_id_map["moderator"] = mod_id
            mod_model = ParticipantModel(
                id=mod_id,
                discussion_id=disc_id,
                name=mod_data["name"],
                occupation=mod_data["occupation"],
                stance=mod_data["stance"],
                perspective=mod_data["perspective"],
                color_hex=mod_data["color_hex"],
                role="moderator",
                total_turns_spoken=0,
                last_spoken_turn=None,
                created_at=disc_created_at,
            )
            session.add(mod_model)

            # Experts
            for exp_data in sample["experts"]:
                exp_id = gen_id(f"{sample['key']}_{exp_data['key']}")
                participant_id_map[exp_data["key"]] = exp_id
                exp_model = ParticipantModel(
                    id=exp_id,
                    discussion_id=disc_id,
                    name=exp_data["name"],
                    occupation=exp_data["occupation"],
                    stance=exp_data["stance"],
                    perspective=exp_data["perspective"],
                    color_hex=exp_data["color_hex"],
                    role="expert",
                    total_turns_spoken=0,
                    last_spoken_turn=None,
                    created_at=disc_created_at,
                )
                session.add(exp_model)

            # Turns
            turn_models = []
            for t_idx, turn_data in enumerate(sample["turns"], start=1):
                speaker_key = turn_data["speaker"]
                speaker_id = participant_id_map[speaker_key]
                speaker_name = (
                    mod_data["name"]
                    if speaker_key == "moderator"
                    else next(
                        e["name"]
                        for e in sample["experts"]
                        if e["key"] == speaker_key
                    )
                )

                target_id = None
                if turn_data.get("target"):
                    target_id = participant_id_map.get(turn_data["target"])

                turn_time = disc_created_at + timedelta(minutes=t_idx * 5)
                turn_id = gen_id(f"{sample['key']}_turn_{t_idx}")

                turn_model = TurnModel(
                    id=turn_id,
                    discussion_id=disc_id,
                    turn_number=t_idx,
                    round_number=min((t_idx - 1) // 2 + 1, sample["current_round"]),
                    speaker_id=speaker_id,
                    speaker_name=speaker_name,
                    action_type=turn_data["action_type"],
                    content=turn_data["content"],
                    rationale=turn_data.get("rationale"),
                    priority_score=turn_data.get("priority_score", 85.0),
                    target_speaker_id=target_id,
                    timestamp=turn_time,
                )
                session.add(turn_model)
                turn_models.append(turn_model)

            # Consensus Items
            for c_idx, c_data in enumerate(sample["consensus"], start=1):
                cons_id = f"{disc_id}_cons_{c_idx}"
                cons_model = ConsensusItemModel(
                    id=cons_id,
                    discussion_id=disc_id,
                    statement=c_data["statement"],
                    supporting_agents=json.dumps(c_data["supporting"], ensure_ascii=False),
                    confidence=c_data["confidence"],
                    resolved_turn=c_data["resolved_turn"],
                    created_at=disc_created_at + timedelta(minutes=20 + c_idx * 5),
                )
                session.add(cons_model)

            # Divergence Items
            for d_idx, d_data in enumerate(sample["divergence"], start=1):
                div_id = f"{disc_id}_div_{d_idx}"
                div_model = DivergenceItemModel(
                    id=div_id,
                    discussion_id=disc_id,
                    tension=d_data["tension"],
                    opposing_stances=json.dumps(d_data["opposing"], ensure_ascii=False),
                    intensity=d_data["intensity"],
                    is_active=True,
                    created_at=disc_created_at + timedelta(minutes=25 + d_idx * 5),
                )
                session.add(div_model)

            # Seed Historical Events for SSE ring replay
            events_data = [
                ("session_status_changed", {"new_status": "created", "timestamp": disc_created_at.isoformat()}),
                ("session_status_changed", {"new_status": "running", "timestamp": (disc_created_at + timedelta(seconds=10)).isoformat()}),
            ]
            for t in turn_models:
                events_data.append(
                    (
                        "speech_completed",
                        {
                            "turn_id": t.id,
                            "turn_number": t.turn_number,
                            "speaker_id": t.speaker_id,
                            "speaker_name": t.speaker_name,
                            "action_type": t.action_type,
                            "content": t.content,
                            "timestamp": t.timestamp.isoformat(),
                        },
                    )
                )
            events_data.append(
                (
                    "session_status_changed",
                    {
                        "new_status": "completed",
                        "summary": sample["summary"],
                        "timestamp": disc_updated_at.isoformat(),
                    },
                )
            )

            for seq, (ev_type, payload) in enumerate(events_data, start=1):
                ev_model = EventModel(
                    discussion_id=disc_id,
                    seq_id=seq,
                    event_type=ev_type,
                    payload=json.dumps(payload, ensure_ascii=False),
                    created_at=disc_created_at + timedelta(minutes=seq),
                )
                session.add(ev_model)

        await session.commit()
        print("✅ Seeding successfully completed! 5 full discussions ready.")


if __name__ == "__main__":
    asyncio.run(seed_database())
