import React from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { Trash2, RotateCcw, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const TrashModal: React.FC = () => {
  const { isTrashModalOpen, setModal, trashProjects, fetchProjects, fetchTrash } = useStudioStore();

  if (!isTrashModalOpen) return null;

  const handleRestore = async (projectName: string) => {
    try {
      await fetch('/api/projects/restore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_name: projectName })
      });
      fetchTrash();
      fetchProjects();
    } catch (e) {
      alert('Failed restoring project: ' + e);
    }
  };

  const handlePurge = async (projectName: string) => {
    if (!confirm(`Permanently delete "${projectName}"? This cannot be undone.`)) return;
    try {
      await fetch('/api/projects/purge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_name: projectName })
      });
      fetchTrash();
    } catch (e) {
      alert('Failed purging: ' + e);
    }
  };

  const handleEmptyTrash = async () => {
    if (!confirm('Are you sure you want to permanently delete all projects in the trash?')) return;
    try {
      await fetch('/api/projects/empty-trash', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      fetchTrash();
    } catch (e) {
      alert('Failed emptying trash: ' + e);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-[#0c0f18] border border-slate-700/80 rounded-2xl w-full max-w-2xl max-h-[85vh] p-5 sm:p-6 flex flex-col gap-4 shadow-2xl overflow-hidden font-sans"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#1f2736] pb-3 shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-400 flex items-center justify-center">
                <Trash2 className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-bold text-xs text-slate-100 uppercase tracking-wider">
                  Recently Deleted Projects
                </h3>
                <p className="text-[10px] text-slate-400">
                  Projects remain here for 7 days before permanent automatic purge
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleEmptyTrash}
                className="text-xs text-rose-400 hover:text-rose-300 font-semibold px-2.5 py-1 rounded-lg border border-rose-500/30 hover:border-rose-500/60 bg-rose-950/30 transition cursor-pointer"
              >
                Empty Trash
              </button>
              <button
                onClick={() => setModal('trash', false)}
                className="w-7 h-7 rounded-lg hover:bg-[#161b26] text-slate-400 hover:text-white flex items-center justify-center text-xs transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Feed */}
          <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-2.5">
            {trashProjects.length === 0 ? (
              <div className="p-8 text-center flex flex-col items-center justify-center text-slate-500 gap-2">
                <Trash2 className="w-8 h-8 opacity-30" />
                <span className="text-xs">Trash is empty. Deleted projects appear here for 7 days.</span>
              </div>
            ) : (
              trashProjects.map((p) => {
                const thumb = p.thumbnail_url || (p.scenes && p.scenes[0]?.image_url);
                return (
                  <div
                    key={p.project_name}
                    className="bg-[#0d111a]/80 border border-[#1f2736] hover:border-slate-600 p-3 rounded-xl flex items-center justify-between gap-3 transition"
                  >
                    <div className="flex items-center gap-3 overflow-hidden">
                      <div className="w-12 h-16 bg-[#07090e] rounded-lg overflow-hidden shrink-0 border border-[#1f2736] flex items-center justify-center">
                        {thumb ? (
                          <img src={thumb} alt="" className="w-full h-full object-cover opacity-70" />
                        ) : (
                          <span className="text-[9px] text-slate-600">No Img</span>
                        )}
                      </div>
                      <div className="overflow-hidden">
                        <div className="font-bold text-xs text-slate-200 truncate">
                          {p.title || p.project_name}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-[10px] text-amber-400 font-semibold bg-amber-950/40 border border-amber-600/30 px-1.5 py-0.5 rounded">
                            ⏳ {p.days_left ?? 7}d remaining
                          </span>
                          <span className="text-[10px] text-slate-500 uppercase">
                            {p.aspect_ratio || '9:16'}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => handleRestore(p.project_name)}
                        className="px-3 py-1.5 rounded-lg bg-emerald-950/40 hover:bg-emerald-900 border border-emerald-600/40 text-emerald-300 text-xs font-semibold flex items-center gap-1 transition active:scale-95 cursor-pointer"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        <span>Restore</span>
                      </button>
                      <button
                        onClick={() => handlePurge(p.project_name)}
                        title="Permanently delete now"
                        className="p-1.5 rounded-lg hover:bg-rose-950/50 text-slate-500 hover:text-rose-400 border border-transparent hover:border-rose-800 transition cursor-pointer"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
