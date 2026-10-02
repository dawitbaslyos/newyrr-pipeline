import React from 'react';

interface AvatarRingProps {
  initials?: string;
  src?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  ringColor?: string;
  className?: string;
}

export const AvatarRing: React.FC<AvatarRingProps> = ({
  initials = 'N',
  src,
  size = 'md',
  ringColor = 'border-cyan-400/40',
  className = ''
}) => {
  const sizeMap = {
    sm: { box: 'w-7 h-7', inner: 'w-6 h-6', text: 'text-[11px]' },
    md: { box: 'w-10 h-10', inner: 'w-8 h-8', text: 'text-xs' },
    lg: { box: 'w-13 h-13', inner: 'w-11 h-11', text: 'text-base font-black' },
    xl: { box: 'w-16 h-16', inner: 'w-14 h-14', text: 'text-lg font-black' },
  };

  const { box, inner, text } = sizeMap[size];

  return (
    <div className={`relative rounded-full p-0.5 border-2 ${ringColor} flex items-center justify-center shrink-0 ${box} ${className}`}>
      {src ? (
        <img src={src} alt="Avatar" className={`rounded-full object-cover ${inner}`} />
      ) : (
        <div className={`rounded-full bg-cyan-400 text-black font-black flex items-center justify-center ${inner} ${text}`}>
          {initials.toUpperCase()}
        </div>
      )}
    </div>
  );
};
