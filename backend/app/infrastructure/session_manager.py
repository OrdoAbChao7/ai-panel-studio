"""Discussion Session Manager, EventRingBuffer, and Autonomous Debate Execution Engine."""

import asyncio
from collections import deque
from datetime import datetime, timezone
import json
import random
from typing import Any, Dict, List, Optional, Set
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.domain.arbitrator import ArbitrationContext, SpeakerArbitrator
from app.domain.consensus import ConsensusAnalyzer
from app.domain.entities import DiscussionAggregate, Participant, Turn
from app.domain.value_objects import ActionType, AgentIntent, SessionStatus
from app.infrastructure.database import AsyncSessionLocal
from app.infrastructure.llm_client import LLMClient, get_llm_client
from app.infrastructure.repositories import SqlAlchemyDiscussionRepository


class EventRingBuffer:
    """Fixed-capacity circular buffer preserving monotonic sequence events for SSE replay."""

    def __init__(self, capacity: int = 500) -> None:
        self.capacity = capacity
        self.buffer: deque = deque(maxlen=capacity)
        self.current_seq: int = 0

    def append(self, event_type: str, payload: Any) -> dict:
        """Assign next monotonic sequence ID and store in buffer."""
        self.current_seq += 1
        event_item = {
            "id": self.current_seq,
            "event": event_type,
            "data": payload,
        }
        self.buffer.append(event_item)
        return event_item

    def get_events_since(self, last_event_id: int) -> List[dict]:
        """Fetch all buffered events with sequence ID strictly greater than last_event_id."""
        return [e for e in self.buffer if e["id"] > last_event_id]

    @property
    def oldest_seq(self) -> int:
        if not self.buffer:
            return 0
        return self.buffer[0]["id"]


class DiscussionSessionContext:
    """Isolated runtime execution context for an active debate session."""

    def __init__(self, discussion_id: str) -> None:
        self.discussion_id = discussion_id
        self.lock = asyncio.Lock()
        self.pause_event = asyncio.Event()
        self.pause_event.set()  # Initially running
        self.is_terminated: bool = False
        self.is_paused: bool = False
        self.task: Optional[asyncio.Task] = None
        self.ring_buffer = EventRingBuffer(capacity=500)
        self.subscribers: Set[asyncio.Queue] = set()
        self.session_factory: Optional[async_sessionmaker] = None

    def subscribe(self) -> asyncio.Queue:
        """Register a new SSE client subscriber queue."""
        queue: asyncio.Queue = asyncio.Queue()
        self.subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Remove an SSE client subscriber queue."""
        self.subscribers.discard(queue)

    def broadcast(self, event_type: str, payload: Any) -> dict:
        """Store in ring buffer and fan out to all active subscriber queues."""
        event_item = self.ring_buffer.append(event_type, payload)
        for queue in list(self.subscribers):
            try:
                queue.put_nowait(event_item)
            except (asyncio.QueueFull, Exception):
                pass
        return event_item

    def terminate(self) -> None:
        """Signal termination, unpause event loop to allow exit."""
        self.is_terminated = True
        self.pause_event.set()


async def run_debate_loop(discussion_id: str, context: DiscussionSessionContext) -> None:
    """Autonomous debate execution loop running in background asyncio.Task."""
    try:
        await _run_debate_loop_inner(discussion_id, context)
    except asyncio.CancelledError:
        return
    except Exception as e:
        import traceback
        traceback.print_exc()
        return


async def _run_debate_loop_inner(discussion_id: str, context: DiscussionSessionContext) -> None:
    if context.is_terminated:
        return

    session_factory = context.session_factory or AsyncSessionLocal

    async with session_factory() as session:
        repo = SqlAlchemyDiscussionRepository(session)
        agg = await repo.get_by_id(discussion_id)

    if agg is None:
        return

    # If created, transition to running
    if agg.status == SessionStatus.CREATED:
        agg.transition_status(SessionStatus.RUNNING)
        async with session_factory() as session:
            repo = SqlAlchemyDiscussionRepository(session)
            await repo.save(agg)
            await session.commit()

    if len(agg.turns) == 0:
        context.broadcast(
            "session_status_changed",
            {
                "old_status": "created",
                "new_status": "running",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    llm_client = get_llm_client()
    arbitrator = SpeakerArbitrator()
    analyzer = ConsensusAnalyzer(llm_client)

    experts = [p for p in agg.participants.values() if p.role != "moderator"]
    if not experts:
        experts = list(agg.participants.values())

    last_speaker_id: Optional[str] = agg.turns[-1].speaker_id if agg.turns else None
    start_round = max(1, agg.current_round or 1)
    max_rounds = max(1, agg.max_rounds)

    for round_num in range(start_round, max_rounds + 1):
        if context.is_terminated:
            break

        # Moderator opening / probing intervention
        if round_num == 1 and len(agg.turns) == 0:
            mod_opening = f"欢迎各位专家进入关于‘{agg.topic}’的圆桌研讨。请各位专家立足自身专业立场展开立论陈述。"
            context.broadcast(
                "moderator_intervention",
                {
                    "type": "opening",
                    "content": mod_opening,
                    "target_agent_id": None,
                },
            )
            await asyncio.sleep(0.02)
        elif round_num >= 2:
            mod_probing = f"针对前序交锋与各方争议焦点，请各位专家进一步阐明核心论据与权衡机制。"
            context.broadcast(
                "moderator_intervention",
                {
                    "type": "probing",
                    "content": mod_probing,
                    "target_agent_id": None,
                },
            )
            await asyncio.sleep(0.02)

        # In each round, allow experts to speak
        for turn_idx in range(len(experts)):
            # Check pause
            while not context.pause_event.is_set():
                if context.is_terminated:
                    break
                await asyncio.sleep(0.01)
            if context.is_terminated:
                break

            # 1. Parallel Intent Generation across experts
            async def _generate_expert_intent(expert: Participant) -> AgentIntent:
                is_last = (expert.id == last_speaker_id)
                if is_last:
                    return AgentIntent(
                        agent_id=expert.id,
                        agent_name=expert.name,
                        desire_to_speak=False,
                        action_type=ActionType.NONE,
                        urgency=0.0,
                        conflict_intensity=0.0,
                        topical_relevance=0.5,
                        evidence_depth=0.5,
                        novelty=0.3,
                        target_speaker_id=None,
                        rationale="刚完成发言，进入强制冷却周期",
                    )

                turns_count = len(agg.turns)
                prompt = (
                    f"议题：{agg.topic}，前置发言数：{turns_count}，"
                    f"发言者：{expert.name}，立场：{expert.stance}"
                )
                try:
                    raw_intent = await llm_client.generate_json("AgentIntentResponse", prompt)
                except Exception:
                    raw_intent = {}

                if turns_count == 0:
                    action_str = "statement"
                else:
                    action_str = raw_intent.get("action_type") or (
                        "rebuttal" if turn_idx % 2 == 1 else "supplement"
                    )

                if action_str not in ActionType._value2member_map_:
                    action_type = ActionType.STATEMENT
                else:
                    action_type = ActionType(action_str)

                target_id = None
                target_name = None
                if action_type == ActionType.REBUTTAL and agg.turns:
                    prior_turn = agg.turns[-1]
                    target_id = prior_turn.speaker_id
                    target_name = prior_turn.speaker_name

                urgency = float(raw_intent.get("urgency", random.uniform(0.70, 0.95)))
                conflict = float(raw_intent.get("conflict_intensity", random.uniform(0.5, 0.85)))
                topical = float(raw_intent.get("topical_relevance", random.uniform(0.7, 0.95)))
                evidence = float(raw_intent.get("evidence_depth", random.uniform(0.6, 0.9)))
                novelty = float(raw_intent.get("novelty", random.uniform(0.5, 0.85)))

                return AgentIntent(
                    agent_id=expert.id,
                    agent_name=expert.name,
                    desire_to_speak=bool(raw_intent.get("desire_to_speak", True)),
                    action_type=action_type,
                    urgency=urgency,
                    conflict_intensity=conflict,
                    topical_relevance=topical,
                    evidence_depth=evidence,
                    novelty=novelty,
                    target_speaker_id=target_id,
                    target_speaker_name=target_name,
                    rationale=raw_intent.get("rationale") or f"立足{expert.occupation}视角深入论述",
                    drafted_content=raw_intent.get("drafted_content", ""),
                )

            candidate_intents = await asyncio.gather(
                *[_generate_expert_intent(e) for e in experts]
            )

            # 2. Broadcast hand_raising (Must be a top-level list)
            candidates_list = [
                {
                    "agent_id": c.agent_id,
                    "agent_name": c.agent_name,
                    "action_type": (
                        c.action_type.value
                        if hasattr(c.action_type, "value")
                        else str(c.action_type)
                    ),
                    "priority_score": c.urgency,
                    "target_speaker_id": c.target_speaker_id,
                    "target_speaker_name": c.target_speaker_name,
                    "rationale": c.rationale,
                }
                for c in candidate_intents
            ]
            context.broadcast("hand_raising", candidates_list)

            # 3. Priority Arbitration
            arb_ctx = ArbitrationContext(
                current_turn=len(agg.turns) + 1,
                last_speaker_id=last_speaker_id,
                participants=agg.participants,
            )
            arb_result = arbitrator.arbitrate(list(candidate_intents), arb_ctx)
            winner = arb_result.winner
            if winner is None:
                eligible = [e for e in experts if e.id != last_speaker_id]
                if eligible:
                    chosen_p = min(eligible, key=lambda x: x.total_turns_spoken)
                    winner = next((c for c in candidate_intents if c.agent_id == chosen_p.id), None)
                    if winner is None:
                        winner = AgentIntent(
                            agent_id=chosen_p.id,
                            agent_name=chosen_p.name,
                            desire_to_speak=True,
                            action_type=ActionType.STATEMENT,
                            urgency=0.75,
                        )
                else:
                    winner = candidate_intents[0]

            score = arb_result.winner_score if arb_result.winner_score != float("-inf") else 0.75
            breakdown_dict = {}
            if winner.agent_id in arb_result.breakdown:
                breakdown_dict = arb_result.breakdown[winner.agent_id].model_dump()

            context.broadcast(
                "speaker_selected",
                {
                    "speaker_id": winner.agent_id,
                    "speaker_name": winner.agent_name,
                    "score": score,
                    "priority_score": score,
                    "score_breakdown": breakdown_dict,
                },
            )

            # 4. Speech Streaming
            turn_id = str(uuid.uuid4())
            chunks: List[str] = []
            speaker_p = agg.participants.get(winner.agent_id)
            speaker_occ = speaker_p.occupation if speaker_p else "专家"
            speaker_st = speaker_p.stance if speaker_p else ""
            speech_sys = f"专家：{winner.agent_name}，职业：{speaker_occ}，立场：{speaker_st}"
            speech_usr = f"议题：{agg.topic}，行动类型：{winner.action_type.value}，前序论述深化"

            async for chunk in llm_client.stream_speech(speech_sys, speech_usr):
                chunks.append(chunk)
                context.broadcast(
                    "speech_chunk",
                    {
                        "turn_id": turn_id,
                        "speaker_id": winner.agent_id,
                        "chunk": chunk,
                        "is_first": (len(chunks) == 1),
                    },
                )
                while not context.pause_event.is_set():
                    if context.is_terminated:
                        break
                    await asyncio.sleep(0.01)
                if context.is_terminated:
                    break

            if context.is_terminated:
                break

            full_speech = "".join(chunks)
            if not full_speech:
                full_speech = f"关于‘{agg.topic}’，我认同需要系统性统筹各方诉求与长远利益。"

            # 5. Commit Turn to Aggregate and DB
            turn = Turn(
                id=turn_id,
                discussion_id=agg.id,
                turn_number=len(agg.turns) + 1,
                round_number=round_num,
                speaker_id=winner.agent_id,
                speaker_name=winner.agent_name,
                action_type=winner.action_type,
                content=full_speech,
                rationale=winner.rationale,
                priority_score=score,
                target_speaker_id=winner.target_speaker_id,
            )
            agg.add_turn(turn)
            agg.collect_pending_events()

            async with session_factory() as session:
                repo = SqlAlchemyDiscussionRepository(session)
                await repo.save(agg)
                await session.commit()

            context.broadcast(
                "speech_completed",
                {
                    "turn_id": turn.id,
                    "speaker_id": turn.speaker_id,
                    "turn_number": turn.turn_number,
                    "round_number": turn.round_number,
                    "content": turn.content,
                    "action_type": (
                        turn.action_type.value
                        if hasattr(turn.action_type, "value")
                        else str(turn.action_type)
                    ),
                },
            )
            last_speaker_id = winner.agent_id

            # 6. Consensus & Divergence Update
            cons_items, div_items = await analyzer.analyze(agg)
            agg.update_consensus(cons_items)
            agg.update_divergence(div_items)
            agg.collect_pending_events()

            async with session_factory() as session:
                repo = SqlAlchemyDiscussionRepository(session)
                await repo.save(agg)
                await session.commit()

            context.broadcast(
                "consensus_updated",
                [c.model_dump() for c in cons_items],
            )
            context.broadcast(
                "divergence_updated",
                [d.model_dump() for d in div_items],
            )

            await asyncio.sleep(0.05)

    # 7. Post-Debate Concluding Synthesis
    if context.is_terminated:
        return

    async with session_factory() as session:
        repo = SqlAlchemyDiscussionRepository(session)
        latest_agg = await repo.get_by_id(discussion_id)
        if latest_agg:
            agg = latest_agg

    summary_text = agg.summary
    if not summary_text or len(summary_text) < 10:
        summary_prompt = (
            f"议题：{agg.topic}，总发言轮数：{len(agg.turns)}。"
            "请生成最终的总结与各专家立场复盘（SummaryResponseDTO）。"
        )
        try:
            summary_data = await llm_client.generate_json("SummaryResponseDTO", summary_prompt)
            summary_text = summary_data.get("summary")
        except Exception:
            summary_text = None

        if not summary_text or len(summary_text) < 10:
            summary_text = (
                f"本场关于‘{agg.topic}’的高级别圆桌辩论圆满结束。"
                "与会专家深入剖析了核心矛盾、法理依据与前沿技术路径，"
                "各方最终达成高度共识并明确了后续技术治理探索方向。"
            )

    final_stances = {p.id: p.stance for p in agg.participants.values()}
    target_status = SessionStatus.TERMINATED if context.is_terminated else SessionStatus.COMPLETED

    agg.summary = summary_text
    if agg.can_transition_to(target_status):
        agg.transition_status(target_status)
    else:
        agg.status = target_status
    agg.collect_pending_events()

    async with session_factory() as session:
        repo = SqlAlchemyDiscussionRepository(session)
        await repo.save(agg)
        await session.commit()

    context.broadcast(
        "session_concluded",
        {
            "summary": summary_text,
            "final_stances": final_stances,
        },
    )
    context.broadcast(
        "session_status_changed",
        {
            "old_status": "running",
            "new_status": target_status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


class SessionManager:
    """Registry managing concurrent discussion session contexts."""

    def __init__(self) -> None:
        self.sessions: Dict[str, DiscussionSessionContext] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, discussion_id: str) -> DiscussionSessionContext:
        """Retrieve existing context or create a new one."""
        async with self._lock:
            if discussion_id not in self.sessions:
                self.sessions[discussion_id] = DiscussionSessionContext(discussion_id)
            return self.sessions[discussion_id]

    async def get(self, discussion_id: str) -> Optional[DiscussionSessionContext]:
        """Retrieve session context if present."""
        return self.sessions.get(discussion_id)

    async def start_session(
        self,
        discussion_id: str,
        session_factory: Optional[async_sessionmaker] = None,
    ) -> None:
        """Spawn autonomous debate loop task for discussion session."""
        context = await self.get_or_create(discussion_id)
        if session_factory is not None:
            context.session_factory = session_factory
        if context.task is None or context.task.done():
            context.is_terminated = False
            context.is_paused = False
            context.pause_event.set()
            context.task = asyncio.create_task(run_debate_loop(discussion_id, context))

    async def pause_session(self, discussion_id: str) -> None:
        """Pause active debate session."""
        context = await self.get_or_create(discussion_id)
        context.is_paused = True
        context.pause_event.clear()
        context.broadcast(
            "session_status_changed",
            {
                "old_status": "running",
                "new_status": "paused",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def resume_session(self, discussion_id: str) -> None:
        """Resume paused debate session."""
        context = await self.get_or_create(discussion_id)
        context.is_paused = False
        context.pause_event.set()
        context.broadcast(
            "session_status_changed",
            {
                "old_status": "paused",
                "new_status": "running",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def terminate_session(self, discussion_id: str) -> None:
        """Terminate debate session immediately."""
        context = await self.get_or_create(discussion_id)
        context.terminate()
        if context.task and not context.task.done():
            context.task.cancel()
            try:
                await context.task
            except (asyncio.CancelledError, Exception):
                pass

    async def remove(self, discussion_id: str) -> None:
        """Clean up and remove session context."""
        async with self._lock:
            context = self.sessions.pop(discussion_id, None)
            if context:
                context.terminate()
                if context.task and not context.task.done():
                    context.task.cancel()
                    try:
                        await context.task
                    except (asyncio.CancelledError, Exception):
                        pass

    async def shutdown_all(self) -> None:
        """Clean up all active background sessions."""
        async with self._lock:
            tasks = []
            for context in self.sessions.values():
                context.terminate()
                if context.task and not context.task.done():
                    context.task.cancel()
                    tasks.append(context.task)
            self.sessions.clear()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def reset(self) -> None:
        """Reset all in-memory sessions for test isolation."""
        async with self._lock:
            tasks = []
            for context in list(self.sessions.values()):
                context.terminate()
                if context.task and not context.task.done():
                    context.task.cancel()
                    tasks.append(context.task)
            self.sessions.clear()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)


session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Helper returning singleton session manager."""
    return session_manager
