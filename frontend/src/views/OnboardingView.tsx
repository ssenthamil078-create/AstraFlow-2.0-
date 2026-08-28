import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export const OnboardingView: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);

  const nextStep = () => {
    if (step < 5) setStep(step + 1);
    else navigate('/dashboard');
  };

  const skip = () => navigate('/dashboard');

  return (
    <div className="min-h-screen bg-[#030615] flex flex-col items-center justify-center text-slate-100 p-4">
      <div className="w-full max-w-2xl p-10 rounded-3xl bg-[rgba(10,16,38,0.72)] backdrop-blur-[20px] border border-[rgba(139,92,246,0.2)] shadow-[0_8px_32px_0_rgba(0,0,0,0.37)]">
        
        {/* Progress indicator */}
        <div className="flex items-center justify-between mb-12">
          {[1, 2, 3, 4, 5].map((num) => (
            <div key={num} className={`flex flex-col items-center gap-2 ${step >= num ? 'text-cyan-400' : 'text-slate-600'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${step >= num ? 'border-cyan-400 bg-cyan-400/10' : 'border-slate-600'}`}>
                0{num}
              </div>
            </div>
          ))}
        </div>

        {/* Content */}
        <div className="text-center min-h-[200px] flex flex-col justify-center">
          {step === 1 && (
            <>
              <h2 className="text-3xl font-bold mb-4">Welcome to AstraFlow</h2>
              <p className="text-slate-400">Your financial life is about to become a living, breathing universe.</p>
            </>
          )}
          {step === 2 && (
            <>
              <h2 className="text-3xl font-bold mb-4">Unit of Account</h2>
              <p className="text-slate-400 mb-6">Choose your primary currency.</p>
              <select className="bg-[#050816] border border-white/10 rounded-xl px-4 py-3 outline-none mx-auto block">
                <option value="INR">₹ INR</option>
                <option value="USD">$ USD</option>
                <option value="EUR">€ EUR</option>
                <option value="GBP">£ GBP</option>
              </select>
            </>
          )}
          {step === 3 && (
            <>
              <h2 className="text-3xl font-bold mb-4">Add your first financial data</h2>
              <p className="text-slate-400">Connect a data source to begin charting your cosmos.</p>
            </>
          )}
          {step === 4 && (
            <>
              <h2 className="text-3xl font-bold mb-4">Build your financial twin</h2>
              <p className="text-slate-400">We are assembling your ground truth balance, obligations, and goals into a digital model.</p>
            </>
          )}
          {step === 5 && (
            <>
              <h2 className="text-3xl font-bold mb-4">Explore your universe</h2>
              <p className="text-cyan-400">Your Financial Twin is ready.</p>
            </>
          )}
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between mt-12 pt-8 border-t border-white/5">
          <button onClick={skip} className="text-slate-400 hover:text-white px-4 py-2">
            Skip
          </button>
          <div className="flex gap-4">
            {step > 1 && (
              <button onClick={() => setStep(step - 1)} className="px-6 py-3 rounded-full border border-white/10 hover:bg-white/5 transition-colors">
                Back
              </button>
            )}
            <button onClick={nextStep} className="px-8 py-3 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold rounded-full shadow-[0_0_15px_rgba(34,211,238,0.3)] transition-all">
              {step === 5 ? 'Enter Universe' : 'Continue'}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
