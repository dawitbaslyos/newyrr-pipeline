import React, { useState } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { X, Tv, Loader2, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const AddUserChannelModal: React.FC = () => {
  const { isAddUserChannelOpen, setModal, fetchChannels } = useStudioStore();
  const [handle, setHandle] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isAddUserChannelOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!handle.trim()) return;

    let cleanHandle = handle.trim();
    // Allow pasting full URL: extract @handle
    if (cleanHandle.includes('youtube.com/')) {
      const match = cleanHandle.match(/@([a-zA-Z0-9_\-\.]+)/);
      if (match) cleanHandle = '@' + match[1];
    }
    if (!cleanHandle.startsWith('@')) cleanHandle = '@' + cleanHandle;

    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/channels/user-add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ handle: cleanHandle })
      });

      if (!res.ok) {
        throw new Error('Could not connect to YouTube to verify channel.');
      }

      await fetchChannels();
      setModal('addUserChannel', false);
      setHandle('');
    } catch (err: any) {
      setError(err.message || 'Failed to add channel.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-[#0c0f18] border border-slate-700/80 rounded-2xl w-full max-w-sm p-5 flex flex-col gap-4 shadow-2xl font-sans"
        >
          <div className="flex items-center justify-between border-b border-[#1f2736] pb-2.5">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-cyan-400/20 border border-cyan-400/40 flex items-center justify-center text-cyan-400 text-sm">
                <Tv className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-bold text-xs text-slate-100 uppercase tracking-wider">
                  Add Your Channel
                </h3>
                <p className="text-[10px] text-slate-400">
                  Enter handle and we'll fetch subscribers & stats
                </p>
              </div>
            </div>
            <button
              onClick={() => setModal('addUserChannel', false)}
              className="w-7 h-7 rounded-lg hover:bg-[#161b26] text-slate-400 hover:text-white flex items-center justify-center text-xs transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
            <div>
              <label className="text-[11px] font-bold text-slate-300 uppercase tracking-wider block mb-1.5">
                YouTube Channel @handle
              </label>
              <input
                type="text"
                autoFocus
                disabled={isLoading}
                placeholder="e.g. @internetchill or youtube.com/@yourchannel"
                value={handle}
                onChange={(e) => setHandle(e.target.value)}
                className="w-full bg-[#07090e] border border-[#1f2736] rounded-xl px-3.5 py-2.5 text-xs text-slate-100 outline-none focus:border-cyan-400 font-mono transition"
              />
              <span className="text-[10px] text-slate-400 mt-1 block">
                Channel name, subscribers, and stats will be resolved automatically.
              </span>
            </div>

            {error && (
              <div className="text-xs text-rose-400 bg-rose-950/30 border border-rose-800/40 p-2.5 rounded-xl">
                {error}
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#1f2736]">
              <button
                type="button"
                disabled={isLoading}
                onClick={() => setModal('addUserChannel', false)}
                className="px-3.5 py-1.5 text-xs font-semibold text-slate-400 hover:text-white cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading || !handle.trim()}
                className="bg-cyan-400 hover:bg-cyan-300 disabled:opacity-50 text-black font-bold text-xs px-4 py-2 rounded-xl transition shadow active:scale-95 flex items-center gap-1.5 cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Resolving Channel...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Add & Switch</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
