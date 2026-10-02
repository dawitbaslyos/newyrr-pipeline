import React from 'react';
import { motion } from 'framer-motion';

interface DynamicIslandProps {
  icon?: React.ReactNode;
  label: string;
  sublabel?: string;
  dotColor?: string;
  onClick?: () => void;
  className?: string;
}

export const DynamicIsland: React.FC<DynamicIslandProps> = ({
  icon,
  label,
  sublabel,
  dotColor = 'bg-emerald-400',
  onClick,
  className = ''
}) => {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.96 }}
      onClick={onClick}
      className={`inline-flex items-center gap-2 bg-[#0d111a] hover:bg-[#161b26] border border-[#1f2736] hover:border-cyan-400/50 px-3.5 py-1.5 rounded-full text-xs text-slate-200 transition-colors shadow-sm cursor-pointer ${className}`}
    >
      <span className={`w-2 h-2 rounded-full ${dotColor} animate-pulse shrink-0`} />
      {icon && <span className="text-xs shrink-0">{icon}</span>}
      <span className="font-semibold text-[11px] truncate max-w-[200px] sm:max-w-none">{label}</span>
      {sublabel && <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">• {sublabel}</span>}
    </motion.button>
  );
};
