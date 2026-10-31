import React from "react";

interface AudioWaveformProps {
  isActive: boolean;
  statusText?: string;
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({ isActive, statusText }) => {
  return (
    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-900/60 border border-slate-700/50">
      <div className="flex items-center gap-0.5 h-4">
        {[0.4, 0.8, 1.0, 0.6, 0.9, 0.5, 0.7].map((heightScale, idx) => (
          <span
            key={idx}
            className={`w-0.5 rounded-full bg-sky-400 transition-all duration-300 ${
              isActive ? "animate-pulse" : "opacity-30"
            }`}
            style={{
              height: isActive ? `${heightScale * 14}px` : "4px",
              animationDelay: `${idx * 150}ms`,
            }}
          />
        ))}
      </div>
      {statusText && <span className="text-xs text-slate-300 font-mono tracking-wide">{statusText}</span>}
    </div>
  );
};
