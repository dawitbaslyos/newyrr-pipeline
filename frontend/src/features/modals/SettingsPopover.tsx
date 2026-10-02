import React, { useState } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { X, Cpu, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const SettingsPopover: React.FC = () => {
  const { isSettingsOpen, setModal, settings, saveSettings } = useStudioStore();
  const [localSettings, setLocalSettings] = useState(settings);
  const [isSaved, setIsSaved] = useState(false);

  if (!isSettingsOpen) return null;

  // Cost calculation
  let llmCost = 0.0004;
  let imgCost = 0.075;
  if (localSettings.image_model.includes('3.1-flash') || (localSettings.image_model.includes('banana') && !localSettings.image_model.includes('lite'))) {
    imgCost = 0.010;
  } else if (localSettings.image_model.includes('lite')) {
    imgCost = 0.004;
  } else if (localSettings.image_model.includes('flux')) {
    imgCost = 0.015;
  }

  let vidCost = 0.040;
  if (localSettings.video_provider.includes('seedance')) {
    vidCost = 0.840;
  } else if (localSettings.video_provider.includes('openrouter') || localSettings.video_provider.includes('hailuo')) {
    vidCost = 3.250;
  }

  const totalCost = llmCost + imgCost + vidCost + 0.0015;

  const handleSave = async () => {
    await saveSettings(localSettings);
    setIsSaved(true);
    setTimeout(() => {
      setIsSaved(false);
      setModal('settings', false);
    }, 600);
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-start justify-end p-4 sm:p-6 pointer-events-none">
        <motion.div
          initial={{ opacity: 0, y: -10, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10, scale: 0.95 }}
          className="pointer-events-auto w-[340px] sm:w-[380px] bg-[#0b0f19] border border-slate-700/80 rounded-2xl shadow-[0_25px_60px_rgba(0,0,0,0.98)] p-4 sm:p-5 flex flex-col gap-3 font-sans mt-12"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#1f2736] pb-2.5">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-cyan-400/20 border border-cyan-400/30 flex items-center justify-center text-cyan-400">
                <Cpu className="w-3.5 h-3.5" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wider">Engine Settings</h3>
                <p className="text-[10px] text-slate-400">Pure Cloud API • Instant Switch</p>
              </div>
            </div>
            <button
              onClick={() => setModal('settings', false)}
              className="w-6 h-6 rounded-full hover:bg-[#161b26] text-slate-400 hover:text-white flex items-center justify-center transition cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Model Pickers */}
          <div className="flex flex-col gap-2.5 text-xs">
            {/* LLM */}
            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">LLM Model</label>
              <select
                value={localSettings.llm_model}
                onChange={(e) => setLocalSettings({ ...localSettings, llm_model: e.target.value })}
                className="w-full bg-[#07090e] border border-[#1f2736] text-slate-200 text-xs rounded-xl px-3 py-2 outline-none focus:border-cyan-400 cursor-pointer"
              >
                <option value="openai/gpt-4o-mini">GPT-4o Mini ($0.0004 / Short)</option>
                <option value="anthropic/claude-3.5-sonnet">Claude 3.5 Sonnet ($0.006 / Short)</option>
                <option value="deepseek/deepseek-chat">DeepSeek V3 ($0.0003 / Short)</option>
                <option value="google/gemini-2.0-flash-exp:free">Gemini 2.0 Flash (Free)</option>
              </select>
            </div>

            {/* Image Model */}
            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Keyframe Image Generator</label>
              <select
                value={localSettings.image_model}
                onChange={(e) => setLocalSettings({ ...localSettings, image_model: e.target.value })}
                className="w-full bg-[#07090e] border border-[#1f2736] text-slate-200 text-xs rounded-xl px-3 py-2 outline-none focus:border-cyan-400 cursor-pointer"
              >
                <option value="krea/krea-2-medium-turbo">Krea Turbo ($0.015 / frame)</option>
                <option value="black-forest-labs/flux-1-schnell">Flux Schnell ($0.003 / frame)</option>
                <option value="google/gemini-3.1-flash-banana">Nano Banana 2 ($0.002 / frame)</option>
              </select>
            </div>

            {/* Video Model */}
            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Video Motion Model</label>
              <select
                value={localSettings.video_provider}
                onChange={(e) => setLocalSettings({ ...localSettings, video_provider: e.target.value })}
                className="w-full bg-[#07090e] border border-[#1f2736] text-slate-200 text-xs rounded-xl px-3 py-2 outline-none focus:border-cyan-400 cursor-pointer"
              >
                <option value="bytedance/seedance-2.0-mini">ByteDance Seedance 2.0 Mini ($0.84 / Short)</option>
                <option value="runpod-minimax-h3">RunPod MiniMax H3 ($0.04 / Short)</option>
                <option value="minimax/video-01">OpenRouter Hailuo-3 ($3.25 / Short)</option>
              </select>
            </div>
            {/* TTS Voice */}
            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                <span>TTS Voice (OpenRouter & Neural)</span>
                <span className="text-[9px] text-cyan-400/80 font-normal">Pure Cloud Audio</span>
              </label>
              <select
                value={localSettings.tts_voice || 'Charon'}
                onChange={(e) => {
                  const voice = e.target.value;
                  let model = 'google/gemini-3.8-flash-lite-tts';
                  if (voice.startsWith('flux-')) model = 'deepgram/flux-tts';
                  else if (voice.startsWith('en-US-')) model = 'edge-tts';
                  setLocalSettings({ ...localSettings, tts_voice: voice, tts_model: model });
                }}
                className="w-full bg-[#07090e] border border-[#1f2736] text-slate-200 text-xs rounded-xl px-3 py-2 outline-none focus:border-cyan-400 cursor-pointer"
              >
                <optgroup label="Google Gemini Flash Studio (OpenRouter)">
                  <option value="Charon">Charon (Deep Documentary • Authoritative)</option>
                  <option value="Puck">Puck (Fast Storyteller • Viral Pacing)</option>
                  <option value="Fenrir">Fenrir (Intense Cinematic • Dramatic)</option>
                  <option value="Aoede">Aoede (Smooth Documentary • Narrative)</option>
                  <option value="Kore">Kore (Calm Educational • Scientific)</option>
                </optgroup>
                <optgroup label="Deepgram Flux (OpenRouter Free)">
                  <option value="flux-cliff-en">Flux Cliff (Gritty Baritone Narrator)</option>
                  <option value="flux-perseus-en">Flux Perseus (Dynamic Explainer)</option>
                </optgroup>
                <optgroup label="Microsoft Edge Neural (Free High-Fidelity)">
                  <option value="en-US-ChristopherNeural">Christopher (Natural Documentary)</option>
                  <option value="en-US-GuyNeural">Guy (Casual YouTube Creator)</option>
                  <option value="en-US-JennyNeural">Jenny (Expressive Narrative Female)</option>
                  <option value="en-US-AriaNeural">Aria (High-Paced Informative Female)</option>
                </optgroup>
              </select>
            </div>

            {/* Art Style */}
            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                <span>Default Art Style</span>
                <span className="text-[9px] text-cyan-400/80 font-normal">Clio Cohesive Bible</span>
              </label>
              <select
                value={localSettings.art_style || 'photo_35mm'}
                onChange={(e) => setLocalSettings({ ...localSettings, art_style: e.target.value })}
                className="w-full bg-[#07090e] border border-[#1f2736] text-slate-200 text-xs rounded-xl px-3 py-2 outline-none focus:border-cyan-400 cursor-pointer"
              >
                <optgroup label="Cinematic & Photography">
                  <option value="photo_35mm">📸 35mm Photography (Kodak Realism)</option>
                  <option value="photo_surveillance">📸 Surveillance Camera (CCTV Mystery)</option>
                  <option value="photo_wes_anderson">📸 Wes Anderson (Pastel Symmetry)</option>
                </optgroup>
                <optgroup label="3D Render & Animation">
                  <option value="render_unreal">🧊 Unreal Engine 5 (Raytraced Lumen)</option>
                  <option value="render_spiderverse">🧊 Spider-Verse (Halftone Kinetic)</option>
                  <option value="render_coraline">🧊 Coraline Stop-Motion (Tactile Macro)</option>
                  <option value="design_lego_hybrid">🧱 LEGO Minifigure & Set Style</option>
                  <option value="design_minecraft">⛏️ Minecraft Voxel Cinematic</option>
                </optgroup>
                <optgroup label="Graphic & Comic Art">
                  <option value="design_butcher_billy">🎨 Butcher Billy (Punk Pop Graphic)</option>
                  <option value="comic_franco_belgian">📖 Franco-Belgian Comic (Moebius Line)</option>
                  <option value="comic_hellboy">📖 Hellboy Style (Mignola Noir)</option>
                  <option value="comic_vintage">📖 Vintage 1970s Comic</option>
                  <option value="digital_xray">🩻 X-Ray Forensic Glow</option>
                  <option value="cover_gta_v">🎮 GTA V Polished Cover Art</option>
                  <option value="paint_tenebrism">🖌️ Tenebrism (Dramatic Chiaroscuro)</option>
                  <option value="toon_rick_and_morty">🛸 Rick and Morty Sci-Fi Cartoon</option>
                </optgroup>
              </select>
            </div>
          </div>

          {/* Cost preview & Save button */}
          <div className="border-t border-[#1f2736] pt-3 flex items-center justify-between">
            <div>
              <div className="text-[10px] text-slate-400 font-mono">Estimated Cost</div>
              <div className="text-sm font-bold text-cyan-400 font-mono">${totalCost.toFixed(3)} / Short</div>
            </div>
            <button
              onClick={handleSave}
              className="bg-cyan-400 hover:bg-cyan-300 text-black font-bold text-xs px-4 py-2 rounded-xl transition shadow active:scale-95 flex items-center gap-1.5 cursor-pointer"
            >
              {isSaved ? <Check className="w-3.5 h-3.5" /> : null}
              <span>{isSaved ? 'Saved!' : 'Save Settings'}</span>
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
