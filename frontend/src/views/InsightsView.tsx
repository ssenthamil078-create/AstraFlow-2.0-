import React, { useState, useEffect } from 'react';
import {
  TrendingUp, TrendingDown, Zap, ShieldCheck, Target,
  AlertCircle, Bot, BarChart3, ArrowUpRight, ArrowDownRight,
  Clock, Sparkles, CheckCircle2,
} from 'lucide-react';
import { FinancialState, FinancialEvent, FinancialGoal, IncomeSource } from '../types.ts';
import { apiFetch } from '../services/api.ts';

interface InsightsViewProps {
  financialState: FinancialState | null;
  events: FinancialEvent[];
  goals: FinancialGoal[];
  incomeSources: IncomeSource[];
  currency?: string;
}

interface AiInsight {
  type: 'positive' | 'warning' | 'neutral';
  title: string;
  body: string;
}

export const InsightsView: React.FC<InsightsViewProps> = ({
  financialState, events, goals, incomeSources, currency = '?',
}) => {
  const [aiInsights, setAiInsights] = useState<AiInsight[]>([]);
  const [loadingAi, setLoadingAi] = useState(false);

  const confirmedEvents = events.filter((e) => e.status === 'CONFIRMED');
  const pendingEvents = events.filter((e) => e.status === 'LIKELY' || e.status === 'UNCERTAIN');
  const credits = confirmedEvents.filter((e) => (e.direction || e.type) === 'CREDIT');
  const debits = confirmedEvents.filter((e) => (e.direction || e.type) === 'DEBIT');
  const totalIncome = credits.reduce((s, e) => s + (e.amount || 0), 0);
  const totalExpenses = debits.reduce((s, e) => s + (e.amount || 0), 0);
  const netCashFlow = totalIncome - totalExpenses;
  const savingsRate = totalIncome > 0 ? ((netCashFlow / totalIncome) * 100).toFixed(1) : '0.0';
  const avgReliability = incomeSources.length > 0
    ? incomeSources.reduce((s, x) => s + (x.reliabilityScore || 50), 0) / incomeSources.length : 0;
  const completedGoals = goals.filter((g) => (g.progressPercent || 0) >= 100).length;
  const activeGoals = goals.filter((g) => (g.progressPercent || 0) < 100).length;
  const confirmedBalance = financialState?.confirmedBalance ?? 0;
  const expectedBalance = financialState?.expectedBalance ?? 0;

  const categoryTotals: Record<string, number> = {};
  debits.forEach((e) => { const c = e.category || 'Uncategorised'; categoryTotals[c] = (categoryTotals[c] || 0) + (e.amount || 0); });
  const sortedCategories = Object.entries(categoryTotals).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const maxCatAmount = sortedCategories[0]?.[1] || 1;

  const generateRuleInsights = () => {
    const ins: AiInsight[] = [];
    if (Number(savingsRate) >= 20) ins.push({ type: 'positive', title: 'Strong Savings Rate', body: `You are saving ${savingsRate}% of income — well above the recommended 15%.` });
    else if (Number(savingsRate) < 10 && totalIncome > 0) ins.push({ type: 'warning', title: 'Low Savings Rate', body: `Your savings rate is ${savingsRate}%. Consider reducing discretionary expenses.` });
    if (pendingEvents.length > 3) ins.push({ type: 'warning', title: `${pendingEvents.length} Events Need Review`, body: `${pendingEvents.length} unconfirmed events are affecting your digital twin accuracy.` });
    else ins.push({ type: 'positive', title: 'Clean Event Ledger', body: 'Almost all financial events are confirmed — your digital twin is highly accurate.' });
    if (avgReliability >= 75) ins.push({ type: 'positive', title: 'High Income Reliability', body: `Average income reliability is ${avgReliability.toFixed(0)}% — excellent stability.` });
    else if (incomeSources.length > 0) ins.push({ type: 'neutral', title: 'Income Reliability Building', body: `Average reliability is ${avgReliability.toFixed(0)}%. Record more observations to improve.` });
    if (confirmedBalance > 0 && expectedBalance > confirmedBalance) ins.push({ type: 'positive', title: 'Expected Surplus Ahead', body: `Expected balance ${currency}${(expectedBalance - confirmedBalance).toLocaleString('en-IN')} higher than confirmed.` });
    setAiInsights(ins.slice(0, 4));
  };

  const fetchAiInsights = async () => {
    setLoadingAi(true);
    try {
      const res = await apiFetch<any>('/api/chat', { method: 'POST', body: JSON.stringify({ message: 'Give me 4 concise financial insights from my data. Format as JSON array with fields: type (positive/warning/neutral), title (short), body (1 sentence). Return only the JSON array.' }) });
      const text: string = res.reply || res.message || '';
      const m = text.match(/\[[\s\S]*\]/);
      if (m) { const p = JSON.parse(m[0]); if (Array.isArray(p)) { setAiInsights(p.slice(0, 4)); return; } }
      generateRuleInsights();
    } catch { generateRuleInsights(); }
    finally { setLoadingAi(false); }
  };

  useEffect(() => { generateRuleInsights(); }, [events, incomeSources, goals, financialState]);

  const insightStyle = (t: string) => t === 'positive' ? 'border-emerald-500/30 bg-emerald-500/5 text-emerald-300' : t === 'warning' ? 'border-amber-500/30 bg-amber-500/5 text-amber-300' : 'border-cyan-500/20 bg-cyan-500/5 text-cyan-300';
  const InsightIcon = ({ t }: { t: string }) => t === 'positive' ? <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" /> : t === 'warning' ? <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" /> : <Zap className="w-4 h-4 text-cyan-400 flex-shrink-0" />;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 font-heading">AI-Powered Financial Intelligence</span>
          <h1 className="text-2xl font-bold text-white font-heading mt-1">Insights</h1>
          <p className="text-sm text-slate-400 mt-1">Pattern analysis and recommendations from your live financial universe.</p>
        </div>
        <button onClick={fetchAiInsights} disabled={loadingAi} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#b600f8]/20 border border-[#b600f8]/40 text-[#ebb2ff] text-xs font-semibold hover:bg-[#b600f8]/30 transition-all disabled:opacity-50">
          <Bot className={`w-4 h-4 ${loadingAi ? 'animate-pulse' : ''}`} />
          {loadingAi ? 'Analysing with Gemini...' : 'Refresh with Astra AI'}
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-2xl border border-white/5">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-2"><TrendingUp className="w-3.5 h-3.5 text-emerald-400" />Total Income</div>
          <div className="text-xl font-bold text-emerald-300 font-mono">{currency}{totalIncome.toLocaleString('en-IN')}</div>
          <div className="text-[11px] text-slate-500 mt-1">{credits.length} confirmed events</div>
        </div>
        <div className="glass-panel p-4 rounded-2xl border border-white/5">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-2"><TrendingDown className="w-3.5 h-3.5 text-rose-400" />Total Expenses</div>
          <div className="text-xl font-bold text-rose-300 font-mono">{currency}{totalExpenses.toLocaleString('en-IN')}</div>
          <div className="text-[11px] text-slate-500 mt-1">{debits.length} confirmed events</div>
        </div>
        <div className="glass-panel p-4 rounded-2xl border border-white/5">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
            {netCashFlow >= 0 ? <ArrowUpRight className="w-3.5 h-3.5 text-cyan-400" /> : <ArrowDownRight className="w-3.5 h-3.5 text-rose-400" />}
            Net Cash Flow
          </div>
          <div className={`text-xl font-bold font-mono ${netCashFlow >= 0 ? 'text-cyan-300' : 'text-rose-300'}`}>{netCashFlow >= 0 ? '+' : '-'}{currency}{Math.abs(netCashFlow).toLocaleString('en-IN')}</div>
          <div className="text-[11px] text-slate-500 mt-1">Savings rate: {savingsRate}%</div>
        </div>
        <div className="glass-panel p-4 rounded-2xl border border-white/5">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-2"><ShieldCheck className="w-3.5 h-3.5 text-[#ebb2ff]" />Confirmed Balance</div>
          <div className="text-xl font-bold text-[#ebb2ff] font-mono">{currency}{confirmedBalance.toLocaleString('en-IN')}</div>
          <div className="text-[11px] text-slate-500 mt-1">Expected: {currency}{expectedBalance.toLocaleString('en-IN')}</div>
        </div>
      </div>

      {/* AI Insights + Spending */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <div className="flex items-center gap-2"><Sparkles className="w-4 h-4 text-[#ebb2ff]" /><h2 className="text-sm font-bold text-white font-heading">Astra Recommendations</h2></div>
          {aiInsights.length === 0 && <div className="glass-panel p-6 rounded-2xl border border-white/5 text-center text-sm text-slate-500">Add events or income sources to generate insights.</div>}
          {aiInsights.map((ins, i) => (
            <div key={i} className={`p-4 rounded-2xl border flex gap-3 ${insightStyle(ins.type)}`}>
              <InsightIcon t={ins.type} />
              <div><div className="text-xs font-bold mb-0.5">{ins.title}</div><div className="text-[11px] opacity-80">{ins.body}</div></div>
            </div>
          ))}
        </div>
        <div className="space-y-3">
          <div className="flex items-center gap-2"><BarChart3 className="w-4 h-4 text-cyan-400" /><h2 className="text-sm font-bold text-white font-heading">Top Spending Categories</h2></div>
          <div className="glass-panel p-5 rounded-2xl border border-white/5 space-y-3">
            {sortedCategories.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No expense events yet. Ingest a bank statement to see your spending breakdown.</p>
            ) : sortedCategories.map(([cat, amt]) => (
              <div key={cat}>
                <div className="flex justify-between text-xs mb-1"><span className="text-slate-300 capitalize">{cat}</span><span className="text-white font-mono">{currency}{amt.toLocaleString('en-IN')}</span></div>
                <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden"><div className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-[#b600f8]" style={{ width: `${(amt / maxCatAmount) * 100}%` }} /></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Summary Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel p-5 rounded-2xl border border-white/5 space-y-2">
          <div className="flex items-center gap-2 mb-1"><Target className="w-4 h-4 text-[#ebb2ff]" /><h3 className="text-sm font-bold text-white font-heading">Goals Summary</h3></div>
          <div className="flex justify-between text-xs"><span className="text-slate-400">Total</span><span className="text-white font-mono">{goals.length}</span></div>
          <div className="flex justify-between text-xs"><span className="text-slate-400">Active</span><span className="text-amber-300 font-mono">{activeGoals}</span></div>
          <div className="flex justify-between text-xs"><span className="text-slate-400">Completed</span><span className="text-emerald-300 font-mono">{completedGoals}</span></div>
          {goals.length === 0 && <p className="text-[11px] text-slate-500 pt-1">No goals set yet.</p>}
        </div>
        <div className="glass-panel p-5 rounded-2xl border border-white/5 space-y-2">
          <div className="flex items-center gap-2 mb-1"><Clock className="w-4 h-4 text-cyan-400" /><h3 className="text-sm font-bold text-white font-heading">Ledger Health</h3></div>
          <div className="flex justify-between text-xs"><span className="text-slate-400">Total events</span><span className="text-white font-mono">{events.length}</span></div>
          <div className="flex justify-between text-xs"><span className="text-slate-400">Confirmed</span><span className="text-emerald-300 font-mono">{confirmedEvents.length}</span></div>
          <div className="flex justify-between text-xs"><span className="text-slate-400">Pending review</span><span className="text-amber-300 font-mono">{pendingEvents.length}</span></div>
          <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden mt-1"><div className="h-full rounded-full bg-emerald-400" style={{ width: events.length > 0 ? `${(confirmedEvents.length / events.length) * 100}%` : '0%' }} /></div>
        </div>
        <div className="glass-panel p-5 rounded-2xl border border-white/5 space-y-2">
          <div className="flex items-center gap-2 mb-1"><ShieldCheck className="w-4 h-4 text-emerald-400" /><h3 className="text-sm font-bold text-white font-heading">Income Reliability</h3></div>
          <div className="flex justify-between text-xs"><span className="text-slate-400">Sources tracked</span><span className="text-white font-mono">{incomeSources.length}</span></div>
          <div className="flex justify-between text-xs"><span className="text-slate-400">Avg reliability</span>
            <span className={`font-mono font-bold ${avgReliability >= 75 ? 'text-emerald-300' : avgReliability >= 50 ? 'text-amber-300' : 'text-rose-300'}`}>{avgReliability.toFixed(0)}%</span>
          </div>
          {incomeSources.length === 0 && <p className="text-[11px] text-slate-500 pt-1">No income sources registered yet.</p>}
          {incomeSources.length > 0 && <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden mt-1"><div className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400" style={{ width: `${avgReliability}%` }} /></div>}
        </div>
      </div>
    </div>
  );
};
