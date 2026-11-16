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
    <div className="flex flex-col gap-6 max-w-5xl mx-auto pb-12">
      {/* Creation Studio Card */}
      <section className="bg-surface-raised border border-hairline rounded-xl p-8 shadow-card">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-[10px] bg-accent-soft flex items-center justify-center">
            <Users className="w-5 h-5 text-accent" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-ink">发起全新圆桌辩论</h2>
            <p className="text-xs text-ink-muted">
              输入科技与前沿社会议题，由大模型自主生成多元立场的专业专家阵容
            </p>
          </div>
        </div>

        {/* Preset Chips */}
        <div className="mb-6">
          <label className="text-xs font-medium text-ink-muted block mb-2">
            推荐议题快捷选择：
          </label>
          <div className="flex flex-wrap gap-2">
            {presets.map((preset) => {
              const selected = topic === preset;
              return (
                <button
                  key={preset}
                  type="button"
                  onClick={() => setTopic(preset)}
                  aria-pressed={selected}
                  className={`text-xs px-3 py-1.5 rounded-pill border transition-colors duration-150 ${
                    selected
                      ? 'bg-accent-soft border-accent/40 text-accent font-medium'
                      : 'bg-surface-sunken hover:bg-black/[.05] text-ink-muted border-hairline'
                  }`}
                >
                  {preset}
                </button>
              );
            })}
          </div>
        </div>

        {/* Topic Input */}
        <div className="mb-6">
          <label htmlFor="topic-input" className="text-xs font-medium text-ink-muted block mb-2">
            核心辩题：
          </label>
          <input
            id="topic-input"
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="w-full bg-surface-sunken border border-hairline rounded-[10px] px-4 h-10 text-sm text-ink placeholder:text-ink-faint hover:border-edge focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/25 focus:bg-surface-raised transition-colors duration-150"
            placeholder="请输入辩论议题..."
          />
        </div>

        {/* Participant Count Selector */}
        <div className="mb-6 flex items-center justify-between">
          <span className="text-xs font-medium text-ink-muted">
            专家席位数量：{participantCount} 位 (默认 4 人)
          </span>
          <div className="flex gap-2" role="group" aria-label="专家席位数量">
            {[2, 3, 4, 5, 6].map((num) => {
              const selected = participantCount === num;
              return (
                <button
                  key={num}
                  type="button"
                  onClick={() => setParticipantCount(num)}
                  aria-pressed={selected}
                  className={`w-8 h-8 rounded-[8px] text-xs font-semibold transition-colors duration-150 ${
                    selected
                      ? 'bg-accent text-white'
                      : 'bg-surface-raised text-ink-muted border border-hairline hover:bg-surface-sunken hover:text-ink'
                  }`}
                >
                  {num}
                </button>
              );
            })}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 mb-8">
          <button
            type="button"
            onClick={handleGenerate}
            disabled={loading || !topic}
            className="flex-1 h-10 bg-accent hover:bg-accent-hover disabled:opacity-45 disabled:cursor-not-allowed text-white text-xs font-medium rounded-[10px] flex items-center justify-center gap-2 transition-colors duration-150"
          >
            <Sparkles className="w-4 h-4" aria-hidden="true" />
            {loading ? '生成专家阵容中...' : '生成专家阵容'}
          </button>
          {experts.length > 0 && (
            <button
              type="button"
              onClick={handleCreate}
              disabled={loading}
              className="flex-1 h-10 bg-surface-raised border border-edge hover:bg-surface-sunken disabled:opacity-45 text-ink text-xs font-medium rounded-[10px] flex items-center justify-center gap-2 transition-colors duration-150"
            >
              确认阵容并进入演播室
              <ArrowRight className="w-4 h-4" aria-hidden="true" />
            </button>
          )}
        </div>

        {/* Expert Preview Grid */}
        {experts.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {experts.map((exp, idx) => {
              const color = exp.color_hex || '#4d6bfe';
              return (
                <div
                  key={idx}
                  className="bg-surface-sunken border border-hairline rounded-xl p-4 relative overflow-hidden pl-5"
                >
                  <div
                    className="absolute top-0 left-0 bottom-0 w-1"
                    style={{ backgroundColor: color }}
                  />
                  <div className="flex items-center justify-between gap-3 mb-2">
                    <span className="font-semibold text-sm text-ink">{exp.name}</span>
                    <span
                      className="text-[11px] px-2 py-0.5 rounded-pill border font-medium whitespace-nowrap"
                      style={{
                        backgroundColor: `${color}12`,
                        color,
                        borderColor: `${color}33`,
                      }}
                    >
                      {exp.occupation}
                    </span>
                  </div>
                  <p className="text-xs text-ink-muted mb-2 leading-relaxed">
                    <strong className="text-ink font-medium">立场：</strong> {exp.stance}
                  </p>
                  <p className="text-xs text-ink-faint leading-relaxed">
                    <strong className="text-ink-muted font-medium">视角：</strong> {exp.perspective}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Historical & Seeded Discussions Library */}
      <section className="bg-surface-raised border border-hairline rounded-xl p-8 shadow-card">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-[10px] bg-surface-sunken flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-ink-muted" aria-hidden="true" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-ink">历史讨论与预设案例库</h2>
              <p className="text-xs text-ink-muted">
                支持直接加载已结题的经典圆桌研讨，复盘交锋实录、共识分歧与专家立场演化
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={fetchDiscussions}
            className="text-xs text-ink-muted hover:text-ink hover:bg-surface-sunken px-2.5 h-7 rounded-[8px] transition-colors duration-150"
          >
            刷新列表
          </button>
        </div>

        {historyLoading ? (
          <p className="text-xs text-ink-faint py-6 text-center">正在加载历史辩论列表...</p>
        ) : historyList.length === 0 ? (
          <p className="text-xs text-ink-faint py-6 text-center">
            暂无历史讨论记录。可运行 seed.py 导入 5 组预设经典圆桌。
          </p>
        ) : (
          <div className="flex flex-col gap-3">
            {historyList.map((item) => (
              <div
                key={item.id}
                className="bg-surface-sunken border border-hairline rounded-xl p-4 flex items-center justify-between gap-4 hover:border-edge transition-colors duration-150"
              >
                <div className="flex flex-col gap-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-sm text-ink truncate">{item.topic}</span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-pill font-medium border whitespace-nowrap ${
                        item.status === 'completed'
                          ? 'bg-positive/8 text-positive border-positive/25'
                          : item.status === 'running'
                          ? 'bg-accent-soft text-accent border-accent/25'
                          : 'bg-surface-raised text-ink-muted border-hairline'
                      }`}
                    >
                      {item.status === 'completed'
                        ? '已结题 (Completed)'
                        : item.status === 'running'
                        ? '进行中 (Running)'
                        : item.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-ink-muted flex-wrap">
                    <span className="flex items-center gap-1">
                      <Users className="w-3.5 h-3.5 text-ink-faint" aria-hidden="true" />
                      {item.participant_count} 位专家席位
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-ink-faint" aria-hidden="true" />
                      轮次: {item.current_round} / {item.max_rounds}
                    </span>
                    <span className="text-[11px] text-ink-faint font-mono">
                      ID: {item.id.slice(0, 8)}...
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={() => onSelectDiscussion?.(item.id, 'studio')}
                    className="flex items-center gap-1 px-3 h-8 rounded-[8px] bg-surface-raised hover:bg-black/[.04] text-ink text-xs font-medium border border-hairline transition-colors duration-150"
                  >
                    演播厅实况
                    <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
                  </button>
                  {item.status === 'completed' && (
                    <button
                      type="button"
                      onClick={() => onSelectDiscussion?.(item.id, 'summary')}
                      className="flex items-center gap-1 px-3 h-8 rounded-[8px] bg-accent-soft hover:bg-accent/15 text-accent text-xs font-medium border border-accent/25 transition-colors duration-150"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
                      总结报告
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
