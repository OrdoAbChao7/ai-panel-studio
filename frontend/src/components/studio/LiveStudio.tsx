import { useEffect, useRef, useState, type FC } from 'react';
import {
  Play,
  Pause,
  Square,
  Radio,
  Shield,
  CheckCircle2,
  AlertTriangle,
  Hand,
  Volume2,
  FileCheck,
} from 'lucide-react';
import { Turn, ConsensusItem, DivergenceItem, Participant, SessionStatus } from '../../types';
import { controlDiscussion, getDiscussion, getSummary, getTranscript } from '../../api/client';
import { useSSE, SSEEvent } from '../../hooks/useSSE';

interface LiveStudioProps {
  discussionId?: string | null;
  onTerminate?: () => void;
}

interface HandRaiseInfo {
  action_type: string;
  priority_score: number;
  reason?: string;
}

export const LiveStudio: FC<LiveStudioProps> = ({ discussionId, onTerminate }) => {
  const [topic, setTopic] = useState('圆桌演播室');
  const [status, setStatus] = useState<SessionStatus>('created');
  const [currentRound, setCurrentRound] = useState(1);
  const [maxRounds, setMaxRounds] = useState(5);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [activeSpeakerId, setActiveSpeakerId] = useState<string | null>(null);
  const [activeSpeakerName, setActiveSpeakerName] = useState<string | null>(null);
  const [streamingChunk, setStreamingChunk] = useState<string>('');
  const [handRaisedMap, setHandRaisedMap] = useState<Record<string, HandRaiseInfo>>({});
  const [transcript, setTranscript] = useState<Turn[]>([]);
  const [consensusItems, setConsensusItems] = useState<ConsensusItem[]>([]);
  const [divergenceItems, setDivergenceItems] = useState<DivergenceItem[]>([]);
  const [moderatorMessage, setModeratorMessage] = useState<string>(
    '欢迎各位专家入席。本演播室由事件驱动多智能体自主决策发言顺序与交锋逻辑。'
  );

  const transcriptEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll teleprompter transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript, streamingChunk]);

  // Initial load
  useEffect(() => {
    if (!discussionId) return;

    getDiscussion(discussionId)
      .then((disc) => {
        setTopic(disc.topic);
        setStatus(disc.status);
        setCurrentRound(disc.current_round || 1);
        setMaxRounds(disc.max_rounds || 5);
        if (disc.participants) {
          setParticipants(disc.participants);
        }
      })
      .catch((e) => console.error('Failed to load discussion details', e));

    getTranscript(discussionId)
      .then((turns) => {
        setTranscript(turns);
      })
      .catch((e) => console.error('Failed to load transcript', e));

    // Backfill consensus/divergence boards from persisted state. The boards are
    // otherwise only populated by live SSE events, so reopening a concluded
    // discussion (or one streamed before a backend restart, once the in-memory
    // ring buffer is gone) left both panels permanently empty.
    getSummary(discussionId)
      .then((s) => {
        if (s.consensus_items?.length) setConsensusItems(s.consensus_items);
        if (s.divergence_items?.length) setDivergenceItems(s.divergence_items);
      })
      .catch((e) => console.error('Failed to load summary for boards', e));
  }, [discussionId]);

  // Handle SSE events
  const handleSSE = (event: SSEEvent) => {
    const { event: type, data } = event;

    switch (type) {
      case 'session_status_changed':
        if (data.new_status) {
          setStatus(data.new_status);
        }
        if (data.current_round) {
          setCurrentRound(data.current_round);
        }
        break;

      case 'hand_raising':
        if (data.agent_id) {
          setHandRaisedMap((prev) => ({
            ...prev,
            [data.agent_id]: {
              action_type: data.action_type || 'statement',
              priority_score: data.priority_score || 80,
              reason: data.rationale,
            },
          }));
        }
        break;

      case 'speaker_selected':
        setActiveSpeakerId(data.speaker_id);
        setActiveSpeakerName(data.speaker_name);
        setStreamingChunk('');
        // Clear hand raised badge for the selected speaker
        setHandRaisedMap((prev) => {
          const next = { ...prev };
          delete next[data.speaker_id];
          return next;
        });
        break;

      case 'speech_chunk':
        if (data.chunk) {
          setStreamingChunk((prev) => prev + data.chunk);
        }
        break;

      case 'speech_completed': {
        setActiveSpeakerId(null);
        setActiveSpeakerName(null);
        setStreamingChunk('');

        const newTurn: Turn = {
          id: data.turn_id || `turn-${Date.now()}`,
          turn_number: data.turn_number || transcript.length + 1,
          round_number: data.round_number || currentRound,
          speaker_id: data.speaker_id,
          speaker_name:
            data.speaker_name ||
            participants.find((p) => p.id === data.speaker_id)?.name ||
            'AI 专家',
          action_type: data.action_type || 'statement',
          content: data.content,
          priority_score: 85,
          timestamp: new Date().toISOString(),
        };

        setTranscript((prev) => {
          if (prev.some((t) => t.id === newTurn.id)) return prev;
          return [...prev, newTurn];
        });

        // Update turn count on participant
        setParticipants((prev) =>
          prev.map((p) =>
            p.id === data.speaker_id
              ? { ...p, total_turns_spoken: (p.total_turns_spoken || 0) + 1 }
              : p
          )
        );
        break;
      }

      case 'moderator_intervention':
        if (data.content) {
          setModeratorMessage(data.content);
        }
        break;

      case 'consensus_updated':
        if (data.item) {
          setConsensusItems((prev) => {
            const exists = prev.some((c) => c.id === data.item.id);
            if (exists) return prev;
            return [...prev, data.item];
          });
        }
        break;

      case 'divergence_updated':
        if (data.item) {
          setDivergenceItems((prev) => {
            const exists = prev.some((d) => d.id === data.item.id);
            if (exists) return prev;
            return [...prev, data.item];
          });
        }
        break;

      case 'session_concluded':
        setStatus('completed');
        setActiveSpeakerId(null);
        setStreamingChunk('');
        break;

      default:
        break;
    }
  };

  useSSE(discussionId || null, handleSSE);

  const handleStart = async () => {
    if (!discussionId) return;
    try {
      await controlDiscussion(discussionId, 'start');
      setStatus('running');
    } catch (e) {
      console.error('Failed to start discussion', e);
    }
  };

  const handlePause = async () => {
    if (!discussionId) return;
    try {
      await controlDiscussion(discussionId, 'pause');
      setStatus('paused');
    } catch (e) {
      console.error('Failed to pause discussion', e);
    }
  };

  const handleResume = async () => {
    if (!discussionId) return;
    try {
      await controlDiscussion(discussionId, 'resume');
      setStatus('running');
    } catch (e) {
      console.error('Failed to resume discussion', e);
    }
  };

  const handleTerminate = async () => {
    if (!discussionId) return;
    try {
      await controlDiscussion(discussionId, 'terminate');
      setStatus('terminated');
      onTerminate?.();
    } catch (e) {
      console.error('Failed to terminate discussion', e);
    }
  };

  const moderator = participants.find((p) => p.role === 'moderator');
  const experts = participants.filter((p) => p.role !== 'moderator');

  return (
    <div className="flex flex-col gap-4 h-[calc(100vh-6.5rem)]">
      {/* Studio Top Control Toolbar */}
      <div className="bg-surface-raised border border-hairline rounded-xl px-5 h-12 flex items-center justify-between gap-4 shadow-card">
        <div className="flex items-center gap-3 min-w-0">
          <span
            className={`w-2 h-2 rounded-full shrink-0 ${
              status === 'running'
                ? 'bg-positive animate-pulse'
                : status === 'paused'
                ? 'bg-caution'
                : status === 'completed'
                ? 'bg-accent'
                : 'bg-ink-faint'
            }`}
            aria-hidden="true"
          />
          <h2 className="text-sm font-semibold text-ink tracking-tight truncate max-w-md">
            {topic} {discussionId ? `(#${discussionId.slice(0, 8)})` : ''}
          </h2>
          <span className="text-[11px] px-2 py-0.5 rounded-pill bg-accent-soft text-accent border border-accent/20 font-medium whitespace-nowrap">
            第 {currentRound} / {maxRounds} 轮
          </span>
          <span
            className={`text-[11px] px-2 py-0.5 rounded-pill font-medium border whitespace-nowrap ${
              status === 'running'
                ? 'bg-positive/8 text-positive border-positive/25'
                : status === 'paused'
                ? 'bg-caution/8 text-caution border-caution/25'
                : status === 'completed'
                ? 'bg-accent-soft text-accent border-accent/25'
                : 'bg-surface-sunken text-ink-muted border-hairline'
            }`}
          >
            状态：
            {status === 'running'
              ? '交锋激烈进行中'
              : status === 'paused'
              ? '已暂停'
              : status === 'completed'
              ? '已结题 (Completed)'
              : status === 'terminated'
              ? '提前结束'
              : '准备就绪'}
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {status !== 'running' && status !== 'completed' && status !== 'terminated' && (
            <button
              type="button"
              onClick={status === 'paused' ? handleResume : handleStart}
              className="flex items-center gap-1.5 px-3 h-8 rounded-[8px] bg-accent hover:bg-accent-hover text-white text-xs font-medium transition-colors duration-150"
            >
              <Play className="w-3.5 h-3.5" aria-hidden="true" />
              {status === 'paused' ? '继续交锋' : '开启圆桌辩论'}
            </button>
          )}

          {status === 'running' && (
            <button
              type="button"
              onClick={handlePause}
              className="flex items-center gap-1.5 px-3 h-8 rounded-[8px] bg-surface-raised hover:bg-surface-sunken text-ink text-xs font-medium border border-edge transition-colors duration-150"
            >
              <Pause className="w-3.5 h-3.5" aria-hidden="true" />
              暂停
            </button>
          )}

          {status !== 'completed' && status !== 'terminated' && (
            <button
              type="button"
              onClick={handleTerminate}
              className="flex items-center gap-1.5 px-3 h-8 rounded-[8px] bg-surface-raised hover:bg-danger/8 text-danger text-xs font-medium border border-hairline hover:border-danger/30 transition-colors duration-150"
            >
              <Square className="w-3.5 h-3.5" aria-hidden="true" />
              提前结题
            </button>
          )}

          {status === 'completed' && (
            <button
              type="button"
              onClick={onTerminate}
              className="flex items-center gap-1.5 px-3 h-8 rounded-[8px] bg-accent hover:bg-accent-hover text-white text-xs font-medium transition-colors duration-150"
            >
              <FileCheck className="w-3.5 h-3.5" aria-hidden="true" />
              查看总结审计报告
            </button>
          )}
        </div>
      </div>

      {/* Studio 3-Panel Main Layout */}
      <div className="grid grid-cols-12 gap-4 flex-1 min-h-0">
        {/* Left Column: Moderator & Expert Monitors */}
        <div className="col-span-3 flex flex-col gap-3 overflow-y-auto pr-1">
          {/* Moderator Desk Card */}
          <div className="bg-surface-raised border border-hairline rounded-xl p-4 shadow-card">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-ink-muted" aria-hidden="true" />
              <span className="text-xs font-semibold text-ink">
                {moderator ? moderator.name : '主持人·林知远'}
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded-pill bg-surface-sunken text-ink-muted border border-hairline ml-auto whitespace-nowrap">
                全局仲裁与控场
              </span>
            </div>
            <p className="text-xs text-ink-muted leading-relaxed bg-surface-sunken p-2.5 rounded-[8px]">
              {moderatorMessage}
            </p>
          </div>

          {/* Expert Monitors */}
          <div className="flex-1 flex flex-col gap-2.5">
            <span className="text-xs font-medium text-ink-muted px-1">
              专家监控席 ({experts.length > 0 ? experts.length : 4} 位)
            </span>
            {experts.map((exp) => {
              const isSpeaking = activeSpeakerId === exp.id;
              const handRaised = handRaisedMap[exp.id];
              const color = exp.color_hex || '#4d6bfe';

              return (
                <div
                  key={exp.id}
                  className={`bg-surface-raised border rounded-xl p-3.5 pl-4 transition-all duration-200 relative overflow-hidden ${
                    isSpeaking
                      ? 'border-accent/50 ring-1 ring-accent/20 shadow-card'
                      : 'border-hairline'
                  }`}
                >
                  <div
                    className="absolute top-0 left-0 bottom-0 w-1"
                    style={{ backgroundColor: color }}
                  />
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="font-semibold text-xs text-ink flex items-center gap-1.5">
                      {exp.name}
                      {isSpeaking && (
                        <span className="flex items-center gap-1 text-[10px] text-positive font-normal">
                          <Volume2 className="w-3 h-3" aria-hidden="true" />
                          发言中
                        </span>
                      )}
                    </span>
                    <span
                      className="text-[10px] px-1.5 py-0.5 rounded-pill font-medium truncate max-w-[110px]"
                      style={{ backgroundColor: `${color}12`, color }}
                    >
                      {exp.occupation}
                    </span>
                  </div>

                  <p className="text-[11px] text-ink-muted leading-snug line-clamp-2">
                    {exp.stance}
                  </p>

                  {/* Hand-raising badge */}
                  {handRaised && !isSpeaking && (
                    <div className="mt-2 flex items-center gap-1.5 text-[10px] text-caution bg-caution/8 border border-caution/20 px-2 py-0.5 rounded-[6px]">
                      <Hand className="w-3 h-3" aria-hidden="true" />
                      <span>
                        申请抢答 [{handRaised.action_type}] 优先级: {handRaised.priority_score}
                      </span>
                    </div>
                  )}

                  <div className="mt-2 flex items-center justify-between text-[10px] text-ink-faint border-t border-hairline pt-1">
                    <span>已发言: {exp.total_turns_spoken || 0} 轮</span>
                    <span style={{ color }}>● 席位活跃</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Center Column: Teleprompter Streaming Transcript */}
        <div className="col-span-6 bg-surface-raised border border-hairline rounded-xl flex flex-col overflow-hidden shadow-card">
          <div className="px-5 h-11 border-b border-hairline flex items-center justify-between bg-surface-sidebar shrink-0">
            <span className="text-xs font-semibold text-ink flex items-center gap-2">
              <Radio className="w-3.5 h-3.5 text-accent" aria-hidden="true" />
              实况交锋实录 (Live Teleprompter Feed)
            </span>
            <span className="text-xs text-ink-muted">{transcript.length} 条发言已记录</span>
          </div>

          <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-3">
            {transcript.length === 0 && !streamingChunk ? (
              <div className="flex-1 flex flex-col items-center justify-center text-ink-faint text-xs text-center px-8">
                <Radio className="w-8 h-8 mb-2 opacity-25" aria-hidden="true" />
                点击上方“开启圆桌辩论”按钮，专家将基于 8 因子动态仲裁算法自主举手与交锋
              </div>
            ) : (
              <>
                {transcript.map((t) => {
                  const speaker = participants.find((p) => p.id === t.speaker_id);
                  const color = speaker?.color_hex || '#4d6bfe';

                  return (
                    <div
                      key={t.id}
                      className="shrink-0 bg-surface-sunken border border-hairline rounded-xl p-4 pl-5 relative overflow-hidden"
                    >
                      <div
                        className="absolute top-0 left-0 bottom-0 w-1"
                        style={{ backgroundColor: color }}
                      />
                      <div className="flex items-center justify-between mb-2 gap-3">
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="font-semibold text-xs text-ink">{t.speaker_name}</span>
                          <span className="text-[10px] text-ink-faint whitespace-nowrap">
                            第 {t.turn_number} 顺位
                          </span>
                        </div>
                        <span
                          className="text-[10px] px-2 py-0.5 rounded-pill font-medium border whitespace-nowrap"
                          style={{
                            backgroundColor: `${color}12`,
                            color: color,
                            borderColor: `${color}33`,
                          }}
                        >
                          [{t.action_type}]
                        </span>
                      </div>
                      <p className="text-xs text-ink leading-relaxed whitespace-pre-wrap">
                        {t.content}
                      </p>
                    </div>
                  );
                })}

                {/* Active Streaming Speech Teleprompter */}
                {activeSpeakerId && (
                  <div className="shrink-0 bg-accent-soft/50 border border-accent/30 rounded-xl p-4 pl-5 relative overflow-hidden">
                    <div
                      className="absolute top-0 left-0 bottom-0 w-1 bg-accent"
                    />
                    <div className="flex items-center justify-between mb-2 gap-3">
                      <span className="font-semibold text-xs text-accent flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-positive" aria-hidden="true" />
                        {activeSpeakerName || '专家'} 正在现场发言...
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-pill bg-surface-raised text-accent border border-accent/25 font-medium whitespace-nowrap">
                        实时打字机流 (Typing Stream)
                      </span>
                    </div>
                    <p className="text-xs text-ink leading-relaxed whitespace-pre-wrap">
                      {streamingChunk}
                      <span className="inline-block w-[2px] h-3.5 bg-accent ml-0.5 align-middle caret-blink" />
                    </p>
                  </div>
                )}

                <div ref={transcriptEndRef} />
              </>
            )}
          </div>
        </div>

        {/* Right Column: Real-Time Consensus & Divergence Sideboards */}
        <div className="col-span-3 flex flex-col gap-3 overflow-y-auto">
          {/* Consensus Board */}
          <div className="bg-surface-raised border border-hairline rounded-xl p-4 shadow-card flex-1">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle2 className="w-4 h-4 text-positive" aria-hidden="true" />
              <h3 className="text-xs font-semibold text-ink">共识收敛看板</h3>
            </div>
            {consensusItems.length === 0 ? (
              <p className="text-xs text-ink-faint text-center py-6 leading-relaxed">
                辩论推进中，系统将动态捕捉多方一致性论点
              </p>
            ) : (
              <div className="flex flex-col gap-2.5">
                {consensusItems.map((c) => (
                  <div
                    key={c.id}
                    className="bg-surface-sunken border border-hairline rounded-[10px] p-3"
                  >
                    <p className="text-xs text-ink mb-1.5 leading-relaxed">{c.statement}</p>
                    <div className="flex items-center justify-between gap-2 text-[10px]">
                      <span className="text-ink-muted truncate">
                        支持: {Array.isArray(c.supporting_agents) ? c.supporting_agents.join(', ') : ''}
                      </span>
                      <span className="text-positive font-semibold whitespace-nowrap">
                        可信度: {(c.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Divergence Board */}
          <div className="bg-surface-raised border border-hairline rounded-xl p-4 shadow-card flex-1">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-caution" aria-hidden="true" />
              <h3 className="text-xs font-semibold text-ink">激烈争议焦点</h3>
            </div>
            {divergenceItems.length === 0 ? (
              <p className="text-xs text-ink-faint text-center py-6 leading-relaxed">
                实时追踪对立观点与博弈张力
              </p>
            ) : (
              <div className="flex flex-col gap-2.5">
                {divergenceItems.map((d) => (
                  <div
                    key={d.id}
                    className="bg-surface-sunken border border-hairline rounded-[10px] p-3"
                  >
                    <p className="text-xs text-ink mb-1.5 leading-relaxed">{d.tension}</p>
                    <div className="flex items-center justify-between gap-2 text-[10px]">
                      <span className="text-ink-muted">对立博弈</span>
                      <span className="text-danger font-semibold whitespace-nowrap">
                        冲突烈度: {(d.intensity * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
