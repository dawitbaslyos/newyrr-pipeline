import React, { useState } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { X, Play } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const AddChannelModal: React.FC = () => {
  const { isAddTrackedChannelOpen, setModal, fetchChannels } = useStudioStore();
  const [handle, setHandle] = useState('');
  const [focus, setFocus] = useState('');

  if (!isAddTrackedChannelOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!handle.trim()) return;
    let cleanHandle = handle.trim();
    if (!cleanHandle.startsWith('@') && !cleanHandle.includes(' ')) {
      cleanHandle = '@' + cleanHandle;
    }

    try {
      await fetch('/api/channels/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          handle: cleanHandle,
          name: cleanHandle.replace('@', ''),
          focus: focus.trim() || 'Science Trivia'
        })
      });
      setModal('addTrackedChannel', false);
      fetchChannels();
    } catch (err) {
      alert('Failed to add channel: ' + err);
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
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-cyan-400/20 border border-cyan-400/40 flex items-center justify-center text-cyan-400 text-xs">
                <Play className="w-3.5 h-3.5 fill-current" />
              </div>
              <div>
                <h3 className="font-bold text-xs text-slate-100 uppercase tracking-wider">
                  Track Inspiration Channel
                </h3>
                <p className="text-[10px] text-slate-400">Monitor competitor viral topics & signals</p>
              </div>
            </div>
            <button
              onClick={() => setModal('addTrackedChannel', false)}
              className="w-7 h-7 rounded-lg hover:bg-[#161b26] text-slate-400 hover:text-white flex items-center justify-center text-xs transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div>
              <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                YouTube Handle or Name
              </label>
              <input
                type="text"
                placeholder="e.g. @Veritasium or @BeSmart"
                value={handle}
                onChange={(e) => setHandle(e.target.value)}
                className="w-full bg-[#07090e] border border-[#1f2736] rounded-xl px-3 py-2 text-xs text-slate-100 outline-none focus:border-cyan-400 font-mono"
              />
            </div>
            <div>
              <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                Topic Focus / Niche
              </label>
              <input
                type="text"
                placeholder="e.g. Physics, Material Science, Biology"
                value={focus}
                onChange={(e) => setFocus(e.target.value)}
                className="w-full bg-[#07090e] border border-[#1f2736] rounded-xl px-3 py-2 text-xs text-slate-100 outline-none focus:border-cyan-400"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#1f2736]">
              <button
                type="button"
                onClick={() => setModal('addTrackedChannel', false)}
                className="px-3.5 py-1.5 text-xs font-semibold text-slate-400 hover:text-white cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="bg-cyan-400 hover:bg-cyan-300 text-black font-bold text-xs px-4 py-2 rounded-xl transition shadow active:scale-95 cursor-pointer"
              >
                + Track Channel
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
