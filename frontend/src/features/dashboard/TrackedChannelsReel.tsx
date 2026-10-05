import React from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { AnimatedTooltip, type TooltipItem } from '../../components/ui/animated-tooltip';
import { Plus, Zap, Users } from 'lucide-react';

interface TrackedChannelsReelProps {
  selectedChannelHandle?: string | null;
  onSelectChannelHandle?: (handle: string | null) => void;
}

export const TrackedChannelsReel: React.FC<TrackedChannelsReelProps> = ({
  selectedChannelHandle,
  onSelectChannelHandle,
}) => {
  const {
    trackedChannels,
    fetchChannels,
    setModal,
    selectedTrackedChannel: storeSelectedHandle,
    setSelectedTrackedChannel: setStoreSelectedHandle,
    fetchShortsFeed,
  } = useStudioStore();

  const [isSyncing, setIsSyncing] = React.useState(false);

  const activeHandle = selectedChannelHandle !== undefined ? selectedChannelHandle : storeSelectedHandle;
  const selectHandle = onSelectChannelHandle || setStoreSelectedHandle;

  const tooltipItems: TooltipItem[] = trackedChannels.map((c) => ({
    id: c.handle,
    name: c.name,
    designation: c.focus ? `${c.handle} • ${c.focus}` : c.handle,
    image: c.avatar_url || '',
    handle: c.handle,
  }));

  const handleAvatarClick = (item: TooltipItem) => {
    if (activeHandle?.toLowerCase() === item.handle?.toLowerCase()) {
      selectHandle(null); // toggle off
    } else {
      selectHandle(item.handle || null);
    }
  };

  const handleSyncRSS = async () => {
    setIsSyncing(true);
    try {
      await fetch('/api/channels/sync', { method: 'POST' });
      await fetchChannels();
      await fetchShortsFeed(true);
    } catch (e) {
      console.error('Failed syncing channels:', e);
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="relative z-30 bg-[#0d111a] border border-[#1f2736] rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm overflow-visible">
      {/* Left: Tracked label & Animated Tooltip Avatars */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3.5 sm:gap-6 overflow-visible">
        <div className="flex items-center gap-2 shrink-0">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center">
            <Users className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Tracked Channels
            </h3>
            <span className="text-[10px] text-slate-500 font-mono">
              {trackedChannels.length} active inspiration sources
            </span>
          </div>
        </div>

        {/* Aceternity Animated Tooltip Row */}
        <div className="pl-1 sm:pl-0 overflow-visible py-1">
          {tooltipItems.length === 0 ? (
            <span className="text-xs text-slate-500">No channels tracked yet</span>
          ) : (
            <AnimatedTooltip
              items={tooltipItems}
              activeId={activeHandle}
              onItemClick={handleAvatarClick}
            />
          )}
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
        <button
          onClick={handleSyncRSS}
          disabled={isSyncing}
          title="Sync latest competitor RSS feeds"
          className="h-8 px-2.5 rounded-xl bg-[#131926] hover:bg-[#1b2333] border border-[#232c3d] text-slate-300 hover:text-cyan-400 text-xs font-medium flex items-center gap-1.5 transition active:scale-95 cursor-pointer disabled:opacity-50"
        >
          <Zap className={`w-3 h-3 text-cyan-400 ${isSyncing ? 'animate-spin' : ''}`} />
          <span>{isSyncing ? 'Syncing...' : 'Sync RSS'}</span>
        </button>

        <button
          onClick={() => setModal('addTrackedChannel', true)}
          className="h-8 px-3 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 text-xs font-bold flex items-center gap-1.5 transition active:scale-95 cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add Channel to Track</span>
        </button>
      </div>
    </div>
  );
};
