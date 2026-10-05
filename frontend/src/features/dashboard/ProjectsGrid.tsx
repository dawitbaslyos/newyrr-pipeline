import React, { useState } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { KineticCard } from '../../components/ui/kinetic-card';
import { Trash2, MoreVertical, Play, Trash } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const ProjectsGrid: React.FC = () => {
  const { projects, trashProjects, openEditor, fetchProjects, setModal } = useStudioStore();
  const [activeMenuProject, setActiveMenuProject] = useState<string | null>(null);

  const handleMoveToTrash = async (projectName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setActiveMenuProject(null);
    try {
      await fetch('/api/projects/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_name: projectName })
      });
      fetchProjects();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* 1. Create New Blank Project Section */}
      <div>
        <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
          Create New Blank Project
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Blank 9:16 */}
          <KineticCard
            onClick={() => {
              window.sessionStorage.setItem('newDraftAspect', '9:16');
              setModal('newDraft', true);
            }}
            className="p-4 sm:p-5 flex items-center gap-3.5 group"
          >
            <div className="w-10 h-16 border-2 border-dashed border-slate-500 group-hover:border-cyan-400 rounded-lg flex items-center justify-center font-bold text-xs text-slate-400 group-hover:text-cyan-400 shrink-0">
              9:16
            </div>
            <div>
              <div className="font-bold text-sm text-slate-100 group-hover:text-cyan-400">
                Blank 9:16 Short
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">Vertical 9:16 (768×1344)</div>
            </div>
          </KineticCard>

          {/* Blank 16:9 */}
          <KineticCard
            onClick={() => {
              window.sessionStorage.setItem('newDraftAspect', '16:9');
              setModal('newDraft', true);
            }}
            className="p-4 sm:p-5 flex items-center gap-3.5 group opacity-85"
          >
            <div className="w-16 h-10 border-2 border-dashed border-slate-500 group-hover:border-cyan-400 rounded-lg flex items-center justify-center font-bold text-xs text-slate-400 group-hover:text-cyan-400 shrink-0">
              16:9
            </div>
            <div>
              <div className="font-bold text-sm text-slate-100 group-hover:text-cyan-400">
                Blank 16:9 Video
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">Landscape (1344×768)</div>
            </div>
          </KineticCard>

          {/* Recently Deleted 7-Day Bin */}
          <KineticCard
            onClick={() => setModal('trash', true)}
            hoverBorder="hover:border-rose-500/50"
            className="p-4 sm:p-5 flex items-center gap-3.5 group"
          >
            <div className="w-12 h-12 rounded-xl bg-[#07090e] border border-[#1f2736] group-hover:border-rose-500/40 text-slate-400 group-hover:text-rose-400 flex items-center justify-center text-xl transition shrink-0">
              <Trash2 className="w-5 h-5 text-rose-400" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-sm text-slate-100 group-hover:text-rose-400">
                  Recently Deleted
                </span>
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full border ${
                  trashProjects.length > 0
                    ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                    : 'bg-slate-800 text-slate-400 border-slate-700'
                }`}>
                  {trashProjects.length}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">Auto-purged after 7 days</div>
            </div>
          </KineticCard>
        </div>
      </div>

      {/* 2. Previously Created Projects & Drafts */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Previously Created Videos & Drafts
          </h3>
          <span className="text-xs text-slate-500">{projects.length} projects</span>
        </div>

        {projects.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs border border-dashed border-[#1f2736] rounded-2xl">
            No projects created yet. Click "Blank 9:16 Short" or choose a viral topic above!
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
            {projects.map((p) => {
              const thumb = p.thumbnail_url || (p.scenes && p.scenes[0]?.image_url);
              const isMenuOpen = activeMenuProject === p.project_name;

              return (
                <div
                  key={p.project_name}
                  className="bg-[#0d111a] hover:bg-[#161b26] border border-[#1f2736] hover:border-cyan-400/60 rounded-xl overflow-hidden transition flex flex-col group relative shadow-sm"
                >
                  {/* Thumbnail / Aspect Ratio */}
                  <div
                    onClick={() => openEditor(p.project_name)}
                    className="aspect-[9/16] bg-black overflow-hidden relative cursor-pointer"
                  >
                    {thumb ? (
                      <img
                        src={thumb}
                        alt={p.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-[10px] text-slate-600">
                        Draft
                      </div>
                    )}
                    <div className="absolute top-2 left-2 flex items-center gap-1">
                      <span className="bg-black/70 text-[9px] font-bold px-1.5 py-0.5 rounded text-slate-300">
                        {p.aspect_ratio || '9:16'}
                      </span>
                      {p.project_type === 'repurpose' && (
                        <span className="bg-indigo-950/80 border border-indigo-500/40 text-[9px] font-bold px-1.5 py-0.5 rounded text-indigo-300">
                          Repurpose
                        </span>
                      )}
                    </div>
                  </div>

                  {/* 3-Dots Action Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveMenuProject(isMenuOpen ? null : p.project_name);
                    }}
                    title="Project options"
                    className="absolute top-2 right-2 w-7 h-7 rounded-full bg-black/75 hover:bg-black/95 border border-slate-700/80 text-slate-200 hover:text-white flex items-center justify-center text-xs opacity-80 hover:opacity-100 transition z-10 shadow-lg cursor-pointer"
                  >
                    <MoreVertical className="w-3.5 h-3.5" />
                  </button>

                  {/* Popover Action Menu */}
                  <AnimatePresence>
                    {isMenuOpen && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="absolute top-10 right-2 w-40 bg-[#0c0f18] border border-slate-700/80 rounded-xl shadow-2xl p-1 z-30 flex flex-col gap-1 text-xs"
                      >
                        <button
                          onClick={() => {
                            setActiveMenuProject(null);
                            openEditor(p.project_name);
                          }}
                          className="w-full text-left px-2.5 py-1.5 rounded-lg hover:bg-[#161b26] text-slate-200 hover:text-cyan-400 font-semibold flex items-center gap-2 transition cursor-pointer"
                        >
                          <Play className="w-3.5 h-3.5 text-cyan-400" />
                          <span>Open in Studio</span>
                        </button>
                        <button
                          onClick={(e) => handleMoveToTrash(p.project_name, e)}
                          className="w-full text-left px-2.5 py-1.5 rounded-lg hover:bg-rose-950/40 text-rose-400 font-semibold flex items-center gap-2 transition cursor-pointer"
                        >
                          <Trash className="w-3.5 h-3.5 text-rose-400" />
                          <span>Move to Trash</span>
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Card Title & Status */}
                  <div
                    onClick={() => openEditor(p.project_name)}
                    className="p-2.5 flex flex-col justify-between flex-1 cursor-pointer"
                  >
                    <div className="font-bold text-xs truncate text-slate-200 group-hover:text-cyan-400">
                      {p.title || p.project_name}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-1 uppercase font-semibold">
                      {(p.status || 'Draft').replace('_', ' ')}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
