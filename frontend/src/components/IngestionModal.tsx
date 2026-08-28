import React, { useState, useRef, useCallback } from "react";
import {
  X, Upload, FileSpreadsheet, MessageSquare, FileText,
  CheckCircle2, AlertCircle, Loader2, CloudUpload, File,
} from "lucide-react";
import { ingestionApi } from "../services/ingestionApi.ts";
import { IngestionBatchResult } from "../types.ts";

interface IngestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (result: IngestionBatchResult) => void;
}

type Tab = "csv" | "sms" | "pdf";

interface FileDropZoneProps {
  accept: string;
  label: string;
  hint: string;
  icon: React.ReactNode;
  file: File | null;
  onFile: (f: File) => void;
}

const FileDropZone: React.FC<FileDropZoneProps> = ({ accept, label, hint, icon, file, onFile }) => {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) onFile(f);
  }, [onFile]);

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={`relative cursor-pointer rounded-2xl border-2 border-dashed transition-all p-8 flex flex-col items-center justify-center gap-3 text-center
        ${dragging ? "border-cyan-400 bg-cyan-400/10" : file ? "border-emerald-500/50 bg-emerald-500/5" : "border-white/15 hover:border-cyan-400/50 hover:bg-white/3"}`}
    >
      <input ref={inputRef} type="file" accept={accept} className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f); }} />
      {file ? (
        <>
          <CheckCircle2 className="w-8 h-8 text-emerald-400" />
          <div>
            <p className="text-sm font-semibold text-emerald-300">{file.name}</p>
            <p className="text-xs text-slate-400 mt-0.5">{(file.size / 1024).toFixed(1)} KB — ready to upload</p>
          </div>
        </>
      ) : (
        <>
          <div className="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center">{icon}</div>
          <div>
            <p className="text-sm font-semibold text-slate-200">{label}</p>
            <p className="text-xs text-slate-400 mt-1">{hint}</p>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-cyan-400 font-medium">
            <CloudUpload className="w-3.5 h-3.5" />
            Click or drag & drop
          </div>
        </>
      )}
    </div>
  );
};

export const IngestionModal: React.FC<IngestionModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [tab, setTab] = useState<Tab>("csv");
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [smsFile, setSmsFile] = useState<File | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [processingStage, setProcessingStage] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [batchResult, setBatchResult] = useState<IngestionBatchResult | null>(null);

  const activeFile = tab === "csv" ? csvFile : tab === "sms" ? smsFile : pdfFile;

  const runWithStages = async (fn: () => Promise<IngestionBatchResult>) => {
    setLoading(true);
    setError(null);
    setBatchResult(null);
    setProcessingStage(0);
    const ticker = setInterval(() => setProcessingStage((s) => Math.min(s + 1, 5)), 400);
    try {
      const res = await fn();
      clearInterval(ticker);
      setProcessingStage(5);
      setBatchResult(res);
      onSuccess(res);
    } catch (err: any) {
      clearInterval(ticker);
      setError(err?.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!activeFile) { setError("Please select a file first."); return; }
    if (tab === "csv") await runWithStages(() => ingestionApi.importCsvFile(activeFile));
    else if (tab === "sms") await runWithStages(() => ingestionApi.importSmsFile(activeFile));
    else await runWithStages(() => ingestionApi.uploadDocumentFile(activeFile));
  };

  const handleClose = () => {
    if (!loading) {
      setCsvFile(null); setSmsFile(null); setPdfFile(null);
      setError(null); setBatchResult(null); setProcessingStage(0);
      onClose();
    }
  };

  if (!isOpen) return null;

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "csv", label: "CSV Statement", icon: <FileSpreadsheet className="w-4 h-4" /> },
    { id: "sms", label: "SMS Messages", icon: <MessageSquare className="w-4 h-4" /> },
    { id: "pdf", label: "PDF / Doc", icon: <FileText className="w-4 h-4" /> },
  ];

  const stages = ["Uploading file", "Parsing transactions", "Detecting events", "Checking duplicates", "Updating twin"];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="w-full max-w-lg rounded-3xl overflow-hidden bg-[#070b1f] border border-white/10 shadow-[0_0_60px_rgba(0,242,255,0.15)]">

        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-white/8 bg-[#0a1028]/70">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-cyan-400/15 flex items-center justify-center">
              <Upload className="w-4 h-4 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white font-heading">Upload Financial Data</h3>
              <p className="text-[11px] text-slate-400">Bank statements, SMS, or PDF documents</p>
            </div>
          </div>
          <button onClick={handleClose} className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/8 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-white/8">
          {tabs.map((t) => (
            <button key={t.id} onClick={() => { setTab(t.id); setError(null); setBatchResult(null); }}
              className={`flex-1 flex items-center justify-center gap-2 py-3 text-xs font-semibold transition-all
                ${tab === t.id ? "text-cyan-300 border-b-2 border-cyan-400 bg-cyan-400/5" : "text-slate-400 hover:text-slate-200"}`}>
              {t.icon}{t.label}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">

          {/* Error */}
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Success */}
          {batchResult && (
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-200 text-xs space-y-1">
              <div className="flex items-center gap-2 font-bold text-emerald-300 text-sm">
                <CheckCircle2 className="w-4 h-4" />
                Upload Complete!
              </div>
              <p>Detected <strong>{batchResult.totalDetected}</strong> events</p>
              <div className="flex gap-4 mt-1">
                <span className="text-emerald-400">✓ {batchResult.confirmedCount} confirmed</span>
                <span className="text-amber-400">~ {batchResult.likelyCount} likely</span>
                <span className="text-slate-400">? {batchResult.uncertainCount} uncertain</span>
              </div>
            </div>
          )}

          {/* Processing animation */}
          {loading && (
            <div className="py-8 flex flex-col items-center gap-5">
              <div className="relative w-20 h-20">
                <Loader2 className="w-20 h-20 text-cyan-400/20 animate-spin absolute" />
                <Loader2 className="w-16 h-16 text-cyan-400 animate-spin absolute top-2 left-2" style={{ animationDuration: "0.8s" }} />
                <span className="absolute inset-0 flex items-center justify-center text-cyan-300 font-bold text-sm">{processingStage}/5</span>
              </div>
              <div className="space-y-2 w-full">
                {stages.map((s, i) => (
                  <div key={s} className={`flex items-center gap-3 text-xs transition-colors ${processingStage > i ? "text-cyan-300" : "text-slate-600"}`}>
                    <div className={`w-2 h-2 rounded-full flex-shrink-0 transition-all ${processingStage > i ? "bg-cyan-400 shadow-[0_0_6px_#22d3ee]" : "bg-slate-700"}`} />
                    {String(i + 1).padStart(2, "0")} {s}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Drop Zones */}
          {!loading && !batchResult && (
            <>
              {tab === "csv" && (
                <FileDropZone
                  accept=".csv,text/csv"
                  label="Bank Statement CSV"
                  hint="Export from HDFC, SBI, ICICI, Axis, or any bank — Date, Description, Amount columns"
                  icon={<FileSpreadsheet className="w-6 h-6 text-cyan-400" />}
                  file={csvFile}
                  onFile={setCsvFile}
                />
              )}
              {tab === "sms" && (
                <FileDropZone
                  accept=".txt,text/plain"
                  label="SMS Messages (.txt)"
                  hint="Save your bank SMS alerts as a .txt file — one SMS per line"
                  icon={<MessageSquare className="w-6 h-6 text-[#ebb2ff]" />}
                  file={smsFile}
                  onFile={setSmsFile}
                />
              )}
              {tab === "pdf" && (
                <FileDropZone
                  accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/*"
                  label="PDF Statement or Receipt"
                  hint="Upload a bank e-statement PDF, invoice, or receipt image for OCR extraction"
                  icon={<FileText className="w-6 h-6 text-amber-400" />}
                  file={pdfFile}
                  onFile={setPdfFile}
                />
              )}
            </>
          )}

          {/* Format hints */}
          {!loading && !batchResult && (
            <div className="p-3 rounded-xl bg-white/3 border border-white/8 text-[11px] text-slate-400 leading-relaxed">
              {tab === "csv" && <><strong className="text-slate-300">CSV format:</strong> Date, Description, Amount, Type (CREDIT/DEBIT), Category</>}
              {tab === "sms" && <><strong className="text-slate-300">SMS format:</strong> One SMS per line e.g. "HDFC Bank: Rs 1,85,000 credited to a/c **4102 on 01-Aug-2026"</>}
              {tab === "pdf" && <><strong className="text-slate-300">Supported:</strong> PDF statements, PNG/JPG receipts, scanned invoices — text is extracted automatically</>}
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-3 pt-1">
            {batchResult ? (
              <button onClick={handleClose} className="flex-1 py-2.5 rounded-xl bg-emerald-500 text-slate-950 font-bold text-sm hover:bg-emerald-400 transition-all">
                Done — View Events
              </button>
            ) : (
              <>
                <button onClick={handleClose} disabled={loading} className="px-5 py-2.5 rounded-xl text-slate-300 hover:text-white border border-white/10 hover:border-white/20 text-sm transition-colors disabled:opacity-40">
                  Cancel
                </button>
                <button onClick={handleUpload} disabled={loading || !activeFile}
                  className="flex-1 py-2.5 rounded-xl bg-cyan-400 text-slate-950 font-bold text-sm hover:bg-cyan-300 transition-all disabled:opacity-40 flex items-center justify-center gap-2">
                  {loading ? <><Loader2 className="w-4 h-4 animate-spin" />Processing...</> : <><Upload className="w-4 h-4" />Upload & Extract Events</>}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
