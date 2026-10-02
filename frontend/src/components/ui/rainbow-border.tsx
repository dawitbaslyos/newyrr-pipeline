import React, { useId } from 'react';

interface RainbowBorderProps {
  isLoading: boolean;
  progress?: number; // 0 to 100. If undefined or -1, runs smooth indeterminate sweep
  borderRadius?: number;
  strokeWidth?: number;
  className?: string;
  glow?: boolean;
}

export const RainbowBorder: React.FC<RainbowBorderProps> = ({
  isLoading,
  progress = -1,
  borderRadius = 16,
  strokeWidth = 3,
  className = '',
  glow = true
}) => {
  const gradientId = useId().replace(/:/g, '_');
  if (!isLoading) return null;

  const isDeterminate = progress >= 0 && progress <= 100;
  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <div 
      style={{ borderRadius: `${borderRadius}px` }}
      className={`absolute inset-0 pointer-events-none z-30 overflow-hidden ${className}`}
    >
      {/* Subtle Dark Skeleton Shimmer in background */}
      <div className="absolute inset-0 bg-[#07090e]/75 backdrop-blur-[2px] transition-opacity duration-300">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/10 to-transparent animate-shimmer" />
      </div>

      {/* SVG Google Rainbow Perimeter Border - Starts at top-left corner */}
      <svg 
        className="absolute inset-0 w-full h-full pointer-events-none" 
        style={{ filter: glow ? 'drop-shadow(0 0 6px rgba(66, 133, 244, 0.75))' : 'none' }}
      >
        <defs>
          <linearGradient id={`grad_${gradientId}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#4285F4" />
            <stop offset="28%" stopColor="#EA4335" />
            <stop offset="60%" stopColor="#FBBC05" />
            <stop offset="85%" stopColor="#34A853" />
            <stop offset="100%" stopColor="#4285F4" />
          </linearGradient>
        </defs>

        <rect
          x={strokeWidth / 2}
          y={strokeWidth / 2}
          width={`calc(100% - ${strokeWidth}px)`}
          height={`calc(100% - ${strokeWidth}px)`}
          rx={borderRadius}
          ry={borderRadius}
          fill="none"
          stroke={`url(#grad_${gradientId})`}
          strokeWidth={strokeWidth}
          pathLength={100}
          strokeDasharray={100}
          strokeDashoffset={isDeterminate ? 100 - clampedProgress : undefined}
          className={!isDeterminate ? 'rainbow-indeterminate-border' : 'transition-all duration-300 ease-out'}
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
};

export default RainbowBorder;
