import React, { useState, useEffect, useRef } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import type { ShortFeedItem } from '../../types';
import { 
  Sparkles, 
  ExternalLink, 
  RefreshCw, 
  Film, 
  Play, 
  Clock, 
  Flame, 
  Calendar, 
  ChevronDown, 
  X,
  Zap
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface TrackedShortsFeedProps {
  selectedChannelHandle?: string | null;
  onSelectChannelHandle?: (handle: string | null) => void;
}

export const TrackedShortsFeed: React.FC<TrackedShortsFeedProps> = ({
  selectedChannelHandle,
  onSelectChannelHandle,
}) => {
  const { 
    trackedChannels, 
    setModal,
    shortsFeed,
    isShortsLoading,
    shortsFormat,
    shortsSort,
    setShortsFormat,
    setShortsSort,
    fetchShortsFeed,
    selectedTrackedChannel: storeSelectedHandle,
    setSelectedTrackedChannel: setStoreSelectedHandle
  } = useStudioStore();

  const [isSortDropdownOpen, setIsSortDropdownOpen] = useState(false);
  const sortDropdownRef = useRef<HTMLDivElement>(null);

  const activeChannelFilter = selectedChannelHandle !== undefined ? selectedChannelHandle : storeSelectedHandle;
  const selectFilter = onSelectChannelHandle || setStoreSelectedHandle;

  // Initial fetch from store cache or network on first mount
  useEffect(() => {
    if (shortsFeed.length === 0) {
      fetchShortsFeed();
    }
  }, []);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (sortDropdownRef.current && !sortDropdownRef.current.contains(event.target as Node)) {
        setIsSortDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleClearChannelFilter = () => {
    selectFilter(null);
  };

  const handleRecreate = (short: ShortFeedItem) => {
    // Strip emojis or extra hashtags for cleaner topic prompt
    const cleanTitle = short.title
      .replace(/#\w+/g, '')
      .replace(/[^\w\s',.?!-]/g, '')
      .trim();
    window.sessionStorage.setItem('prefilledTopic', cleanTitle || short.title);
    if (short.video_url) {
      window.sessionStorage.setItem('prefilledReferenceUrl', short.video_url);
    }
    setModal('newDraft', true);
  };

  // Filter items by channel handle client-side for instant 0ms switching
  const filteredItems = activeChannelFilter
    ? shortsFeed.filter(
        (s) => s.channel_handle?.toLowerCase().trim() === activeChannelFilter.toLowerCase().trim()
      )
    : shortsFeed;

  const activeSoloChannel = trackedChannels.find(
    (c) => c.handle.toLowerCase().trim() === activeChannelFilter?.toLowerCase().trim()
  );

  const formatRelativeTime = (isoString?: string) => {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      if (diffHours < 1) return 'Just now';
      if (diffHours < 24) return `${diffHours}h ago`;
      const diffDays = Math.floor(diffHours / 24);
      if (diffDays < 7) return `${diffDays}d ago`;
      return `${Math.floor(diffDays / 7)}w ago`;
    } catch {
      return '';
    }
  };

  return (
    <div className="flex flex-col gap-3.5">
      {/* ── Header & Feed Controls (Yellow renovated section) ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Left: Feed title + Active solo channel pill */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-300">
            <Film className="w-3.5 h-3.5 text-cyan-400" />
            <span>Inspiration Feed</span>
          </div>

          <span className="text-[10px] text-slate-500 font-mono">
            {filteredItems.length} posts
          </span>

          {/* Active Solo Channel Filter Indicator */}
          {activeSoloChannel && (
            <div className="flex items-center gap-1.5 bg-cyan-500/10 border border-cyan-500/25 text-cyan-300 px-2 py-0.5 rounded-full text-[11px] font-semibold animate-in fade-in zoom-in-95">
              <span>Solo: <strong>{activeSoloChannel.name}</strong></span>
              <button
                onClick={handleClearChannelFilter}
                className="w-3.5 h-3.5 rounded-full hover:bg-cyan-500/20 text-cyan-400 flex items-center justify-center cursor-pointer transition active:scale-90"
                title="Clear filter (show all channels)"
              >
                <X className="w-2.5 h-2.5" />
              </button>
            </div>
          )}
        </div>

        {/* Right: Format Segmented Trigger + Sort Dropdown + Refresh */}
        <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
          {/* Format Switcher: Shorts / Videos / All */}
          <div className="flex items-center bg-[#0d121c] border border-[#1f2736] p-0.5 rounded-xl shadow-xs">
            <button
              onClick={() => setShortsFormat('shorts')}
              className={`h-7 px-2.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition active:scale-95 cursor-pointer ${
                shortsFormat === 'shorts'
                  ? 'bg-cyan-500 text-black font-bold shadow-[0_0_10px_rgba(0,242,254,0.3)]'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Zap className="w-3 h-3 fill-current" />
              <span>Shorts</span>
            </button>

            <button
              onClick={() => setShortsFormat('videos')}
              className={`h-7 px-2.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition active:scale-95 cursor-pointer ${
                shortsFormat === 'videos'
                  ? 'bg-cyan-500 text-black font-bold shadow-[0_0_10px_rgba(0,242,254,0.3)]'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Film className="w-3 h-3" />
              <span>Videos</span>
            </button>

            <button
              onClick={() => setShortsFormat('all')}
              className={`h-7 px-2 rounded-lg text-xs font-semibold flex items-center gap-1 transition active:scale-95 cursor-pointer ${
                shortsFormat === 'all'
                  ? 'bg-cyan-500 text-black font-bold shadow-[0_0_10px_rgba(0,242,254,0.3)]'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <span>All</span>
            </button>
          </div>

          {/* Mini Sort Dropdown */}
          <div className="relative" ref={sortDropdownRef}>
            <button
              onClick={() => setIsSortDropdownOpen(!isSortDropdownOpen)}
              className="h-8 px-2.5 rounded-xl bg-[#0d121c] hover:bg-[#151c2a] border border-[#1f2736] hover:border-[#28354b] text-slate-300 hover:text-cyan-400 text-xs font-medium flex items-center gap-1.5 transition active:scale-95 cursor-pointer"
              title="Sort feed"
            >
              {shortsSort === 'latest' && <Clock className="w-3 h-3 text-cyan-400" />}
              {shortsSort === 'popular' && <Flame className="w-3 h-3 text-amber-400" />}
              {shortsSort === 'oldest' && <Calendar className="w-3 h-3 text-slate-400" />}
              <span className="capitalize">{shortsSort}</span>
              <ChevronDown className={`w-3 h-3 text-slate-400 transition-transform ${isSortDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {isSortDropdownOpen && (
              <div className="absolute right-0 mt-1 w-32 bg-[#0c1017] border border-[#222c3d] rounded-xl shadow-[0_12px_30px_rgba(0,0,0,0.8)] py-1 z-50 animate-in fade-in zoom-in-95">
                <button
                  onClick={() => {
                    setShortsSort('latest');
                    setIsSortDropdownOpen(false);
                  }}
                  className={`w-full px-3 py-1.5 text-left text-xs flex items-center gap-2 hover:bg-[#161f30] transition ${
                    shortsSort === 'latest' ? 'text-cyan-400 font-bold bg-[#131b2a]' : 'text-slate-300'
                  }`}
                >
                  <Clock className="w-3 h-3 text-cyan-400" />
                  <span>Latest</span>
                </button>

                <button
                  onClick={() => {
                    setShortsSort('popular');
                    setIsSortDropdownOpen(false);
                  }}
                  className={`w-full px-3 py-1.5 text-left text-xs flex items-center gap-2 hover:bg-[#161f30] transition ${
                    shortsSort === 'popular' ? 'text-amber-400 font-bold bg-[#131b2a]' : 'text-slate-300'
                  }`}
                >
                  <Flame className="w-3 h-3 text-amber-400" />
                  <span>Popular</span>
                </button>

                <button
                  onClick={() => {
                    setShortsSort('oldest');
                    setIsSortDropdownOpen(false);
                  }}
                  className={`w-full px-3 py-1.5 text-left text-xs flex items-center gap-2 hover:bg-[#161f30] transition ${
                    shortsSort === 'oldest' ? 'text-slate-200 font-bold bg-[#131b2a]' : 'text-slate-400'
                  }`}
                >
                  <Calendar className="w-3 h-3 text-slate-400" />
                  <span>Oldest</span>
                </button>
              </div>
            )}
          </div>

          {/* Refresh Feed Button */}
          <button
            onClick={() => fetchShortsFeed(true)}
            disabled={isShortsLoading}
            title="Refresh latest YouTube feeds"
            className="h-8 w-8 rounded-xl bg-[#0d121c] hover:bg-[#161f30] border border-[#1f2736] text-slate-400 hover:text-cyan-400 flex items-center justify-center transition active:scale-95 shrink-0 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isShortsLoading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* ── Pinterest-like 9:16 Shorts Grid ── */}
      {isShortsLoading && shortsFeed.length === 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 sm:gap-4">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="aspect-[9/16] rounded-2xl bg-[#0d121c]/60 border border-[#1a2233] animate-pulse flex flex-col justify-end p-3.5"
            >
              <div className="h-4 bg-[#1f2a3e] rounded w-3/4 mb-2" />
              <div className="h-3 bg-[#1f2a3e] rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="rounded-2xl bg-[#0d121c] border border-[#1f2736] p-8 text-center flex flex-col items-center justify-center gap-2">
          <Film className="w-8 h-8 text-slate-600 mb-1" />
          <p className="text-sm font-semibold text-slate-300">
            {activeSoloChannel ? `No posts found for ${activeSoloChannel.name}` : 'No inspiration posts found'}
          </p>
          <p className="text-xs text-slate-500">
            {activeSoloChannel 
              ? 'Try clearing the solo filter or hit the refresh button to re-fetch.'
              : 'Hit the refresh button to re-fetch the latest channel feeds.'}
          </p>
          {activeSoloChannel && (
            <button
              onClick={handleClearChannelFilter}
              className="mt-2 text-xs text-cyan-400 hover:underline cursor-pointer"
            >
              Show all tracked channels
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 sm:gap-4">
          <AnimatePresence mode="popLayout">
            {filteredItems.map((short) => (
              <motion.div
                key={short.id}
                layout
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.96 }}
                transition={{ duration: 0.2 }}
                className="group relative aspect-[9/16] rounded-2xl overflow-hidden bg-[#0d121c] border border-[#1e2738] hover:border-cyan-500/60 transition-all duration-300 shadow-md hover:shadow-[0_10px_25px_-5px_rgba(0,242,254,0.15)] flex flex-col justify-between"
              >
                {/* Background Thumbnail Image */}
                <img
                  src={short.thumbnail_url}
                  alt={short.title}
                  referrerPolicy="no-referrer"
                  className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  loading="lazy"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    if (!target.src.includes('hqdefault')) {
                      target.src = `https://i.ytimg.com/vi/${short.id}/hqdefault.jpg`;
                    }
                  }}
                />

                {/* Scrim Gradients */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/40 to-black/25 pointer-events-none" />

                {/* Top Badges */}
                <div className="relative z-10 p-2.5 sm:p-3 flex items-center justify-between gap-1.5">
                  <span className={`${short.is_short === false ? 'bg-indigo-600/90' : 'bg-red-600/90'} text-white text-[9px] uppercase font-bold px-1.5 py-0.5 rounded tracking-wide shadow-sm flex items-center gap-1`}>
                    <Play className="w-2.5 h-2.5 fill-current" />
                    {short.is_short === false ? 'Video' : 'Short'}
                  </span>

                  {short.published_at && (
                    <span className="text-[10px] text-slate-300/90 font-mono bg-black/60 backdrop-blur-xs px-1.5 py-0.5 rounded border border-white/10">
                      {formatRelativeTime(short.published_at)}
                    </span>
                  )}
                </div>

                {/* Bottom Metadata & Recreate Action */}
                <div className="relative z-10 p-3 sm:p-3.5 flex flex-col gap-2">
                  {/* Channel Tag */}
                  <div className="flex items-center gap-1.5">
                    {short.avatar_url ? (
                      <img
                        src={short.avatar_url}
                        alt={short.channel_name}
                        referrerPolicy="no-referrer"
                        className="w-4 h-4 rounded-full object-cover border border-white/20 shrink-0"
                      />
                    ) : (
                      <div className="w-4 h-4 rounded-full bg-cyan-500/20 text-cyan-300 text-[8px] font-bold flex items-center justify-center border border-cyan-400/30">
                        {short.channel_name ? short.channel_name[0] : '@'}
                      </div>
                    )}
                    <span className="text-[11px] font-medium text-slate-300 truncate">
                      {short.channel_name}
                    </span>
                  </div>

                  {/* Title */}
                  <h4 className="text-xs sm:text-[13px] font-bold text-white line-clamp-2 leading-snug group-hover:text-cyan-300 transition-colors">
                    {short.title}
                  </h4>

                  {/* Recreate & View Actions */}
                  <div className="flex items-center gap-1.5 pt-1">
                    <button
                      onClick={() => handleRecreate(short)}
                      className="flex-1 py-1.5 px-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-xs flex items-center justify-center gap-1.5 transition active:scale-95 shadow-[0_0_12px_rgba(0,242,254,0.3)] cursor-pointer"
                      title="Generate new script using this concept"
                    >
                      <Sparkles className="w-3.5 h-3.5 fill-black" />
                      <span>Recreate</span>
                    </button>

                    <a
                      href={short.video_url || `https://www.youtube.com/watch?v=${short.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      title="Watch on YouTube"
                      className="w-7 h-7 rounded-xl bg-black/60 hover:bg-black/90 border border-white/20 text-slate-300 hover:text-white flex items-center justify-center transition active:scale-95 shrink-0"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};

