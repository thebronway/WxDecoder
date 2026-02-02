import React from 'react';

const Disclaimer = () => {
  return (
    <div className="max-w-2xl mx-auto text-gray-300 space-y-6 pt-10">
      <h1 className="text-3xl font-bold text-white text-orange-500">Legal Disclaimer</h1>
      <div className="p-6 bg-neutral-800 rounded-lg border border-neutral-700">
        <p className="mb-4">
          <strong>GoNoGo AI is for educational and situational awareness purposes only.</strong>
        </p>
        <ul className="list-disc pl-5 space-y-2 text-sm">
            <li>This tool is NOT a substitute for an official weather briefing (1800-WX-BRIEF).</li>
            <li>AI can hallucinate or misinterpret data. Always verify raw METAR/TAF/NOTAM text.</li>
            <li>The Pilot in Command (PIC) is solely responsible for the safety of the flight.</li>
            <li>Dynamic TFRs (VIP, Stadiums) are NOT checked by this tool. (yet)</li>
        </ul>
      </div>
    </div>
  );
};

export default Disclaimer;