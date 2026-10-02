import React, { useState, useEffect } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  Sparkles, 
  Download, 
  Film, 
  RefreshCw, 
  Volume2, 
  Crop, 
  ShieldCheck, 
  Radio, 
  ExternalLink,
  ChevronRight,
  Loader2
} from 'lucide-react';

interface DeconstructResult {
  video_id: string;
  title: string;
  hook: string;
  full_narration: string;
  key_takeaway: string;
  original_title: string;
  original_channel: string;
  thumbnail_url: string;
}

interface CompetitorVideo {
  id: string;
  channel_name: string;
  title: string;
  thumbnail_url: string;
  published_at: string;
}

export const RepurposeModal: React.FC = () => {
  const { isRepurposeModalOpen, setModal, studioMode, setStudioMode } = useStudioStore();
  
  // Tabs
  const [activeTab, setActiveTab] = useState<'url' | 'feed'>('url');
  const [sourceUrl, setSourceUrl] = useState('');
  
  // Competitor Feed
  const [competitorVideos, setCompetitorVideos] = useState<CompetitorVideo[]>([]);
  const [isLoadingFeed, setIsLoadingFeed] = useState(false);
  
  // Deconstruction state
  const [isDeconstructing, setIsDeconstructing] = useState(false);
  const [deconstructed, setDeconstructed] = useState<DeconstructResult | null>(null);
  
  // Customization
  const [narration, setNarration] = useState('');
  const [voiceKey, setVoiceKey] = useState('christopher');
  const [formatMode, setFormatMode] = useState<'shorts_9_16' | 'original_16_9'>('shorts_9_16');
  const [watermarkDefense, setWatermarkDefense] = useState<'punch_in' | 'scrim' | 'none'>('punch_in');
  const [burnSubtitles, setBurnSubtitles] = useState(true);
  
  // Render state
  const [isRendering, setIsRendering] = useState(false);
  const [renderedUrl, setRenderedUrl] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Load competitor feed when feed tab opens
  useEffect(() => {
    if (activeTab === 'feed' && competitorVideos.length === 0) {
      loadCompetitorFeed();
    }
  }, [activeTab]);

  if (!isRepurposeModalOpen && studioMode !== 'repurpose') return null;

  const loadCompetitorFeed = async () => {
    setIsLoadingFeed(true);
    try {
      const res = await fetch('/api/repurpose/competitor-feed');
      if (res.ok) {
        const data = await res.json();
        setCompetitorVideos(data || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingFeed(false);
    }
  };

  const handleDeconstruct = async (urlToUse?: string) => {
    const targetUrl = urlToUse || sourceUrl;
    if (!targetUrl.trim()) return;

    setIsDeconstructing(true);
    setErrorMsg(null);
    setDeconstructed(null);
    setRenderedUrl(null);

    try {
      const res = await fetch('/api/repurpose/deconstruct', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: targetUrl.trim(), target_seconds: 45 })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to deconstruct video');
      }

      const data: DeconstructResult = await res.json();
      setDeconstructed(data);
      setNarration(data.full_narration || '');
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to deconstruct video.');
    } finally {
      setIsDeconstructing(false);
    }
  };

  const handleRender = async () => {
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
      setErrorMsg(e.message || 'Rendering failed.');
    } finally {
      setIsRendering(false);
    }
  };

  const handleClose = () => {
    setModal('repurpose', false);
    if (studioMode === 'repurpose') {
      setStudioMode('create');
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/85 backdrop-blur-md font-sans">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.2 }}
          className="w-full max-w-5xl bg-[#0c0f18] border border-[#1f2736] rounded-3xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-[#1f2736]">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center">
                <Film className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  Viral Video Repurposing Studio
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">
                    yt-dlp • Gemini • Edge-TTS • FFmpeg
                  </span>
                </h2>
                <p className="text-[11px] text-slate-400">
                  Deconstruct viral shorts into clean video, fresh AI narrative, and re-voiced 9:16 vertical exports
                </p>
              </div>
            </div>

            <button
              onClick={handleClose}
              className="w-8 h-8 rounded-full bg-[#161b26] hover:bg-[#202738] text-slate-400 hover:text-slate-200 flex items-center justify-center transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Subheader Navigation */}
          <div className="px-6 py-2.5 bg-[#07090e] border-b border-[#1f2736] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('url')}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                  activeTab === 'url'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#161b26]'
                }`}
              >
                Paste Video URL
              </button>
              <button
                onClick={() => setActiveTab('feed')}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer ${
                  activeTab === 'feed'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#161b26]'
                }`}
              >
                <Radio className="w-3.5 h-3.5 text-cyan-400" />
                <span>Competitor 0-Quota RSS Feed</span>
              </button>
            </div>

            {deconstructed && (
              <span className="text-[11px] font-mono text-cyan-400 bg-cyan-950/30 px-2 py-0.5 rounded border border-cyan-400/30">
                Source: {deconstructed.original_channel || deconstructed.video_id}
              </span>
            )}
          </div>

          {/* Main Body */}
          <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left 6 cols: Ingest & Deconstructed Script */}
            <div className="lg:col-span-6 flex flex-col gap-4">
              {activeTab === 'url' ? (
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-semibold text-slate-300">
                    Source YouTube Short or Video URL
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="url"
                      disabled={isDeconstructing}
                      placeholder="e.g. https://www.youtube.com/shorts/5v2Xabcdef1"
                      value={sourceUrl}
                      onChange={(e) => setSourceUrl(e.target.value)}
                      className="flex-1 bg-[#07090e] border border-[#1f2736] focus:border-indigo-500 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 outline-none transition font-mono"
                    />
                    <button
                      onClick={() => handleDeconstruct()}
                      disabled={isDeconstructing || !sourceUrl.trim()}
                      className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl flex items-center gap-1.5 transition active:scale-95 cursor-pointer"
                    >
                      {isDeconstructing ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Analyzing...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>Deconstruct</span>
                        </>
                      )}
                    </button>
                  </div>
                  <span className="text-[10px] text-slate-400">
                    Pulls video via yt-dlp, extracts transcript, and writes a retention explainer script via Gemini.
                  </span>
                </div>
              ) : (
                /* Competitor Feed Tab */
                <div className="flex flex-col gap-2.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-slate-300">
                      Recent Uploads from Tracked Channels
                    </label>
                    <button
                      onClick={loadCompetitorFeed}
                      className="text-xs text-cyan-400 hover:underline flex items-center gap-1 cursor-pointer"
                    >
                      <RefreshCw className={`w-3 h-3 ${isLoadingFeed ? 'animate-spin' : ''}`} />
                      <span>Refresh Feed</span>
                    </button>
                  </div>

                  <div className="flex flex-col gap-2 max-h-[300px] overflow-y-auto pr-1">
                    {isLoadingFeed ? (
                      <div className="p-8 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
                        <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
                        <span>Querying 0-quota YouTube RSS feeds...</span>
                      </div>
                    ) : competitorVideos.length === 0 ? (
                      <div className="p-6 text-center text-xs text-slate-500 bg-[#07090e] border border-[#1f2736] rounded-2xl">
                        No competitor videos found. Add channels in Tracked Channels to populate.
                      </div>
                    ) : (
                      competitorVideos.map((vid) => (
                        <div
                          key={vid.id}
                          onClick={() => {
                            setSourceUrl(`https://www.youtube.com/watch?v=${vid.id}`);
                            setActiveTab('url');
                            handleDeconstruct(`https://www.youtube.com/watch?v=${vid.id}`);
                          }}
                          className="bg-[#07090e] hover:bg-[#161b26] border border-[#1f2736] hover:border-indigo-500/50 p-2.5 rounded-2xl flex items-center justify-between gap-3 cursor-pointer transition group"
                        >
                          <div className="flex items-center gap-3 overflow-hidden">
                            <img
                              src={vid.thumbnail_url}
                              alt=""
                              className="w-16 h-10 object-cover rounded-lg shrink-0 border border-[#1f2736]"
                            />
                            <div className="overflow-hidden">
                              <span className="text-[10px] font-bold text-cyan-400 block truncate">
                                {vid.channel_name}
                              </span>
                              <span className="text-xs font-semibold text-slate-200 line-clamp-1 group-hover:text-indigo-300">
                                {vid.title}
                              </span>
                            </div>
                          </div>
                          <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 shrink-0" />
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Error Banner */}
              {errorMsg && (
                <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/50 text-xs text-rose-300">
                  {errorMsg}
                </div>
              )}

              {/* Deconstructed Results */}
              {deconstructed && (
                <div className="flex flex-col gap-3 mt-2 bg-[#07090e] border border-[#1f2736] p-4 rounded-2xl">
                  <div className="flex items-start gap-3">
                    <img
                      src={deconstructed.thumbnail_url}
                      alt=""
                      className="w-20 h-14 object-cover rounded-xl shrink-0 border border-[#1f2736]"
                    />
                    <div className="overflow-hidden">
                      <span className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">
                        Original Reference
                      </span>
                      <h4 className="text-xs font-bold text-slate-100 line-clamp-1">
                        {deconstructed.original_title}
                      </h4>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        By {deconstructed.original_channel}
                      </p>
                    </div>
                  </div>

                  {/* Viral Hook */}
                  <div className="bg-[#0c0f18] p-3 rounded-xl border border-[#1f2736]">
                    <span className="text-[10px] uppercase font-bold text-amber-400 tracking-wider block mb-1">
                      Viral Hook (First 3 Seconds)
                    </span>
                    <p className="text-xs text-slate-200 font-medium italic">
                      "{deconstructed.hook}"
                    </p>
                  </div>

                  {/* Editable Narration */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[11px] font-bold text-slate-300 uppercase tracking-wider flex items-center justify-between">
                      <span>Explainer Voiceover Script</span>
                      <span className="text-[10px] text-slate-500 font-normal">
                        {narration.split(' ').filter(Boolean).length} words (~{Math.round(narration.split(' ').filter(Boolean).length / 2.4)}s)
                      </span>
                    </label>
                    <textarea
                      rows={5}
                      value={narration}
                      onChange={(e) => setNarration(e.target.value)}
                      className="w-full bg-[#0c0f18] border border-[#1f2736] rounded-xl p-3 text-xs text-slate-100 outline-none focus:border-indigo-500 leading-relaxed resize-none"
                    />
                  </div>

                  {/* Core Takeaway */}
                  <div className="text-[11px] text-slate-400 bg-[#0c0f18] p-2.5 rounded-xl border border-[#1f2736]/60">
                    <strong className="text-slate-300">Core Takeaway:</strong> {deconstructed.key_takeaway}
                  </div>
                </div>
              )}
            </div>

            {/* Right 6 cols: Production Config & Output Video Player */}
            <div className="lg:col-span-6 flex flex-col gap-4">
              {/* Configuration Controls */}
              <div className="bg-[#07090e] border border-[#1f2736] p-4 rounded-2xl flex flex-col gap-3.5">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  Repurposing Render Pipeline
                </h3>

                {/* Voice Profile */}
                <div className="flex flex-col gap-1">
                  <label className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5">
                    <Volume2 className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Narration Voice (Edge-TTS Studio)</span>
                  </label>
                  <select
                    value={voiceKey}
                    onChange={(e) => setVoiceKey(e.target.value)}
                    className="w-full bg-[#0c0f18] border border-[#1f2736] rounded-xl px-3 py-2 text-xs text-slate-200 outline-none focus:border-indigo-500 cursor-pointer"
                  >
                    <option value="christopher">Christopher (Authoritative Documentary • Deep)</option>
                    <option value="guy">Guy (Casual YouTube Creator • Dynamic)</option>
                    <option value="jenny">Jenny (Intelligent Explainer • Professional Female)</option>
                    <option value="eric">Eric (Bold & Energetic • Viral Pacing)</option>
                    <option value="brian">Brian (Refined British Intellectual)</option>
                  </select>
                </div>

                {/* Format Mode */}
                <div className="flex flex-col gap-1">
                  <label className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5">
                    <Crop className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Output Format & Framing</span>
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setFormatMode('shorts_9_16')}
                      className={`p-2.5 rounded-xl border text-xs font-semibold text-left transition cursor-pointer ${
                        formatMode === 'shorts_9_16'
                          ? 'border-indigo-500 bg-indigo-950/40 text-indigo-200'
                          : 'border-[#1f2736] bg-[#0c0f18] text-slate-400 hover:border-slate-600'
                      }`}
                    >
                      <div className="font-bold">9:16 Vertical Short</div>
                      <div className="text-[10px] text-slate-400 font-normal">Auto-chops side watermarks</div>
                    </button>

                    <button
                      type="button"
                      onClick={() => setFormatMode('original_16_9')}
                      className={`p-2.5 rounded-xl border text-xs font-semibold text-left transition cursor-pointer ${
                        formatMode === 'original_16_9'
                          ? 'border-indigo-500 bg-indigo-950/40 text-indigo-200'
                          : 'border-[#1f2736] bg-[#0c0f18] text-slate-400 hover:border-slate-600'
                      }`}
                    >
                      <div className="font-bold">16:9 Landscape</div>
                      <div className="text-[10px] text-slate-400 font-normal">Full original framing</div>
                    </button>
                  </div>
                </div>

                {/* Watermark Defense */}
                <div className="flex flex-col gap-1">
                  <label className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Watermark & Caption Defense</span>
                  </label>
                  <select
                    value={watermarkDefense}
                    onChange={(e: any) => setWatermarkDefense(e.target.value)}
                    className="w-full bg-[#0c0f18] border border-[#1f2736] rounded-xl px-3 py-2 text-xs text-slate-200 outline-none focus:border-indigo-500 cursor-pointer"
                  >
                    <option value="punch_in">8% Punch-In Zoom (Eliminates edge logos & captions)</option>
                    <option value="scrim">Dark Lower-Third Scrim (Masks old burned-in subtitles)</option>
                    <option value="none">None (Keep exact pixels)</option>
                  </select>
                </div>

                {/* Subtitles Toggle */}
                <div className="flex items-center justify-between pt-1">
                  <span className="text-xs font-semibold text-slate-300">
                    Burn High-Visibility CapCut Subtitles
                  </span>
                  <input
                    type="checkbox"
                    checked={burnSubtitles}
                    onChange={(e) => setBurnSubtitles(e.target.checked)}
                    className="w-4 h-4 accent-indigo-500 cursor-pointer"
                  />
                </div>

                {/* Render Action Trigger */}
                <button
                  disabled={!deconstructed || isRendering || !narration.trim()}
                  onClick={handleRender}
                  className="w-full mt-2 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-[#161b26] disabled:text-slate-600 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-2 transition active:scale-98 shadow-lg shadow-indigo-600/20 cursor-pointer disabled:cursor-not-allowed"
                >
                  {isRendering ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Rendering MP4 (yt-dlp ➔ Edge-TTS ➔ Whisper ➔ FFmpeg)...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>Render Repurposed Video</span>
                    </>
                  )}
                </button>
              </div>

              {/* Output Video Player */}
              <div className="flex-1 bg-[#07090e] border border-[#1f2736] rounded-2xl overflow-hidden flex flex-col items-center justify-center p-4 min-h-[260px]">
                {renderedUrl ? (
                  <div className="w-full flex flex-col items-center gap-3">
                    <video
                      src={renderedUrl}
                      controls
                      autoPlay
                      className={`rounded-xl border border-[#1f2736] shadow-xl max-h-[280px] ${
                        formatMode === 'shorts_9_16' ? 'aspect-[9/16]' : 'aspect-video'
                      }`}
                    />
                    <div className="flex items-center gap-2">
                      <a
                        href={renderedUrl}
                        download={`repurposed_${deconstructed?.video_id || 'video'}.mp4`}
                        className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-xs rounded-xl transition flex items-center gap-1.5 shadow-md shadow-emerald-500/20 cursor-pointer"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download Final MP4</span>
                      </a>
                      <a
                        href={renderedUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-2 bg-[#161b26] hover:bg-[#222a3d] text-slate-300 text-xs font-semibold rounded-xl transition flex items-center gap-1 cursor-pointer"
                      >
                        <ExternalLink className="w-3 h-3" />
                        <span>Pop Out</span>
                      </a>
                    </div>
                  </div>
                ) : isRendering ? (
                  <div className="flex flex-col items-center gap-3 text-slate-400">
                    <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
                    <p className="text-xs text-center">
                      Processing video pipeline...<br />
                      <span className="text-[10px] text-slate-500">
                        Downloading video, dubbing narration & burning timed subtitles
                      </span>
                    </p>
                  </div>
                ) : (
                  <div className="text-center text-slate-600 flex flex-col items-center gap-2 p-6">
                    <Film className="w-10 h-10 stroke-[1.2]" />
                    <p className="text-xs font-medium">
                      Paste a URL, click <strong>Deconstruct</strong>, then hit <strong>Render</strong> to preview the output video here.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
