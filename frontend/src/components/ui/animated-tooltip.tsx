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

const TooltipItemBubble: React.FC<{
  item: TooltipItem;
  isActive: boolean;
  isHovered: boolean;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
  onMouseMove: (e: React.MouseEvent<HTMLDivElement>) => void;
  onClick: () => void;
  translateX: any;
  rotate: any;
}> = ({
  item,
  isActive,
  isHovered,
  onMouseEnter,
  onMouseLeave,
  onMouseMove,
  onClick,
  translateX,
  rotate,
}) => {
  const [imgError, setImgError] = useState(false);

  return (
    <div
      className="relative group cursor-pointer"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onMouseMove={onMouseMove}
      onClick={onClick}
    >
      <AnimatePresence mode="popLayout">
        {isHovered && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.7 }}
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
            exit={{ opacity: 0, y: 10, scale: 0.7 }}
            style={{
              translateX: translateX,
              rotate: rotate,
              whiteSpace: 'nowrap',
            }}
            className="absolute -top-14 left-1/2 -translate-x-1/2 flex flex-col items-center justify-center rounded-xl bg-[#0b0f17] border border-[#232d3e] shadow-[0_12px_32px_rgba(0,0,0,0.9),0_0_15px_rgba(0,242,254,0.18)] px-3.5 py-1.5 z-50 pointer-events-none"
          >
            {/* Tooltip Pointer Triangle */}
            <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-[#0b0f17] border-b border-r border-[#232d3e] rotate-45 pointer-events-none" />

            {/* Subtle top glowing hairline */}
            <div className="absolute inset-x-3 -top-px h-[1.5px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent" />

            <div className="font-bold text-white text-xs tracking-tight relative z-10">
              {item.name}
            </div>
            {item.designation && (
              <div className="text-[10px] text-cyan-400 font-mono mt-0.5 relative z-10">
                {item.designation}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Avatar Pill / Bubble */}
      <div
        className={`relative rounded-full transition-all duration-200 group-hover:scale-110 group-hover:z-30 ${
          isActive
            ? 'ring-2 ring-cyan-400 scale-105 z-20 shadow-[0_0_14px_rgba(0,242,254,0.45)]'
            : 'ring-2 ring-[#07090e] hover:ring-cyan-500/80'
        }`}
      >
        {item.image && !imgError ? (
          <img
            src={item.image}
            alt={item.name}
            referrerPolicy="no-referrer"
            loading="eager"
            className="w-10 h-10 sm:w-11 sm:h-11 rounded-full object-cover bg-[#131926] shadow-sm select-none"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-full bg-gradient-to-br from-[#1a2333] to-[#0f1420] border border-[#283449] flex items-center justify-center text-xs font-bold text-cyan-300 select-none">
            {item.name ? item.name.charAt(0).toUpperCase() : '@'}
          </div>
        )}
      </div>
    </div>
  );
};

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
    <div className="flex items-center -space-x-3 sm:-space-x-3.5 py-1 overflow-visible">
      {items.map((item) => {
        const isActive = activeId === item.id || activeId === item.handle;
        return (
          <TooltipItemBubble
            key={item.id || item.name}
            item={item}
            isActive={!!isActive}
            isHovered={hoveredIndex === item.id}
            onMouseEnter={() => setHoveredIndex(item.id)}
            onMouseLeave={() => setHoveredIndex(null)}
            onMouseMove={handleMouseMove}
            onClick={() => onItemClick && onItemClick(item)}
            translateX={translateX}
            rotate={rotate}
          />
        );
      })}
    </div>
  );
};

