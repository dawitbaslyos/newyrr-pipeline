import React from 'react';
import { motion } from 'framer-motion';

export interface TabOption {
  id: string;
  label: string;
  icon?: React.ReactNode;
  badge?: string;
}

interface SegmentedTabsProps {
  options: TabOption[];
  activeId: string;
  onChange: (id: string) => void;
  className?: string;
  layoutId?: string;
}

export const SegmentedTabs: React.FC<SegmentedTabsProps> = ({
  options,
  activeId,
  onChange,
  className = '',
  layoutId = 'segmentedTab'
}) => {
  return (
    <div className={`relative flex items-center p-1 bg-[#07090e] border border-[#1f2736] rounded-xl ${className}`}>
      {options.map((opt) => {
        const isActive = opt.id === activeId;
        return (
          <button
            key={opt.id}
            onClick={() => onChange(opt.id)}
            className={`relative flex-1 py-1.5 px-2.5 text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-colors z-10 ${
              isActive ? 'text-cyan-400 font-bold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {isActive && (
              <motion.div
                layoutId={layoutId}
                className="absolute inset-0 bg-[#161b26] border border-cyan-400/40 rounded-lg shadow-sm -z-10"
                transition={{ type: 'spring', stiffness: 450, damping: 35 }}
              />
            )}
            {opt.icon && <span className="text-xs">{opt.icon}</span>}
            <span>{opt.label}</span>
            {opt.badge && (
              <span className="text-[9px] px-1.5 py-0.2 rounded-full bg-cyan-400/20 text-cyan-300 font-mono">
                {opt.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
