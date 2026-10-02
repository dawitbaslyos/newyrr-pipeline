import React, { useState, useEffect } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { RainbowBorder } from '../../components/ui/rainbow-border';
import { 
  Radio, 
  RefreshCw, 
  Sparkles, 
  Download, 
  Film, 
  ExternalLink,
  Plus,
  X,
  Clock
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface CompetitorVideo {
  id: string;
  channel_name: string;
  channel_handle?: string;
  title: string;
  thumbnail_url: string;
  published_at: string;
  video_url: string;
}

interface DeconstructResult {
  video_id: string;
  title: string;
  hook: string;
  full_narration: string;
  key_takeaway: string;
  original_title: string;
  original_channel: string;
  thumbnail_url: string;
  detected_credits?: string[];
}

export const RepurposeFeedView: React.FC = () => {
  const { trackedChannels, setModal } = useStudioStore();
  
  // State
  const [videos, setVideos] = useState<CompetitorVideo[]>([]);
  const [selectedChannel, setSelectedChannel] = useState<string>(''); // '' means all
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [sourceUrlInput, setSourceUrlInput] = useState('');

  // Active Repurpose Modal / Drawer State
  const [activeVideo, setActiveVideo] = useState<CompetitorVideo | null>(null);
  const [isDeconstructing, setIsDeconstructing] = useState(false);
  const [deconstructed, setDeconstructed] = useState<DeconstructResult | null>(null);
  const [narration, setNarration] = useState('');
  const [targetDuration, setTargetDuration] = useState<number>(45);
  const [voiceKey, setVoiceKey] = useState('christopher');
  const [formatMode, setFormatMode] = useState<'shorts_9_16' | 'original_16_9'>('shorts_9_16');
  const [watermarkDefense, setWatermarkDefense] = useState<'punch_in' | 'scrim' | 'none'>('punch_in');
  const [burnSubtitles, setBurnSubtitles] = useState(true);
  const [isRendering, setIsRendering] = useState(false);
  const [renderedUrl, setRenderedUrl] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Load competitor videos
  const loadFeed = async (refresh = false) => {
    if (refresh) setIsRefreshing(true);
    else setIsLoading(true);
    try {
      const url = `/api/repurpose/competitor-feed?refresh=${refresh}&handle=${encodeURIComponent(selectedChannel)}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setVideos(data || []);
      }
    } catch (e) {
      console.error('Failed loading competitor feed:', e);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadFeed(false);
  }, [selectedChannel]);

  // Handle Deconstruct
  const handleStartRepurpose = async (vid: CompetitorVideo | { id: string; url: string; title: string }) => {
    const videoId = vid.id;
    setActiveVideo(vid as any);
    setIsDeconstructing(true);
    setErrorMsg(null);
    setDeconstructed(null);
    setRenderedUrl(null);

    try {
      const res = await fetch('/api/repurpose/deconstruct', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: (vid as any).video_url || `https://www.youtube.com/watch?v=${videoId}`,
          target_seconds: targetDuration
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed deconstructing video');
      }

      const data: DeconstructResult = await res.json();
      setDeconstructed(data);
      setNarration(data.full_narration || '');
    } catch (e: any) {
      setErrorMsg(e.message || 'Deconstruction failed. Make sure URL is accessible.');
    } finally {
      setIsDeconstructing(false);
    }
  };

  // Handle URL form submit
  const handleUrlSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceUrlInput.trim()) return;
    handleStartRepurpose({
      id: sourceUrlInput.trim(),
      url: sourceUrlInput.trim(),
      title: 'Direct URL Video'
    });
  };

  // Render Repurposed Video
  const handleRenderRepurposed = async () => {
    if (!deconstructed || !narration.trim()) return;
    setIsRendering(true);
    setErrorMsg(null);
    setRenderedUrl(null);

    try {
      const res = await fetch('/api/repurpose/render', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_id: deconstructed.video_id,
          narration_text: narration.trim(),
          voice_key: voiceKey,
          format_mode: formatMode,
          watermark_defense: watermarkDefense,
          burn_subtitles: burnSubtitles
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Rendering failed');
      }

      const data = await res.json();
      setRenderedUrl(data.video_url);
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed rendering repurposed video.');
    } finally {
      setIsRendering(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 font-sans">
      {/* 1. Quick URL Deconstruct Hero Bar */}
      <div className="bg-[#0c0f18] border border-[#1f2736] rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-lg shrink-0">
            <Radio className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm sm:text-base font-bold text-slate-100 flex items-center gap-2">
              <span>Viral Competitor Radar & Repurposer</span>
              <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-black">
                0-Quota RSS
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Live uploads from tracked channels. 1-click deconstruction, AI re-scripting, and watermark defense.
            </p>
          </div>
        </div>

        {/* Quick URL Input */}
        <form onSubmit={handleUrlSubmit} className="flex items-center gap-2 w-full sm:w-auto">
          <input
            type="text"
            placeholder="Paste any YouTube Short or Video URL..."
            value={sourceUrlInput}
            onChange={(e) => setSourceUrlInput(e.target.value)}
            className="bg-[#07090e] border border-[#1f2736] rounded-xl px-3 py-2 text-xs text-slate-200 outline-none focus:border-indigo-400 w-full sm:w-72"
          />
          <button
            type="submit"
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold px-3.5 py-2 rounded-xl transition flex items-center gap-1.5 shrink-0 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Repurpose</span>
          </button>
        </form>
      </div>

      {/* 2. Tracked Channels Radar Bar & Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#1f2736] pb-3">
        <div className="flex items-center gap-2 overflow-x-auto scrollbar-none py-1">
          <button
            onClick={() => setSelectedChannel('')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold shrink-0 transition cursor-pointer ${
              selectedChannel === ''
                ? 'bg-indigo-600 text-white font-bold shadow-sm'
                : 'bg-[#0d111a] text-slate-400 hover:text-slate-200 border border-[#1f2736]'
            }`}
          >
            All Competitors ({videos.length})
          </button>

          {trackedChannels.map((c) => {
            const isSelected = selectedChannel.toLowerCase() === c.handle.toLowerCase();
            return (
              <button
                key={c.handle}
                onClick={() => setSelectedChannel(isSelected ? '' : c.handle)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold shrink-0 transition cursor-pointer flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-indigo-600 text-white font-bold shadow-sm'
                    : 'bg-[#0d111a] text-slate-400 hover:text-slate-200 border border-[#1f2736]'
                }`}
              >
                <span>{c.name}</span>
                <span className="text-[10px] opacity-70 font-mono">{c.handle}</span>
              </button>
            );
          })}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            disabled={isRefreshing}
            onClick={() => loadFeed(true)}
            className="text-xs bg-[#0d111a] hover:bg-[#161b26] border border-[#1f2736] text-slate-300 hover:text-white px-2.5 py-1.5 rounded-xl transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            {isRefreshing ? (
              <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
            ) : (
              <RefreshCw className="w-3.5 h-3.5" />
            )}
            <span>Sync Feeds</span>
          </button>
          <button
            onClick={() => setModal('addTrackedChannel', true)}
            className="text-xs bg-indigo-950/60 hover:bg-indigo-900 border border-indigo-400/40 text-indigo-300 px-2.5 py-1.5 rounded-xl transition flex items-center gap-1 cursor-pointer font-semibold"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Track Channel</span>
          </button>
        </div>
      </div>

      {/* 3. Competitor Video Radar Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="aspect-[9/16] bg-[#0d111a] border border-[#1f2736] rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : videos.length === 0 ? (
        <div className="p-12 text-center text-slate-500 text-xs border border-dashed border-[#1f2736] rounded-2xl flex flex-col items-center gap-2">
          <Radio className="w-8 h-8 opacity-40 text-indigo-400" />
          <span>No competitor videos tracked yet. Click "Track Channel" above to add competitor handles!</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {videos.map((vid) => (
            <div
              key={vid.id}
              className="bg-[#0c0f18] hover:bg-[#131722] border border-[#1f2736] hover:border-indigo-400/60 rounded-2xl overflow-hidden transition flex flex-col group shadow-sm"
            >
              {/* Thumbnail */}
              <div className="relative aspect-video bg-black overflow-hidden">
                <img
                  src={vid.thumbnail_url}
                  alt={vid.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                />
                <div className="absolute top-2 left-2 bg-black/80 px-2 py-0.5 rounded text-[10px] font-bold text-slate-200">
                  {vid.channel_name}
                </div>
              </div>

              {/* Info */}
              <div className="p-3.5 flex flex-col justify-between flex-1 gap-3">
                <div>
                  <h3 className="text-xs font-bold text-slate-100 group-hover:text-indigo-300 leading-snug line-clamp-2">
                    {vid.title}
                  </h3>
                  {vid.published_at && (
                    <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1 font-mono">
                      <Clock className="w-3 h-3" />
                      <span>{vid.published_at.slice(0, 10)}</span>
                    </div>
                  )}
                </div>

                <div className="pt-2 border-t border-[#1f2736]/60 flex items-center justify-between">
                  <a
                    href={vid.video_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] text-slate-400 hover:text-white flex items-center gap-1"
                  >
                    <span>Original</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>

                  <button
                    onClick={() => handleStartRepurpose(vid)}
                    className="bg-indigo-600 hover:bg-indigo-500 active:scale-95 text-white text-xs font-bold px-3 py-1.5 rounded-xl transition flex items-center gap-1.5 shadow-sm cursor-pointer"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>⚡ Repurpose</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 4. Streamlined In-Place Repurpose Studio Modal */}
      <AnimatePresence>
        {activeVideo && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/85 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              className="w-full max-w-4xl bg-[#0c0f18] border border-[#1f2736] rounded-3xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-[#1f2736] shrink-0 bg-[#0c0f18]">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">
                      Viral Explainer Repurposer
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      Distilling source footage into a high-retention Short
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => setActiveVideo(null)}
                  className="w-8 h-8 rounded-xl bg-[#07090e] hover:bg-[#161b26] border border-[#1f2736] text-slate-400 hover:text-white flex items-center justify-center transition cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Body */}
              <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-5">
                {isDeconstructing ? (
                  <div className="relative p-12 text-center flex flex-col items-center justify-center gap-3 bg-[#0d111a] border border-[#1f2736] rounded-2xl overflow-hidden">
                    <RainbowBorder isLoading={true} borderRadius={16} strokeWidth={3} />
                    <div className="bg-[#07090e]/90 border border-slate-700/80 px-4 py-2 rounded-full shadow-2xl flex items-center gap-2.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-indigo-400 animate-ping" />
                      <span className="text-xs font-bold text-slate-100 uppercase tracking-wider">
                        Deconstructing Video & Synthesizing Script
                      </span>
                    </div>
                    <span className="text-xs text-slate-400 max-w-sm">
                      Extracting audio transcript, removing filler words, and writing viral hook via Gemini
                    </span>
                  </div>
                ) : deconstructed ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    {/* Left Column: Script */}
                    <div className="flex flex-col gap-3">
                      <div className="flex items-center justify-between">
                        <label className="text-xs font-bold uppercase tracking-wider text-slate-300">
                          Spoken Voiceover Script
                        </label>
                        <span className="text-xs font-mono text-indigo-400 font-bold">
                          ~{narration.split(' ').length} words
                        </span>
                      </div>

                      <textarea
                        rows={6}
                        value={narration}
                        onChange={(e) => setNarration(e.target.value)}
                        className="w-full bg-[#07090e] border border-[#1f2736] rounded-xl p-3 text-xs text-slate-100 outline-none focus:border-indigo-400 resize-none leading-relaxed"
                      />

                      {/* Hook & Takeaway */}
                      <div className="bg-[#07090e] border border-[#1f2736] p-3 rounded-xl flex flex-col gap-1.5 text-xs">
                        <div className="text-[10px] uppercase font-bold text-amber-400">Opening Hook</div>
                        <div className="text-slate-200 italic">"{deconstructed.hook}"</div>
                        <div className="text-[10px] uppercase font-bold text-emerald-400 mt-1">Core Takeaway</div>
                        <div className="text-slate-300">{deconstructed.key_takeaway}</div>
                      </div>
                    </div>

                    {/* Right Column: Rendering Controls */}
                    <div className="flex flex-col gap-3.5">
                      {/* Target Duration */}
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <label className="text-[11px] font-bold uppercase text-slate-400">
                            Target Short Length
                          </label>
                          <span className="text-[10px] font-mono text-indigo-400 font-bold">{targetDuration}s</span>
                        </div>
                        <div className="grid grid-cols-3 gap-1.5">
                          {[30, 45, 60].map((sec) => (
                            <button
                              key={sec}
                              onClick={() => setTargetDuration(sec)}
                              className={`p-1.5 rounded-xl border text-center text-xs font-bold transition cursor-pointer ${
                                targetDuration === sec
                                  ? 'border-indigo-400 bg-indigo-950/40 text-indigo-300'
                                  : 'border-[#1f2736] hover:bg-[#161b26] text-slate-400'
                              }`}
                            >
                              {sec}s
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Format */}
                      <div>
                        <label className="text-[11px] font-bold uppercase text-slate-400 block mb-1">
                          Output Aspect Ratio
                        </label>
                        <select
                          value={formatMode}
                          onChange={(e) => setFormatMode(e.target.value as any)}
                          className="w-full bg-[#07090e] border border-[#1f2736] rounded-xl p-2.5 text-xs text-slate-200 outline-none focus:border-indigo-400"
                        >
                          <option value="shorts_9_16">9:16 Vertical Short (Smart Center Crop - cuts off 16:9 watermarks)</option>
                          <option value="original_16_9">16:9 Widescreen (Original Explainer)</option>
                        </select>
                      </div>

                      {/* Watermark Defense */}
                      <div>
                        <label className="text-[11px] font-bold uppercase text-slate-400 block mb-1">
                          Watermark Defense Mode
                        </label>
                        <select
                          value={watermarkDefense}
                          onChange={(e) => setWatermarkDefense(e.target.value as any)}
                          className="w-full bg-[#07090e] border border-[#1f2736] rounded-xl p-2.5 text-xs text-slate-200 outline-none focus:border-indigo-400"
                        >
                          <option value="punch_in">8% Clean Punch-In (Zooms past edge logos & bottom subtitles)</option>
                          <option value="scrim">Dark Lower-Third Scrim (Masks old subtitles with vignette box)</option>
                          <option value="none">Direct Passthrough (No crop or mask)</option>
                        </select>
                      </div>

                      {/* Voiceover Actor */}
                      <div>
                        <label className="text-[11px] font-bold uppercase text-slate-400 block mb-1">
                          Neural Voice Actor (Edge-TTS)
                        </label>
                        <select
                          value={voiceKey}
                          onChange={(e) => setVoiceKey(e.target.value)}
                          className="w-full bg-[#07090e] border border-[#1f2736] rounded-xl p-2.5 text-xs text-slate-200 outline-none focus:border-indigo-400"
                        >
                          <option value="christopher">Christopher (Deep Authoritative Documentary)</option>
                          <option value="guy">Guy (Confident Tech Specialist)</option>
                          <option value="eric">Eric (Energetic Storyteller)</option>
                          <option value="sonia">Sonia (British Articulate Narrative)</option>
                          <option value="jenny">Jenny (Warm Natural Explainer)</option>
                        </select>
                      </div>

                      {/* Burn Subtitles Toggle */}
                      <div className="flex items-center justify-between p-2.5 bg-[#07090e] border border-[#1f2736] rounded-xl text-xs">
                        <span className="text-slate-300">Burn CapCut Kinetic Subtitles</span>
                        <input
                          type="checkbox"
                          checked={burnSubtitles}
                          onChange={(e) => setBurnSubtitles(e.target.checked)}
                          className="accent-indigo-500 w-4 h-4 cursor-pointer"
                        />
                      </div>

                      {/* Render Button */}
                      <button
                        disabled={isRendering}
                        onClick={handleRenderRepurposed}
                        className="w-full mt-2 bg-indigo-600 hover:bg-indigo-500 active:scale-95 text-white font-bold py-2.5 rounded-xl transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 shadow-lg shadow-indigo-950/50 text-xs"
                      >
                        {isRendering ? (
                          <>
                            <span className="w-2.5 h-2.5 rounded-full bg-cyan-300 animate-ping" />
                            <span>Downloading & Rendering Repurposed Short...</span>
                          </>
                        ) : (
                          <>
                            <Film className="w-4 h-4" />
                            <span>⚡ Render Repurposed Video</span>
                          </>
                        )}
                      </button>

                      {/* Rendered Result Preview */}
                      {renderedUrl && (
                        <div className="mt-3 p-3 bg-indigo-950/30 border border-indigo-400/40 rounded-2xl flex flex-col gap-2.5">
                          <div className="flex items-center justify-between text-xs font-bold text-indigo-300">
                            <span>Render Complete!</span>
                            <a
                              href={renderedUrl}
                              download
                              className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white px-2.5 py-1 rounded-lg flex items-center gap-1 font-semibold"
                            >
                              <Download className="w-3.5 h-3.5" />
                              <span>Download MP4</span>
                            </a>
                          </div>
                          <video src={renderedUrl} controls className="w-full rounded-xl max-h-56 object-contain bg-black" />
                        </div>
                      )}

                      {errorMsg && (
                        <div className="text-xs text-rose-400 bg-rose-950/40 border border-rose-800/50 p-2.5 rounded-xl">
                          {errorMsg}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  errorMsg && (
                    <div className="text-xs text-rose-400 bg-rose-950/40 border border-rose-800/50 p-4 rounded-xl text-center">
                      {errorMsg}
                    </div>
                  )
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default RepurposeFeedView;
