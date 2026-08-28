import React from 'react';
import { useNavigate } from 'react-router-dom';

export const LandingView: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#030615] flex flex-col items-center justify-center text-slate-100 overflow-hidden relative">
      <div className="absolute inset-0 z-0 opacity-40 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-900/20 via-[#030615] to-[#030615]"></div>
      
      <div className="z-10 text-center space-y-6 max-w-3xl px-4">
        <h1 className="text-5xl md:text-7xl font-bold tracking-tighter">
          The Living <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500">Financial Cosmos</span>
        </h1>
        <p className="text-xl text-slate-400 font-light">
          Navigate, predict, and prosper with an interactive 3D Financial Earth. Your personal wealth, visualized as a living universe.
        </p>
        
        <div className="flex items-center justify-center gap-4 pt-8">
          <button 
            onClick={() => navigate('/onboarding')}
            className="px-8 py-4 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold rounded-full transition-all shadow-[0_0_20px_rgba(34,211,238,0.4)]"
          >
            Launch Universe
          </button>
          <button 
            onClick={() => navigate('/login')}
            className="px-8 py-4 bg-white/5 hover:bg-white/10 text-white font-medium rounded-full backdrop-blur-md border border-white/10 transition-all"
          >
            Login
          </button>
        </div>
      </div>
    </div>
  );
};
