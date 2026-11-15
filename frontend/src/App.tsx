import { useState } from 'react';
import { Header } from './components/common/Header';
import { DiscussionCreator } from './components/creation/DiscussionCreator';
import { LiveStudio } from './components/studio/LiveStudio';
import { DiscussionSummary } from './components/summary/DiscussionSummary';

export default function App() {
  const [activeTab, setActiveTab] = useState<'create' | 'studio' | 'summary'>('create');
  const [currentDiscussionId, setCurrentDiscussionId] = useState<string | null>(null);

  const handleDiscussionCreated = (discussionId: string) => {
    setCurrentDiscussionId(discussionId);
    setActiveTab('studio');
  };

  const handleDiscussionTerminated = () => {
    setActiveTab('summary');
  };

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-100 flex flex-col font-sans">
      {/* Studio Header */}
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Studio Viewport */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {activeTab === 'create' && (
          <DiscussionCreator onDiscussionCreated={handleDiscussionCreated} />
        )}

        {activeTab === 'studio' && (
          <LiveStudio
            discussionId={currentDiscussionId}
            onTerminate={handleDiscussionTerminated}
          />
        )}

        {activeTab === 'summary' && (
          <DiscussionSummary discussionId={currentDiscussionId} />
        )}
      </main>
    </div>
  );
}
