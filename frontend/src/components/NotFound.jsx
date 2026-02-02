import React from 'react';
import { Link } from 'react-router-dom';

const NotFound = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center font-mono text-gray-200">
      
      {/* Container Box */}
      <div className="relative border-2 border-red-500 bg-[#141414]/90 p-10 max-w-lg w-full shadow-[0_0_20px_rgba(239,68,68,0.2)] mx-4">
        
        {/* Stripes Effect (Inline style for specific gradient) */}
        <div 
            className="h-2.5 w-full mb-8 opacity-50"
            style={{
                background: "repeating-linear-gradient(45deg, #ef4444, #ef4444 10px, #0a0a0a 10px, #0a0a0a 20px)"
            }}
        ></div>

        {/* 404 Header */}
        <h1 className="text-8xl font-black text-red-500 tracking-tighter leading-none m-0">
            404
        </h1>

        {/* Subtitle */}
        <h2 className="mt-4 mb-6 text-lg uppercase tracking-[4px] border-b border-neutral-800 pb-4 text-gray-300">
            Navigation Error
        </h2>

        {/* Message */}
        <div className="space-y-4 text-sm text-gray-400 leading-relaxed">
            <p className="uppercase font-bold text-red-400">
                WAYPOINT NOT FOUND
            </p>
            <p>
                The coordinates you entered do not match any known sector. 
                <br />
                You have deviated from the flight plan.
            </p>
        </div>

        {/* Button */}
        <Link 
            to="/" 
            className="inline-block mt-8 px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold uppercase tracking-wider rounded transition-colors text-sm"
        >
            Return to Base
        </Link>
      </div>

    </div>
  );
};

export default NotFound;