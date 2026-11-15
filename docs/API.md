# RESTful & SSE Interface Specification — AI Panel Studio

## 1. REST Endpoints Summary

| Method | Path | Description | Success Code |
|---|---|---|---|
| `GET` | `/api/health` | Health check endpoint | 200 OK |
| `POST` | `/api/discussions/roster/generate` | Generate candidate expert panel for a topic | 200 OK |
| `POST` | `/api/discussions` | Create a new discussion session with confirmed panel | 201 Created |
| `GET` | `/api/discussions` | List all discussions with summary statistics | 200 OK |
| `GET` | `/api/discussions/{id}` | Get detailed state of a single discussion | 200 OK |
| `POST` | `/api/discussions/{id}/start` | Start the autonomous debate execution loop | 200 OK |
| `POST` | `/api/discussions/{id}/pause` | Pause the running debate execution loop | 200 OK |
| `POST` | `/api/discussions/{id}/resume` | Resume a paused debate execution loop | 200 OK |
| `POST` | `/api/discussions/{id}/terminate` | Terminate debate execution immediately | 200 OK |
| `GET` | `/api/discussions/{id}/transcript` | Get full historical transcript turns | 200 OK |
| `GET` | `/api/discussions/{id}/summary` | Get post-debate synthesis, consensus, and stance audit | 200 OK |
| `GET` | `/api/discussions/{id}/events` | Server-Sent Events (SSE) streaming endpoint | 200 OK (Stream) |

---

## 2. REST Endpoint Details & JSON Schemas

### 2.1 Health Check
- **Endpoint**: `GET /api/health`
- **Response `200 OK`**:
  ```json
  {
    "status": "ok",
    "app": "AI Panel Studio",
    "version": "0.1.0"
  }
  ```

---

### 2.2 Generate Candidate Roster
- **Endpoint**: `POST /api/discussions/roster/generate`
- **Request Body**:
  ```json
  {
    "topic": "通用人工智能的伦理与监管边界",
    "participant_count": 4
  }
  ```
- **Validation**:
  - `topic`: non-empty string, min length 3.
  - `participant_count`: integer in range $[2, 6]$, default 4.
- **Response `200 OK`**:
  ```json
  {
    "topic": "通用人工智能的伦理与监管边界",
    "experts": [
      {
        "name": "沈清源",
        "occupation": "认知AI伦理学家",
        "stance": "主张立即实施强监管与对齐约束，优先预防不可逆的自主性失控风险",
        "perspective": "规范伦理学、价值对齐理论与长期主义风险评估",
        "color_hex": "#3B82F6"
      },
      {
        "name": "陆宏宇",
        "occupation": "前沿大模型总架构师",
        "stance": "主张通过技术创新与开源生态自发演进解决安全问题，反对扼杀创新的过早强管制",
        "perspective": "工程实用主义、系统演化论与计算博弈论",
        "color_hex": "#10B981"
      },
      {
        "name": "周思敏",
        "occupation": "科技反垄断与数字法学专家",
        "stance": "主张确立明确的算法法律追责机制，防止科技寡头借开源之名规避侵权与合规责任",
        "perspective": "法经济学、主体责任法理与市场反垄断",
        "color_hex": "#F59E0B"
      },
      {
        "name": "韩立诚",
        "occupation": "战略竞争与技术地缘政治学者",
        "stance": "主张在国家科技主权与产业战略优势前提下审视监管节奏，避免单边自缚手脚",
        "perspective": "结构现实主义、科技冷战博弈与产业安全",
        "color_hex": "#8B5CF6"
      }
    ]
  }
  ```

---

### 2.3 Create Discussion Session
- **Endpoint**: `POST /api/discussions`
- **Request Body**:
  ```json
  {
    "topic": "通用人工智能的伦理与监管边界",
    "max_rounds": 5,
    "participants": [
      {
        "name": "沈清源",
        "occupation": "认知AI伦理学家",
        "stance": "主张强监管与价值对齐",
        "perspective": "伦理与对齐",
        "color_hex": "#3B82F6",
        "role": "expert"
      },
      {
        "name": "陆宏宇",
        "occupation": "前沿大模型总架构师",
        "stance": "主张技术自发演进与开源自由",
        "perspective": "工程实用主义",
        "color_hex": "#10B981",
        "role": "expert"
      }
    ]
  }
  ```
- **Response `201 Created`**:
  ```json
  {
    "id": "c1f7b024-871d-48ef-b0a6-5744cb89d311",
    "topic": "通用人工智能的伦理与监管边界",
    "status": "created",
    "current_round": 0,
    "max_rounds": 5,
    "participants": [
      {
        "id": "p-101",
        "name": "沈清源",
        "occupation": "认知AI伦理学家",
        "stance": "主张强监管与价值对齐",
        "perspective": "伦理与对齐",
        "color_hex": "#3B82F6",
        "role": "expert",
        "total_turns_spoken": 0
      }
    ],
    "created_at": "2026-11-15T09:40:00Z"
  }
  ```

---

### 2.4 List Discussions
- **Endpoint**: `GET /api/discussions`
- **Response `200 OK`**:
  ```json
  [
    {
      "id": "c1f7b024-871d-48ef-b0a6-5744cb89d311",
      "topic": "通用人工智能的伦理与监管边界",
      "status": "created",
      "current_round": 0,
      "max_rounds": 5,
      "participant_count": 4,
      "created_at": "2026-11-15T09:40:00Z"
    }
  ]
  ```

---

### 2.5 Get Discussion Details
- **Endpoint**: `GET /api/discussions/{id}`
- **Response `200 OK`**:
  ```json
  {
    "id": "c1f7b024-871d-48ef-b0a6-5744cb89d311",
    "topic": "通用人工智能的伦理与监管边界",
    "status": "running",
    "current_round": 2,
    "max_rounds": 5,
    "participants": [
      {
        "id": "p-101",
        "name": "沈清源",
        "occupation": "认知AI伦理学家",
        "stance": "主张强监管与价值对齐",
        "perspective": "伦理与对齐",
        "color_hex": "#3B82F6",
        "role": "expert",
        "total_turns_spoken": 1
      }
    ],
    "summary": null,
    "created_at": "2026-11-15T09:40:00Z",
    "updated_at": "2026-11-15T09:42:00Z"
  }
  ```

---

### 2.6 Discussion Lifecycle Controls
- **Endpoints**:
  - `POST /api/discussions/{id}/start`
  - `POST /api/discussions/{id}/pause`
  - `POST /api/discussions/{id}/resume`
  - `POST /api/discussions/{id}/terminate`
- **Response `200 OK`**:
  ```json
  {
    "success": true,
    "discussion_id": "c1f7b024-871d-48ef-b0a6-5744cb89d311",
    "status": "running",
    "message": "Discussion started successfully."
  }
  ```
- **Error Response `409 Conflict`** (when transition is invalid):
  ```json
  {
    "detail": "Cannot start discussion in 'running' status.",
    "error_code": "INVALID_STATUS_TRANSITION"
  }
  ```

---

### 2.7 Historical Transcript
- **Endpoint**: `GET /api/discussions/{id}/transcript`
- **Response `200 OK`**:
  ```json
  [
    {
      "id": "t-001",
      "turn_number": 1,
      "round_number": 1,
      "speaker_id": "p-101",
      "speaker_name": "沈清源",
      "action_type": "statement",
      "content": "各位同仁，当前大模型的跃迁速度已经远超传统立法与对齐技术的发展周期...",
      "rationale": "立论破题，强调强监管与对齐紧迫性",
      "priority_score": 0.842,
      "target_speaker_id": null,
      "timestamp": "2026-11-15T09:41:00Z"
    }
  ]
  ```

---

### 2.8 Post-Debate Summary & Stance Audit
- **Endpoint**: `GET /api/discussions/{id}/summary`
- **Response `200 OK`**:
  ```json
  {
    "discussion_id": "c1f7b024-871d-48ef-b0a6-5744cb89d311",
    "topic": "通用人工智能的伦理与监管边界",
    "status": "completed",
    "summary": "本次圆桌研讨围绕通用人工智能监管边界展开了多轮激烈交锋。各方最终在重大基础设施分级安全审计与致命应用红线规制上达成共识，但在开源生态责任穿透与地缘战略竞争节奏上仍保留结构性分歧...",
    "consensus_items": [
      {
        "id": "cons-1",
        "statement": "对超过一定算力门槛的基础前沿模型实行强制性红线对齐评估与可信第三方审计",
        "supporting_agents": ["沈清源", "周思敏", "陆宏宇"],
        "confidence": 0.92,
        "resolved_turn": 8
      }
    ],
    "divergence_items": [
      {
        "id": "div-1",
        "tension": "开源模型开发者的法律侵权责任穿透边界",
        "opposing_stances": {
          "陆宏宇": "反对穿透至底层模型提供者，应由应用部署主体承担直接责任",
          "周思敏": "必须设立开发者注意义务，禁止以开源为由完全免除过错推定责任"
        },
        "intensity": 0.78,
        "is_active": true
      }
    ],
    "stance_audit": [
      {
        "participant_id": "p-101",
        "name": "沈清源",
        "initial_stance": "主张立即实施强监管与对齐约束",
        "final_stance": "坚持前沿强监管，但赞同对通用开源开发提供沙盒豁免空间",
        "shifted": true,
        "turns_spoken": 4
      }
    ]
  }
  ```

---

## 3. Server-Sent Events (SSE) Protocol

### Connection Specification
- **Endpoint**: `GET /api/discussions/{id}/events`
- **Request Headers**:
  - `Accept: text/event-stream`
  - `Last-Event-ID: <seq_id>` *(optional, for reconnection)*
- **Response Headers**:
  - `Content-Type: text/event-stream`
  - `Cache-Control: no-cache`
  - `Connection: keep-alive`
  - `X-Accel-Buffering: no`

### Event Payloads & Monotonic Sequence Format

#### 1. `session_status_changed`
```http
id: 1
event: session_status_changed
data: {"old_status": "created", "new_status": "running", "timestamp": "2026-11-15T09:40:05Z"}
```

#### 2. `hand_raising`
```http
id: 2
event: hand_raising
data: [{"agent_id": "p-101", "agent_name": "沈清源", "action_type": "statement", "priority_score": 0.842, "target_speaker_id": null, "rationale": "开篇立论"}, {"agent_id": "p-102", "agent_name": "陆宏宇", "action_type": "rebuttal", "priority_score": 0.789, "target_speaker_id": "p-101", "rationale": "反驳其过度监管论调"}]
```

#### 3. `speaker_selected`
```http
id: 3
event: speaker_selected
data: {"speaker_id": "p-101", "speaker_name": "沈清源", "score": 0.842, "score_breakdown": {"urgency": 0.90, "conflict": 0.80, "topical": 0.95, "evidence": 0.85, "novelty": 0.75, "fairness": 1.00, "cooldown_penalty": 0.0, "jitter": 0.002}}
```

#### 4. `speech_chunk`
```http
id: 4
event: speech_chunk
data: {"turn_id": "t-001", "speaker_id": "p-101", "chunk": "我认为在目前的算力演进路径下，", "is_first": true}
```

#### 5. `speech_completed`
```http
id: 5
event: speech_completed
data: {"turn_id": "t-001", "speaker_id": "p-101", "turn_number": 1, "round_number": 1, "content": "我认为在目前的算力演进路径下，任何脱离技术安全对齐的盲目扩张，都是在为未来的不可逆失控积累系统性风险。", "action_type": "statement"}
```

#### 6. `moderator_intervention`
```http
id: 6
event: moderator_intervention
data: {"type": "probing_question", "content": "陆宏宇工程师指出了开源生态对创新的根本价值，沈清源伦理学家则担忧责任真空。请两位直面核心问题：当开源模型被第三方恶意微调解除安全限制时，法律责任的边界究竟应划在模型提供方还是微调部署方？", "target_agent_id": null}
```

#### 7. `consensus_updated`
```http
id: 7
event: consensus_updated
data: [{"statement": "同意关键基础设施领域的AI模型必须具备可溯源的安全评估日志", "supporting_agents": ["沈清源", "陆宏宇", "周思敏"], "confidence": 0.88}]
```

#### 8. `divergence_updated`
```http
id: 8
event: divergence_updated
data: [{"tension": "开源开发者责任穿透与豁免权界限", "opposing_stances": {"陆宏宇": "开发者享有避风港豁免", "周思敏": "开发者承担过错推定责任"}, "intensity": 0.82}]
```

#### 9. `session_concluded`
```http
id: 9
event: session_concluded
data: {"summary": "本次圆桌研讨顺利结束。经过5轮深层交锋，专家们在分级监管上建立了共识基线...", "final_stances": {"沈清源": "支持分级对齐监管与沙盒制度", "陆宏宇": "支持开源生态保护并接受关键接口安全要求"}}
```
