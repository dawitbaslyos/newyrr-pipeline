import React, { useState } from 'react';
import {
  motion,
  useTransform,
  AnimatePresence,
  useMotionValue,
  useSpring,
} from 'framer-motion';

export interface TooltipItem {
  id: number | string;
  name: string;
  designation?: string;
  image?: string;
  handle?: string;
}

interface AnimatedTooltipProps {
  items: TooltipItem[];
  activeId?: string | number | null;
  onItemClick?: (item: TooltipItem) => void;
}

export const AnimatedTooltip: React.FC<AnimatedTooltipProps> = ({
  items,
  activeId,
  onItemClick,
}) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | string | null>(null);
  const springConfig = { stiffness: 100, damping: 5 };
  const x = useMotionValue(0);

  const rotate = useSpring(
    useTransform(x, [-100, 100], [-45, 45]),
    springConfig
  );
  const translateX = useSpring(
    useTransform(x, [-100, 100], [-50, 50]),
    springConfig
  );

  const handleMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
    const halfWidth = event.currentTarget.offsetWidth / 2;
    x.set(event.nativeEvent.offsetX - halfWidth);
  };

  return (
    <div className="flex items-center -space-x-3 sm:-space-x-3.5 py-1">
      {items.map((item) => {
        const isActive = activeId === item.id || activeId === item.handle;
        return (
          <div
            className="relative group cursor-pointer"
            key={item.id || item.name}
            onMouseEnter={() => setHoveredIndex(item.id)}
            onMouseLeave={() => setHoveredIndex(null)}
            onMouseMove={handleMouseMove}
            onClick={() => onItemClick && onItemClick(item)}
          >
            <AnimatePresence mode="popLayout">
              {hoveredIndex === item.id && (
                <motion.div
                  initial={{ opacity: 0, y: 12, scale: 0.6 }}
                  animate={{
                    opacity: 1,
                    y: 0,
                    scale: 1,
                    transition: {
                      type: 'spring',
                      stiffness: 260,
                      damping: 10,
                    },
                  }}
                  exit={{ opacity: 0, y: 12, scale: 0.6 }}
                  style={{
                    translateX: translateX,
                    rotate: rotate,
                    whiteSpace: 'nowrap',
                  }}
                  className="absolute -top-16 left-1/2 -translate-x-1/2 flex flex-col items-center justify-center rounded-xl bg-[#0d121c] border border-[#222c3d] shadow-[0_10px_25px_-5px_rgba(0,0,0,0.8),0_0_15px_rgba(0,242,254,0.15)] px-3.5 py-1.5 z-50 pointer-events-none"
                >
                  {/* Subtle top indicator bar */}
                  <div className="absolute inset-x-4 z-30 w-[40%] mx-auto -bottom-px bg-gradient-to-r from-transparent via-cyan-400 to-transparent h-[1.5px]" />
                  <div className="font-bold text-white text-xs tracking-tight">
                    {item.name}
                  </div>
                  {item.designation && (
                    <div className="text-[10px] text-cyan-400 font-mono mt-0.5">
                      {item.designation}
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Avatar Pill / Bubble */}
            <div
              className={`relative rounded-full transition-all duration-300 group-hover:scale-115 group-hover:z-30 ${
                isActive
                  ? 'ring-2 ring-cyan-400 scale-105 z-20 shadow-[0_0_12px_rgba(0,242,254,0.4)]'
                  : 'ring-2 ring-[#07090e] hover:ring-cyan-500/70'
              }`}
            >
              {item.image ? (
                <img
                  src={item.image}
                  alt={item.name}
                  className="w-10 h-10 sm:w-11 sm:h-11 rounded-full object-cover bg-[#131926] shadow-sm select-none"
                  onError={(e) => {
                    // Fallback to initial if image fails
                    (e.target as HTMLElement).style.display = 'none';
                  }}
                />
              ) : null}

              {/* Fallback Initials if image missing or hidden */}
              <div
                className={`w-10 h-10 sm:w-11 sm:h-11 rounded-full bg-gradient-to-br from-[#1a2333] to-[#0f1420] border border-[#283449] flex items-center justify-center text-xs font-bold text-cyan-300 select-none ${
                  item.image ? 'hidden' : 'flex'
                }`}
              >
                {item.name ? item.name[0].toUpperCase() : '@'}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
