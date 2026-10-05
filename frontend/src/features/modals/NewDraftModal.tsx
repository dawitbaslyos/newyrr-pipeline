import React, { useState, useEffect } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { X, Sparkles, Link2, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const NewDraftModal: React.FC = () => {
  const { isNewDraftModalOpen, setModal, openEditor, fetchProjects, settings, studioMode } = useStudioStore();
  const [topic, setTopic] = useState('');
  const [aspect, setAspect] = useState<'9:16' | '16:9'>('9:16');
  const [artStyle, setArtStyle] = useState(settings.art_style || 'photo_35mm');
  const [voice, setVoice] = useState(settings.tts_voice || 'Charon');
  const [referenceUrl, setReferenceUrl] = useState('');
  const [isWriting, setIsWriting] = useState(false);

  useEffect(() => {
    if (isNewDraftModalOpen) {
      setArtStyle(settings.art_style || 'photo_35mm');
      setVoice(settings.tts_voice || 'Charon');
      const prefilled = window.sessionStorage.getItem('prefilledTopic');
      const prefAspect = window.sessionStorage.getItem('newDraftAspect') as '9:16' | '16:9';
      const prefRef = window.sessionStorage.getItem('prefilledReferenceUrl');
      if (prefilled) {
        setTopic(prefilled);
        window.sessionStorage.removeItem('prefilledTopic');
      }
      if (prefAspect) {
        setAspect(prefAspect);
        window.sessionStorage.removeItem('newDraftAspect');
      }
      if (prefRef) {
        setReferenceUrl(prefRef);
        window.sessionStorage.removeItem('prefilledReferenceUrl');
      }
    }
  }, [isNewDraftModalOpen, settings]);

  if (!isNewDraftModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setIsWriting(true);
    try {
      const res = await fetch('/api/project/create-draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          topic: topic.trim(), 
          aspect_ratio: aspect,
          art_style: artStyle,
          tts_voice: voice,
          reference_url: referenceUrl.trim() || undefined,
          project_type: studioMode
        })
      });
      if (res.ok) {
        const data = await res.json();
        setModal('newDraft', false);
        setTopic('');
        setReferenceUrl('');
        fetchProjects();
        useStudioStore.setState({ activeProject: data, activeSceneIdx: 0, isEditorOpen: true });
        openEditor(data.project_name);
      } else {
        const err = await res.json().catch(() => ({ detail: 'Failed to create draft' }));
        throw new Error(err.detail || 'Failed to create draft');
      }
    } catch (e: any) {
      alert('Draft creation failed: ' + e.message);
    } finally {
      setIsWriting(false);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-[#0c0f18] border border-slate-700/80 rounded-2xl w-full max-w-md p-5 flex flex-col gap-4 shadow-2xl font-sans"
        >
          <div className="flex items-center justify-between border-b border-[#1f2736] pb-2.5">
            <h3 className="font-bold text-xs text-slate-100 uppercase tracking-wider">
              Create New Short Draft
            </h3>
            <button
              onClick={() => setModal('newDraft', false)}
              className="w-7 h-7 rounded-lg hover:bg-[#161b26] text-slate-400 hover:text-white flex items-center justify-center text-xs transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            {studioMode === 'repurpose' && (
              <div className="bg-indigo-950/40 border border-indigo-500/30 rounded-xl p-2.5 flex items-center gap-2 text-[11px] text-indigo-200">
                <RefreshCw className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                <span>
                  <strong>Repurpose Workflow Active:</strong> Uses video slicing & keyframe extraction under the hood (Zero OpenRouter AI image/video credits).
                </span>
              </div>
            )}

            <div>
              <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                Topic or Contradiction
              </label>
              <textarea
                rows={3}
                placeholder="e.g. Why glass is secretly a moving liquid..."
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="w-full bg-[#07090e] border border-[#1f2736] rounded-xl p-3 text-xs text-slate-100 outline-none focus:border-cyan-400 resize-none leading-relaxed"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Link2 className="w-3 h-3 text-cyan-400" />
                  <span>Cadence Reference Short</span>
                  <span className="text-[10px] text-slate-500 font-normal lowercase">(optional)</span>
                </label>
                {referenceUrl && (
                  <button
                    type="button"
                    onClick={() => setReferenceUrl('')}
                    className="text-[10px] text-slate-400 hover:text-rose-400 transition cursor-pointer"
                  >
                    Clear
                  </button>
                )}
              </div>
              <input
                type="text"
                placeholder="https://www.youtube.com/shorts/... (clones viral pacing & WPM)"
                value={referenceUrl}
                onChange={(e) => setReferenceUrl(e.target.value)}
                className="w-full bg-[#07090e] border border-[#1f2736] rounded-xl px-3 py-2 text-xs text-slate-100 placeholder:text-slate-600 outline-none focus:border-cyan-400"
              />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Aspect:</span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setAspect('9:16')}
                  className={`px-3 py-1 rounded-lg text-xs font-bold transition cursor-pointer ${
                    aspect === '9:16' ? 'bg-cyan-400 text-black' : 'bg-[#07090e] border border-[#1f2736] text-slate-300'
                  }`}
                >
                  9:16 (Vertical)
                </button>
                <button
                  type="button"
                  onClick={() => setAspect('16:9')}
                  className={`px-3 py-1 rounded-lg text-xs font-bold transition cursor-pointer ${
                    aspect === '16:9' ? 'bg-cyan-400 text-black' : 'bg-[#07090e] border border-[#1f2736] text-slate-300'
                  }`}
                >
                  16:9 (Landscape)
                </button>
              </div>
            </div>

            {/* Visual Style Selection */}
            <div className="flex flex-col gap-1">
              <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Art Direction Style
              </label>
              <select
                value={artStyle}
                onChange={(e) => setArtStyle(e.target.value)}
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
                  <option value="toon_doodle_minimal">✏️ Minimalist Doodle (Practical Psychology)</option>
                </optgroup>
              </select>
            </div>

            {/* TTS Voice Selection */}
            <div className="flex flex-col gap-1">
              <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Narration Voice
              </label>
              <select
                value={voice}
                onChange={(e) => setVoice(e.target.value)}
                className="w-full bg-[#07090e] border border-[#1f2736] text-slate-200 text-xs rounded-xl px-3 py-2 outline-none focus:border-cyan-400 cursor-pointer"
              >
                <optgroup label="Google Gemini Flash (OpenRouter)">
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

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#1f2736]">
              <button
                type="button"
                onClick={() => setModal('newDraft', false)}
                className="px-3.5 py-1.5 text-xs font-semibold text-slate-400 hover:text-white cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isWriting}
                className="bg-cyan-400 hover:bg-cyan-300 text-black font-bold text-xs px-4 py-2 rounded-xl transition shadow active:scale-95 flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>{isWriting ? 'Writing Screenplay...' : 'Create Draft'}</span>
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
