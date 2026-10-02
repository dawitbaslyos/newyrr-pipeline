import React from 'react';
import { motion } from 'framer-motion';

interface KineticCardProps {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
  hoverBorder?: string;
}

export const KineticCard: React.FC<KineticCardProps> = ({
  children,
  onClick,
  className = '',
  hoverBorder = 'hover:border-cyan-400/60'
}) => {
  return (
    <motion.div
      whileHover={{ y: -2, transition: { duration: 0.18, ease: 'easeOut' } }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`bg-[#0d111a] hover:bg-[#161b26] border border-[#1f2736] ${hoverBorder} rounded-2xl transition-all duration-200 shadow-sm cursor-pointer ${className}`}
    >
      {children}
    </motion.div>
  );
};
