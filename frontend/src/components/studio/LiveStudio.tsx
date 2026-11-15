import { useState, type FC } from 'react';
import { Play, Pause, Square, Radio, Shield, CheckCircle2, AlertTriangle } from 'lucide-react';
import { Turn, ConsensusItem, DivergenceItem } from '../../types';

interface LiveStudioProps {
  discussionId?: string | null;
  onTerminate?: () => void;
}

export const LiveStudio: FC<LiveStudioProps> = ({ discussionId, onTerminate }) => {
  const [status, setStatus] = useState<'created' | 'running' | 'paused' | 'completed' | 'terminated'>('created');
  const [activeSpeakerId] = useState<string | null>(null);
  const [transcript] = useState<Turn[]>([]);
  const [consensusItems] = useState<ConsensusItem[]>([]);
  const [divergenceItems] = useState<DivergenceItem[]>([]);

  const handleStart = async () => {
    setStatus('running');
  };

  const handlePause = async () => {
    setStatus('paused');
  };

  const handleResume = async () => {
    setStatus('running');
  };

  const handleTerminate = async () => {
    setStatus('terminated');
    onTerminate?.();
  };

  const experts = [
    { id: '1', name: '沈清源', occupation: '认知AI伦理学家', color_hex: '#3B82F6', stance: '强监管' },
    { id: '2', name: '陆宏宇', occupation: '前沿大模型总架构师', color_hex: '#10B981', stance: '开源自由' },
    { id: '3', name: '周思敏', occupation: '科技反垄断专家', color_hex: '#F59E0B', stance: '穿透合规' },
    { id: '4', name: '韩立诚', occupation: '地缘政治学者', color_hex: '#8B5CF6', stance: '战略审慎' },
  ];

  return (
    <div className="flex flex-col gap-4 h-[calc(100vh-6rem)]">
      {/* Studio Top Control Toolbar */}
      <div className="bg-[#131B2B] border border-[#2A364F] rounded-xl px-6 py-3 flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-3">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
          <h2 className="text-sm font-bold text-white tracking-wide truncate max-w-md">
            通用人工智能的伦理与监管边界 {discussionId ? `(#${discussionId.slice(0, 8)})` : ''}
          </h2>
          <span className="text-xs px-2.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
            第 1 / 5 轮
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">
            状态：{status === 'running' ? '讨论中' : status === 'paused' ? '已暂停' : status === 'completed' ? '已结题' : '就绪'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {status !== 'running' && status !== 'completed' && status !== 'terminated' && (
            <button
              onClick={status === 'paused' ? handleResume : handleStart}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
              {status === 'paused' ? '继续' : '开始辩论'}
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
              <span className="text-xs font-bold text-white">主持人席位</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 ml-auto">
                仲裁控场
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed bg-[#1A2337] p-2.5 rounded-lg border border-[#2A364F]/50">
              欢迎各位专家入席。本次圆桌辩论由多智能体自主决策发言顺序与交锋逻辑。
            </p>
          </div>

          {/* Expert Monitors */}
          <div className="flex-1 flex flex-col gap-2.5">
            <span className="text-xs font-semibold text-slate-400 px-1">专家监控席 (4 位)</span>
            {experts.map((exp) => {
              const isSpeaking = activeSpeakerId === exp.id;
              return (
                <div
                  key={exp.id}
                  className={`bg-[#131B2B] border rounded-xl p-3.5 transition-all duration-300 relative overflow-hidden ${
                    isSpeaking
                      ? 'border-blue-500 shadow-lg shadow-blue-500/20 ring-2 ring-blue-500/30'
                      : 'border-[#2A364F]'
                  }`}
                >
                  <div
                    className="absolute top-0 left-0 bottom-0 w-1"
                    style={{ backgroundColor: exp.color_hex }}
                  />
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs text-white flex items-center gap-1.5">
                      {exp.name}
                      {isSpeaking && (
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                      )}
                    </span>
                    <span
                      className="text-[10px] px-1.5 py-0.5 rounded font-medium"
                      style={{ backgroundColor: `${exp.color_hex}22`, color: exp.color_hex }}
                    >
                      {exp.occupation}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 truncate">{exp.stance}</p>
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
              实况交锋实录 (Teleprompter Feed)
            </span>
            <span className="text-xs text-slate-400">{transcript.length} 条发言已记录</span>
          </div>

          <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-4">
            {transcript.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 text-xs">
                <Radio className="w-8 h-8 mb-2 opacity-30 animate-pulse" />
                点击上方“开始辩论”按钮，专家将自主产生发言意愿并展开交锋
              </div>
            ) : (
              transcript.map((t) => (
                <div key={t.id} className="bg-[#1A2337] border border-[#2A364F] rounded-xl p-4 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-xs text-white">{t.speaker_name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                      [{t.action_type}]
                    </span>
                  </div>
                  <p className="text-xs text-slate-200 leading-relaxed">{t.content}</p>
                </div>
              ))
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
              <p className="text-xs text-slate-500 text-center py-6">辩论初期，尚未沉淀明确共识</p>
            ) : (
              <div className="flex flex-col gap-2.5">
                {consensusItems.map((c) => (
                  <div key={c.id} className="bg-[#1A2337] border border-[#2A364F] rounded-lg p-3">
                    <p className="text-xs text-slate-200 mb-1">{c.statement}</p>
                    <span className="text-[10px] text-emerald-400 font-semibold">
                      可信度: {(c.confidence * 100).toFixed(0)}%
                    </span>
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
              <p className="text-xs text-slate-500 text-center py-6">正在捕捉多方交锋中的张力</p>
            ) : (
              <div className="flex flex-col gap-2.5">
                {divergenceItems.map((d) => (
                  <div key={d.id} className="bg-[#1A2337] border border-[#2A364F] rounded-lg p-3">
                    <p className="text-xs text-slate-200 mb-1">{d.tension}</p>
                    <span className="text-[10px] text-rose-400 font-semibold">
                      冲突烈度: {(d.intensity * 100).toFixed(0)}%
                    </span>
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
