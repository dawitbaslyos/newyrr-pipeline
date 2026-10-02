import React, { useRef } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { AvatarRing } from '../../components/ui/avatar-ring';
import { ChevronLeft, ChevronRight, Plus, X } from 'lucide-react';

export const TrackedChannelsReel: React.FC = () => {
  const { trackedChannels, fetchChannels, setModal } = useStudioStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: 'left' | 'right') => {
    if (scrollRef.current) {
      const offset = direction === 'left' ? -280 : 280;
      scrollRef.current.scrollBy({ left: offset, behavior: 'smooth' });
    }
  };

  const handleUntrack = async (handle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await fetch('/api/channels/remove-tracked', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ handle })
      });
      fetchChannels();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex flex-col gap-2.5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Tracked Inspiration Channels
          </h3>
          <span className="text-[10px] text-slate-500 font-mono">
            {trackedChannels.length} tracked
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => scroll('left')}
            className="w-6 h-6 rounded-lg bg-[#0d111a] hover:bg-[#161b26] border border-[#1f2736] text-slate-300 hover:text-white flex items-center justify-center text-xs transition active:scale-95 cursor-pointer"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => scroll('right')}
            className="w-6 h-6 rounded-lg bg-[#0d111a] hover:bg-[#161b26] border border-[#1f2736] text-slate-300 hover:text-white flex items-center justify-center text-xs transition active:scale-95 cursor-pointer"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setModal('addTrackedChannel', true)}
            className="text-xs text-cyan-400 hover:underline font-semibold flex items-center gap-1 ml-1 cursor-pointer"
          >
            <Plus className="w-3 h-3" />
            <span>Add Channel</span>
          </button>
        </div>
      </div>

      {/* Horizontal Snap Scroll Container */}
      <div
        ref={scrollRef}
        className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-none snap-x snap-mandatory scroll-smooth"
      >
        {trackedChannels.length === 0 ? (
          <div className="text-xs text-slate-500 py-3 px-2">No inspiration channels tracked yet.</div>
        ) : (
          trackedChannels.map((c) => (
            <div
              key={c.handle}
              className="min-w-[240px] sm:min-w-[260px] shrink-0 snap-start bg-[#0d111a] hover:bg-[#161b26] border border-[#1f2736] hover:border-slate-600 p-3 rounded-2xl flex items-center justify-between gap-3 group transition shadow-sm"
            >
              <div className="flex items-center gap-2.5 overflow-hidden">
                <AvatarRing initials={c.name[0] || '@'} size="sm" />
                <div className="overflow-hidden">
                  <div className="font-bold text-xs truncate text-slate-100">{c.name}</div>
                  <div className="text-[10px] text-slate-400 truncate">{c.focus || c.handle}</div>
                </div>
              </div>

              {/* Hover untrack button */}
              <button
                onClick={(e) => handleUntrack(c.handle, e)}
                title="Untrack channel"
                className="w-6 h-6 rounded-full hover:bg-rose-950/60 text-slate-500 hover:text-rose-400 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition shrink-0 cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
