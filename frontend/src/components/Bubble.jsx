import React from 'react';

const Bubble = ({ label, value, highlight, risk }) => {
  let colorClass = "bg-neutral-800 border-neutral-700";
  
  // Logic for Category Highlight (VFR/IFR)
  if (highlight) {
    if (value === "VFR") colorClass = "bg-green-900/40 border-green-600";
    else if (value === "MVFR") colorClass = "bg-blue-900/40 border-blue-600";
    else if (value === "IFR") colorClass = "bg-red-900/40 border-red-600";
    else colorClass = "bg-pink-900/40 border-pink-600"; // LIFR
  }

  // Logic for Risk Levels (Specifically for Wind)
  if (risk) {
    if (risk === "HIGH") {
        colorClass = "bg-red-600/20 border-red-500 animate-pulse"; // Red for Danger
    } else if (risk === "MODERATE") {
        colorClass = "bg-yellow-600/20 border-yellow-500"; // Yellow for Caution
    }
  }

  return (
    <div className={`${colorClass} border rounded-xl h-32 p-2 flex flex-col items-center relative overflow-hidden transition-colors duration-300`}>
      
      {/* Label Container */}
      <div className="h-6 flex items-end justify-center pb-0.5 shrink-0 z-10">
        <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest">
          {label}
        </span>
      </div>

      {/* Value Container */}
      <div className="flex-1 flex items-center justify-center w-full z-10">
        <span className="text-lg md:text-xl font-bold text-white text-center leading-tight px-1 line-clamp-3">
          {value}
        </span>
      </div>
    </div>
  );
};

export default Bubble;