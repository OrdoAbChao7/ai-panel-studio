import { useEffect, useState, type FC } from 'react';
import { BarChart3, Download, FileText, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';
import { SummaryData } from '../../types';
import { getSummary } from '../../api/client';

interface DiscussionSummaryProps {
  summaryData?: SummaryData | null;
  discussionId?: string | null;
}

export const DiscussionSummary: FC<DiscussionSummaryProps> = ({ summaryData, discussionId }) => {
  const [data, setData] = useState<SummaryData | null>(summaryData || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (summaryData) {
      setData(summaryData);
      return;
    }
    if (!discussionId) return;

    setLoading(true);
    setError(null);
    getSummary(discussionId)
      .then((res) => {
        setData(res);
      })
      .catch((err) => {
        console.error('Failed to load summary', err);
        setError('加载总结数据失败，请确认该讨论是否已结题。');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [discussionId, summaryData]);

  const handleExportJSON = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `discussion-summary-${data.discussion_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportMarkdown = () => {
    if (!data) return;
    const md = `# 研讨结题报告: ${data.topic}

## 主持人宏观综合评述
${data.summary}

## 最终达成共识
${data.consensus_items.map((c) => `- **${c.statement}** (可信度: ${(c.confidence * 100).toFixed(0)}%)`).join('\n')}

## 核心分歧焦点
${data.divergence_items.map((d) => `- **${d.tension}** (冲突烈度: ${(d.intensity * 100).toFixed(0)}%)`).join('\n')}

## 专家心智与立场变迁审计
| 专家 | 初始立场 | 最终立场 | 是否发生演化 |
|---|---|---|---|
${data.stance_audit.map((s) => `| ${s.name} | ${s.initial_stance} | ${s.final_stance} | ${s.shifted ? '是' : '否'} |`).join('\n')}
`;
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `discussion-summary-${data.discussion_id}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-slate-400 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="text-sm">正在提炼生成本场辩论总结报告与立场演变审计...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-[#131B2B] border border-[#2A364F] rounded-xl p-8 max-w-3xl mx-auto text-center">
        <h3 className="text-base font-bold text-white mb-2">暂无已选中的结题研讨</h3>
        <p className="text-xs text-slate-400 mb-4">
          {error || '请在话题创建页选择一场已结题的历史圆桌，或在直播间完成辩论后查看总结报告。'}
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6 pb-12">
      {/* Header Card */}
      <div className="bg-[#131B2B] border border-[#2A364F] rounded-xl p-6 shadow-xl flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold text-blue-400 block mb-1">
            研讨终局与审计看板 (ID: {data.discussion_id.slice(0, 8)}...)
          </span>
          <h2 className="text-xl font-bold text-white">{data.topic}</h2>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleExportJSON}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1A2337] hover:bg-[#2A364F] text-slate-200 text-xs font-semibold border border-[#2A364F] transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            导出 JSON
          </button>
          <button
            onClick={handleExportMarkdown}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow transition-colors"
          >
            <FileText className="w-3.5 h-3.5" />
            导出 Markdown
          </button>
        </div>
      </div>

      {/* Moderator Concluding Synthesis */}
      <div className="bg-[#131B2B] border border-[#2A364F] rounded-xl p-6 shadow-xl">
        <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-purple-400" />
          主持人自然语言综合评述 (Moderator Synthesis)
        </h3>
        <div className="text-xs text-slate-300 leading-relaxed bg-[#1A2337] p-4 rounded-lg border border-[#2A364F]/50 whitespace-pre-wrap">
          {data.summary}
        </div>
      </div>

      {/* Consensus & Divergence Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Consensus */}
        <div className="bg-[#131B2B] border border-[#2A364F] rounded-xl p-6 shadow-xl">
          <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            最终收敛共识
          </h3>
          <div className="flex flex-col gap-3">
            {data.consensus_items.length === 0 ? (
              <p className="text-xs text-slate-500 py-4 text-center">本场讨论未达成显著共识</p>
            ) : (
              data.consensus_items.map((c) => (
                <div key={c.id} className="bg-[#1A2337] border border-[#2A364F] rounded-lg p-3.5">
                  <p className="text-xs text-slate-200 mb-2 font-medium">{c.statement}</p>
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>
                      支持专家:{' '}
                      {Array.isArray(c.supporting_agents)
                        ? c.supporting_agents.join('、')
                        : String(c.supporting_agents)}
                    </span>
                    <span className="text-emerald-400 font-bold">
                      {(c.confidence * 100).toFixed(0)}% 可信度
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Divergence */}
        <div className="bg-[#131B2B] border border-[#2A364F] rounded-xl p-6 shadow-xl">
          <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            未决核心分歧
          </h3>
          <div className="flex flex-col gap-3">
            {data.divergence_items.length === 0 ? (
              <p className="text-xs text-slate-500 py-4 text-center">各方观点相对趋同，未见高烈度分歧</p>
            ) : (
              data.divergence_items.map((d) => (
                <div key={d.id} className="bg-[#1A2337] border border-[#2A364F] rounded-lg p-3.5">
                  <p className="text-xs text-slate-200 mb-2 font-medium">{d.tension}</p>
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>双方各持论据</span>
                    <span className="text-rose-400 font-bold">
                      {(d.intensity * 100).toFixed(0)}% 冲突烈度
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Stance Evolution Audit */}
      {data.stance_audit && data.stance_audit.length > 0 && (
        <div className="bg-[#131B2B] border border-[#2A364F] rounded-xl p-6 shadow-xl">
          <h3 className="text-sm font-bold text-white mb-4">
            专家心智与立场演进审计 (Stance Evolution Audit)
          </h3>
          <div className="flex flex-col gap-3">
            {data.stance_audit.map((audit) => (
              <div
                key={audit.participant_id}
                className="bg-[#1A2337] border border-[#2A364F] rounded-lg p-4 flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="w-32">
                  <span className="font-bold text-sm text-white block">{audit.name}</span>
                  <span className="text-[11px] text-slate-400">共发言 {audit.turns_spoken} 轮</span>
                </div>

                <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="bg-[#0B0F17] p-2.5 rounded border border-[#2A364F]/50">
                    <span className="text-[10px] text-slate-500 block mb-1">初始立场</span>
                    <span className="text-slate-300">{audit.initial_stance}</span>
                  </div>
                  <div className="bg-[#0B0F17] p-2.5 rounded border border-[#2A364F]/50">
                    <span className="text-[10px] text-slate-500 block mb-1">最终立场</span>
                    <span className="text-emerald-400">{audit.final_stance}</span>
                  </div>
                </div>

                <div className="w-24 text-right">
                  {audit.shifted ? (
                    <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold">
                      立场有调和
                    </span>
                  ) : (
                    <span className="text-xs px-2.5 py-1 rounded-full bg-slate-700/50 text-slate-400 font-semibold">
                      立场坚定
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
