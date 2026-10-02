import React, { useEffect } from 'react';
import { useStudioStore } from './stores/useStudioStore';
import { Header } from './features/header/Header';
import { ChannelHub } from './features/dashboard/ChannelHub';
import { TopicsReel } from './features/dashboard/TopicsReel';
import { TrackedChannelsReel } from './features/dashboard/TrackedChannelsReel';
import { ProjectsGrid } from './features/dashboard/ProjectsGrid';
import { AnalyticsView } from './features/analytics/AnalyticsView';
import { BottomNavDock } from './features/navigation/BottomNavDock';
import { StudioEditor } from './features/studio/StudioEditor';

// Modals
import { ExportModal } from './features/export/ExportModal';
import { TrashModal } from './features/trash/TrashModal';
import { AddChannelModal } from './features/modals/AddChannelModal';
import { AddUserChannelModal } from './features/modals/AddUserChannelModal';
import { SettingsPopover } from './features/modals/SettingsPopover';
import { NewDraftModal } from './features/modals/NewDraftModal';
import { TopicHistoryDrawer } from './features/modals/TopicHistoryDrawer';
import { RepurposeModal } from './features/repurpose/RepurposeModal';
import { RepurposeFeedView } from './features/dashboard/RepurposeFeedView';

export const App: React.FC = () => {
  const {
    activeTab,
    studioMode,
    isEditorOpen,
    fetchChannels,
    fetchTopics,
    fetchProjects,
    fetchSettings
  } = useStudioStore();

  useEffect(() => {
    fetchSettings();
    fetchChannels();
    fetchTopics();
    fetchProjects();
  }, [fetchSettings, fetchChannels, fetchTopics, fetchProjects]);

  return (
    <div className="h-screen w-screen flex flex-col bg-[#07090e] text-[#f1f5f9] overflow-hidden font-sans select-none antialiased">
      {/* Top Header Bar */}
      <Header />

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto p-4 sm:p-6 pb-28 max-w-5xl mx-auto w-full">
        {activeTab === 'channels' && (
          studioMode === 'repurpose' ? (
            <RepurposeFeedView />
          ) : (
            <div className="flex flex-col gap-6">
              <ChannelHub />
              <TopicsReel />
              <TrackedChannelsReel />
            </div>
          )
        )}

        {activeTab === 'analytics' && <AnalyticsView />}

        {activeTab === 'projects' && <ProjectsGrid />}
      </main>

      {/* Floating Bottom Nav Dock (Minimal Primitives style) */}
      <BottomNavDock />

      {/* Fullscreen Studio Editor */}
      {isEditorOpen && <StudioEditor />}

      {/* Overlays & Modals */}
      <ExportModal />
      <TrashModal />
      <AddChannelModal />
      <AddUserChannelModal />
      <SettingsPopover />
      <NewDraftModal />
      <TopicHistoryDrawer />
      <RepurposeModal />
    </div>
  );
};

export default App;
