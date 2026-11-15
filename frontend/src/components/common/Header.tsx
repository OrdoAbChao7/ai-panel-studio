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
    <header className="h-16 border-b border-[#2A364F] bg-[#131B2B]/90 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Radio className="w-5 h-5 text-white animate-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold tracking-tight text-white">
              AI Panel Studio
            </h1>
            <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30 font-medium">
              MVP
            </span>
            {health && (
              <span
                className={`text-[11px] px-2.5 py-0.5 rounded-full flex items-center gap-1 border font-medium ${
                  health.is_mock_mode
                    ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                }`}
                title={
                  health.is_mock_mode
                    ? '当前运行于离线零网络高仿真 Mock 引擎模式。在后端环境配置密钥即可接入 DeepSeek 等真实大模型。'
                    : `当前运行于真实大模型引擎模式 (${health.model})。`
                }
              >
                {health.is_mock_mode ? (
                  <>
                    <Cpu className="w-3 h-3 text-amber-400" />
                    <span>离线高仿真 Mock 引擎</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-3 h-3 text-emerald-400" />
                    <span>在线大模型: {health.model}</span>
                  </>
                )}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400">多智能体自主圆桌辩论演播室 · 零凭证暴露安全架构</p>
        </div>
      </div>

      <nav className="flex items-center gap-1 bg-[#1A2337] p-1 rounded-lg border border-[#2A364F]">
        <button
          onClick={() => setActiveTab('create')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            activeTab === 'create'
              ? 'bg-blue-600 text-white shadow'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          话题创建与案库
        </button>
        <button
          onClick={() => setActiveTab('studio')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            activeTab === 'studio'
              ? 'bg-blue-600 text-white shadow'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <MessageSquare className="w-3.5 h-3.5" />
          辩论直播间
        </button>
        <button
          onClick={() => setActiveTab('summary')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            activeTab === 'summary'
              ? 'bg-blue-600 text-white shadow'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          总结审计报告
        </button>
      </nav>
    </header>
  );
};
