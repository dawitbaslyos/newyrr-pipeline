import React, { useState } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { AvatarRing } from '../../components/ui/avatar-ring';
import { ChevronDown, Plus, RefreshCw, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const ChannelHub: React.FC = () => {
  const { activeChannel, userChannels, selectActiveChannel, fetchChannels, setModal } = useStudioStore();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  const channel = activeChannel || {
    name: 'Newyr',
    handle: '@Newyrr',
    subscribers: '8',
    videos: 3,
    niche: 'Shorts',
    top_video: '1.5K'
  };

  const handleSyncActive = async () => {
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

  return (
    <div className="bg-[#0d111a] border border-[#1f2736] rounded-2xl p-5 flex flex-col gap-4 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Left: Avatar with glowing ring & Channel Info */}
        <div className="flex items-center gap-3.5">
          {channel.avatar_url ? (
            <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-cyan-400/60 shadow-[0_0_12px_rgba(0,242,254,0.2)] shrink-0">
              <img src={channel.avatar_url} alt={channel.name} className="w-full h-full object-cover" />
            </div>
          ) : (
            <AvatarRing
              initials={channel.name[0] || 'N'}
              size="lg"
              ringColor="border-cyan-400/50 shadow-[0_0_12px_rgba(0,242,254,0.2)]"
            />
          )}
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-100 leading-tight">
                {channel.name}
              </h2>
              <button
                disabled={isSyncing}
                onClick={handleSyncActive}
                title="Sync live stats from YouTube"
                className="w-5 h-5 rounded-md hover:bg-[#161b26] text-slate-400 hover:text-cyan-400 flex items-center justify-center transition cursor-pointer disabled:opacity-50"
              >
                {isSyncing ? (
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                ) : (
                  <RefreshCw className="w-3 h-3" />
                )}
              </button>
            </div>
            <p className="text-xs text-cyan-400 font-mono mt-0.5">
              {channel.handle}
            </p>
          </div>
        </div>

        {/* Right: Accurate Channel Metrics & Switcher */}
        <div className="flex flex-wrap sm:flex-nowrap items-center gap-4 sm:border-l border-[#1f2736] sm:pl-5">
          <div className="flex gap-4 text-center sm:text-left">
            <div>
              <div className="text-[10px] uppercase font-bold text-slate-400">Subscribers</div>
              <div className="text-base font-bold text-slate-100">{channel.subscribers || '0'}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase font-bold text-slate-400">Videos</div>
              <div className="text-base font-bold text-slate-100">{channel.videos ?? 0}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase font-bold text-slate-400">Niche</div>
              <div className="text-base font-bold text-emerald-400">{channel.niche || 'Shorts'}</div>
            </div>
          </div>

          {/* Switcher & Add Channel Buttons */}
          <div className="flex items-center gap-2 ml-auto sm:ml-2 relative">
            <button
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="bg-[#07090e] hover:bg-[#161b26] border border-[#1f2736] hover:border-slate-500 text-slate-200 text-xs font-semibold px-3 py-1.5 rounded-xl transition flex items-center gap-1.5 active:scale-95 shadow-sm cursor-pointer"
            >
              <span>Switch</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            <AnimatePresence>
              {isDropdownOpen && (
                <motion.div
                  initial={{ opacity: 0, y: 6, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 6, scale: 0.98 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 top-full mt-2 w-72 bg-[#0c0f18] border border-slate-700/80 rounded-2xl shadow-2xl p-2 z-50 flex flex-col gap-1 font-sans"
                >
                  <div className="px-2.5 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-[#1f2736] pb-1.5 mb-1 flex items-center justify-between">
                    <span>My YouTube Channels</span>
                    <span className="text-[9px] text-slate-500 font-mono">{userChannels.length} total</span>
                  </div>

                  <div className="max-h-60 overflow-y-auto flex flex-col gap-1 pr-1">
                    {userChannels.map((ch) => {
                      const isActive = ch.handle.toLowerCase() === channel.handle.toLowerCase();
                      return (
                        <div
                          key={ch.handle}
                          onClick={() => {
                            selectActiveChannel(ch.handle);
                            setIsDropdownOpen(false);
                          }}
                          className={`p-2 rounded-xl flex items-center justify-between cursor-pointer transition group ${
                            isActive
                              ? 'bg-cyan-950/40 border border-cyan-400/40 text-cyan-300'
                              : 'hover:bg-[#161b26] text-slate-200 border border-transparent'
                          }`}
                        >
                          <div className="flex items-center gap-2 overflow-hidden flex-1 mr-2">
                            {ch.top_video && ch.avatar_url ? (
                              <img src={ch.avatar_url} alt="" className="w-6 h-6 rounded-full object-cover shrink-0" />
                            ) : (
                              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-black shrink-0 ${
                                isActive ? 'bg-cyan-400 text-black' : 'bg-[#07090e] border border-[#1f2736] text-slate-300'
                              }`}>
                                {ch.name[0]?.toUpperCase() || '@'}
                              </div>
                            )}
                            <div className="overflow-hidden">
                              <div className="font-bold text-xs truncate leading-tight flex items-center gap-1.5">
                                <span>{ch.name}</span>
                                {isActive && <span className="text-[8px] bg-cyan-400/20 text-cyan-300 px-1 rounded">Active</span>}
                              </div>
                              <div className="text-[10px] text-slate-400 truncate">{ch.handle} • {ch.subscribers || '0'} subs</div>
                            </div>
                          </div>

                          <div className="flex items-center gap-1 shrink-0">
                            {/* Remove channel 'x' button */}
                            <button
                              onClick={(e) => handleRemoveChannel(ch.handle, e)}
                              title={`Delete ${ch.name}`}
                              className="w-6 h-6 rounded-lg hover:bg-rose-950/60 text-slate-500 hover:text-rose-400 flex items-center justify-center transition cursor-pointer"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <button
                    onClick={() => {
                      setIsDropdownOpen(false);
                      setModal('addUserChannel', true);
                    }}
                    className="w-full mt-1 pt-1.5 border-t border-[#1f2736] text-left px-2 py-1.5 text-xs text-cyan-400 hover:underline font-semibold flex items-center gap-1.5 cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Another Channel</span>
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            <button
              onClick={() => setModal('addUserChannel', true)}
              className="bg-cyan-950/40 hover:bg-cyan-900/50 border border-cyan-400/40 text-cyan-300 text-xs font-semibold px-3 py-1.5 rounded-xl transition flex items-center gap-1 active:scale-95 shadow-sm cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Channel</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChannelHub;
