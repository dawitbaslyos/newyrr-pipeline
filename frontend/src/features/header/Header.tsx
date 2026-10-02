import React, { useState } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { ChevronDown, Settings, Sparkles, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const Header: React.FC = () => {
  const { studioMode, setStudioMode, setActiveTab, settings, setModal, isEditorOpen } = useStudioStore();
  const [isModeMenuOpen, setIsModeMenuOpen] = useState(false);

  if (isEditorOpen) return null; // Studio mode has its own dedicated top bar

  const getImgShortName = () => {
    const m = (settings.image_model || '').toLowerCase();
    if (m.includes('krea')) return 'Krea Turbo';
    if (m.includes('flux')) return 'Flux Schnell';
    if (m.includes('banana')) return 'Banana 2';
    return m.split('/').pop() || 'Krea Turbo';
  };

  const getVidShortName = () => {
    const v = (settings.video_provider || '').toLowerCase();
    if (v.includes('seedance')) return 'Seedance 2.0';
    if (v.includes('minimax') || v.includes('h3')) return 'MiniMax H3';
    if (v.includes('hailuo')) return 'Hailuo-3';
    return v.split('/').pop() || 'Seedance 2.0';
  };

  const getVoiceName = () => settings.tts_voice || 'Charon';

  return (
    <header className="h-14 border-b border-[#1f2736] bg-[#07090e]/90 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between shrink-0 z-30">
      {/* Left: Mode Selector (SmoothUI Pill Dropdown) */}
      <div className="relative">
        <button
          onClick={() => setIsModeMenuOpen(!isModeMenuOpen)}
          className="flex items-center gap-2 bg-[#0d111a] hover:bg-[#161b26] border border-[#1f2736] hover:border-cyan-400/50 px-3.5 py-1.5 rounded-full text-xs font-semibold text-slate-200 transition-all active:scale-95 shadow-sm cursor-pointer"
        >
          <span>{studioMode === 'create' ? <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> : <RefreshCw className="w-3.5 h-3.5 text-indigo-400" />}</span>
          <span className="font-bold">{studioMode === 'create' ? 'Create' : 'Repurpose'}</span>
          <ChevronDown className="w-3 h-3 text-slate-400" />
        </button>

        <AnimatePresence>
          {isModeMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: 6, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 6, scale: 0.98 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full left-0 mt-2 w-72 bg-[#0c0f18] border border-slate-700/80 rounded-2xl shadow-2xl p-2 z-50 flex flex-col gap-1.5"
            >
              <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Studio Generation Mode
              </div>

              {/* Mode 1: Create */}
              <div
                onClick={() => {
                  setStudioMode('create');
                  setActiveTab('channels');
                  setIsModeMenuOpen(false);
                }}
                className={`p-2.5 rounded-xl border cursor-pointer transition flex items-start gap-2.5 ${
                  studioMode === 'create'
                    ? 'border-cyan-400/40 bg-cyan-950/20'
                    : 'border-[#1f2736] hover:border-slate-600 hover:bg-[#161b26]'
                }`}
              >
                <div className="w-7 h-7 rounded-lg bg-cyan-400 text-black font-black flex items-center justify-center text-xs shrink-0 mt-0.5">
                  ✨
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-100">Create (From Scratch)</span>
                    {studioMode === 'create' && (
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-cyan-400/20 text-cyan-300">
                        Active
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-slate-400 mt-0.5 leading-snug">
                    AI Screenplay ➔ Stills ➔ Video ➔ CapCut Subtitles
                  </p>
                </div>
              </div>

              {/* Mode 2: Repurpose */}
              <div
                onClick={() => {
                  setStudioMode('repurpose');
                  setActiveTab('channels');
                  setIsModeMenuOpen(false);
                }}
                className={`p-2.5 rounded-xl border cursor-pointer transition flex items-start gap-2.5 ${
                  studioMode === 'repurpose'
                    ? 'border-indigo-500/40 bg-indigo-950/30'
                    : 'border-[#1f2736] hover:border-slate-600 hover:bg-[#161b26]'
                }`}
              >
                <div className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 font-black flex items-center justify-center text-xs shrink-0 mt-0.5">
                  🔄
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-200">Repurpose (Video-as-Code)</span>
                    <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                      HyperFrames
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-0.5 leading-snug">
                    Recreate viral shorts with Motion Canvas & SVG-ORA
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Right: Dynamic Model Stack Indicator + Settings Trigger */}
      <div className="flex items-center gap-2.5">
        <button
          onClick={() => setModal('settings', true)}
          title="Active Model Stack (Click to configure)"
          className="hidden sm:flex items-center gap-2 bg-[#0d111a] hover:bg-[#161b26] border border-[#1f2736] hover:border-cyan-400/50 px-3.5 py-1.5 rounded-full text-xs font-medium text-slate-300 transition active:scale-95 shadow-sm cursor-pointer"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          <span className="text-slate-200 font-bold">{getImgShortName()}</span>
          <span className="text-slate-600">+</span>
          <span className="text-slate-200 font-bold">{getVidShortName()}</span>
          <span className="text-slate-600">·</span>
          <span className="text-cyan-400 font-mono text-[11px] font-semibold">{getVoiceName()}</span>
        </button>

        <button
          onClick={() => setModal('settings', true)}
          title="Pipeline Engine & Model Settings"
          className="w-8 h-8 rounded-full bg-[#0d111a] hover:bg-[#161b26] border border-[#1f2736] hover:border-cyan-400 text-slate-300 hover:text-cyan-400 flex items-center justify-center transition-all active:scale-95 shadow-sm cursor-pointer"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
