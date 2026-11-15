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
import { controlDiscussion, getDiscussion, getTranscript } from '../../api/client';
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
      <div className="bg-[#131B2B] border border-[#2A364F] rounded-xl px-6 py-3 flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-3">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              status === 'running'
                ? 'bg-emerald-500 animate-ping'
                : status === 'paused'
                ? 'bg-amber-500'
                : status === 'completed'
                ? 'bg-blue-500'
                : 'bg-slate-500'
            }`}
          />
          <h2 className="text-sm font-bold text-white tracking-wide truncate max-w-md">
            {topic} {discussionId ? `(#${discussionId.slice(0, 8)})` : ''}
          </h2>
          <span className="text-xs px-2.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
            第 {currentRound} / {maxRounds} 轮
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded font-medium ${
              status === 'running'
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : status === 'paused'
                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                : status === 'completed'
                ? 'bg-purple-500/10 text-purple-300 border border-purple-500/20'
                : 'bg-slate-800 text-slate-300'
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

        <div className="flex items-center gap-2">
          {status !== 'running' && status !== 'completed' && status !== 'terminated' && (
            <button
              onClick={status === 'paused' ? handleResume : handleStart}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
              {status === 'paused' ? '继续交锋' : '开启圆桌辩论'}
            </button>
          )}

          {status === 'running' && (
            <button
              onClick={handlePause}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold shadow transition-colors"
            >
              <Pause className="w-3.5 h-3.5" />
              暂停
            </button>
          )}

          {status !== 'completed' && status !== 'terminated' && (
            <button
              onClick={handleTerminate}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow transition-colors"
            >
              <Square className="w-3.5 h-3.5" />
              提前结题
            </button>
          )}

          {status === 'completed' && (
            <button
              onClick={onTerminate}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow transition-colors"
            >
              <FileCheck className="w-3.5 h-3.5" />
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
          <div className="bg-[#131B2B] border border-[#2A364F] rounded-xl p-4 shadow">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-purple-400" />
              <span className="text-xs font-bold text-white">
                {moderator ? moderator.name : '主持人·林知远'}
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 ml-auto">
                全局仲裁与控场
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed bg-[#1A2337] p-2.5 rounded-lg border border-[#2A364F]/50">
              {moderatorMessage}
            </p>
          </div>

          {/* Expert Monitors */}
          <div className="flex-1 flex flex-col gap-2.5">
            <span className="text-xs font-semibold text-slate-400 px-1">
              专家监控席 ({experts.length > 0 ? experts.length : 4} 位)
            </span>
            {experts.map((exp) => {
              const isSpeaking = activeSpeakerId === exp.id;
              const handRaised = handRaisedMap[exp.id];

              return (
                <div
                  key={exp.id}
                  className={`bg-[#131B2B] border rounded-xl p-3.5 transition-all duration-300 relative overflow-hidden ${
                    isSpeaking
                      ? 'border-blue-500 shadow-lg shadow-blue-500/30 ring-2 ring-blue-500/40'
                      : 'border-[#2A364F]'
                  }`}
                >
                  <div
                    className="absolute top-0 left-0 bottom-0 w-1.5"
                    style={{ backgroundColor: exp.color_hex }}
                  />
                  <div className="flex items-center justify-between mb-1.5 pl-1">
                    <span className="font-bold text-xs text-white flex items-center gap-1.5">
                      {exp.name}
                      {isSpeaking && (
                        <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-normal">
                          <Volume2 className="w-3 h-3 animate-bounce" />
                          发言中
                        </span>
                      )}
                    </span>
                    <span
                      className="text-[10px] px-1.5 py-0.5 rounded font-medium"
                      style={{ backgroundColor: `${exp.color_hex}22`, color: exp.color_hex }}
                    >
                      {exp.occupation}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-400 pl-1 leading-snug line-clamp-2">
                    {exp.stance}
                  </p>

                  {/* Hand-raising badge */}
                  {handRaised && !isSpeaking && (
                    <div className="mt-2 pl-1 flex items-center gap-1.5 text-[10px] text-amber-300 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-md animate-pulse">
                      <Hand className="w-3 h-3 text-amber-400" />
                      <span>
                        申请抢答 [{handRaised.action_type}] 优先级: {handRaised.priority_score}
                      </span>
                    </div>
                  )}

                  <div className="mt-2 pl-1 flex items-center justify-between text-[10px] text-slate-500 border-t border-[#2A364F]/50 pt-1">
                    <span>已发言: {exp.total_turns_spoken || 0} 轮</span>
                    <span style={{ color: exp.color_hex }}>● 席位活跃</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Center Column: Teleprompter Streaming Transcript */}
        <div className="col-span-6 bg-[#131B2B] border border-[#2A364F] rounded-xl flex flex-col overflow-hidden shadow">
          <div className="px-5 py-3 border-b border-[#2A364F] flex items-center justify-between bg-[#1A2337]/50">
            <span className="text-xs font-bold text-white flex items-center gap-2">
              <Radio className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
              实况交锋实录 (Live Teleprompter Feed)
            </span>
            <span className="text-xs text-slate-400">{transcript.length} 条发言已记录</span>
          </div>

          <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-4">
            {transcript.length === 0 && !streamingChunk ? (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 text-xs">
                <Radio className="w-8 h-8 mb-2 opacity-30 animate-pulse" />
                点击上方“开启圆桌辩论”按钮，专家将基于 8 因子动态仲裁算法自主举手与交锋
              </div>
            ) : (
              <>
                {transcript.map((t) => {
                  const speaker = participants.find((p) => p.id === t.speaker_id);
                  const color = speaker?.color_hex || '#3B82F6';

                  return (
                    <div
                      key={t.id}
                      className="bg-[#1A2337] border border-[#2A364F] rounded-xl p-4 shadow-sm relative overflow-hidden"
                    >
                      <div
                        className="absolute top-0 left-0 bottom-0 w-1"
                        style={{ backgroundColor: color }}
                      />
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-white">{t.speaker_name}</span>
                          <span className="text-[10px] text-slate-400">第 {t.turn_number} 顺位</span>
                        </div>
                        <span
                          className="text-[10px] px-2 py-0.5 rounded font-medium border"
                          style={{
                            backgroundColor: `${color}15`,
                            color: color,
                            borderColor: `${color}30`,
                          }}
                        >
                          [{t.action_type}]
                        </span>
                      </div>
                      <p className="text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">
                        {t.content}
                      </p>
                    </div>
                  );
                })}

                {/* Active Streaming Speech Teleprompter */}
                {activeSpeakerId && (
                  <div className="bg-[#1A2337] border border-blue-500/50 rounded-xl p-4 shadow-md ring-1 ring-blue-500/20">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-xs text-blue-300 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                        {activeSpeakerName || '专家'} 正在现场发言...
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30 font-medium">
                        实时打字机流 (Typing Stream)
                      </span>
                    </div>
                    <p className="text-xs text-slate-100 leading-relaxed whitespace-pre-wrap">
                      {streamingChunk}
                      <span className="inline-block w-1.5 h-3.5 bg-blue-400 ml-0.5 animate-pulse" />
                    </p>
                  </div>
                )}

                <div ref={transcriptEndRef} />
              </>
            )}
          </div>
        </div>

        {/* Right Column: Real-Time Consensus & Divergence Sideboards */}
        <div className="col-span-3 flex flex-col gap-4 overflow-y-auto">
          {/* Consensus Board */}
          <div className="bg-[#131B2B] border border-[#2A364F] rounded-xl p-4 shadow flex-1">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <h3 className="text-xs font-bold text-white">共识收敛看板</h3>
            </div>
            {consensusItems.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-6">
                辩论推进中，系统将动态捕捉多方一致性论点
              </p>
            ) : (
              <div className="flex flex-col gap-2.5">
                {consensusItems.map((c) => (
                  <div
                    key={c.id}
                    className="bg-[#1A2337] border border-emerald-500/20 rounded-lg p-3"
                  >
                    <p className="text-xs text-slate-200 mb-1 leading-relaxed">{c.statement}</p>
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-slate-400">
                        支持: {Array.isArray(c.supporting_agents) ? c.supporting_agents.join(', ') : ''}
                      </span>
                      <span className="text-emerald-400 font-semibold">
                        可信度: {(c.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Divergence Board */}
          <div className="bg-[#131B2B] border border-[#2A364F] rounded-xl p-4 shadow flex-1">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs font-bold text-white">激烈争议焦点</h3>
            </div>
            {divergenceItems.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-6">
                实时追踪对立观点与博弈张力
              </p>
            ) : (
              <div className="flex flex-col gap-2.5">
                {divergenceItems.map((d) => (
                  <div
                    key={d.id}
                    className="bg-[#1A2337] border border-amber-500/20 rounded-lg p-3"
                  >
                    <p className="text-xs text-slate-200 mb-1 leading-relaxed">{d.tension}</p>
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-slate-400">对立博弈</span>
                      <span className="text-rose-400 font-semibold">
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
