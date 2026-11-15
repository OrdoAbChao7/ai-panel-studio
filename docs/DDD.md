# Domain-Driven Design (DDD) Specification — AI Panel Studio

## 1. Strategic Design

### 1.1 Bounded Contexts
AI Panel Studio is structured into three distinct bounded contexts with clear conceptual boundaries:

```
+-------------------------------------------------------------+
|                     Studio Web Context                      |
|  (React 19 Frontend: UI Views, Controls, SSE Subscriptions) |
+------------------------------+------------------------------+
                               | REST API & SSE Protocol
                               v
+-------------------------------------------------------------+
|                     Discussion Context                      |
|                         (Core Domain)                       |
|   Aggregates: DiscussionAggregate, Participant, Turn        |
|   Domain Services: SpeakerArbitrator, ConsensusAnalyzer     |
|   Repositories: IDiscussionRepository, IEventStreamRepo    |
+------------------------------+------------------------------+
                               | Anti-Corruption Layer (ACL)
                               v
+-------------------------------------------------------------+
|                   LLM Integration Context                   |
|                    (Supporting Domain)                      |
|       LLMClient Gateway, Prompt Templates, Mock Engine      |
+-------------------------------------------------------------+
```

1. **Discussion Context (Core Domain)**:
   - **Core Responsibilities**: Discussion aggregate lifecycle, participant registration, intent evaluation, priority arbitration, consensus and divergence tracking, moderator interventions, and domain event publishing.
   - **Characteristics**: Contains the high-value business logic and domain invariants that define the autonomous debate experience.
2. **LLM Integration Context (Supporting Domain)**:
   - **Core Responsibilities**: Acts as an Anti-Corruption Layer (ACL) isolating the domain model from LLM provider API specifics. Translates domain intent into prompts, parses structured JSON outputs, handles network retries, and powers the 100% offline Mock engine.
3. **Studio Web Context (Interface / Downstream)**:
   - **Core Responsibilities**: Consumes RESTful APIs and SSE streams; renders the 3 studio views; translates user interactions into domain commands (`StartDiscussion`, `PauseDiscussion`, `ResumeDiscussion`, `TerminateDiscussion`).

### 1.2 Context Map & Relationships
- **Studio Web Context $\rightarrow$ Discussion Context**:
  - Relationship: **Customer-Supplier** (Downstream / Upstream).
  - Integration: `Discussion Context` publishes an **Open-Host Service (OHS)** with a **Published Language (PL)** consisting of REST DTOs and SSE event payloads.
- **Discussion Context $\rightarrow$ LLM Integration Context**:
  - Relationship: **Customer-Supplier** mediated by an **Anti-Corruption Layer (ACL)**.
  - The domain interacts solely with the abstract `ILLMClient` gateway interface. Changes in LLM SDKs or model schemas never leak into core domain entities.

### 1.3 Ubiquitous Language (通用语言)
| Term (EN) | Term (ZH) | Domain Definition |
|---|---|---|
| `Discussion` | 研讨/辩论会话 | The aggregate root representing a complete multi-agent debate session around a specific topic. |
| `Participant` | 参会专家/主持人 | An autonomous entity in the debate with a specific identity, stance, and speaking history. |
| `Intent` | 发言意向 | An agent's self-generated desire to speak, declaring action type, priority score, rationale, and draft argument. |
| `Arbitration` | 发言权仲裁 | The algorithmic evaluation process selecting the next speaker based on an 8-factor mathematical scoring model. |
| `Turn` | 发言轮次 | A single atomic speech contribution delivered by a participant, committed to the transcript. |
| `Consensus` | 共识点 | A synthesized proposition agreed upon by two or more participants from differing initial stances. |
| `Divergence` | 分歧点 | An active axis of ideological, technical, or ethical conflict between opposing participant camps. |
| `Moderator Intervention` | 主持人介入 | An autonomous action taken by the moderator to probe, cool down, or pivot discussion flow. |
| `Ring Buffer` | 环形重放缓冲 | An in-memory circular event buffer preserving monotonic sequence events for `Last-Event-ID` SSE replay. |

---

## 2. Tactical Design

### 2.1 Aggregate Root: `DiscussionAggregate`
The `DiscussionAggregate` is the sole consistency boundary for debate sessions. External layers cannot modify internal participants, turns, or consensus items directly.

- **Root Entity**: `DiscussionAggregate`
  - Attributes: `id: str`, `topic: str`, `status: SessionStatus`, `current_round: int`, `max_rounds: int`, `summary: Optional[str]`, `created_at: datetime`, `updated_at: datetime`.
  - Internal Collections:
    - `participants: dict[str, Participant]`
    - `turns: list[Turn]`
    - `consensus_items: list[ConsensusItem]`
    - `divergence_items: list[DivergenceItem]`
    - `pending_events: list[DomainEvent]`

#### Aggregate Invariants Enforced by `DiscussionAggregate`:
1. **Status Transition Invariant**:
   - `created` $\rightarrow$ `running`
   - `running` $\leftrightarrow$ `paused`
   - `running` / `paused` $\rightarrow$ `completed` / `terminated`
   - Any invalid state transition raises `DomainStateError` (translated to HTTP 409 Conflict).
2. **Consecutive Speaker Cooldown Invariant**:
   - If participant $P$ spoke in turn $T-1$, participant $P$ cannot speak in turn $T$ ($\Delta t = 0 \implies P_{cd} = +\infty \implies S = -\infty$).
3. **Max Rounds Boundary Invariant**:
   - When `current_round == max_rounds`, no further expert turns are scheduled. The aggregate transitions to `completed` after generating the final summary.
4. **Speaker Identity Invariant**:
   - The speaker selected for a turn must be an active, registered participant in `discussion.participants`.
5. **Turn Immutability Invariant**:
   - Once a `Turn` is committed to the transcript, its content, speaker, action type, and turn number cannot be modified or reordered.

---

### 2.2 Entities & Value Objects

#### Entity: `Participant`
- `id: str` (UUID or unique slug)
- `discussion_id: str`
- `name: str`
- `occupation: str`
- `stance: str`
- `perspective: str`
- `color_hex: str` (Hex visual cue, e.g. `#3B82F6`)
- `role: str` (`"expert"` or `"moderator"`)
- `total_turns_spoken: int` (Tracked for fairness calculation $F_i$)
- `last_spoken_turn: Optional[int]` (Tracked for cooldown calculation $\Delta t_i$)

#### Entity: `Turn`
- `id: str`
- `discussion_id: str`
- `turn_number: int` (Monotonically increasing 1, 2, 3...)
- `round_number: int`
- `speaker_id: str`
- `speaker_name: str`
- `action_type: ActionType`
- `content: str`
- `rationale: Optional[str]`
- `priority_score: float`
- `target_speaker_id: Optional[str]`
- `timestamp: datetime`

#### Value Objects (Immutable & Self-Validating)
1. **`ActionType` (Enum)**:
   - `STATEMENT` (立论陈述)
   - `REBUTTAL` (针对反驳)
   - `SUPPLEMENT` (补充论据)
   - `QUESTION` (质询问询)
   - `CLARIFICATION` (澄清说明)
   - `CONSENSUS_PROPOSAL` (共识提案)
   - `CONCESSION` (妥协让步)
2. **`SessionStatus` (Enum)**:
   - `CREATED`
   - `RUNNING`
   - `PAUSED`
   - `COMPLETED`
   - `TERMINATED`
3. **`AgentIntent`**:
   - `agent_id: str`
   - `desire_to_speak: bool`
   - `action_type: ActionType`
   - `urgency: float` ($U_i \in [0, 1]$)
   - `conflict_intensity: float` ($C_i \in [0, 1]$)
   - `topical_relevance: float` ($T_i \in [0, 1]$)
   - `evidence_depth: float` ($E_i \in [0, 1]$)
   - `novelty: float` ($N_i \in [0, 1]$)
   - `target_speaker_id: Optional[str]`
   - `rationale: str`
   - `drafted_content: str`
4. **`SpeakerScore`**:
   - `urgency: float`
   - `conflict: float`
   - `topical: float`
   - `evidence: float`
   - `novelty: float`
   - `fairness: float`
   - `cooldown_penalty: float`
   - `jitter: float`
   - `final_score: float`
5. **`ConsensusItem`**:
   - `id: str`
   - `statement: str`
   - `supporting_agents: list[str]`
   - `confidence: float`
   - `resolved_turn: int`
6. **`DivergenceItem`**:
   - `id: str`
   - `tension: str`
   - `opposing_stances: dict[str, str]`
   - `intensity: float`
   - `is_active: bool`

---

### 2.3 Domain Services

#### 1. `SpeakerArbitrator`
- **Responsibility**: Programmatic 8-factor mathematical priority calculation and speaker selection.
- **Interface**:
  ```python
  class SpeakerArbitrator:
      def arbitrate(
          self,
          candidates: list[AgentIntent],
          context: ArbitrationContext,
      ) -> ArbitrationResult: ...
  ```
- **Formula**:
  $$S_i = 0.20 U_i + 0.25 C_i + 0.15 T_i + 0.15 E_i + 0.10 N_i + 0.15 F_i - P_{cd}(i) + \epsilon_i$$
- **Operational Factor Definitions**:
  - **Urgency ($U_i$)**: Subjective drive from candidate intent.
  - **Conflict ($C_i$)**: Ideological distance and direct challenge to prior speaker.
  - **Topical Relevance ($T_i$)**: Semantic alignment with the discussion core topic.
  - **Evidence Depth ($E_i$)**: Presence of data, empirical precedents, or formal proofs.
  - **Novelty ($N_i$)**: Cognitive distance from already established transcript points.
  - **Fairness ($F_i$)**:
    $$F_i = 1.0 - \frac{\text{turns\_spoken}_i}{\max(1, \sum_{k} \text{turns\_spoken}_k)}$$
  - **Cooldown Penalty ($P_{cd}(i)$)**:
    $$P_{cd}(i) = \begin{cases} +\infty & \text{if } \Delta t_i = 0 \\ 0.4 / \Delta t_i & \text{if } \Delta t_i = 1 \\ 0.0 & \text{if } \Delta t_i \ge 2 \end{cases}$$
  - **Micro-Jitter ($\epsilon_i$)**: $\epsilon_i \sim \mathcal{U}(-0.005, 0.005)$.

#### 2. `ConsensusAnalyzer`
- **Responsibility**: Inspects newly completed turn against existing consensus/divergence collections to detect convergence and emerging controversy.
- **Interface**:
  ```python
  class ConsensusAnalyzer:
      async def analyze_turn(
          self,
          turn: Turn,
          discussion: DiscussionAggregate,
      ) -> tuple[list[ConsensusItem], list[DivergenceItem]]: ...
  ```

#### 3. `ModeratorPolicy`
- **Responsibility**: Decides whether the moderator should intervene based on conflict thresholds, quiet expert detection, and debate milestones.
- **Interface**:
  ```python
  class ModeratorPolicy:
      def evaluate(
          self,
          discussion: DiscussionAggregate,
      ) -> Optional[ModeratorAction]: ...
  ```

---

### 2.4 Domain Events
The system emits domain events to capture all meaningful state occurrences:
1. `DiscussionCreatedEvent(discussion_id, topic, participant_count)`
2. `SessionStatusChangedEvent(discussion_id, old_status, new_status)`
3. `HandRaisedEvent(discussion_id, candidate_intents)`
4. `SpeakerSelectedEvent(discussion_id, speaker_id, score, score_breakdown)`
5. `SpeechChunkProducedEvent(discussion_id, turn_id, speaker_id, chunk, is_first)`
6. `TurnCompletedEvent(discussion_id, turn)`
7. `ModeratorInterventionEvent(discussion_id, intervention_type, content, target_agent_id)`
8. `ConsensusUpdatedEvent(discussion_id, consensus_items)`
9. `DivergenceUpdatedEvent(discussion_id, divergence_items)`
10. `SessionConcludedEvent(discussion_id, summary, final_stances)`

---

### 2.5 Repository Interfaces
```python
from abc import ABC, abstractmethod
from typing import Optional

class IDiscussionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, discussion_id: str) -> Optional[DiscussionAggregate]:
        """Fetch discussion aggregate by ID."""
        pass

    @abstractmethod
    async def save(self, discussion: DiscussionAggregate) -> None:
        """Persist discussion aggregate and its child entities atomically."""
        pass

    @abstractmethod
    async def list_all(self) -> list[DiscussionAggregate]:
        """List all discussion summaries."""
        pass

    @abstractmethod
    async def delete(self, discussion_id: str) -> bool:
        """Delete discussion session by ID."""
        pass


class IEventStreamRepository(ABC):
    @abstractmethod
    async def append_event(self, discussion_id: str, event: DomainEvent) -> int:
        """Append event with monotonic seq_id."""
        pass

    @abstractmethod
    async def get_events_since(self, discussion_id: str, last_seq_id: int) -> list[DomainEvent]:
        """Fetch events strictly greater than last_seq_id."""
        pass
```
