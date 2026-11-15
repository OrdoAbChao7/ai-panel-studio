import { useEffect, useState, type FC } from 'react';
import { Users, Sparkles, ArrowRight, BookOpen, Clock, CheckCircle2, ChevronRight } from 'lucide-react';
import { Participant } from '../../types';

interface DiscussionCreatorProps {
  onDiscussionCreated?: (discussionId: string) => void;
  onSelectDiscussion?: (discussionId: string, targetTab: 'studio' | 'summary') => void;
}

interface HistoricalDiscussion {
  id: string;
  topic: string;
  status: string;
  current_round: number;
  max_rounds: number;
  participant_count: number;
  created_at: string;
}

export const DiscussionCreator: FC<DiscussionCreatorProps> = ({
  onDiscussionCreated,
  onSelectDiscussion,
}) => {
  const [topic, setTopic] = useState('AI 是否会取代大部分初级程序员？');
  const [participantCount, setParticipantCount] = useState(4);
  const [loading, setLoading] = useState(false);
  const [experts, setExperts] = useState<Partial<Participant>[]>([]);
  const [historyList, setHistoryList] = useState<HistoricalDiscussion[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const presets = [
    'AI 是否会取代大部分初级程序员？',
    '中国大学生应该优先就业还是读研？',
    '自动驾驶技术距离全面普及还有多远？',
    'AI Agent 是否会改变传统 SaaS 商业模式？',
    '大学生是否应该在本科阶段创业？',
  ];

  const fetchDiscussions = async () => {
    setHistoryLoading(true);
    try {
      const res = await fetch('/api/discussions');
      if (res.ok) {
        const data = await res.json();
        setHistoryList(data);
      }
    } catch (e) {
      console.error('Failed to load discussions history', e);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    fetchDiscussions();
  }, []);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/discussions/roster/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, participant_count: participantCount }),
      });
      if (res.ok) {
        const data = await res.json();
        setExperts(data.experts || []);
      }
    } catch (e) {
      console.error('Failed to generate roster', e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/discussions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic,
          max_rounds: 4,
          participants: experts.length > 0 ? experts : undefined,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        onDiscussionCreated?.(data.id);
      }
    } catch (e) {
      console.error('Failed to create discussion', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-8 max-w-5xl mx-auto pb-12">
      {/* Creation Studio Card */}
      <div className="bg-[#131B2B] border border-[#2A364F] rounded-xl p-8 shadow-xl">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
            <Users className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">发起全新圆桌辩论</h2>
            <p className="text-xs text-slate-400">
              输入科技与前沿社会议题，由大模型自主生成多元立场的专业专家阵容
            </p>
          </div>
        </div>

        {/* Preset Chips */}
        <div className="mb-6">
          <label className="text-xs font-semibold text-slate-400 block mb-2">
            推荐议题快捷选择：
          </label>
          <div className="flex flex-wrap gap-2">
            {presets.map((preset) => (
              <button
                key={preset}
                onClick={() => setTopic(preset)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                  topic === preset
                    ? 'bg-blue-600/20 border-blue-500 text-blue-300 font-medium'
                    : 'bg-[#1A2337] hover:bg-[#2A364F] text-slate-300 border-[#2A364F]'
                }`}
              >
                {preset}
              </button>
            ))}
          </div>
        </div>

        {/* Topic Input */}
        <div className="mb-6">
          <label className="text-xs font-semibold text-slate-400 block mb-2">核心辩题：</label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="w-full bg-[#0B0F17] border border-[#2A364F] rounded-lg px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
            placeholder="请输入辩论议题..."
          />
        </div>

        {/* Participant Count Selector */}
        <div className="mb-6 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400">
            专家席位数量：{participantCount} 位 (默认 4 人)
          </span>
          <div className="flex gap-2">
            {[2, 3, 4, 5, 6].map((num) => (
              <button
                key={num}
                onClick={() => setParticipantCount(num)}
                className={`w-8 h-8 rounded-md text-xs font-semibold ${
                  participantCount === num
                    ? 'bg-blue-600 text-white'
                    : 'bg-[#1A2337] text-slate-400 border border-[#2A364F] hover:bg-[#2A364F]'
                }`}
              >
                {num}
              </button>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 mb-8">
          <button
            onClick={handleGenerate}
            disabled={loading || !topic}
            className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 shadow"
          >
            <Sparkles className="w-4 h-4" />
            {loading ? '生成专家阵容中...' : '生成专家阵容'}
          </button>
          {experts.length > 0 && (
            <button
              onClick={handleCreate}
              disabled={loading}
              className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 shadow"
            >
              确认阵容并进入演播室
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Expert Preview Grid */}
        {experts.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {experts.map((exp, idx) => (
              <div
                key={idx}
                className="bg-[#1A2337] border border-[#2A364F] rounded-lg p-4 relative overflow-hidden"
              >
                <div
                  className="absolute top-0 left-0 bottom-0 w-1"
                  style={{ backgroundColor: exp.color_hex || '#3B82F6' }}
                />
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-sm text-white">{exp.name}</span>
                  <span
                    className="text-xs px-2 py-0.5 rounded text-white font-medium"
                    style={{
                      backgroundColor: `${exp.color_hex || '#3B82F6'}33`,
                      color: exp.color_hex,
                    }}
                  >
                    {exp.occupation}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mb-2 leading-relaxed">
                  <strong className="text-slate-400">立场：</strong> {exp.stance}
                </p>
                <p className="text-xs text-slate-400 leading-relaxed">
                  <strong className="text-slate-500">视角：</strong> {exp.perspective}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Historical & Seeded Discussions Library */}
      <div className="bg-[#131B2B] border border-[#2A364F] rounded-xl p-8 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">历史讨论与预设案例库</h2>
              <p className="text-xs text-slate-400">
                支持直接加载已结题的经典圆桌研讨，复盘交锋实录、共识分歧与专家立场演化
              </p>
            </div>
          </div>
          <button
            onClick={fetchDiscussions}
            className="text-xs text-slate-400 hover:text-slate-200 underline"
          >
            刷新列表
          </button>
        </div>

        {historyLoading ? (
          <p className="text-xs text-slate-500 py-6 text-center">正在加载历史辩论列表...</p>
        ) : historyList.length === 0 ? (
          <p className="text-xs text-slate-500 py-6 text-center">
            暂无历史讨论记录。可运行 seed.py 导入 5 组预设经典圆桌。
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {historyList.map((item) => (
              <div
                key={item.id}
                className="bg-[#1A2337] border border-[#2A364F] rounded-lg p-4 flex items-center justify-between hover:border-slate-500 transition-colors"
              >
                <div className="flex flex-col gap-1.5 flex-1 pr-4">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-white">{item.topic}</span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${
                        item.status === 'completed'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : item.status === 'running'
                          ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                          : 'bg-slate-700 text-slate-300 border-slate-600'
                      }`}
                    >
                      {item.status === 'completed'
                        ? '已结题 (Completed)'
                        : item.status === 'running'
                        ? '进行中 (Running)'
                        : item.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <Users className="w-3.5 h-3.5 text-slate-500" />
                      {item.participant_count} 位专家席位
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      轮次: {item.current_round} / {item.max_rounds}
                    </span>
                    <span className="text-[11px] text-slate-500 font-mono">
                      ID: {item.id.slice(0, 8)}...
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onSelectDiscussion?.(item.id, 'studio')}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-md bg-[#243048] hover:bg-[#2F3F5E] text-slate-200 text-xs font-medium border border-[#3A4B6E] transition-colors"
                  >
                    演播厅实况
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                  {item.status === 'completed' && (
                    <button
                      onClick={() => onSelectDiscussion?.(item.id, 'summary')}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-md bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 text-xs font-medium border border-purple-500/40 transition-colors"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      总结报告
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
