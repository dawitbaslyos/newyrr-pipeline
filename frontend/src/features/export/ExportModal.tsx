import React, { useState } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { X, Zap, Download } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const ExportModal: React.FC = () => {
  const { 
    isExportModalOpen, 
    setModal, 
    activeProject,
    captionColor,
    captionFont,
    captionFontSize,
    captionStroke,
    captionUppercase,
    captionPacing,
    captionY
  } = useStudioStore();
  const [percent, setPercent] = useState(0);
  const [statusText, setStatusText] = useState('Ready to assemble');
  const [isProcessing, setIsProcessing] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [resolution, setResolution] = useState('1080');

  if (!isExportModalOpen || !activeProject) return null;

  const handleProcess = async () => {
    setIsProcessing(true);
    setPercent(15);
    setStatusText('1/3 Compiling scene stills...');

    try {
      setTimeout(() => {
        setPercent(55);
        setStatusText('2/3 Mixing high-bitrate audio & sound cues...');
      }, 1200);

      setTimeout(() => {
        setPercent(85);
        setStatusText('3/3 Rendering CapCut subtitles & final MP4...');
      }, 2500);

      const res = await fetch('/api/project/assemble', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: activeProject.project_name,
          caption_y_percent: activeProject.caption_y_percent || captionY || 72,
          caption_color: captionColor || 'yellow',
          font_family: captionFont || 'Impact',
          font_size: Math.round((captionFontSize || 24) * 2.1),
          outline_thickness: captionStroke || 4.5,
          all_caps: captionUppercase ?? true,
          chunk_size: captionPacing === 'single' ? 2 : captionPacing === 'phrase' ? 5 : 3,
          archive: true
        })
      });

      if (res.ok) {
        const data = await res.json();
        setPercent(100);
        setStatusText('Short Ready! ⚡');
        setDownloadUrl(data.final_video_url);
      } else {
        throw new Error('Assembly failed');
      }
    } catch (e: any) {
      alert('Export failed: ' + e.message);
      setPercent(0);
      setStatusText('Assembly failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const thumb = activeProject.thumbnail_url || (activeProject.scenes && activeProject.scenes[0]?.image_url);

  return (
    <AnimatePresence>
      <div className="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-[#0c0f18] border border-slate-700/80 rounded-2xl w-full max-w-md p-5 flex flex-col gap-4 shadow-2xl overflow-hidden font-sans"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#1f2736] pb-3">
            <h3 className="font-bold text-xs text-slate-100 uppercase tracking-wider">
              Export YouTube Short
            </h3>
            <button
              onClick={() => setModal('export', false)}
              className="w-7 h-7 rounded-lg hover:bg-[#161b26] text-slate-400 hover:text-white flex items-center justify-center text-xs transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Center Card with CapCut Perimeter Progress Border */}
          <div className="flex flex-col items-center justify-center py-2">
            <div className="relative w-28 aspect-[9/16] bg-black rounded-xl overflow-hidden shadow-2xl flex items-center justify-center">
              {thumb ? (
                <img src={thumb} alt="" className="w-full h-full object-cover" />
              ) : (
                <div className="text-[10px] text-slate-600">Draft</div>
              )}

              {/* CapCut SVG Perimeter Progress Border */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 112 198">
                <rect
                  x="2"
                  y="2"
                  width="108"
                  height="194"
                  rx="12"
                  fill="none"
                  stroke="#00f2fe"
                  strokeWidth="3.5"
                  pathLength="100"
                  strokeDasharray="100"
                  strokeDashoffset={100 - percent}
                  className="transition-all duration-300 ease-out"
                />
              </svg>

              {/* In-Center Spinner during processing */}
              {isProcessing && (
                <div className="absolute inset-0 bg-black/75 flex flex-col items-center justify-center gap-1.5 p-2 text-center">
                  <div className="w-6 h-6 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
                  <span className="font-mono font-black text-xs text-cyan-300">{percent}%</span>
                </div>
              )}
            </div>

            <span className="font-semibold text-xs text-slate-200 mt-3 text-center">{statusText}</span>
          </div>

          {/* Resolution Preset Dropdown */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Resolution Preset
            </label>
            <select
              value={resolution}
              onChange={(e) => setResolution(e.target.value)}
              className="w-full bg-[#07090e] border border-[#1f2736] text-slate-200 text-xs rounded-xl p-2.5 outline-none focus:border-cyan-400 cursor-pointer"
            >
              <option value="1080">1080p 60fps (Recommended)</option>
              <option value="4k">4K Ultra HD (2160p)</option>
              <option value="720">720p Fast Render</option>
            </select>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between gap-3 border-t border-[#1f2736] pt-3 mt-1">
            <button
              onClick={() => setModal('export', false)}
              className="text-xs font-semibold text-slate-400 hover:text-white px-3 py-2 cursor-pointer"
            >
              Cancel
            </button>
            <div className="flex items-center gap-2">
              <button
                onClick={handleProcess}
                disabled={isProcessing}
                className="bg-cyan-400 hover:bg-cyan-300 text-black font-bold text-xs px-5 py-2.5 rounded-xl shadow-lg transition active:scale-95 flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <Zap className="w-3.5 h-3.5 fill-current" />
                <span>Process</span>
              </button>
              {downloadUrl && (
                <a
                  href={downloadUrl}
                  download={`${activeProject.project_name}_final.mp4`}
                  className="bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-xs px-5 py-2.5 rounded-xl shadow-lg transition active:scale-95 flex items-center justify-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download</span>
                </a>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
