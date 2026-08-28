import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, X, Sparkles, ArrowUpRight, HelpCircle, Loader2 } from 'lucide-react';
import { chatApi } from '../services/provenanceApi.ts';
import { ChatMessage, UserProfile } from '../types.ts';

interface AstraCopilotProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (route: any) => void;
  user: UserProfile | null;
}

export const AstraCopilot: React.FC<AstraCopilotProps> = ({
  isOpen,
  onClose,
  onNavigate,
  user,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'init_1',
      role: 'assistant',
      content: `Welcome back to your financial cosmos, ${user?.name || 'Commander'}. I am Astra, your predictive copilot. I continuously simulate your cash flow, stress-test your portfolio against volatility, and track the mathematical evidence behind every rupee. How can I assist your financial universe today?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedQuestions = [
    'Why did my balance change?',
    'What expenses increased?',
    'Which transactions are uncertain?',
    'How reliable is my income?',
    'How close am I to my goals?',
  ];

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || inputValue).trim();
    if (!query || loading) return;

    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputValue('');
    setLoading(true);

    try {
      const res = await chatApi.sendMessage(query);
      const assistantMsg: ChatMessage = {
        id: `ast_${Date.now()}`,
        role: 'assistant',
        content: res.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `ast_err_${Date.now()}`,
        role: 'assistant',
        content: 'Astra intelligence synchronized locally. Please verify your connection or review the latest events in your universe.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Slide-out Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Slide-out Drawer */}
      <div
        className={`fixed top-0 right-0 h-full w-full sm:w-[440px] z-50 bg-[#070b1f]/95 backdrop-blur-2xl border-l border-cyan-500/20 shadow-[0_0_50px_rgba(0,0,0,0.8)] flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Drawer Header */}
        <div className="p-5 border-b border-white/10 flex items-center justify-between bg-gradient-to-r from-cyan-950/40 via-transparent to-[#070b1f]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-cyan-500 to-[#b600f8] p-[1.5px] shadow-[0_0_15px_rgba(0,242,255,0.4)]">
              <div className="w-full h-full rounded-full bg-[#050816] flex items-center justify-center">
                <Bot className="w-5 h-5 text-cyan-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-white font-heading text-base">Astra Copilot</h3>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-400/20 text-cyan-300 uppercase tracking-wider">
                  AI Active
                </span>
              </div>
              <p className="text-xs text-slate-400">Grounded Financial Reasoning</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Suggested Queries Chips */}
        <div className="p-3.5 border-b border-white/5 bg-[#0a1028]/60 overflow-x-auto no-scrollbar">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-[#ebb2ff]" />
            <span>Suggested Insights</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {suggestedQuestions.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSend(q)}
                className="text-xs px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-slate-300 hover:bg-cyan-500/15 hover:border-cyan-400/30 hover:text-cyan-200 transition-all text-left truncate max-w-[280px]"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-[88%] p-3.5 rounded-2xl text-sm leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-gradient-to-r from-cyan-600 to-cyan-500 text-slate-950 font-medium rounded-tr-none shadow-[0_0_20px_rgba(0,242,255,0.2)]'
                    : 'glass-panel text-slate-200 rounded-tl-none border-white/10'
                }`}
              >
                {m.content}
              </div>
              <span className="text-[10px] text-slate-500 mt-1 px-1">{m.timestamp}</span>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-xs text-cyan-400 font-medium p-3 glass-panel rounded-2xl w-fit">
              <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
              <span>Analyzing financial state & simulations...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Navigation Footer */}
        <div className="px-4 py-2 bg-[#050816]/70 border-t border-white/5 flex items-center justify-between text-xs text-slate-400">
          <span>Quick Access:</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                onNavigate('events');
                onClose();
              }}
              className="hover:text-cyan-300 underline flex items-center gap-0.5"
            >
              Events <ArrowUpRight className="w-3 h-3" />
            </button>
            <span className="text-slate-600">•</span>
            <button
              onClick={() => {
                onNavigate('cash-flow');
                onClose();
              }}
              className="hover:text-cyan-300 underline flex items-center gap-0.5"
            >
              Cash Flow <ArrowUpRight className="w-3 h-3" />
            </button>
            <span className="text-slate-600">•</span>
            <button
              onClick={() => {
                onNavigate('goals');
                onClose();
              }}
              className="hover:text-cyan-300 underline flex items-center gap-0.5"
            >
              Goals <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Message Input Box */}
        <div className="p-4 border-t border-white/10 bg-[#070b1f]">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="relative flex items-center"
          >
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask about your balance, cash flow, alerts..."
              className="w-full pl-4 pr-12 py-3 rounded-xl bg-[#192122]/90 border border-white/10 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all"
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || loading}
              className="absolute right-2 p-2 rounded-lg bg-cyan-400 text-slate-950 hover:bg-cyan-300 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </>
  );
};
