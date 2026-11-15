# Product Requirements Document (PRD) — AI Panel Studio

## 1. Product Overview & Value Proposition
- **Product Name**: AI Panel Studio (AI 圆桌研讨室)
- **Tagline**: Autonomous Multi-Agent Round-Table Debate Studio with Dynamic Intent Arbitration and Real-Time Event-Driven Streaming.
- **Value Proposition**:
  - Eliminates rigid, unnatural round-robin multi-agent workflows by introducing an autonomous, event-driven intent evaluation and 8-factor mathematical priority arbitration engine ($S_i$).
  - Delivers a television broadcast-style dark-themed studio UI (`#0B0F17`) featuring real-time expert hand-raising, glowing active speaker auras, teleprompter streaming transcripts, and live consensus/divergence sideboards.
  - Serves as a reference implementation of Specification-Driven Development (SDD), Domain-Driven Design (DDD), and Test-Driven Development (TDD) for high-caliber technical recruitment review.
- **Target Audience**:
  - Engineering Hiring Managers & Technical Interviewers assessing software engineering excellence, system architecture, and DDD design.
  - AI Engineers & Researchers evaluating autonomous agent interaction dynamics and non-deterministic turn-taking mechanisms.
  - Domain Specialists simulating multi-perspective debates on technology, policy, healthcare, and economic dilemmas.

---

## 2. User Personas & Core User Journeys

### Persona A: Lead System Architect (Reviewer)
- **Goal**: Audit system cleanliness, DDD separation of concerns, concurrency isolation, and zero-credential-leak security.
- **Journey**:
  1. Clones repository and inspects `.env.example`, `.gitignore`, and backend architecture.
  2. Runs automated tests covering domain logic, API integration, SQLite persistence, LLM mocks, and session isolation.
  3. Launches application in Mock mode and tests concurrent debates.
  4. Inspects Server-Sent Events (SSE) `Last-Event-ID` recovery and SQLite transaction logs.

### Persona B: AI Product Evaluator
- **Goal**: Observe multi-agent debate realism, dynamic rebuttals, consensus convergence, and moderator intervention.
- **Journey**:
  1. Enters a custom topic (e.g. "通用人工智能的伦理与监管边界") and selects 4 participants.
  2. Generates and inspects the AI expert roster (names, occupations, initial stances, and color identities).
  3. Confirms panel and launches into the Live Studio.
  4. Observes real-time hand-raising priority scores, glowing speaker aura, streaming transcript with action badges, and dynamic updates to consensus and divergence sideboards.
  5. Reviews the post-debate moderator synthesis and stance evolution audit.

### Persona C: Demo User / Casual Observer
- **Goal**: Instantly experience high-quality simulated debates without configuration.
- **Journey**:
  1. Selects one of the 5 pre-built topic chips (e.g. "开源大模型与AGI安全").
  2. Immediately sees a pre-configured 4-expert panel and clicks "进入演播室".
  3. Controls debate playback (Start, Pause, Resume, Terminate).
  4. Exports the complete transcript to Markdown or JSON.

---

## 3. Detailed Functional Requirements

### R1. Full-Stack Core & Layered Architecture
- **Layered DDD Architecture**: Strict separation of concerns across Domain, Application, Infrastructure, and Interfaces layers.
- **Backend Stack**: FastAPI (Python 3.13), SQLAlchemy 2 (async SQLite via `aiosqlite`), Pydantic 2, and asyncio.
- **Frontend Stack**: React 19, TypeScript, Vite (running on port 5174 with `strictPort: true`), and Tailwind CSS.
- **Security & Credential Hygiene**: All LLM credentials strictly loaded from environment variables (`LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`). Zero credentials exposed to the frontend or version control.
- **Offline Mock Mode**: When `LLM_API_KEY` is empty or set to `"mock"`, the system automatically activates the offline `MockLLMClient` with zero external network dependency.

### R2. Autonomous Event-Driven AI Debate Engine
- **Non-Deterministic Turn-Taking**: Turns are decided through autonomous parallel intent generation and algorithmic arbitration rather than round-robin scheduling.
- **Parallel Intent Evaluation**: In each turn, all idle experts evaluate current discussion context in parallel and produce an `AgentIntent` containing:
  - `desire_to_speak`: boolean flag.
  - `action_type`: `statement`, `rebuttal`, `supplement`, `question`, `clarification`, `consensus_proposal`, `concession`.
  - Factor scores: `urgency` ($U_i$), `conflict_intensity` ($C_i$), `topical_relevance` ($T_i$), `evidence_depth` ($E_i$), `novelty` ($N_i$) in range $[0.0, 1.0]$.
  - `target_speaker_id`: target of rebuttal or inquiry.
  - `rationale`: meta-reasoning for speaking desire.
  - `drafted_content`: summary of intended argument.
- **SpeakerArbitrator 8-Factor Scoring Formula**:
  $$S_i = 0.20 U_i + 0.25 C_i + 0.15 T_i + 0.15 E_i + 0.10 N_i + 0.15 F_i - P_{cd}(i) + \epsilon_i$$
  - Fairness score: $F_i = 1.0 - \frac{\text{turns\_spoken}_i}{\max(1, \sum_k \text{turns\_spoken}_k)}$.
  - Consecutive speaker cooldown: $P_{cd}(i) = +\infty$ if $\Delta t_i = 0$ (spoke in turn $T-1$), enforcing strict alternation invariant. For $\Delta t_i = 1$, $P_{cd}(i) = 0.4$. For $\Delta t_i \ge 2$, $P_{cd}(i) = 0.0$.
  - Micro-jitter: $\epsilon_i \sim \mathcal{U}(-0.005, 0.005)$ to break score deadlocks deterministically.
- **Real-Time Consensus & Divergence Tracking**:
  - Dynamically synthesizes agreements and emerging disagreements after each turn.
  - Consensus items track statements, supporting agents, and confidence scores.
  - Divergence items track core tension axes, opposing stances per camp, and conflict intensity.
- **Autonomous Moderator Interventions**:
  - Floor management and cooldown enforcement.
  - Socratic probing questions injected when divergence intensity exceeds 0.85 for 2 consecutive turns.
  - Concluding multi-perspective synthesis when round limit is reached.
- **Lifecycle Controls**: Non-blocking asynchronous start, pause, resume, and terminate controls.

### R3. Studio-Style Web Interface (3 Views in Chinese Dark Theme `#0B0F17`)
- **View 1: Discussion Creation (研讨室创建)**:
  - Topic input with preset chips (AGI Ethics, Remote Work, Clean Energy, Algorithm Recommendations, Commercial Space).
  - Participant count selector (slider / buttons: 2 to 6, default 4).
  - Dynamic expert panel generation displaying name, occupation, stance, perspective, and color identity.
  - Panel confirmation and direct launch into Live Studio.
- **View 2: Live Studio (研讨室直播现场)**:
  - Top Control Bar: Topic display, round indicators, status badge, Start / Pause / Resume / Terminate buttons.
  - Left Panel: Moderator broadcast desk and expert status monitors with glowing speaker aura, animated hand-raising badges, and priority scores.
  - Center Panel: Teleprompter-style real-time streaming transcript with typed action badges (`[反驳]`, `[补充]`, `[质询]`, `[共识提案]`, `[让步]`) and typewriter effect.
  - Right Panel: Real-time consensus and divergence sideboards with confidence/intensity progress bars.
- **View 3: Discussion Summary & Audit (研讨终局与审计)**:
  - Natural language moderator concluding synthesis.
  - Core argument map and final consensus/divergence ledgers.
  - Stance evolution audit table tracking initial vs. final expert stances.
  - Historical transcript review with speaker filtering and Markdown/JSON export.

### R4. Multi-Discussion Concurrency Isolation
- Multi-session concurrency where every discussion session possesses isolated state, discussion ID, participants, transcript, event sequence, task lifecycle, synchronization locks (`asyncio.Lock`), and SSE subscriptions.
- Event streaming with monotonic sequence IDs and ring-buffer reconnection recovery via `Last-Event-ID`.
- Operations on one discussion (such as pausing) do not affect concurrent sessions.

### R5. Engineering Lifecycle, Verification & Release Deliverables
- Disciplined phased engineering workflow (SDD -> DDD -> TDD -> Integration -> E2E -> Release).
- Comprehensive documentation suite in `docs/` (`PRD.md`, `DDD.md`, `ARCHITECTURE.md`, `ER_DIAGRAM.md`, `API.md`, `TEST_PLAN.md`, `PROMPTS.md`, `WORKFLOW.md`, `README.md`, `FINAL_ACCEPTANCE_REPORT.md`).
- Database seeding script (`seed.py`) with 5 complete sample discussions.
- Automated multi-tier test suites (unit, integration, mock, and E2E).
- Clean standalone release ZIP package excluding `.venv`, `node_modules`, `.env`, and temporary caches.

---

## 4. Edge Cases & Resilience Behavior

| Code | Scenario | Trigger Condition | System Behavior |
|---|---|---|---|
| E01 | Zero Speaking Desire | All candidate experts evaluate `desire_to_speak = False` | Moderator intervenes with a direct probe targeting the expert with highest fairness score $F_i$ (least turns spoken). |
| E02 | Arbitration Deadlock | Two agents obtain identical priority score $S_i$ ($|S_a - S_b| < 10^{-5}$) | Micro-jitter $\epsilon_i$ breaks tie; if still identical, deterministically select candidate with higher fairness score $F_i$, then lexicographical participant ID. |
| E03 | Consecutive Cooldown Invariant | Candidate agent spoke in turn $T-1$ ($\Delta t_i = 0$) | Strict invariant: $P_{cd}(i) = +\infty \implies S_i = -\infty$. Agent cannot be selected under any circumstances. If all other agents pass, Moderator takes the floor. |
| E04 | Invalid Lifecycle Transition | User requests `POST /start` on already `running` discussion | Return HTTP 409 Conflict with error code `INVALID_STATUS_TRANSITION`. |
| E05 | Invalid Resume Action | User requests `POST /resume` on `created` or `completed` discussion | Return HTTP 409 Conflict: "Cannot resume a session that is not in paused state." |
| E06 | Concurrent Session Isolation | Discussion A paused while Discussion B active | Discussion A sets its local `asyncio.Event` to cleared; Discussion B's event loop executes concurrently without latency or state leakage. |
| E07 | SSE Reconnection Replay | Client connects with `Last-Event-ID: 15`, current sequence is `20` | Server immediately emits missed events 16-20 from in-memory ring buffer before piping live events. |
| E08 | Ring Buffer Gap Overflow | Client reconnects with `Last-Event-ID` older than oldest buffer event | Server emits `sync_required` event, instructing client to fetch full REST snapshot via `/api/discussions/{id}`. |
| E09 | Transient LLM Failure | LLM returns HTTP 429 Rate Limit or 503 Service Unavailable | Retries with exponential backoff (2 attempts); if still failing, falls back to offline persona mock speech without crashing. |
| E10 | Unconfigured LLM Key | Server launched with empty `LLM_API_KEY` | System automatically starts in Mock mode with labeled mock status in health/API responses. |
| E11 | Participant Count Boundary | User requests roster generation with count outside $[2, 6]$ | Returns HTTP 422 Unprocessable Entity with validation error message. |
| E12 | Max Rounds Reached | Discussion hits `current_round == max_rounds` | Engine ceases expert turns, triggers moderator concluding summary, marks session as `completed`, and emits `session_concluded`. |

---

## 5. Non-Functional Requirements (NFR)
1. **Performance**: Local SSE chunk delivery latency < 50ms; arbitration evaluation < 200ms; frontend rendering at 60fps without layout thrashing.
2. **Reliability & Availability**: Graceful recovery on LLM timeouts; retry with backoff; zero unhandled 500 exceptions.
3. **Security**: Zero API credentials in frontend bundle or repository; strict CORS configuration.
4. **Compatibility**: Windows 11, Chromium-based browsers, Firefox, Safari on desktop viewports ($\ge 1280 \times 800$).
