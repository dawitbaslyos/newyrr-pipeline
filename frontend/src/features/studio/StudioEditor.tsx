import React, { useState, useRef, useEffect } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { CircularProgress } from '../../components/ui/circular-progress';
import { RainbowBorder } from '../../components/ui/rainbow-border';
import { 
  ArrowLeft, 
  Settings, 
  Play, 
  Pause, 
  Square, 
  Sparkles, 
  Film, 
  Share2, 
  Save, 
  X, 
  ChevronRight,
  Mic,
  Image as ImageIcon,
  Video as VideoIcon,
  RefreshCw,
  Sliders,
  Type,
  CheckCircle2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const StudioEditor: React.FC = () => {
  const {
    activeProject,
    activeSceneIdx,
    setActiveSceneIdx,
    isInspectorFolded,
    setInspectorFolded,
    captionColor,
    captionFont,
    captionFontSize,
    captionStroke,
    captionUppercase,
    captionPacing,
    captionY,
    setCaptionSettings,
    closeEditor,
    updateActiveScene,
    setModal,
    isPlaying,
    setIsPlaying,
    fetchProjects
  } = useStudioStore();

  const [isShimmering, setIsShimmering] = useState(false);
  const [shimmerText, setShimmerText] = useState('Rendering Keyframe...');
  const [isRenderingSceneStill, setIsRenderingSceneStill] = useState(false);
  const [isRenderingSceneVideo, setIsRenderingSceneVideo] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [activeSubTab, setActiveSubTab] = useState<'prompts' | 'styling'>('prompts');

  // Viewport display layer & overlay controls
  const [viewLayer, setViewLayer] = useState<'video' | 'image'>('video');
  const [showCaptions, setShowCaptions] = useState(true);
  const [generationProgress, setGenerationProgress] = useState<number>(-1);

  const dragRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  if (!activeProject) return null;

  const scenes = activeProject.scenes || [];
  const currentScene = scenes[activeSceneIdx] || scenes[0];

  const updateCaptionY = (val: number) => {
    setCaptionSettings({ captionY: val });
    if (activeProject) {
      useStudioStore.setState({
        activeProject: { ...activeProject, caption_y_percent: val }
      });
    }
  };

  // Draggable Subtitles
  const handleDrag = () => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const handleMouseMove = (moveEvent: MouseEvent) => {
      const y = moveEvent.clientY - rect.top;
      const percent = Math.min(88, Math.max(15, (y / rect.height) * 100));
      updateCaptionY(Math.round(percent));
    };

    const handleMouseUp = () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  const getCaptionPreviewText = () => {
    if (!currentScene?.narration) return 'CAPTION PREVIEW';
    const words = currentScene.narration.split(' ');
    const count = captionPacing === 'single' ? 2 : captionPacing === 'phrase' ? 6 : 4;
    const chunk = words.slice(0, count).join(' ');
    return captionUppercase ? chunk.toUpperCase() : chunk;
  };

  // Playback Loop
  useEffect(() => {
    let timer: any = null;
    if (isPlaying) {
      if (currentScene?.audio_url) {
        if (!audioRef.current) {
          audioRef.current = new Audio(currentScene.audio_url);
        } else {
          audioRef.current.src = currentScene.audio_url;
        }
        audioRef.current.play().catch(() => {});
        audioRef.current.onended = () => {
          if (activeSceneIdx < scenes.length - 1) {
            setActiveSceneIdx(activeSceneIdx + 1);
          } else {
            setIsPlaying(false);
            setActiveSceneIdx(0);
          }
        };
      } else {
        // Fallback timer when audio isn't rendered yet
        timer = setTimeout(() => {
          if (activeSceneIdx < scenes.length - 1) {
            setActiveSceneIdx(activeSceneIdx + 1);
          } else {
            setIsPlaying(false);
            setActiveSceneIdx(0);
          }
        }, 4000);
      }
    } else {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      if (timer) clearTimeout(timer);
    }

    return () => {
      if (timer) clearTimeout(timer);
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, [isPlaying, activeSceneIdx, currentScene?.audio_url, scenes.length]);

  // Progressive Batch Execution: All Frames First (Scene-by-scene stream)
  const handleRunAllFrames = async () => {
    setIsShimmering(true);
    setGenerationProgress(5);
    const total = scenes.length || 5;
    setShimmerText(`Rendering Keyframe 1 of ${total}...`);
    try {
      for (let i = 1; i <= total; i++) {
        setShimmerText(`Rendering Keyframe & Audio (${i} of ${total})...`);
        const res = await fetch('/api/project/generate-scene-frame', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            project_name: activeProject.project_name,
            scene_number: i
          })
        });
        if (res.ok) {
          const updated = await res.json();
          useStudioStore.setState({ activeProject: updated });
        } else {
          const errData = await res.json().catch(() => ({ detail: `Failed generating frame for Scene ${i}` }));
          throw new Error(errData.detail || `Failed generating frame for Scene ${i}`);
        }
        setGenerationProgress(Math.round((i / total) * 100));
      }
      fetchProjects();
    } catch (e) {
      alert('Failed generating frames: ' + e);
    } finally {
      setIsShimmering(false);
      setGenerationProgress(-1);
    }
  };

  // Progressive Batch Execution: Animate All Videos (Scene-by-scene stream)
  const handleRunAllVideos = async () => {
    setIsShimmering(true);
    setGenerationProgress(5);
    const total = scenes.length || 5;
    setShimmerText(`Animating Video 1 of ${total}...`);
    try {
      for (let i = 1; i <= total; i++) {
        setShimmerText(`Animating Scene Video (${i} of ${total})...`);
        const res = await fetch('/api/project/render-scene-video', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            project_name: activeProject.project_name,
            scene_number: i
          })
        });
        if (res.ok) {
          const updated = await res.json();
          useStudioStore.setState({ activeProject: updated });
        }
        setGenerationProgress(Math.round((i / total) * 100));
      }
      fetchProjects();
    } catch (e) {
      alert('Failed animating videos: ' + e);
    } finally {
      setIsShimmering(false);
      setGenerationProgress(-1);
    }
  };

  // Scene-Per-Scene: Regenerate / Render Single Still
  const handleRerollSceneStill = async () => {
    if (!currentScene) return;
    setIsRenderingSceneStill(true);
    try {
      const res = await fetch('/api/project/reroll-frame', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: activeProject.project_name,
          scene_number: currentScene.scene_number,
          custom_prompt: currentScene.flux_image_prompt
        })
      });
      if (res.ok) {
        const updated = await res.json();
        useStudioStore.setState({ activeProject: updated });
        fetchProjects();
      } else {
        const errData = await res.json().catch(() => ({ detail: 'Failed regenerating frame' }));
        alert(errData.detail || 'Failed regenerating frame');
      }
    } catch (e) {
      alert('Failed regenerating frame: ' + e);
    } finally {
      setIsRenderingSceneStill(false);
    }
  };

  // Scene-Per-Scene: Regenerate / Render Single Video
  const handleRerollSceneVideo = async () => {
    if (!currentScene) return;
    setIsRenderingSceneVideo(true);
    try {
      const res = await fetch('/api/project/reroll-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: activeProject.project_name,
          scene_number: currentScene.scene_number,
          custom_motion_prompt: currentScene.minimax_motion_prompt
        })
      });
      if (res.ok) {
        const updated = await res.json();
        useStudioStore.setState({ activeProject: updated });
        fetchProjects();
      }
    } catch (e) {
      alert('Failed regenerating video: ' + e);
    } finally {
      setIsRenderingSceneVideo(false);
    }
  };

  // Save Scene Edits
  const handleSaveScene = async () => {
    if (!currentScene) return;
    try {
      await fetch('/api/project/save-scene', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: activeProject.project_name,
          scene_number: currentScene.scene_number,
          narration: currentScene.narration,
          flux_prompt: currentScene.flux_image_prompt,
          motion_prompt: currentScene.minimax_motion_prompt
        })
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (e) {
      alert('Failed saving scene: ' + e);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-[#07090e] flex flex-col font-sans select-none overflow-hidden h-screen w-screen">
      {/* 1. Studio Top Bar (Clean & Screen Adaptive) */}
      <header className="h-13 sm:h-14 border-b border-[#1f2736] bg-[#0c0f18] px-3 sm:px-5 flex items-center justify-between shrink-0 z-30">
        <div className="flex items-center gap-2 sm:gap-3 overflow-hidden">
          <button
            onClick={closeEditor}
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 hover:text-white bg-[#07090e] hover:bg-[#161b26] border border-[#1f2736] px-2.5 sm:px-3 py-1.5 rounded-xl transition cursor-pointer shrink-0"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Projects</span>
          </button>
          
          <div className="flex flex-col overflow-hidden">
            <span className="text-xs sm:text-sm font-bold truncate text-slate-100 max-w-[200px] sm:max-w-xs md:max-w-md">
              {activeProject.title || activeProject.project_name}
            </span>
            {activeProject.hook && (
              <span className="text-[10px] text-slate-400 truncate hidden md:inline">
                {activeProject.hook}
              </span>
            )}
          </div>
        </div>

        {/* Right Action Icons */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => setModal('export', true)}
            className="bg-cyan-400 hover:bg-cyan-300 active:scale-95 text-black text-xs font-bold px-3.5 py-1.5 rounded-xl transition shadow-md flex items-center gap-1 cursor-pointer"
          >
            <Share2 className="w-3.5 h-3.5" />
            <span>Export →</span>
          </button>
          <button
            onClick={() => setModal('settings', true)}
            title="Engine Settings"
            className="w-8 h-8 rounded-xl bg-[#07090e] hover:bg-[#161b26] border border-[#1f2736] hover:border-cyan-400 text-slate-300 hover:text-cyan-400 flex items-center justify-center transition cursor-pointer"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* 2. Studio Body (Canvas Left + Properties Right) */}
      <div className="flex-1 flex overflow-hidden relative min-h-0 w-full">
        {/* Canvas & Playback Area */}
        <div className="flex-1 flex flex-col items-center justify-between p-2 sm:p-3 pb-3 bg-[#07090e]/70 overflow-hidden relative min-h-0">
          
          {/* Floating Drawer Trigger Button (When properties drawer is folded) */}
          {isInspectorFolded && (
            <button
              onClick={() => setInspectorFolded(false)}
              className="absolute top-3 right-3 z-30 flex items-center gap-1.5 bg-[#0c0f18]/95 hover:bg-[#161b26] border border-cyan-400/40 text-cyan-300 text-xs font-semibold px-3 py-1.5 rounded-full shadow-2xl transition cursor-pointer"
            >
              <span>⚙ Scene Properties</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          )}

          {/* 9:16 Canvas Viewport (Screen-Adaptive auto-fit) */}
          <div className="flex-1 w-full flex items-center justify-center min-h-0 relative py-1 sm:py-2">
            <div className="relative flex items-center gap-3 h-full max-h-full min-h-0">
              
              {/* 9:16 Phone Frame */}
              <div
                ref={containerRef}
                className="relative h-full max-h-[calc(100vh-230px)] aspect-[9/16] w-auto bg-black rounded-2xl overflow-hidden border border-[#1f2736] shadow-2xl flex items-center justify-center select-none"
              >
                {/* Google Rainbow Edge Border (Fills perimeter clockwise from top-left) */}
                <RainbowBorder 
                  isLoading={isShimmering || isRenderingSceneStill || isRenderingSceneVideo} 
                  progress={generationProgress}
                  borderRadius={16} 
                  strokeWidth={3.5} 
                />

                {/* Media Image / Video Layer */}
                {viewLayer === 'video' && currentScene.video_url ? (
                  <video 
                    key={currentScene.video_url}
                    src={currentScene.video_url} 
                    className="w-full h-full object-cover" 
                    loop 
                    autoPlay 
                    muted 
                    playsInline 
                  />
                ) : currentScene.image_url ? (
                  <div className="w-full h-full relative">
                    <img src={currentScene.image_url} alt="Scene Still" className="w-full h-full object-cover" />
                    {viewLayer === 'video' && !currentScene.video_url && (
                      <div className="absolute top-3 left-3 bg-black/75 backdrop-blur-sm border border-slate-700/70 px-2.5 py-1 rounded-md text-[9px] font-semibold text-slate-300 flex items-center gap-1.5 shadow-lg">
                        <VideoIcon className="w-3 h-3 text-indigo-400" />
                        <span>Keyframe preview (Video not yet generated)</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center p-6 text-slate-500 text-xs flex flex-col items-center gap-2">
                    <Sparkles className="w-8 h-8 opacity-40 text-cyan-400" />
                    <span>Keyframe not rendered yet</span>
                    <span className="text-[10px] text-slate-600">Use "Render Still" in the right panel</span>
                  </div>
                )}

                {/* In-Canvas Shimmer Loader */}
                {isShimmering && (
                  <div className="absolute inset-0 bg-black/80 backdrop-blur-[2px] flex flex-col items-center justify-center p-6 text-center z-20">
                    <div className="bg-[#0c0f18]/90 border border-slate-700/80 px-4 py-2 rounded-full shadow-2xl flex items-center gap-2.5 mb-2">
                      <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                      <span className="text-xs font-bold text-slate-100 uppercase tracking-wider">{shimmerText}</span>
                    </div>
                    {generationProgress >= 0 && (
                      <div className="w-48 bg-slate-800 rounded-full h-1.5 overflow-hidden border border-slate-700 mt-1">
                        <div 
                          className="bg-gradient-to-r from-blue-500 via-rose-500 to-green-500 h-full transition-all duration-300 rounded-full"
                          style={{ width: `${generationProgress}%` }}
                        />
                      </div>
                    )}
                    <span className="text-[10px] text-slate-400 mt-1">
                      {generationProgress >= 0 ? `${generationProgress}% Complete` : 'Cloud Execution'}
                    </span>
                  </div>
                )}

                {/* Draggable CapCut-Style Subtitle Box */}
                {showCaptions && (
                  <div
                    ref={dragRef}
                    onMouseDown={handleDrag}
                    style={{ top: `${captionY}%` }}
                    className="absolute left-[6%] w-[88%] text-center p-2 rounded-xl transition-all cursor-ns-resize group z-20"
                  >
                    <div className="opacity-0 group-hover:opacity-100 transition text-[9px] font-mono text-cyan-400 mb-0.5 tracking-wider uppercase select-none">
                      ↕ Drag position ({captionY}%)
                    </div>
                    <div 
                      style={{
                        fontFamily: captionFont === 'Impact' ? 'Impact, -apple-system, sans-serif' : captionFont === 'Montserrat' ? 'Montserrat, sans-serif' : captionFont === 'Anton' ? 'Anton, sans-serif' : 'Arial Black, sans-serif',
                        fontSize: `${captionFontSize}px`,
                        textTransform: captionUppercase ? 'uppercase' : 'none',
                        textShadow: captionStroke === 2 
                          ? '1.5px 1.5px 0 #000, -1.5px -1.5px 0 #000, 1.5px -1.5px 0 #000, -1.5px 1.5px 0 #000'
                          : captionStroke === 6
                          ? '3.5px 3.5px 0 #000, -3.5px -3.5px 0 #000, 3.5px -3.5px 0 #000, -3.5px 3.5px 0 #000, 0 4px 10px rgba(0,0,0,0.9)'
                          : '2.5px 2.5px 0 #000, -2.5px -2.5px 0 #000, 2.5px 2.5px 0 #000, -2.5px 2.5px 0 #000, 0 3px 8px rgba(0,0,0,0.85)'
                      }}
                      className={`font-black leading-tight tracking-wide drop-shadow-md select-none transition-all ${
                        captionColor === 'yellow' ? 'text-yellow-400' :
                        captionColor === 'cyan' ? 'text-cyan-400' :
                        captionColor === 'emerald' ? 'text-emerald-400' :
                        captionColor === 'red' ? 'text-rose-400' : 'text-white'
                      }`}
                    >
                      {getCaptionPreviewText()}
                    </div>
                  </div>
                )}
              </div>

              {/* Fast Viewport Layer Toggles beside phone */}
              <div className="hidden sm:flex flex-col gap-1.5 bg-[#0c0f18]/90 backdrop-blur-md border border-[#1f2736] p-1 rounded-2xl shadow-xl z-20">
                <button
                  onClick={() => setViewLayer('image')}
                  title="View Keyframe Still"
                  className={`w-8 h-8 rounded-xl border flex flex-col items-center justify-center transition active:scale-95 cursor-pointer text-[10px] font-black ${
                    viewLayer === 'image'
                      ? 'bg-cyan-950/80 border-cyan-400 text-cyan-300 shadow-[0_0_10px_rgba(0,242,254,0.3)]'
                      : 'bg-[#07090e] border-[#1f2736] text-slate-400 hover:text-cyan-400 hover:border-slate-500'
                  }`}
                >
                  IMG
                </button>
                <button
                  onClick={() => setViewLayer('video')}
                  title="View Animated Video"
                  className={`w-8 h-8 rounded-xl border flex flex-col items-center justify-center transition active:scale-95 cursor-pointer text-[10px] font-black ${
                    viewLayer === 'video'
                      ? 'bg-indigo-950/80 border-indigo-400 text-indigo-300 shadow-[0_0_10px_rgba(99,102,241,0.3)]'
                      : 'bg-[#07090e] border-[#1f2736] text-slate-400 hover:text-indigo-400 hover:border-slate-500'
                  }`}
                >
                  VID
                </button>
                <button
                  onClick={() => setShowCaptions(!showCaptions)}
                  title={showCaptions ? "Hide Subtitles on Viewport" : "Show Subtitles on Viewport"}
                  className={`w-8 h-8 rounded-xl border flex flex-col items-center justify-center transition active:scale-95 cursor-pointer text-[10px] font-black ${
                    showCaptions
                      ? 'bg-amber-950/70 border-amber-400 text-amber-300 shadow-[0_0_10px_rgba(251,191,36,0.25)]'
                      : 'bg-[#07090e] border-[#1f2736] text-slate-500 hover:text-slate-300 hover:border-slate-500'
                  }`}
                >
                  CC
                </button>
              </div>

            </div>
          </div>

          {/* 3. Playback Controls (NOW POSITIONED UNDER VIEWPORT AS REQUESTED) */}
          <div className="flex items-center gap-3 my-1 z-20 bg-[#0c0f18]/95 backdrop-blur-md border border-[#1f2736] px-4 py-1.5 rounded-full shadow-xl shrink-0">
            <button
              onClick={() => {
                setIsPlaying(false);
                setActiveSceneIdx(0);
              }}
              title="Stop and Reset"
              className="w-7 h-7 rounded-full bg-[#07090e] hover:bg-[#161b26] text-slate-400 hover:text-white flex items-center justify-center transition border border-[#1f2736] cursor-pointer"
            >
              <Square className="w-3 h-3 fill-current" />
            </button>

            {/* Play/Pause Button with Circular Progress Dial */}
            <CircularProgress
              size={34}
              strokeWidth={2.5}
              progress={((activeSceneIdx + 1) / scenes.length) * 100}
            >
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="w-7 h-7 rounded-full bg-cyan-400 hover:bg-cyan-300 text-black flex items-center justify-center transition active:scale-95 shadow cursor-pointer"
              >
                {isPlaying ? (
                  <Pause className="w-3.5 h-3.5 fill-current" />
                ) : (
                  <Play className="w-3.5 h-3.5 fill-current ml-0.5" />
                )}
              </button>
            </CircularProgress>

            <div className="text-[11px] font-mono text-slate-300 border-l border-[#1f2736] pl-2.5 flex items-center gap-2">
              <span className="font-bold text-cyan-400">Scene {activeSceneIdx + 1}/{scenes.length}</span>
              <span className="text-slate-500">•</span>
              <span className="text-slate-400">{currentScene?.actual_audio_duration ? `${currentScene.actual_audio_duration.toFixed(1)}s` : '~5.0s'}</span>
              <span className="text-slate-500">•</span>
              <span className="text-slate-400">Caption: <strong className="text-cyan-400">{captionY}%</strong></span>
            </div>
          </div>

          {/* 4. Horizontal Scene Filmstrip Reel (Compact & Adaptive) */}
          <div className="w-full max-w-xl overflow-x-auto touch-pan-x flex gap-2 pt-1 shrink-0 scrollbar-none">
            {scenes.map((s, idx) => {
              const isSelected = idx === activeSceneIdx;
              const isSceneBusy = (isRenderingSceneStill || isRenderingSceneVideo) && isSelected;
              return (
                <div
                  key={s.scene_number}
                  onClick={() => setActiveSceneIdx(idx)}
                  className={`shrink-0 w-16 sm:w-18 aspect-[9/16] bg-[#0c0f18] rounded-xl border ${
                    isSelected ? 'border-cyan-400 shadow-md shadow-cyan-950/60 ring-2 ring-cyan-400/30' : 'border-[#1f2736] hover:border-slate-500'
                  } overflow-hidden relative cursor-pointer group transition-all`}
                >
                  {/* Scene-level Google Rainbow Edge Border during single scene render */}
                  <RainbowBorder 
                    isLoading={isSceneBusy} 
                    borderRadius={12} 
                    strokeWidth={2.5} 
                  />

                  {s.image_url ? (
                    <img src={s.image_url} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-[9px] text-slate-500 font-semibold">
                      Draft
                    </div>
                  )}
                  <div className="absolute top-1 left-1 bg-black/80 px-1.5 py-0.2 rounded text-[8px] font-bold text-slate-200">
                    #{s.scene_number}
                  </div>
                  {s.video_url && (
                    <div className="absolute bottom-1 right-1 w-2 h-2 rounded-full bg-cyan-400 shadow-sm" title="Video Ready" />
                  )}
                </div>
              );
            })}
          </div>

        </div>

        {/* 5. Properties Inspector Drawer (With Unified Prompts & Actions) */}
        <AnimatePresence>
          {!isInspectorFolded && (
            <motion.aside
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 400, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.22, ease: 'easeOut' }}
              className="h-full border-l border-[#1f2736] bg-[#0c0f18] z-30 overflow-y-auto flex flex-col shadow-2xl shrink-0 w-80 sm:w-96 md:w-[400px]"
            >
              {/* Properties Top Header */}
              <div className="flex items-center justify-between p-3.5 border-b border-[#1f2736] shrink-0 bg-[#0c0f18] sticky top-0 z-20 backdrop-blur-md">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-black uppercase px-2 py-0.5 rounded bg-cyan-400/20 text-cyan-300 border border-cyan-400/30">
                    SCENE {currentScene.scene_number}
                  </span>
                  <span className="text-xs font-bold uppercase text-slate-200">Properties</span>
                </div>
                
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={handleSaveScene}
                    className={`text-xs px-2.5 py-1 rounded-lg font-semibold flex items-center gap-1 transition cursor-pointer ${
                      saveSuccess 
                        ? 'bg-emerald-500 text-black' 
                        : 'bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 border border-emerald-700/50'
                    }`}
                  >
                    {saveSuccess ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
                    <span>{saveSuccess ? 'Saved!' : 'Save'}</span>
                  </button>
                  <button
                    onClick={() => setInspectorFolded(true)}
                    className="w-7 h-7 rounded-lg bg-[#07090e] hover:bg-[#161b26] border border-[#1f2736] text-slate-400 hover:text-white flex items-center justify-center text-xs font-bold transition cursor-pointer"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Sub-Tabs: Prompts (Unified) vs Subtitle Style */}
              <div className="flex items-center gap-1 p-2 border-b border-[#1f2736] bg-[#07090e]/60 shrink-0">
                <button
                  onClick={() => setActiveSubTab('prompts')}
                  className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition cursor-pointer ${
                    activeSubTab === 'prompts'
                      ? 'bg-cyan-950/60 text-cyan-300 border border-cyan-400/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Scene Prompts (All-in-One)
                </button>
                <button
                  onClick={() => setActiveSubTab('styling')}
                  className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition cursor-pointer ${
                    activeSubTab === 'styling'
                      ? 'bg-cyan-950/60 text-cyan-300 border border-cyan-400/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Subtitles & Hook
                </button>
              </div>

              {/* Batch Actions Bar (Frames First & Animate All) inside Properties as requested */}
              <div className="p-3 bg-[#07090e]/80 border-b border-[#1f2736] flex flex-col gap-2 shrink-0">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  Batch Production (All Scenes)
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={handleRunAllFrames}
                    className="bg-[#0c0f18] hover:bg-[#161b26] border border-cyan-400/40 hover:border-cyan-400 text-cyan-300 text-[11px] font-semibold p-2 rounded-xl flex items-center justify-center gap-1.5 transition active:scale-95 cursor-pointer shadow-sm"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                    <span>{activeProject.project_type === 'repurpose' ? '1. Slice Keyframes' : '1. Frames First'}</span>
                  </button>
                  <button
                    onClick={handleRunAllVideos}
                    className="bg-[#0c0f18] hover:bg-[#161b26] border border-indigo-400/40 hover:border-indigo-400 text-indigo-300 text-[11px] font-semibold p-2 rounded-xl flex items-center justify-center gap-1.5 transition active:scale-95 cursor-pointer shadow-sm"
                  >
                    <Film className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{activeProject.project_type === 'repurpose' ? '2. Slice Video Clips' : '2. Animate All'}</span>
                  </button>
                </div>
              </div>

              {/* Content Section: Unified Prompts (Script + Still + Video together) */}
              <div className="flex-1 p-3.5 flex flex-col gap-4 overflow-y-auto">
                {activeSubTab === 'prompts' ? (
                  <>
                    {/* Prompt 1: Narration Script */}
                    <div className="bg-[#07090e] border border-[#1f2736] rounded-2xl p-3 flex flex-col gap-2">
                      <div className="flex items-center justify-between">
                        <label className="text-[11px] font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                          <Mic className="w-3.5 h-3.5 text-cyan-400" />
                          <span>1. Spoken Narration (Script)</span>
                        </label>
                        <span className="text-[10px] font-mono text-cyan-400">
                          {currentScene.narration ? `${currentScene.narration.split(' ').length} words` : '0 words'}
                        </span>
                      </div>
                      <textarea
                        rows={3}
                        value={currentScene.narration || ''}
                        onChange={(e) => updateActiveScene({ narration: e.target.value })}
                        placeholder="Words spoken by the narrator in this scene..."
                        className="w-full bg-[#0c0f18] border border-[#1f2736] rounded-xl p-2.5 text-xs text-slate-100 outline-none focus:border-cyan-400 resize-none leading-relaxed"
                      />
                      <div className="flex items-center justify-between text-[10px] text-slate-400 px-0.5">
                        <span>Pacing: ~2.4 words/sec</span>
                        <span className="text-slate-300 font-mono">
                          Duration: <strong className="text-cyan-400">{currentScene.actual_audio_duration ? `${currentScene.actual_audio_duration.toFixed(1)}s` : '~5.0s'}</strong>
                        </span>
                      </div>
                    </div>

                    {/* Prompt 2: Still Keyframe Prompt + Single Scene Regenerate */}
                    <div className="bg-[#07090e] border border-[#1f2736] rounded-2xl p-3 flex flex-col gap-2">
                      <div className="flex items-center justify-between">
                        <label className="text-[11px] font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                          <ImageIcon className="w-3.5 h-3.5 text-cyan-400" />
                          <span>{activeProject.project_type === 'repurpose' ? '2. Source Keyframe Still' : '2. Still Keyframe Prompt'}</span>
                        </label>
                        
                        {/* Scene-Per-Scene Still Render / Regenerate Button */}
                        <button
                          disabled={isRenderingSceneStill}
                          onClick={handleRerollSceneStill}
                          className="bg-cyan-950/70 hover:bg-cyan-900 border border-cyan-400/40 text-cyan-300 text-[10px] font-bold px-2.5 py-1 rounded-lg flex items-center gap-1.5 transition active:scale-95 cursor-pointer disabled:opacity-50"
                        >
                          {isRenderingSceneStill ? (
                            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                          ) : (
                            <RefreshCw className="w-3 h-3 text-cyan-400" />
                          )}
                          <span>{isRenderingSceneStill ? 'Rendering...' : (activeProject.project_type === 'repurpose' ? 'Slice Keyframe' : (currentScene.image_url ? 'Regenerate Still' : 'Render Still'))}</span>
                        </button>
                      </div>

                      <textarea
                        rows={3}
                        value={currentScene.flux_image_prompt || ''}
                        onChange={(e) => updateActiveScene({ flux_image_prompt: e.target.value })}
                        placeholder="Detailed cinematic prompt for the opening still image..."
                        className="w-full bg-[#0c0f18] border border-[#1f2736] rounded-xl p-2.5 text-xs text-slate-100 outline-none focus:border-cyan-400 resize-none leading-relaxed"
                      />

                      {currentScene.image_url && (
                        <div className="flex items-center gap-2 pt-1 border-t border-[#1f2736]/60">
                          <img src={currentScene.image_url} alt="" className="w-10 h-10 rounded-lg object-cover border border-[#1f2736]" />
                          <span className="text-[10px] text-emerald-400 flex items-center gap-1 font-semibold">
                            <CheckCircle2 className="w-3 h-3" /> Keyframe Ready
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Prompt 3: Video Motion Guidance + Single Scene Regenerate */}
                    <div className="bg-[#07090e] border border-[#1f2736] rounded-2xl p-3 flex flex-col gap-2">
                      <div className="flex items-center justify-between">
                        <label className="text-[11px] font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                          <VideoIcon className="w-3.5 h-3.5 text-indigo-400" />
                          <span>{activeProject.project_type === 'repurpose' ? '3. Source Video Clip' : '3. Motion Guidance (Video)'}</span>
                        </label>

                        {/* Scene-Per-Scene Video Render / Regenerate Button */}
                        <button
                          disabled={isRenderingSceneVideo}
                          onClick={handleRerollSceneVideo}
                          className="bg-indigo-950/70 hover:bg-indigo-900 border border-indigo-400/40 text-indigo-300 text-[10px] font-bold px-2.5 py-1 rounded-lg flex items-center gap-1.5 transition active:scale-95 cursor-pointer disabled:opacity-50"
                        >
                          {isRenderingSceneVideo ? (
                            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                          ) : (
                            <RefreshCw className="w-3 h-3 text-indigo-400" />
                          )}
                          <span>{isRenderingSceneVideo ? 'Animating...' : (activeProject.project_type === 'repurpose' ? 'Slice Video Clip' : (currentScene.video_url ? 'Regenerate Video' : 'Animate Scene'))}</span>
                        </button>
                      </div>

                      <textarea
                        rows={3}
                        value={currentScene.minimax_motion_prompt || ''}
                        onChange={(e) => updateActiveScene({ minimax_motion_prompt: e.target.value })}
                        placeholder="Camera directives (e.g. slow continuous macro push-in, subtle floating particles)..."
                        className="w-full bg-[#0c0f18] border border-[#1f2736] rounded-xl p-2.5 text-xs text-slate-100 outline-none focus:border-indigo-400 resize-none leading-relaxed"
                      />

                      {currentScene.video_url && (
                        <div className="flex items-center gap-2 pt-1 border-t border-[#1f2736]/60">
                          <span className="text-[10px] text-cyan-400 flex items-center gap-1 font-semibold">
                            <CheckCircle2 className="w-3 h-3" /> Video Clip Rendered
                          </span>
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  /* CapCut Subtitle & Hook Properties Panel */
                  <div className="flex flex-col gap-3.5">
                    {/* 1. CapCut Color Presets */}
                    <div className="bg-[#07090e] border border-[#1f2736] rounded-2xl p-3 flex flex-col gap-2">
                      <div className="flex items-center justify-between">
                        <label className="text-[11px] font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                          <Sliders className="w-3.5 h-3.5 text-cyan-400" />
                          <span>CapCut Color Preset</span>
                        </label>
                        <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold">{captionColor}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 mt-0.5">
                        {[
                          { id: 'yellow', label: 'Classic Yellow', color: 'bg-yellow-400', desc: 'CapCut Viral Default' },
                          { id: 'cyan', label: 'Cyber Cyan', color: 'bg-cyan-400', desc: 'Tech & Sci-Fi' },
                          { id: 'emerald', label: 'Neon Emerald', color: 'bg-emerald-400', desc: 'Finance & Growth' },
                          { id: 'white', label: 'Crisp White', color: 'bg-white', desc: 'Minimal & Clean' },
                          { id: 'red', label: 'Punch Red', color: 'bg-rose-500', desc: 'Drama & High Hook' },
                        ].map((item) => (
                          <button
                            key={item.id}
                            onClick={() => setCaptionSettings({ captionColor: item.id as any })}
                            className={`flex items-center gap-2 p-2 bg-[#0c0f18] hover:bg-[#161b26] border rounded-xl transition cursor-pointer text-left ${
                              captionColor === item.id ? 'border-cyan-400 bg-cyan-950/20 ring-1 ring-cyan-400/40' : 'border-[#1f2736]'
                            }`}
                          >
                            <div className={`w-3.5 h-3.5 rounded-full ${item.color} shadow-sm shrink-0`} />
                            <div className="overflow-hidden">
                              <div className="text-[11px] font-bold text-slate-200 truncate">{item.label}</div>
                              <div className="text-[9px] text-slate-500 truncate">{item.desc}</div>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* 2. Typography & Font Family */}
                    <div className="bg-[#07090e] border border-[#1f2736] rounded-2xl p-3 flex flex-col gap-2">
                      <label className="text-[11px] font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                        <Type className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Typography & Font Family</span>
                      </label>
                      <div className="grid grid-cols-2 gap-1.5">
                        {[
                          { id: 'Impact', label: 'Impact', desc: 'CapCut Signature' },
                          { id: 'Montserrat', label: 'Montserrat', desc: 'Geometric Bold' },
                          { id: 'Arial Black', label: 'Arial Black', desc: 'Chunky Arcade' },
                          { id: 'Anton', label: 'Anton', desc: 'Tall Condensed' },
                        ].map((font) => (
                          <button
                            key={font.id}
                            onClick={() => setCaptionSettings({ captionFont: font.id as any })}
                            className={`p-2 rounded-xl border text-left transition cursor-pointer ${
                              captionFont === font.id
                                ? 'border-cyan-400 bg-cyan-950/25 text-cyan-300'
                                : 'border-[#1f2736] hover:bg-[#161b26] text-slate-300'
                            }`}
                          >
                            <div className="text-xs font-bold leading-tight" style={{ fontFamily: font.id }}>{font.label}</div>
                            <div className="text-[9px] text-slate-500">{font.desc}</div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* 3. Font Size & Uppercase Switch */}
                    <div className="bg-[#07090e] border border-[#1f2736] rounded-2xl p-3 flex flex-col gap-2.5">
                      <div className="flex items-center justify-between">
                        <label className="text-[11px] font-bold text-slate-200 uppercase tracking-wider">
                          Font Scale & Case
                        </label>
                        <span className="font-mono text-cyan-400 text-xs font-bold">{captionFontSize}px</span>
                      </div>
                      <input
                        type="range"
                        min={18}
                        max={34}
                        value={captionFontSize}
                        onChange={(e) => setCaptionSettings({ captionFontSize: parseInt(e.target.value) })}
                        className="w-full accent-cyan-400 cursor-pointer"
                      />
                      <div className="flex items-center justify-between pt-1">
                        <span className="text-[10px] text-slate-400">Capitalization:</span>
                        <div className="flex items-center gap-1 bg-[#0c0f18] p-0.5 rounded-lg border border-[#1f2736]">
                          <button
                            onClick={() => setCaptionSettings({ captionUppercase: true })}
                            className={`px-2 py-0.5 rounded text-[10px] font-bold transition cursor-pointer ${
                              captionUppercase ? 'bg-cyan-400 text-black' : 'text-slate-400 hover:text-white'
                            }`}
                          >
                            ALL CAPS (Viral)
                          </button>
                          <button
                            onClick={() => setCaptionSettings({ captionUppercase: false })}
                            className={`px-2 py-0.5 rounded text-[10px] font-bold transition cursor-pointer ${
                              !captionUppercase ? 'bg-cyan-400 text-black' : 'text-slate-400 hover:text-white'
                            }`}
                          >
                            Natural
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* 4. Stroke / Outline & Word Pacing */}
                    <div className="bg-[#07090e] border border-[#1f2736] rounded-2xl p-3 flex flex-col gap-2.5">
                      <div className="flex items-center justify-between">
                        <label className="text-[11px] font-bold text-slate-200 uppercase tracking-wider">
                          Outline Stroke Thickness
                        </label>
                        <span className="font-mono text-cyan-400 text-xs font-bold">{captionStroke}px</span>
                      </div>
                      <div className="grid grid-cols-3 gap-1.5">
                        {[
                          { val: 2, label: 'Thin (2px)' },
                          { val: 4, label: 'Standard (4px)' },
                          { val: 6, label: 'Heavy (6px)' },
                        ].map((s) => (
                          <button
                            key={s.val}
                            onClick={() => setCaptionSettings({ captionStroke: s.val })}
                            className={`p-1.5 rounded-xl border text-center text-[10px] font-bold transition cursor-pointer ${
                              captionStroke === s.val
                                ? 'border-cyan-400 bg-cyan-950/30 text-cyan-300'
                                : 'border-[#1f2736] hover:bg-[#161b26] text-slate-400'
                            }`}
                          >
                            {s.label}
                          </button>
                        ))}
                      </div>

                      <div className="pt-2 border-t border-[#1f2736]/60 flex flex-col gap-1.5">
                        <div className="flex items-center justify-between text-[11px] font-bold text-slate-200 uppercase tracking-wider">
                          <span>Kinetic Word Pacing</span>
                          <span className="text-cyan-400 font-mono text-[10px]">{captionPacing}</span>
                        </div>
                        <div className="grid grid-cols-3 gap-1.5">
                          {[
                            { id: 'single', label: 'Single/2-Word', desc: 'Hyper' },
                            { id: 'burst', label: 'CapCut Burst', desc: '3-4 words' },
                            { id: 'phrase', label: 'Full Phrase', desc: '5-6 words' },
                          ].map((p) => (
                            <button
                              key={p.id}
                              onClick={() => setCaptionSettings({ captionPacing: p.id as any })}
                              className={`p-1.5 rounded-xl border text-center transition cursor-pointer ${
                                captionPacing === p.id
                                  ? 'border-cyan-400 bg-cyan-950/30 text-cyan-300'
                                  : 'border-[#1f2736] hover:bg-[#161b26] text-slate-400'
                              }`}
                            >
                              <div className="text-[10px] font-bold leading-tight">{p.label}</div>
                              <div className="text-[8px] text-slate-500">{p.desc}</div>
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* 5. Subtitle Vertical Safe-Zone (Y%) */}
                    <div className="bg-[#07090e] border border-[#1f2736] rounded-2xl p-3 flex flex-col gap-2">
                      <div className="flex items-center justify-between">
                        <label className="text-[11px] font-bold text-slate-200 uppercase tracking-wider">
                          Vertical Position (Safe Zone Y%)
                        </label>
                        <span className="font-mono text-cyan-400 text-xs font-bold">{captionY}%</span>
                      </div>
                      <input
                        type="range"
                        min={15}
                        max={88}
                        value={captionY}
                        onChange={(e) => updateCaptionY(parseInt(e.target.value))}
                        className="w-full accent-cyan-400 cursor-pointer"
                      />
                      <div className="grid grid-cols-3 gap-1.5 mt-0.5">
                        {[
                          { val: 28, label: 'Top Hook (28%)' },
                          { val: 50, label: 'Center (50%)' },
                          { val: 72, label: 'Bottom Safe (72%)' },
                        ].map((zone) => (
                          <button
                            key={zone.val}
                            onClick={() => updateCaptionY(zone.val)}
                            className={`p-1.5 rounded-lg border text-center text-[10px] font-bold transition cursor-pointer ${
                              captionY === zone.val
                                ? 'border-cyan-400 bg-cyan-950/30 text-cyan-300'
                                : 'border-[#1f2736] hover:bg-[#161b26] text-slate-400'
                            }`}
                          >
                            {zone.label}
                          </button>
                        ))}
                      </div>
                      <span className="text-[9px] text-slate-500 mt-0.5">
                        Bottom safe 72% prevents overlap with YouTube Shorts sound pills and title overlays.
                      </span>
                    </div>

                    {/* 6. Viral Hook Headline */}
                    <div className="bg-[#07090e] border border-[#1f2736] rounded-2xl p-3 flex flex-col gap-2">
                      <label className="text-[11px] font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                        <Type className="w-3.5 h-3.5 text-amber-400" />
                        <span>Opening Hook Title</span>
                      </label>
                      <input
                        type="text"
                        value={activeProject.hook || ''}
                        onChange={(e) => useStudioStore.setState({ activeProject: { ...activeProject, hook: e.target.value } })}
                        placeholder="e.g. Why Your Sneakers Smell Like Cheese..."
                        className="w-full bg-[#0c0f18] border border-[#1f2736] rounded-xl p-2.5 text-xs text-amber-300 font-bold outline-none focus:border-cyan-400"
                      />
                    </div>
                  </div>
                )}
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

      </div>
    </div>
  );
};

export default StudioEditor;
