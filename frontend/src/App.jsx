import React from 'react';
import Dashboard from './components/Dashboard';

function App() {
  return (
    // Flex-col + min-h-screen forces Footer to bottom
    <div className="flex flex-col min-h-screen bg-neutral-900 text-gray-200 font-sans">
      
      {/* HEADER */}
      <header className="p-6 border-b border-neutral-800 bg-neutral-900/50">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-white tracking-tight">GoNoGo AI</h1>
          <span className="text-xs uppercase tracking-widest text-neutral-500">Flight Assistant</span>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <main className="flex-grow w-full p-6">
        <Dashboard />
      </main>

      {/* FOOTER */}
      <footer className="w-full py-8 text-center border-t border-neutral-800 bg-black text-xs text-neutral-600">
        <p>GoNoGo AI v0.1 • Built for Pilots</p>
      </footer>
    </div>
  );
}

export default App;