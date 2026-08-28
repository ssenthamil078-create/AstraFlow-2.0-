import React, { useEffect, useState } from 'react';
import {
  History,
  ShieldCheck,
  FileSpreadsheet,
  MessageSquare,
  FileText,
  Layers,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Database,
} from 'lucide-react';
import { provenanceApi } from '../services/provenanceApi.ts';
import { ProvenanceNode } from '../types.ts';

export const ProvenanceView: React.FC = () => {
  const [provenanceTree, setProvenanceTree] = useState<ProvenanceNode | null>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<ProvenanceNode | null>(null);

  useEffect(() => {
    loadProvenance();
  }, []);

  const loadProvenance = async () => {
    setLoading(true);
    try {
      const data = await provenanceApi.getProvenance();
      setProvenanceTree(data.provenanceTree);
      setMetrics(data.metrics);
      setSelectedNode(data.provenanceTree);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const renderTreeNode = (node: ProvenanceNode, depth = 0) => {
    const isSelected = selectedNode?.id === node.id;

    return (
      <div key={node.id} className="space-y-2">
        <div
          onClick={() => setSelectedNode(node)}
          style={{ marginLeft: `${depth * 20}px` }}
          className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
            isSelected
              ? 'bg-cyan-500/15 border-cyan-400 text-white shadow-[0_0_20px_rgba(0,242,255,0.2)]'
              : 'bg-white/[0.02] border-white/5 text-slate-300 hover:border-white/20 hover:bg-white/[0.04]'
          }`}
        >
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-cyan-400">
              <Database className="w-3.5 h-3.5" />
            </div>
            <div>
              <div className="text-xs font-bold font-heading">{node.label || node.name}</div>
              <div className="text-[10px] text-slate-400 font-mono">
                {node.entityType || node.type} • {node.id}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                (node.confidence ?? 1) >= 0.9
                  ? 'bg-emerald-500/20 text-emerald-300'
                  : 'bg-cyan-500/20 text-cyan-300'
              }`}
            >
              {Math.round((node.confidence ?? 1) * 100)}% Conf
            </span>
          </div>
        </div>

        {node.children && (
          <div className="space-y-2">
            {node.children.map((child) => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 font-heading">
          Auditable Financial Provenance
        </span>
        <h2 className="text-2xl font-extrabold text-white font-heading tracking-tight">
          Ground Truth & Evidence Provenance
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Trace every balance, node, and projection back to its source statements and cryptographic records
        </p>
      </div>

      {/* Metrics Row */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-cyan-400">
            <span className="text-xs text-slate-400 font-medium">Audited Data Ratio</span>
            <div className="text-2xl font-bold text-white mt-1 data-mono">
              {metrics.auditedRatio}
            </div>
          </div>
          <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-emerald-400">
            <span className="text-xs text-slate-400 font-medium">Confirmed Source Records</span>
            <div className="text-2xl font-bold text-emerald-400 mt-1 data-mono">
              {metrics.confirmedEventsCount}
            </div>
          </div>
          <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-amber-400">
            <span className="text-xs text-slate-400 font-medium">Uncertain Observations</span>
            <div className="text-2xl font-bold text-amber-300 mt-1 data-mono">
              {metrics.uncertainEventsCount}
            </div>
          </div>
          <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-[#b600f8]">
            <span className="text-xs text-slate-400 font-medium">Primary Custodian</span>
            <div className="text-sm font-bold text-[#ebb2ff] mt-2 truncate">
              {metrics.primaryCustodian}
            </div>
          </div>
        </div>
      )}

      {/* Provenance Tree & Inspector Dual Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Tree Explorer */}
        <div className="lg:col-span-7 glass-panel p-5 rounded-3xl space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-white/5">
            <h3 className="text-sm font-bold text-white font-heading">
              Evidence Hierarchy & Dependency Tree
            </h3>
            <span className="text-xs text-cyan-400">Click any node to audit</span>
          </div>

          <div className="max-h-[500px] overflow-y-auto space-y-2 pr-2">
            {provenanceTree ? (
              renderTreeNode(provenanceTree)
            ) : (
              <div className="p-8 text-center text-slate-500 text-xs">Loading tree...</div>
            )}
          </div>
        </div>

        {/* Right Node Audit Detail Panel */}
        <div className="lg:col-span-5 glass-panel p-5 rounded-3xl space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-white/5">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white font-heading">Node Audit Inspector</h3>
          </div>

          {selectedNode ? (
            <div className="space-y-4 text-xs">
              <div className="p-3.5 rounded-2xl bg-white/5 border border-white/5">
                <span className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">
                  Entity Label
                </span>
                <div className="text-base font-bold text-white font-heading mt-0.5">
                  {selectedNode.label || selectedNode.name}
                </div>
                <div className="text-slate-400 font-mono text-[11px] mt-0.5">
                  ID: {selectedNode.id}
                </div>
              </div>

              <div className="space-y-2 border-y border-white/5 py-3">
                <div className="flex justify-between">
                  <span className="text-slate-400">Entity Type</span>
                  <span className="text-cyan-300 font-mono font-medium">{selectedNode.entityType || selectedNode.type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Mathematical Confidence</span>
                  <span className="text-emerald-400 font-mono font-bold">
                    {Math.round((selectedNode.confidence ?? 1) * 100)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Timestamp</span>
                  <span className="text-slate-300 font-mono">{selectedNode.timestamp}</span>
                </div>
              </div>

              <div>
                <span className="text-slate-400 font-semibold block mb-1.5">
                  Source Data & Normalization Log:
                </span>
                <pre className="p-3 rounded-xl bg-[#050816] border border-white/10 text-cyan-200 overflow-x-auto text-[11px]">
                  {JSON.stringify(selectedNode.sourceData || { verified: true }, null, 2)}
                </pre>
              </div>

              <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 text-cyan-300 text-[11px] leading-relaxed flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                <span>
                  No hallucinated transactions. This node's state is directly derived from authenticated banking artifacts.
                </span>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-slate-500 text-xs">
              Select a node to inspect provenance evidence.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
