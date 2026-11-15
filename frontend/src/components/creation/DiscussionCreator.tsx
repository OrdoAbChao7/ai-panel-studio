import { useState, type FC } from 'react';
import { Users, Sparkles, ArrowRight } from 'lucide-react';
import { Participant } from '../../types';

interface DiscussionCreatorProps {
  onDiscussionCreated?: (discussionId: string) => void;
}

export const DiscussionCreator: FC<DiscussionCreatorProps> = ({ onDiscussionCreated }) => {
  const [topic, setTopic] = useState('通用人工智能的伦理与监管边界');
  const [participantCount, setParticipantCount] = useState(4);
  const [loading, setLoading] = useState(false);
  const [experts, setExperts] = useState<Partial<Participant>[]>([]);

  const presets = [
    '通用人工智能的伦理与监管边界',
    '开源大模型 vs 闭源商业模型的演化终局',
    '远程办公与全员重返办公室的利弊交锋',
    '绿色能源转型中的核能战略定位',
    '算法推荐与信息茧房伦理治理',
  ];

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
          max_rounds: 5,
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
    <div className="bg-[#131B2B] border border-[#2A364F] rounded-xl p-8 shadow-xl max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
          <Users className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">辩题与圆桌专家配置</h2>
          <p className="text-xs text-slate-400">输入前沿辩题，自主生成具备多元立场与鲜明色彩身份的 AI 专家团</p>
        </div>
      </div>

      {/* Preset Chips */}
      <div className="mb-6">
        <label className="text-xs font-semibold text-slate-400 block mb-2">推荐预设议题：</label>
        <div className="flex flex-wrap gap-2">
          {presets.map((preset) => (
            <button
              key={preset}
              onClick={() => setTopic(preset)}
              className="text-xs px-3 py-1.5 rounded-full bg-[#1A2337] hover:bg-[#2A364F] text-slate-300 border border-[#2A364F] transition-colors"
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
        <span className="text-xs font-semibold text-slate-400">专家席位人数：{participantCount} 位</span>
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
                  style={{ backgroundColor: `${exp.color_hex || '#3B82F6'}33`, color: exp.color_hex }}
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
  );
};
