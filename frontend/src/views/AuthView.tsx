import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../services/authApi.ts';
import { AlertCircle, Loader2 } from 'lucide-react';

export const AuthView: React.FC = () => {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLogin) {
        await authApi.login(email, password);
      } else {
        const regRes = await authApi.register(name || email.split('@')[0], email, password);
        if (!localStorage.getItem('astra_token')) {
          await authApi.login(email, password);
        }
      }
      navigate('/dashboard');
    } catch (err: any) {
      console.error('Auth failure:', err);
      setError(err?.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030615] flex text-slate-100">
      {/* Left side - Visuals */}
      <div className="hidden lg:flex flex-1 relative items-center justify-center border-r border-white/5">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-purple-900/20 via-[#030615] to-[#030615]"></div>
        <div className="z-10 text-center max-w-md">
          <h2 className="text-4xl font-bold mb-4">Welcome back to your universe.</h2>
          <p className="text-slate-400">Log in to sync your financial twin and visualize your true cash flow trajectory.</p>
        </div>
      </div>

      {/* Right side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md p-8 rounded-3xl bg-[rgba(10,16,38,0.72)] backdrop-blur-[20px] border border-[rgba(139,92,246,0.2)] shadow-[0_8px_32px_0_rgba(0,0,0,0.37)]">
          <h3 className="text-2xl font-semibold mb-6 text-center">{isLogin ? 'Access Universe' : 'Create Universe'}</h3>
          
          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-sm text-slate-400 mb-1">Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="w-full bg-[#050816] border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-cyan-500/50 transition-colors text-white"
                  placeholder="Nisha"
                />
              </div>
            )}
            
            <div>
              <label className="block text-sm text-slate-400 mb-1">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full bg-[#050816] border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-cyan-500/50 transition-colors text-white"
                placeholder="orbit@astraflow.ai"
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full bg-[#050816] border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-cyan-500/50 transition-colors text-white"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 mt-6 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              <span>{isLogin ? 'Enter AstraFlow' : 'Create My Universe'}</span>
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError(null);
              }}
              className="text-sm text-slate-400 hover:text-cyan-400 transition-colors"
            >
              {isLogin ? "Don't have an account? Sign up" : "Already have an account? Log in"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

