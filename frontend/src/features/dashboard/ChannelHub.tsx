import React, { useState } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { AvatarRing } from '../../components/ui/avatar-ring';
import { ChevronDown, Plus, RefreshCw, X, Sparkles, Clock, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import type { TopicSuggestion } from '../../types';

const DEFAULT_TOPICS: TopicSuggestion[] = [
  {
    title: "Why Astronauts Lose Their Fingernails",
    category: "Extreme Biology",
    hook: "When astronauts work outside the space station, their fingernails can literally pop off in their gloves."
  },
  {
    title: "Why Bulletproof Glass Shatters From The Inside",
    category: "Material Breakdown",
    hook: "Bulletproof glass stops high-powered rifle rounds from outside, but shatters from the inside with a pocket hammer."
  },
  {
    title: "Why Deep Sea Divers Cannot Fly For 24 Hours",
    category: "Extreme Physics",
    hook: "If a commercial diver boards a flight too soon, the nitrogen gas inside their bloodstream will literally boil."
  },
  {
    title: "Why Alcatraz Only Gave Burning Hot Showers",
    category: "Bizarre Realities",
    hook: "Alcatraz prison forced inmates to take steaming hot showers, and the reason was pure calculated warfare."
  },
  {
    title: "Why You Must Never Pop Danger Triangle Pimples",
    category: "Medical Anatomy",
    hook: "Popping a pimple inside this tiny facial zone can send lethal bacteria straight into your brain veins."
  },
  {
    title: "What Happens If You Swallow a Fish Bone",
    category: "Body Horrors",
    hook: "Swallowing a tiny needle-sharp fish bone doesn't just hurt—it can migrate directly through your throat tissue."
  }
];

export const ChannelHub: React.FC = () => {
  const {
    activeChannel,
    userChannels,
    selectActiveChannel,
    fetchChannels,
    setModal,
    topics,
    fetchTopics
  } = useStudioStore();

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isRefreshingTopics, setIsRefreshingTopics] = useState(false);

  const channel = activeChannel || {
    name: 'Newyr',
    handle: '@Newyrr',
    subscribers: '8',
    videos: 3,
    niche: 'Shorts',
    top_video: '1.5K'
  };

  const displayTopics = topics && topics.length > 0 ? topics : DEFAULT_TOPICS;

  const handleSyncActive = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!channel.handle) return;
    setIsSyncing(true);
    try {
      await fetch('/api/channels/sync-user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ handle: channel.handle })
      });
      await fetchChannels();
    } catch (e) {
      console.error('Failed syncing channel:', e);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleRemoveChannel = async (handle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Remove channel "${handle}" from your studio?`)) return;
    try {
      await fetch('/api/channels/remove-user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ handle })
      });
      await fetchChannels();
    } catch (e) {
      console.error('Failed removing channel:', e);
    }
  };

  const handleUseTopic = (topicTitle: string) => {
    window.sessionStorage.setItem('prefilledTopic', topicTitle);
    setModal('newDraft', true);
  };

  const handleRefreshTopics = async () => {
    setIsRefreshingTopics(true);
    await fetchTopics(true);
    setIsRefreshingTopics(false);
  };

  return (
    <div className="bg-[#0d111a] border border-[#1f2736] rounded-2xl p-4 sm:p-5 flex flex-col md:flex-row md:items-start justify-between gap-5 shadow-sm">
      {/* ── LEFT: Minimalist Account Pill & Dropdown Switcher ── */}
      <div className="relative shrink-0">
        <div className="flex items-center gap-2">
          {/* Main Account Trigger Pill */}
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-3 bg-[#131926] hover:bg-[#182030] border border-[#232c3d] hover:border-cyan-500/50 rounded-2xl py-2 px-3.5 transition-all duration-200 active:scale-98 cursor-pointer shadow-sm group"
          >
            {channel.avatar_url ? (
              <div className="w-10 h-10 rounded-full overflow-hidden border-2 border-cyan-400/60 shadow-[0_0_10px_rgba(0,242,254,0.25)] shrink-0">
                <img src={channel.avatar_url} alt={channel.name} className="w-full h-full object-cover" />
              </div>
            ) : (
              <AvatarRing
                initials={channel.name[0] || 'N'}
                size="md"
                ringColor="border-cyan-400/50 shadow-[0_0_10px_rgba(0,242,254,0.25)]"
              />
            )}

            <div className="text-left">
              <div className="text-sm font-bold text-slate-100 group-hover:text-white transition leading-tight flex items-center gap-1.5">
                <span>{channel.name}</span>
              </div>
              <p className="text-xs text-cyan-400 font-mono">
                {channel.handle}
              </p>
            </div>

            <ChevronDown
              className={`w-4 h-4 text-slate-400 group-hover:text-cyan-400 transition-transform duration-200 ml-1.5 ${
                isDropdownOpen ? 'rotate-180 text-cyan-400' : ''
              }`}
            />
          </button>

          {/* Sync Button Next to Channel Pill */}
          <button
            disabled={isSyncing}
            onClick={handleSyncActive}
            title="Sync live stats from YouTube"
            className="w-9 h-9 rounded-xl bg-[#131926] hover:bg-[#182030] border border-[#232c3d] hover:border-cyan-500/50 text-slate-400 hover:text-cyan-400 flex items-center justify-center transition active:scale-95 cursor-pointer disabled:opacity-50 shrink-0"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>

        {/* Dropdown Popover */}
        <AnimatePresence>
          {isDropdownOpen && (
            <motion.div
              initial={{ opacity: 0, y: 8, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 8, scale: 0.98 }}
              transition={{ duration: 0.15 }}
              className="absolute left-0 top-full mt-2 w-72 bg-[#0e131d] border border-[#232c3d] rounded-2xl shadow-[0_15px_35px_-5px_rgba(0,0,0,0.85),0_0_20px_rgba(0,242,254,0.1)] py-2 z-50 flex flex-col gap-1 overflow-hidden"
            >
              <div className="px-3.5 py-1.5 text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                Your Studio Channels
              </div>

              <div className="max-h-60 overflow-y-auto px-1.5 flex flex-col gap-1">
                {userChannels.map((c) => {
                  const isActive = c.handle.toLowerCase() === channel.handle.toLowerCase();
                  return (
                    <div
                      key={c.handle}
                      onClick={() => {
                        selectActiveChannel(c.handle);
                        setIsDropdownOpen(false);
                      }}
                      className={`flex items-center justify-between p-2 rounded-xl transition cursor-pointer group ${
                        isActive
                          ? 'bg-cyan-500/10 border border-cyan-500/30 text-white'
                          : 'hover:bg-[#161c28] text-slate-300'
                      }`}
                    >
                      <div className="flex items-center gap-2.5 overflow-hidden">
                        {c.avatar_url ? (
                          <img
                            src={c.avatar_url}
                            alt={c.name}
                            className="w-7 h-7 rounded-full object-cover border border-cyan-400/40 shrink-0"
                          />
                        ) : (
                          <div className="w-7 h-7 rounded-full bg-cyan-500/20 text-cyan-300 text-xs font-bold flex items-center justify-center border border-cyan-400/30 shrink-0">
                            {c.name[0]}
                          </div>
                        )}
                        <div className="overflow-hidden">
                          <div className="text-xs font-bold truncate flex items-center gap-1">
                            <span>{c.name}</span>
                            {isActive && <Check className="w-3 h-3 text-cyan-400 shrink-0" />}
                          </div>
                          <div className="text-[10px] text-cyan-400 font-mono truncate">
                            {c.handle}
                          </div>
                        </div>
                      </div>

                      {userChannels.length > 1 && (
                        <button
                          onClick={(e) => handleRemoveChannel(c.handle, e)}
                          title="Remove channel"
                          className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 text-slate-500 transition"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Add New Channel Action */}
              <div className="border-t border-[#1f2736] pt-1.5 mt-1 px-2">
                <button
                  onClick={() => {
                    setIsDropdownOpen(false);
                    setModal('addUserChannel', true);
                  }}
                  className="w-full py-2 px-3 rounded-xl bg-[#131926] hover:bg-cyan-500/10 text-cyan-400 text-xs font-bold flex items-center justify-center gap-2 transition active:scale-98 cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Studio Channel</span>
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── RIGHT: Minimalist Text-Only Topic Suggestion Pills ── */}
      <div className="flex-1 flex flex-col gap-2.5 min-w-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>AI Topic Suggestions</span>
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setModal('topicHistory', true)}
              title="Topic brainstorm history"
              className="h-6 px-2 rounded-lg bg-[#131926] hover:bg-[#1a2233] border border-[#232c3d] text-slate-400 hover:text-slate-200 text-[11px] font-medium flex items-center gap-1 transition active:scale-95 cursor-pointer"
            >
              <Clock className="w-3 h-3 text-cyan-400" />
              <span>History</span>
            </button>

            <button
              onClick={handleRefreshTopics}
              disabled={isRefreshingTopics}
              title="Refresh topic suggestions"
              className="w-6 h-6 rounded-lg bg-[#131926] hover:bg-[#1a2233] border border-[#232c3d] text-slate-400 hover:text-cyan-400 flex items-center justify-center transition active:scale-95 cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3 h-3 ${isRefreshingTopics ? 'animate-spin text-cyan-400' : ''}`} />
            </button>
          </div>
        </div>

        {/* Text-Only Topic Buttons / Pills (No bloat, no category badges, no quote cards) */}
        <div className="flex flex-wrap items-center gap-2">
          {displayTopics.map((t) => (
            <button
              key={t.title}
              onClick={() => handleUseTopic(t.title)}
              title={`Click to write script for: "${t.title}"`}
              className="rounded-full py-1.5 px-3.5 text-xs font-medium bg-[#111722] hover:bg-[#192233] border border-[#202b3c] hover:border-cyan-400/60 text-slate-300 hover:text-white transition-all duration-200 active:scale-95 text-left cursor-pointer shadow-xs truncate max-w-full"
            >
              {t.title}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
