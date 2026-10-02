import React, { useEffect, useState } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { X, Clock, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const TopicHistoryDrawer: React.FC = () => {
  const { isTopicHistoryOpen, setModal } = useStudioStore();
  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => {
    if (isTopicHistoryOpen) {
      fetch('/api/topics/history')
        .then((r) => r.json())
        .then((data) => setHistory(data))
        .catch((e) => console.error(e));
    }
  }, [isTopicHistoryOpen]);

  if (!isTopicHistoryOpen) return null;

  const handleUseTopic = (title: string) => {
    setModal('topicHistory', false);
    setModal('newDraft', true);
    window.sessionStorage.setItem('prefilledTopic', title);
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs font-sans">
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
          className="w-full max-w-md bg-[#0c0f18] border-l border-slate-700/80 h-full p-5 flex flex-col gap-4 shadow-2xl overflow-hidden"
        >
          <div className="flex items-center justify-between border-b border-[#1f2736] pb-3">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-cyan-400" />
              <h3 className="font-bold text-xs text-slate-100 uppercase tracking-wider">
                Topic Suggestions History
              </h3>
            </div>
            <button
              onClick={() => setModal('topicHistory', false)}
              className="w-7 h-7 rounded-lg hover:bg-[#161b26] text-slate-400 hover:text-white flex items-center justify-center text-xs transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto flex flex-col gap-2.5 pr-1">
            {history.length === 0 ? (
              <div className="text-xs text-slate-500 py-8 text-center">No history yet.</div>
            ) : (
              history.map((t, idx) => (
                <div
                  key={idx}
                  onClick={() => handleUseTopic(t.title)}
                  className="bg-[#0d111a] hover:bg-[#161b26] border border-[#1f2736] hover:border-cyan-400/50 p-3.5 rounded-xl cursor-pointer transition flex flex-col gap-1.5 group"
                >
                  <div className="flex items-center justify-between text-[10px] text-slate-400">
                    <span className="text-cyan-400 font-semibold">{t.category || 'Science'}</span>
                    <span className="text-cyan-400 group-hover:underline text-[11px] font-bold flex items-center gap-0.5">
                      Use <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                  <div className="font-bold text-xs text-slate-200 group-hover:text-cyan-400">
                    {t.title}
                  </div>
                  {t.hook && (
                    <div className="text-[11px] text-slate-400 italic bg-[#07090e] p-2 rounded-lg border border-[#1f2736]/40">
                      "{t.hook}"
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
