import React, { useState, useEffect } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { Sparkles, ExternalLink, RefreshCw, Film, Play } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface ShortFeedItem {
  id: string;
  title: string;
  channel_name: string;
  channel_handle: string;
  avatar_url?: string;
  thumbnail_url: string;
  video_url: string;
  published_at?: string;
  description?: string;
}

interface TrackedShortsFeedProps {
  selectedChannelHandle?: string | null;
  onSelectChannelHandle?: (handle: string | null) => void;
}

export const TrackedShortsFeed: React.FC<TrackedShortsFeedProps> = ({
  selectedChannelHandle,
  onSelectChannelHandle,
}) => {
  const { trackedChannels, setModal } = useStudioStore();
  const [shorts, setShorts] = useState<ShortFeedItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeFilter, setActiveFilter] = useState<string | null>(selectedChannelHandle || null);

  useEffect(() => {
    setActiveFilter(selectedChannelHandle || null);
  }, [selectedChannelHandle]);

  const fetchShorts = async (refresh: boolean = false) => {
    setIsLoading(true);
    try {
      const url = refresh ? '/api/channels/shorts-feed?refresh=true' : '/api/channels/shorts-feed';
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setShorts(data);
      }
    } catch (e) {
      console.error('Failed fetching shorts feed:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchShorts();
  }, []);

  const handleFilterClick = (handle: string | null) => {
    setActiveFilter(handle);
    if (onSelectChannelHandle) {
      onSelectChannelHandle(handle);
    }
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

  const filteredShorts = activeFilter
    ? shorts.filter((s) => s.channel_handle?.toLowerCase().trim() === activeFilter.toLowerCase().trim())
    : shorts;

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
      {/* Header & Channel Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-400">
            <Film className="w-3.5 h-3.5 text-cyan-400" />
            <span>Recent Inspiration Shorts</span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">
            {filteredShorts.length} posts
          </span>
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          {/* Refresh Feed Button */}
          <button
            onClick={() => fetchShorts(true)}
            disabled={isLoading}
            title="Refresh recent posts"
            className="w-7 h-7 rounded-lg bg-[#0d121c] hover:bg-[#161f30] border border-[#1f2736] text-slate-400 hover:text-cyan-400 flex items-center justify-center transition active:scale-95 shrink-0 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>

          {/* Filter Pills */}
          <div className="flex items-center gap-1.5 shrink-0">
            <button
              onClick={() => handleFilterClick(null)}
              className={`rounded-full px-3 py-1 text-[11px] font-semibold transition active:scale-95 cursor-pointer ${
                activeFilter === null
                  ? 'bg-cyan-500 text-black font-bold shadow-[0_0_12px_rgba(0,242,254,0.3)]'
                  : 'bg-[#0d121c] border border-[#1f2736] text-slate-400 hover:text-white hover:bg-[#151c2a]'
              }`}
            >
              All
            </button>
            {trackedChannels.map((c) => {
              const isSelected = activeFilter?.toLowerCase().trim() === c.handle.toLowerCase().trim();
              return (
                <button
                  key={c.handle}
                  onClick={() => handleFilterClick(c.handle)}
                  className={`rounded-full px-3 py-1 text-[11px] font-semibold transition active:scale-95 shrink-0 cursor-pointer ${
                    isSelected
                      ? 'bg-cyan-500 text-black font-bold shadow-[0_0_12px_rgba(0,242,254,0.3)]'
                      : 'bg-[#0d121c] border border-[#1f2736] text-slate-400 hover:text-white hover:bg-[#151c2a]'
                  }`}
                >
                  {c.name.split(' ')[0]}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Pinterest-like 9:16 Shorts Grid */}
      {isLoading && shorts.length === 0 ? (
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
      ) : filteredShorts.length === 0 ? (
        <div className="rounded-2xl bg-[#0d121c] border border-[#1f2736] p-8 text-center flex flex-col items-center justify-center gap-2">
          <Film className="w-8 h-8 text-slate-600 mb-1" />
          <p className="text-sm font-semibold text-slate-300">No recent Shorts found for this channel</p>
          <p className="text-xs text-slate-500">Hit the refresh button to re-fetch the latest RSS uploads.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 sm:gap-4">
          <AnimatePresence mode="popLayout">
            {filteredShorts.map((short) => (
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
                  className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  loading="lazy"
                  onError={(e) => {
                    // Fallback to high quality YouTube thumbnail format
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
                  <span className="bg-red-600/90 text-white text-[9px] uppercase font-bold px-1.5 py-0.5 rounded tracking-wide shadow-sm flex items-center gap-1">
                    <Play className="w-2.5 h-2.5 fill-current" />
                    Short
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

                  {/* Recreate & View Actions (Always visible on mobile, elevated on hover) */}
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
                      title="Watch Short on YouTube"
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
