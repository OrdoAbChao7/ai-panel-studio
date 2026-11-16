import { useEffect, useState, type FC } from 'react';
import { Radio, Sparkles, MessageSquare, BarChart3, Cpu, Zap } from 'lucide-react';

interface HeaderProps {
  activeTab: 'create' | 'studio' | 'summary';
  setActiveTab: (tab: 'create' | 'studio' | 'summary') => void;
}

interface SystemHealth {
  status: string;
  is_mock_mode: boolean;
  mode: string;
  model: string;
}

const TABS = [
  { id: 'create', label: '话题创建与案库', shortLabel: '创建', Icon: Sparkles },
  { id: 'studio', label: '辩论直播间', shortLabel: '直播', Icon: MessageSquare },
  { id: 'summary', label: '总结审计报告', shortLabel: '总结', Icon: BarChart3 },
] as const;

export const Header: FC<HeaderProps> = ({ activeTab, setActiveTab }) => {
  const [health, setHealth] = useState<SystemHealth | null>(null);

  useEffect(() => {
    fetch('/api/health')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setHealth(data);
      })
      .catch(() => {
        // Fallback if network lag
      });
  }, []);

  return (
    <header className="min-h-16 border-b border-hairline bg-surface-sidebar/90 backdrop-blur px-4 md:px-6 flex items-center justify-between gap-3 sticky top-0 z-50 flex-wrap py-2">
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-9 h-9 rounded-[10px] bg-accent flex items-center justify-center shrink-0">
          <Radio className="w-5 h-5 text-white" aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-base md:text-lg font-semibold tracking-tight text-ink whitespace-nowrap">
              AI Panel Studio
            </h1>
            <span className="hidden sm:inline text-[11px] px-2 py-0.5 rounded-pill bg-accent-soft text-accent border border-accent/20 font-medium">
              MVP
            </span>
            {health && (
              <span
                className={`hidden md:flex text-[11px] px-2.5 py-0.5 rounded-pill items-center gap-1 border font-medium ${
                  health.is_mock_mode
                    ? 'bg-caution/8 text-caution border-caution/25'
                    : 'bg-positive/8 text-positive border-positive/25'
                }`}
                title={
                  health.is_mock_mode
                    ? '当前运行于离线零网络高仿真 Mock 引擎模式。在后端环境配置密钥即可接入 DeepSeek 等真实大模型。'
                    : `当前运行于真实大模型引擎模式 (${health.model})。`
                }
              >
                {health.is_mock_mode ? (
                  <>
                    <Cpu className="w-3 h-3 shrink-0" aria-hidden="true" />
                    <span className="whitespace-nowrap">离线高仿真 Mock 引擎</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-3 h-3 shrink-0" aria-hidden="true" />
                    <span className="whitespace-nowrap">在线大模型: {health.model}</span>
                  </>
                )}
              </span>
            )}
          </div>
          <p className="text-xs text-ink-muted truncate hidden sm:block">
            多智能体自主圆桌辩论演播室 · 零凭证暴露安全架构
          </p>
        </div>
      </div>

      <nav
        className="flex items-center gap-1 bg-surface-sunken p-1 rounded-[10px] border border-hairline overflow-x-auto max-w-full"
        aria-label="主导航"
      >
        {TABS.map(({ id, label, shortLabel, Icon }) => {
          const isActive = activeTab === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => setActiveTab(id)}
              aria-current={isActive ? 'page' : undefined}
              aria-label={label}
              className={`flex items-center gap-2 px-3 h-8 rounded-[8px] text-xs font-medium transition-colors duration-150 whitespace-nowrap shrink-0 ${
                isActive
                  ? 'bg-surface-raised text-ink shadow-card'
                  : 'text-ink-muted hover:text-ink hover:bg-white/70'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-accent' : ''}`} aria-hidden="true" />
              <span className="hidden lg:inline">{label}</span>
              <span className="lg:hidden">{shortLabel}</span>
            </button>
          );
        })}
      </nav>
    </header>
  );
};
