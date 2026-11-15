import type { FC } from 'react';
import { Radio, Sparkles, MessageSquare, BarChart3 } from 'lucide-react';

interface HeaderProps {
  activeTab: 'create' | 'studio' | 'summary';
  setActiveTab: (tab: 'create' | 'studio' | 'summary') => void;
}

export const Header: FC<HeaderProps> = ({ activeTab, setActiveTab }) => {
  return (
    <header className="h-16 border-b border-[#2A364F] bg-[#131B2B]/80 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Radio className="w-5 h-5 text-white animate-pulse" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
            AI Panel Studio
            <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30 font-medium">
              MVP
            </span>
          </h1>
          <p className="text-xs text-slate-400">多智能体自主圆桌辩论演播室</p>
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
          话题创建
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
          总结审计
        </button>
      </nav>
    </header>
  );
};
