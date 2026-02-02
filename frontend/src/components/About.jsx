import React from 'react';

const About = () => {
  return (
    <div className="max-w-2xl mx-auto text-gray-300 space-y-6 pt-10">
      <h1 className="text-3xl font-bold text-white">About GoNoGo AI</h1>
      <p>
        GoNoGo AI was built to solve a simple problem: raw aviation data is tedious to parse. 
        By combining live FAA data with OpenAI's reasoning capabilities, this tool acts as a 
        second set of eyes during your preflight planning.
      </p>
      <p>
        It doesn't just display data; it reads it, checks it against your aircraft's 
        crosswind and performance limitations, and highlights what actually matters.
      </p>
    </div>
  );
};

export default About;