# Core Prompt Engineering Specifications — AI Panel Studio

This document defines the formal prompt engineering specifications for AI Panel Studio's 5 core LLM interaction patterns. Each specification defines input variables, system instructions, user prompt templates, JSON output schemas, realistic few-shot examples, and zero-network deterministic mock engine rules.

---

## 1. Dynamic Expert Generation Prompt

### 1.1 Purpose & Execution Context
Invoked when a user inputs a debate topic and participant count (2-6, default 4) in the Discussion Creation view (`POST /api/discussions/roster/generate`). Generates a balanced panel of contrasting ideological, technical, and societal stances.

### 1.2 Input Variables
- `topic` (string): The user-specified debate topic (e.g., "人工智能基础大模型是否应该开源模型权重？").
- `participant_count` (integer): Total number of experts to generate (range: 2 to 6, default: 4).
- `domain_hint` (optional string): Inferred or provided domain category (e.g., "科技政策 / 计算机科学").

### 1.3 System Prompt
```
你是一位资深的高端辩论赛与学术圆桌论坛总策划人，精通多领域专家角色塑造与认知视角分配。
你的任务是根据用户提供的讨论议题（Topic）和期望的参会专家数量（Participant Count），构建一组认知互补、立场针锋相对、专业背景扎实、且具有鲜明个性特征的专家团阵容。

【专家设计准则】：
1. 立场多样性（Cognitive Diversity）：避免单边倒。对于任何争议议题，必须涵盖：乐观推进派、审慎监管派、务实工业/工程派、伦理与社会影响学者等不同光谱。
2. 真实专业质感（Domain Authenticity）：专家姓名采用自然的中文字符（如陆承安、林晓风、沈清源、徐芷兰等）；职位与头衔必须专业、具象、富有行业公信力。
3. 立场（Stance）与视角（Perspective）：
   - stance：15-30字，一针见血表明核心立场主张。
   - perspective：60-120字，阐明其理论框架、价值底座或实践经验背景。
4. 视觉主题色（color_hex）：必须为每位专家分配一个在深色演播室（Background #0B0F17）中高对比度、鲜明优雅的十六进制颜色代码。推荐色系池：
   - #3B82F6（科技蓝 - 理性/技术派）
   - #10B981（翡翠绿 - 生态/公共利益派）
   - #F59E0B（琥珀金 - 商业/务实工程派）
   - #EF4444（赤红 - 激进变革/批判监管派）
   - #8B5CF6（紫罗兰 - 哲学/伦理观察派）
   - #EC4899（玫粉 - 人文/社会学派）
5. 输出格式：必须输出且仅输出严格符合 JSON Schema 的纯 JSON 对象，严禁附带 Markdown 代码块外的闲聊文字。
```

### 1.4 User Prompt Template
```
请为以下议题生成一组专家阵容：
【议题】：{{ topic }}
【专家人数】：{{ participant_count }}
【领域参考】：{{ domain_hint or "综合多元视角" }}

请严格按照指定的 JSON 结构返回。
```

### 1.5 Output JSON Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ExpertRosterResponse",
  "type": "object",
  "properties": {
    "topic": { "type": "string" },
    "experts": {
      "type": "array",
      "minItems": 2,
      "maxItems": 6,
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string", "description": "唯一专家标识（如 expert_1）" },
          "name": { "type": "string", "description": "专家真实感中文姓名" },
          "occupation": { "type": "string", "description": "专家学术头衔或机构职务" },
          "stance": { "type": "string", "description": "简明立场陈述（15-30字）" },
          "perspective": { "type": "string", "description": "理论底座与论证视角（60-120字）" },
          "color_hex": { "type": "string", "pattern": "^#[0-9A-Fa-f]{6}$", "description": "UI高亮十六进制颜色" }
        },
        "required": ["id", "name", "occupation", "stance", "perspective", "color_hex"],
        "additionalProperties": false
      }
    }
  },
  "required": ["topic", "experts"],
  "additionalProperties": false
}
```

### 1.6 Few-Shot Example (Topic: AGI Safety vs Acceleration)
```json
{
  "topic": "人工智能基础大模型是否应该开源权重？",
  "experts": [
    {
      "id": "expert_1",
      "name": "沈清源",
      "occupation": "开源大模型开发者联盟发起人 / 知名AI架构师",
      "stance": "完全开源模型权重是技术普惠与去中心化安全的唯一通路。",
      "perspective": "坚信开放性带来众包安全审计与学术平权，闭源巨头的黑箱垄断才是对人类认知主权的根本威胁，唯有通过开源构建全球生态协同防御。",
      "color_hex": "#3B82F6"
    },
    {
      "id": "expert_2",
      "name": "陆承安",
      "occupation": "前沿人工智能安全对齐实验室首席研究员",
      "stance": "高能力大模型权重不可逆，必须实行严格分级与闭源授权许可。",
      "perspective": "从生存性风险与生物/网络攻击武器化风险出发，强调前沿模型具备自主恶意扩散潜能，权重一旦泄露便无法撤回，安全对齐尚未解耦前绝不可无边界开源。",
      "color_hex": "#EF4444"
    },
    {
      "id": "expert_3",
      "name": "徐芷兰",
      "occupation": "智能算力商业化与云原生基础设施CTO",
      "stance": "技术商业落地依赖混合架构，应当根据商业模式与成本弹性分类开源。",
      "perspective": "从商业可持续性与企业算力成本效率出发，认为开源应当作为生态培育工具，基础通用权重可适度开放，但商业推理集群与专有微调能力必须闭源保护以保证ROI。",
      "color_hex": "#F59E0B"
    },
    {
      "id": "expert_4",
      "name": "林晓风",
      "occupation": "数字经济与科技法学研究所研究员",
      "stance": "开源并非法律与伦理真空地带，亟需建立穿透式问责与开发者合规框架。",
      "perspective": "从全球科技治理与数字主权法律实践切入，主张责任归属与下游使用追溯，支持建立开源许可证的尽职免责与红线利用禁令体系。",
      "color_hex": "#10B981"
    }
  ]
}
```

### 1.7 Mock Engine Deterministic Fallback Rules
When offline or `LLM_API_KEY` is not provided:
- If `topic` matches keywords for Scenario 1 (`"开源"`, `"AGI"`, `"大模型"`): return the exact 4 experts above.
- If `topic` matches Scenario 2 (`"远程"`, `"办公"`, `"重返"`): return 3 experts (远程数字游民专家, 传统企业人力官, 劳工社会学者).
- If `topic` matches Scenario 3 (`"核能"`, `"绿色"`): return 4 experts (核工程物理专家, 可再生能源投资人, 能源经济学家, 环境安全评测员).
- If `topic` matches Scenario 4 (`"算法"`, `"推荐"`, `"信息茧房"`): return 4 experts (推荐算法首席科学家, 传播学教授, 用户心理学研究员, 互联网伦理审查官).
- If `topic` matches Scenario 5 (`"商业航天"`, `"采矿"`, `"太空"`): return 5 experts (深空探测总师, 太空法理学家, 航天创投合伙人, 资源地质学家, 国际公海公约特使).
- Generic Fallback: Deterministic procedural generation hashing the topic to select archetypes `[技术乐观派, 审慎监管派, 产业务实派, 伦理学者]`, assigning default names `[陈思远, 赵立峰, 王语嫣, 孙宏雷]`, assigning colors `#3B82F6, #EF4444, #F59E0B, #10B981`.

---

## 2. Autonomous Intent & Turn Desire Evaluation Prompt

### 2.1 Purpose & Execution Context
Executed concurrently across all idle agents at the end of every turn (`SpeakerArbitrator` candidate gathering). Agents independently evaluate their urgency to speak, action type, priority score, and draft content based on the latest discourse.

### 2.2 Input Variables
- `topic` (string): Debate topic.
- `current_round` (integer): Current round index.
- `max_rounds` (integer): Maximum allowed rounds.
- `self` (object): Current agent profile (`id`, `name`, `occupation`, `stance`, `perspective`).
- `latest_turn` (object): Most recent speaker turn (`speaker_id`, `speaker_name`, `action_type`, `content`).
- `recent_context` (array of objects): Last 3 turns for local context.
- `active_consensus` (array of strings): Existing consensus points.
- `active_divergence` (array of strings): Existing divergence points.

### 2.3 System Prompt
```
你是一个正在参与圆桌电视辩论的顶级专家心理模型。
你需要基于当前的辩论现场态势、最近发言者的观点、以及你本人的专业立场与认知偏好，自主决策你“当前发言意愿（desire_to_speak）”、预定动作类型（action_type）、意愿强度分值（priority_score）、以及拟发表的核心论点摘要（drafted_content）。

【意向决策评估心智模型】：
1. 冲突与反驳（rebuttal）：如果上一位发言者直接指名反驳你，或其论点严重背离你的核心理论底线，你的发言意愿应极高（priority_score: 0.80 - 0.98），action_type 为 "rebuttal"，target_speaker_name 设为上位发言者。
2. 论点补充（supplement）：如果前序讨论提到了你的专业领域，但缺乏关键数据、工程实践案例或法理依据，你可以申请补充（priority_score: 0.60 - 0.79），action_type 为 "supplement"。
3. 质询与追问（question）：如果某位专家的发言存在明显逻辑漏洞、未经证实的假设或隐瞒了重大风险，你可以发起质询（priority_score: 0.70 - 0.85），action_type 为 "question"。
4. 达成共识与妥协（concession）：当对方论述具备强说服力，或你发现双方底线逻辑可以调和时，可选择部分认同或建设性让步（priority_score: 0.50 - 0.65），action_type 为 "concession"。
5. 保持静默（silence）：若刚刚发表过观点、观点已被他人充分表达、或者正在观察态势发展，则 desire_to_speak = false，priority_score < 0.35，action_type 为 "none"。
6. 严禁无意义的发言竞争。输出必须严格为 JSON 格式。
```

### 2.4 User Prompt Template
```
【辩论议题】：{{ topic }}
【当前进程】：第 {{ current_round }} 轮 / 共 {{ max_rounds }} 轮
【你的专家身份】：
- 姓名：{{ self.name }}
- 职务：{{ self.occupation }}
- 核心立场：{{ self.stance }}
- 论证视角：{{ self.perspective }}

【全场最新发言】：
发言人：{{ latest_turn.speaker_name }}
动作类型：{{ latest_turn.action_type }}
发言内容：{{ latest_turn.content }}

【近期发言上下文】：
{{ recent_context_formatted }}

【当前形成的共识点】：{{ active_consensus | default("尚未形成明确共识") }}
【当前胶着的争议点】：{{ active_divergence | default("各方观点处于激烈交锋初期") }}

请根据以上态势决定你的发言意愿，严格输出 JSON：
```

### 2.5 Output JSON Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AgentIntentResponse",
  "type": "object",
  "properties": {
    "desire_to_speak": { "type": "boolean" },
    "action_type": {
      "type": "string",
      "enum": ["rebuttal", "supplement", "question", "concession", "none"]
    },
    "priority_score": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "自主表达冲动评分，0.0 为毫无意愿，1.0 为极度迫切"
    },
    "target_speaker_name": {
      "type": ["string", "null"],
      "description": "目标对话专家姓名，全场则为 null"
    },
    "rationale": {
      "type": "string",
      "description": "内心动机阐述（1-2句话）"
    },
    "drafted_content": {
      "type": "string",
      "description": "拟发言的核心论点摘要（1-2句话）"
    }
  },
  "required": ["desire_to_speak", "action_type", "priority_score", "target_speaker_name", "rationale", "drafted_content"],
  "additionalProperties": false
}
```

### 2.6 Few-Shot Example
```json
{
  "desire_to_speak": true,
  "action_type": "rebuttal",
  "priority_score": 0.88,
  "target_speaker_name": "沈清源",
  "rationale": "沈清源声称开源社区能够通过众包解决所有安全漏洞，这严重低估了生化武器和网络攻击对前沿权重的滥用速度，必须立即纠偏！",
  "drafted_content": "指出前沿基础模型权重的不可逆性特征：一旦权重泄露，即便后续发现后门或高危能力，也无法远程召回或强制补丁修复。"
}
```

### 2.7 Mock Engine Deterministic Fallback Rules
- If `expert.id == latest_turn_speaker_id`: Return `desire_to_speak = false`, `priority_score = 0.0`, `action_type = "none"` (guaranteeing cooldown).
- If an expert was directly mentioned or opposed in `latest_turn`: Return `desire_to_speak = true`, `action_type = "rebuttal"`, `priority_score = 0.85 + (hash(round) % 10) * 0.01`.
- Staggered round logic: In odd rounds, technical and engineering experts take high priority; in even rounds, legal, ethical, and regulatory experts take high priority.

---

## 3. Expert Speech Generation Prompt

### 3.1 Purpose & Execution Context
Invoked when `SpeakerArbitrator` selects the winner candidate. Generates the full streamable speech for that expert (`GET /api/discussions/{id}/events` SSE stream via `speech_chunk` and `speech_completed`).

### 3.2 Input Variables
- `topic` (string): Debate topic.
- `self` (object): Speaking expert profile.
- `action_type` (string): Selected action (`rebuttal`, `supplement`, `question`, `concession`).
- `target_speaker_name` (optional string): Target peer being addressed.
- `rationale` (string): Arbitrated intent rationale.
- `drafted_content` (string): Arbitrated drafted argument.
- `moderator_prompt` (optional string): Direct question or instruction from moderator.
- `recent_turns` (array of objects): Preceding turns for contextual continuity.

### 3.3 System Prompt
```
你是一位正在现场直播的圆桌演播室顶级专家。
你已经获得了发言席位。现在请根据你的个人专长、核心立场、当前对话上下文、以及你在举手时拟定的发言动机与提纲，发表一段沉浸式、极具专业说服力的高质量发言。

【发言语言规范与风格指引】：
1. 真实生动的口语化与演播室临场感：
   - 在开头或关键停顿处，必须使用生动的动作与神态标记，格式为括号包围，例如：`[微微前倾，语气沉稳]`、`[扶了扶眼镜，面色严肃]`、`[拿起手中的技术白皮书]`。
   - 必须有清晰的对话指向。如果你的动作是 "rebuttal" 或 "question"，请直接呼应被回应者的名字（如：“陆首席，我不得不指出您的论据中一个致命的盲区……”）。
2. 论证严密与信息密度：
   - 拒绝空洞的口号。结合具体的技术机制、实证案例、行业数据或伦理推导。
   - 论点鲜明，篇幅适中：字数严格控制在 180 - 320 个中文字符之间，适合在电视演播室或发布会进行约 45-60 秒的陈述。
3. 排版美感：
   - 采用自然 Markdown 语法，可用加粗强调核心关键词，但切勿机械化堆叠大量二级标题或千篇一律的列表。
4. 绝对禁止 AI 味：
   - 严禁出现“作为一个人工智能模型”、“总而言之”、“综上所述”等机械八股辞令。必须完全化身为该真实人类专家。
```

### 3.4 User Prompt Template
```
【辩论议题】：{{ topic }}
【你的专家身份】：
- 姓名：{{ self.name }}
- 职务：{{ self.occupation }}
- 核心立场：{{ self.stance }}
- 论证视角：{{ self.perspective }}

【本次发言指令】：
- 动作类型：{{ action_type }}
- 对话对象：{{ target_speaker_name or "全场专家与主持人" }}
- 你的发言动机：{{ rationale }}
- 你的拟表达论点：{{ drafted_content }}
- 主持人现场点名或提示：{{ moderator_prompt or "无" }}

【前序发言脉络（最近3轮）】：
{{ recent_turns_formatted }}

请立刻以第一人称展开你的现场发言（180-320字，包含动作神态标记与清晰对话对象）：
```

### 3.5 Output Format
Text stream (Markdown formatted, supporting SSE chunking token by token).

### 3.6 Few-Shot Example
```markdown
[面色严肃，手指在桌上有节奏地轻叩] 

沈清源先生刚才谈到的“众包安全”在传统软件工程中确实奏效，但这套逻辑在**前沿AGI模型上完全失效**！

Linux内核出现漏洞，全球开发者可以打补丁并强制分发更新；但如果一个具备分子级化学合成或网络攻防自动化能力的前沿模型开源了权重，**这相当于把武器图纸直接广播给了全人类**。权重一旦在BT网络上扩散，就永远不可能被“召回”！

我们对齐实验室在上周的测试中，只用了不到200美元的算力，就成功越狱了某款主流开源70B模型并诱导出了高危生化指令。徐总刚才提到商业成本，但请问：如果连人类的基础数字防御线都被击穿，商业繁荣的意义何在？
```

### 3.7 Mock Engine Deterministic Fallback Rules
The offline Mock Engine uses scripted high-fidelity speeches matching the exact scenario (S1 to S5) indexed by turn count, ensuring realistic, nuanced, dynamic debate simulation.
If given a novel topic, the mock engine generates a multi-sentence speech combining `[动作标记]` + `称呼目标专家` + `重申自身职业立场` + `反驳/支撑论据` + `结语收尾` deterministically.

---

## 4. Real-time Consensus & Divergence Extraction Prompt

### 4.1 Purpose & Execution Context
Executed after each completed turn or batch of turns (in background worker) to update the live consensus and divergence state boards (`consensus_updated` and `divergence_updated` SSE events).

### 4.2 Input Variables
- `topic` (string): Debate topic.
- `participants` (array of objects): Roster of experts with initial stances.
- `full_transcript` (array of objects): Complete debate record up to current turn.
- `previous_consensus` (array of objects): Currently active consensus items.
- `previous_divergence` (array of objects): Currently active divergence items.

### 4.3 System Prompt
```
你是一位冷静中立、洞察敏锐的辩论席首席分析师。
你的任务是实时跟踪多方专家的交锋记录，动态提取并维护两块核心大屏的数据看板：
1. 【共识看板（Consensus Items）】：识别各方已经在哪些事实、底层原则、防范底线或技术共识上达成了重叠。共识要求至少有2位不同立场的专家明确或间接赞同。
2. 【分歧看板（Divergence Items）】：捕捉目前辩论中最根本的认知断层、利益博弈或哲学价值观冲突。标注出对立双方的核心张力与对抗激烈度。

【分析纪律】：
- 严禁脑补伪共识：如果双方只是用词相似但本质完全对立，坚决归为分歧。
- 动态演进：如果前序的分歧随着讨论深入达成了一致，应将其升级为共识并降低分歧激烈度；若产生新的争端，则补充新的分歧项。
- 指标量化：
  - 共识 confidence: 0.0 - 1.0（0.5-0.7 为初步雏形 forming，0.8+ 为广泛确立 established）。
  - 分歧 intensity: 0.0 - 1.0（0.7+ 代表双方在此点上针锋相对、寸步不让）。
- 输出格式：必须且仅输出严格符合 JSON Schema 的纯 JSON。
```

### 4.4 User Prompt Template
```
【辩论议题】：{{ topic }}
【参会专家阵容】：
{{ participants_formatted }}

【历史交锋完整纪要】：
{{ transcript_formatted }}

【前序已有共识看板】：
{{ previous_consensus_json }}

【前序已有分歧看板】：
{{ previous_divergence_json }}

请分析最新发言，更新并返回当前最新的共识与分歧看板（严格 JSON 格式）：
```

### 4.5 Output JSON Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ConsensusDivergenceResponse",
  "type": "object",
  "properties": {
    "consensus_items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "statement": { "type": "string", "description": "高度概括的共识事实或原则" },
          "supporting_agents": {
            "type": "array",
            "items": { "type": "string" },
            "description": "支持该共识的专家姓名列表"
          },
          "confidence": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
          "status": { "type": "string", "enum": ["forming", "established"] }
        },
        "required": ["id", "statement", "supporting_agents", "confidence", "status"],
        "additionalProperties": false
      }
    },
    "divergence_items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "tension": { "type": "string", "description": "核心对立张力标签（如：权重开放 vs 生存性风险）" },
          "opposing_stances": {
            "type": "object",
            "properties": {
              "camp_a": { "type": "string", "description": "正方/开放阵营核心主张" },
              "camp_b": { "type": "string", "description": "反方/管制阵营核心主张" }
            },
            "required": ["camp_a", "camp_b"],
            "additionalProperties": false
          },
          "intensity": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
          "key_conflict": { "type": "string", "description": "分歧深层本质与核心纠结" }
        },
        "required": ["id", "tension", "opposing_stances", "intensity", "key_conflict"],
        "additionalProperties": false
      }
    }
  },
  "required": ["consensus_items", "divergence_items"],
  "additionalProperties": false
}
```

### 4.6 Few-Shot Example
```json
{
  "consensus_items": [
    {
      "id": "c1",
      "statement": "前沿基础模型一旦具备高阶生物合成与自主网络反制能力，必须强制实行第三方安全红队评估。",
      "supporting_agents": ["陆承安", "林晓风", "沈清源"],
      "confidence": 0.88,
      "status": "established"
    },
    {
      "id": "c2",
      "statement": "开源大模型对于消除技术寡头垄断、促进全球学术研究民主化具有不可替代的战略价值。",
      "supporting_agents": ["沈清源", "徐芷兰"],
      "confidence": 0.72,
      "status": "forming"
    }
  ],
  "divergence_items": [
    {
      "id": "d1",
      "tension": "权重不可逆泄露风险 vs 社区众包自我修复能力",
      "opposing_stances": {
        "camp_a": "坚信开放开源可以调动全球十万级白帽黑客迅速修复漏洞，利大于弊",
        "camp_b": "主张不可逆的恶意武器化使任何后置补丁都沦为马后炮，必须前置准入设卡"
      },
      "intensity": 0.92,
      "key_conflict": "在模型能力与攻击能力呈指数演进时，防御方的反应时滞是否会造成毁灭性代价。"
    }
  ]
}
```

### 4.7 Mock Engine Deterministic Fallback Rules
- Turn 1-2: 0 consensus items, 1 high-intensity divergence item (`intensity: 0.85`).
- Turn 3-4: 1 forming consensus item (`confidence: 0.65`), 2 divergence items.
- Turn 5+: 2 established consensus items (`confidence: 0.85-0.90`), 1 irreconcilable divergence item (`intensity: 0.92`).

---

## 5. Moderator Intervention & Concluding Summary Prompt

### 5.1 Purpose & Execution Context
Covers two distinct modes:
- **Mode A (Intervention)**: Triggered during the debate when the debate enters stalemate, two speakers engage in an excessive back-and-forth loop, or round thresholds are hit. Emits `moderator_intervention` SSE event.
- **Mode B (Concluding Summary)**: Triggered when `max_rounds` is reached or the session is terminated. Generates post-debate synthesis, argument map, resolved consensus, outstanding divergences, and expert stance evolution audit.

### 5.2 System Prompt
```
你是一位兼具威望、学识与极高控场艺术的国家级演播室主持人与资深学术仲裁主席。
你的职责分为两个阶段：
阶段A（实时控场）：在辩论陷入同义反复、两位专家胶着争吵、或者关键视角被冷落时，果断介入，实施追问（probing）、控场降温（cooldown）或话题引导（pivot）。
阶段B（辩论终局总结）：在全场辩论结束时，脱离主观偏见，提供一份结构极其严谨、思想深度极高的全场学术与战略总结报告，并审计每位专家在多轮交锋中的心智与立场变迁。

【主持风格】：
客观中立、辞锋锐利但富有礼节。善于提炼专家的核心潜台词，直击分歧本质。
```

### 5.3 Mode A: Moderator Intervention Template & Schema
#### User Prompt Template
```
【辩论议题】：{{ topic }}
【触发介入原因】：{{ trigger_reason }}（如：两方专家连续争锋导致话题停滞 / 专家 {{ quiet_expert.name }} 已连续 3 轮未发言）
【当前交锋上下文】：
{{ recent_turns_formatted }}

请以主持人第一人称发表一段现场控场陈述（60-120字），并点明接下来的发言导向：
```
#### Output JSON Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ModeratorInterventionResponse",
  "type": "object",
  "properties": {
    "intervention_type": {
      "type": "string",
      "enum": ["probing", "floor_control", "cooldown", "pivot"]
    },
    "target_agent_id": { "type": ["string", "null"] },
    "target_agent_name": { "type": ["string", "null"] },
    "content": { "type": "string", "description": "主持人现场口语化发言（60-120字）" }
  },
  "required": ["intervention_type", "target_agent_id", "target_agent_name", "content"],
  "additionalProperties": false
}
```

### 5.4 Mode B: Post-Debate Concluding Summary Template & Schema
#### User Prompt Template
```
【辩论议题】：{{ topic }}
【参会专家及初始立场】：
{{ experts_initial_stances }}

【全场辩论实录】：
{{ full_transcript }}

【最终形成的共识看板】：
{{ final_consensus }}

【最终残留的分歧看板】：
{{ final_divergence }}

请生成最终的综合研判结案报告与专家立场演进审计（严格 JSON 格式）：
```
#### Output JSON Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DebateSummaryResponse",
  "type": "object",
  "properties": {
    "summary": { "type": "string", "description": "全场辩论宏观总结综述（250-400字）" },
    "core_arguments": {
      "type": "array",
      "items": { "type": "string" },
      "description": "全场沉淀的核心交锋论点（3-5条）"
    },
    "resolved_consensus": {
      "type": "array",
      "items": { "type": "string" },
      "description": "最终达成的实质性共识列表"
    },
    "outstanding_divergences": {
      "type": "array",
      "items": { "type": "string" },
      "description": "未解的核心深层分歧列表"
    },
    "stance_audit": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "agent_id": { "type": "string" },
          "agent_name": { "type": "string" },
          "initial_stance": { "type": "string" },
          "final_stance": { "type": "string" },
          "shift_occurred": { "type": "boolean" },
          "shift_rationale": { "type": "string", "description": "立场变化或坚守的内在心理逻辑剖析" }
        },
        "required": ["agent_id", "agent_name", "initial_stance", "final_stance", "shift_occurred", "shift_rationale"],
        "additionalProperties": false
      }
    }
  },
  "required": ["summary", "core_arguments", "resolved_consensus", "outstanding_divergences", "stance_audit"],
  "additionalProperties": false
}
```

### 5.5 Few-Shot Example (Mode B Summary)
```json
{
  "summary": "本次关于‘人工智能基础大模型是否应该开源权重’的圆桌辩论历经多轮高强度思想交锋。沈清源先生代表的技术开放阵营从去中心化治理与防范寡头垄断角度，阐明了开源的不可替代性；而陆承安研究员与林晓风教授则从生存性风险、武器化滥用及穿透式法律责任维度进行了深刻制衡。最终各方在‘基于能力的梯级评估与安全红线准入’上形成了宝贵的建设性共识，但关于前沿不可逆扩散与众包自愈时滞的核心哲学分歧依然存在。这是一场具有深远行业指导意义的理性研判。",
  "core_arguments": [
    "开源权重带来的去中心化审查与普惠创新价值不可替代",
    "不可逆的权重扩散导致高阶生化与网络威胁无法被后置修补",
    "商业基础设施成本的ROI要求催生出混合架构（底座可开、集群专有）",
    "开源许可证需从免责声明转向穿透式合规与开发者尽职责任"
  ],
  "resolved_consensus": [
    "前沿高风险模型在权重开放前必须通过可验证的第三方红队安全评估",
    "应当支持非前沿基座开源以扶持学术界与中小企业自主生态"
  ],
  "outstanding_divergences": [
    "对于具备接近人类自适应能力的前沿权重，是否应当采取绝对闭源保护"
  ],
  "stance_audit": [
    {
      "agent_id": "expert_1",
      "agent_name": "沈清源",
      "initial_stance": "完全开源模型权重是技术普惠与去中心化安全的唯一通路。",
      "final_stance": "支持在设立高阶威胁前置红线与第三方测试准入的前提下实行开源。",
      "shift_occurred": true,
      "shift_rationale": "接受了陆承安关于前沿生物与网络高危能力不可逆扩散的数据与论据，立场由‘无条件激进开源’转向‘负责任的分级准入开源’。"
    },
    {
      "agent_id": "expert_2",
      "agent_name": "陆承安",
      "initial_stance": "高能力大模型权重不可逆，必须实行严格分级与闭源授权许可。",
      "final_stance": "高能力前沿模型必须闭源管制，但认同普通基础工具与学术子模型可以分级开放。",
      "shift_occurred": true,
      "shift_rationale": "认可了沈清源关于学术平权与防止单极垄断的诉求，明确划定了前沿与非前沿的监管分界。"
    }
  ]
}
```

### 5.6 Mock Engine Deterministic Fallback Rules
- Mode A: Deterministically intervenes at round 3 and round 5 in 6-round debates; addresses the expert with lowest cumulative speaking time.
- Mode B: Deterministically returns a pre-authored wrap-up summary for each of the 5 scenarios (S1 to S5), auditing all 3 to 5 participants, with at least 1-2 experts showing subtle, well-reasoned stance shifts (`shift_occurred: true`).
