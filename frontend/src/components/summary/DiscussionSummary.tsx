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
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-ink-muted gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-accent" aria-hidden="true" />
        <span className="text-sm">正在提炼生成本场辩论总结报告与立场演变审计...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-surface-raised border border-hairline rounded-xl p-8 max-w-3xl mx-auto text-center shadow-card">
        <h3 className="text-base font-semibold text-ink mb-2">暂无已选中的结题研讨</h3>
        <p className="text-xs text-ink-muted mb-4">
          {error || '请在话题创建页选择一场已结题的历史圆桌，或在直播间完成辩论后查看总结报告。'}
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-5 pb-12">
      {/* Header Card */}
      <div className="bg-surface-raised border border-hairline rounded-xl p-6 shadow-card flex items-center justify-between gap-4 flex-wrap">
        <div className="min-w-0">
          <span className="text-[11px] font-medium text-accent block mb-1">
            研讨终局与审计看板 (ID: {data.discussion_id.slice(0, 8)}...)
          </span>
          <h2 className="text-xl font-semibold text-ink">{data.topic}</h2>
        </div>
        <div className="flex gap-2 shrink-0">
          <button
            type="button"
            onClick={handleExportJSON}
            className="flex items-center gap-1.5 px-3 h-8 rounded-[8px] bg-surface-sunken hover:bg-black/[.05] text-ink text-xs font-medium border border-hairline transition-colors duration-150"
          >
            <Download className="w-3.5 h-3.5" aria-hidden="true" />
            导出 JSON
          </button>
          <button
            type="button"
            onClick={handleExportMarkdown}
            className="flex items-center gap-1.5 px-3 h-8 rounded-[8px] bg-accent hover:bg-accent-hover text-white text-xs font-medium transition-colors duration-150"
          >
            <FileText className="w-3.5 h-3.5" aria-hidden="true" />
            导出 Markdown
          </button>
        </div>
      </div>

      {/* Moderator Concluding Synthesis */}
      <div className="bg-surface-raised border border-hairline rounded-xl p-6 shadow-card">
        <h3 className="text-sm font-semibold text-ink mb-3 flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-ink-muted" aria-hidden="true" />
          主持人自然语言综合评述 (Moderator Synthesis)
        </h3>
        <div className="text-xs text-ink-muted leading-relaxed bg-surface-sunken p-4 rounded-[10px] whitespace-pre-wrap">
          {data.summary}
        </div>
      </div>

      {/* Consensus & Divergence Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Consensus */}
        <div className="bg-surface-raised border border-hairline rounded-xl p-6 shadow-card">
          <h3 className="text-sm font-semibold text-ink mb-3 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-positive" aria-hidden="true" />
            最终收敛共识
          </h3>
          <div className="flex flex-col gap-3">
            {data.consensus_items.length === 0 ? (
              <p className="text-xs text-ink-faint py-4 text-center">本场讨论未达成显著共识</p>
            ) : (
              data.consensus_items.map((c) => (
                <div key={c.id} className="bg-surface-sunken border border-hairline rounded-[10px] p-3.5">
                  <p className="text-xs text-ink mb-2 font-medium leading-relaxed">{c.statement}</p>
                  <div className="flex items-center justify-between gap-3 text-[11px] text-ink-muted">
                    <span className="truncate">
                      支持专家:{' '}
                      {Array.isArray(c.supporting_agents)
                        ? c.supporting_agents.join('、')
                        : String(c.supporting_agents)}
                    </span>
                    <span className="text-positive font-semibold whitespace-nowrap">
                      {(c.confidence * 100).toFixed(0)}% 可信度
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Divergence */}
        <div className="bg-surface-raised border border-hairline rounded-xl p-6 shadow-card">
          <h3 className="text-sm font-semibold text-ink mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-caution" aria-hidden="true" />
            未决核心分歧
          </h3>
          <div className="flex flex-col gap-3">
            {data.divergence_items.length === 0 ? (
              <p className="text-xs text-ink-faint py-4 text-center">各方观点相对趋同，未见高烈度分歧</p>
            ) : (
              data.divergence_items.map((d) => (
                <div key={d.id} className="bg-surface-sunken border border-hairline rounded-[10px] p-3.5">
                  <p className="text-xs text-ink mb-2 font-medium leading-relaxed">{d.tension}</p>
                  <div className="flex items-center justify-between gap-3 text-[11px] text-ink-muted">
                    <span>双方各持论据</span>
                    <span className="text-danger font-semibold whitespace-nowrap">
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
        <div className="bg-surface-raised border border-hairline rounded-xl p-6 shadow-card">
          <h3 className="text-sm font-semibold text-ink mb-4">
            专家心智与立场演进审计 (Stance Evolution Audit)
          </h3>
          <div className="flex flex-col gap-3">
            {data.stance_audit.map((audit) => (
              <div
                key={audit.participant_id}
                className="bg-surface-sunken border border-hairline rounded-[10px] p-4 flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="w-32 shrink-0">
                  <span className="font-semibold text-sm text-ink block">{audit.name}</span>
                  <span className="text-[11px] text-ink-muted">共发言 {audit.turns_spoken} 轮</span>
                </div>

                <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="bg-surface-raised p-2.5 rounded-[8px] border border-hairline">
                    <span className="text-[10px] text-ink-faint block mb-1">初始立场</span>
                    <span className="text-ink-muted">{audit.initial_stance}</span>
                  </div>
                  <div className="bg-surface-raised p-2.5 rounded-[8px] border border-hairline">
                    <span className="text-[10px] text-ink-faint block mb-1">最终立场</span>
                    <span className="text-ink">{audit.final_stance}</span>
                  </div>
                </div>

                <div className="w-24 text-right shrink-0">
                  {audit.shifted ? (
                    <span className="text-[11px] px-2.5 py-1 rounded-pill bg-positive/10 text-positive border border-positive/25 font-medium">
                      立场有调和
                    </span>
                  ) : (
                    <span className="text-[11px] px-2.5 py-1 rounded-pill bg-surface-raised text-ink-muted border border-hairline font-medium">
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
