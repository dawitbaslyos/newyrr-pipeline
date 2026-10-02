import React from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { Tv, BarChart2, Film } from 'lucide-react';
import { motion } from 'framer-motion';

export const BottomNavDock: React.FC = () => {
  const { activeTab, setActiveTab, isEditorOpen } = useStudioStore();

  if (isEditorOpen) return null; // Hidden in full-screen Studio mode

  const tabs = [
    { id: 'channels', label: 'Channels', icon: <Tv className="w-4 h-4" /> },
    { id: 'analytics', label: 'Analytics', icon: <BarChart2 className="w-4 h-4" /> },
    { id: 'projects', label: 'Projects', icon: <Film className="w-4 h-4" /> },
  ] as const;

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-40">
      <div className="flex items-center gap-1 bg-[#0c0f18]/95 backdrop-blur-md border border-slate-700/80 p-1.5 rounded-full shadow-2xl">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`relative flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold transition-colors cursor-pointer ${
                isActive ? 'text-black font-bold' : 'text-slate-400 hover:text-slate-100'
              }`}
            >
              {isActive && (
                <motion.div
                  layoutId="bottomDockPill"
                  className="absolute inset-0 bg-cyan-400 rounded-full shadow-md -z-10"
                  transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                />
              )}
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
