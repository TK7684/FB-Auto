"use client";

import React, { useState } from "react";
import {
  FileUp,
  Zap,
  ShieldCheck,
  History,
  Settings,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Download,
  Loader2,
  Trash2
} from "lucide-react";
import axios from "axios";
import { cn } from "@/lib/utils";

const API_BASE = "http://localhost:8001";

interface FixResult {
  filename: string;
  output_url: string;
  fixes: string[];
  row_count: number;
  processing_time: number;
}

export default function Dashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [platform, setPlatform] = useState("tiktok");
  const [repairRows, setRepairRows] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<FixResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"fast" | "advanced">("fast");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const runFastFix = async () => {
    if (!file) return;
    setIsProcessing(true);
    setResult(null);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("platform", platform);
    formData.append("repair_rows", String(repairRows));

    try {
      const response = await axios.post(`${API_BASE}/fast-fix`, formData);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to process file");
    } finally {
      setIsProcessing(false);
    }
  };

  const runAdvancedFix = async () => {
    if (!file) return;
    setIsProcessing(true);
    setResult(null);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("platform", platform);
    formData.append("column_names", "true");
    formData.append("timestamps", "true");
    formData.append("column_count", "true");
    formData.append("use_fast_mode", "true");

    try {
      const response = await axios.post(`${API_BASE}/fix`, formData);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to process file");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <main className="min-h-screen bg-background p-4 md:p-8">
      <div className="mx-auto max-w-5xl">
        {/* Header */}
        <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="inline-block px-3 py-1 bg-cta text-white font-bold text-xs uppercase tracking-widest border-2 border-slate-900 mb-2 rotate-[-2deg]">
              Version 2.0 Pro Max
            </div>
            <h1 className="text-5xl md:text-7xl font-bold tracking-tighter text-text">
              CSV <span className="text-primary underline decoration-slate-900 underline-offset-8 decoration-4">FIXER</span>
            </h1>
            <p className="mt-4 text-text-muted text-lg max-w-xl font-medium">
              Elite header manipulation and data cleaning for TikTok & Shopee BigQuery exports.
            </p>
          </div>

          <div className="flex gap-3">
            <button className="p-3 block-card rounded-none bg-white text-slate-900 hover:bg-slate-50">
              <History size={24} />
            </button>
            <button className="p-3 block-card rounded-none bg-white text-slate-900 hover:bg-slate-50">
              <Settings size={24} />
            </button>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Main Controls */}
          <div className="lg:col-span-8 space-y-8">

            {/* File Upload Area */}
            <div className={cn(
              "block-card p-8 bg-white relative overflow-hidden transition-colors",
              file ? "border-primary" : "border-slate-900"
            )}>
              <div className="absolute top-0 right-0 w-32 h-32 bg-secondary opacity-5 rotate-45 translate-x-16 -translate-y-16" />

              <div className="flex flex-col items-center justify-center border-4 border-dashed border-slate-100 rounded-none p-12 text-center relative z-10">
                <FileUp size={64} className={cn("mb-4", file ? "text-primary" : "text-slate-300")} />
                <h3 className="text-2xl font-bold mb-2">
                  {file ? file.name : "Drop your export here"}
                </h3>
                <p className="text-text-muted mb-6">
                  {file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : "Supports TikTok & Shopee CSV exports"}
                </p>

                <label className="btn-primary cursor-pointer inline-flex items-center gap-2">
                  <input type="file" className="hidden" accept=".csv" onChange={handleFileChange} />
                  {file ? "Change File" : "Select File"}
                  <ArrowRight size={20} />
                </label>

                {file && (
                  <button
                    onClick={() => setFile(null)}
                    className="mt-4 text-red-500 font-bold text-sm hover:underline flex items-center gap-1"
                  >
                    <Trash2 size={16} /> Remove
                  </button>
                )}
              </div>
            </div>

            {/* Platform & Options */}
            <div className="block-card p-0 bg-white grid grid-cols-1 md:grid-cols-2">
              <div className="p-6 border-b md:border-b-0 md:border-r border-slate-900">
                <h4 className="flex items-center gap-2 text-lg font-bold mb-4">
                  <ShieldCheck size={20} className="text-primary" /> Target Platform
                </h4>
                <div className="flex flex-wrap gap-3">
                  {["tiktok", "shopee"].map((p) => (
                    <button
                      key={p}
                      onClick={() => setPlatform(p)}
                      className={cn(
                        "px-6 py-2 border-2 text-sm font-bold uppercase tracking-wider transition-all",
                        platform === p
                          ? "bg-slate-900 text-white border-slate-900"
                          : "bg-white text-slate-900 border-slate-200 hover:border-slate-900"
                      )}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-6">
                <h4 className="flex items-center gap-2 text-lg font-bold mb-4">
                  <Zap size={20} className="text-cta" /> Quick Options
                </h4>
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <input
                      type="checkbox"
                      className="w-5 h-5 border-2 border-slate-900 accent-cta"
                      checked={repairRows}
                      onChange={(e) => setRepairRows(e.target.checked)}
                    />
                    <span className="font-bold text-sm group-hover:text-cta transition-colors">
                      Repair Column Count (Recommended)
                    </span>
                  </label>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col md:flex-row gap-4">
              <button
                onClick={runFastFix}
                disabled={!file || isProcessing}
                className={cn(
                  "flex-1 btn-cta flex items-center justify-center gap-3 text-xl py-6",
                  (!file || isProcessing) && "opacity-50 cursor-not-allowed grayscale"
                )}
              >
                {isProcessing ? <Loader2 className="animate-spin" /> : <Zap size={24} />}
                Fast Header Fix
              </button>

              <button
                onClick={runAdvancedFix}
                disabled={!file || isProcessing}
                className={cn(
                  "flex-1 btn-primary flex items-center justify-center gap-3 text-xl py-6",
                  (!file || isProcessing) && "opacity-50 cursor-not-allowed grayscale"
                )}
              >
                {isProcessing ? <Loader2 className="animate-spin" /> : <ShieldCheck size={24} />}
                Advanced Clean
              </button>
            </div>
          </div>

          {/* Results & Info */}
          <div className="lg:col-span-4 space-y-8">
            <div className="block-card p-6 bg-slate-900 text-white">
              <h4 className="flex items-center gap-2 text-lg font-bold mb-4">
                <History size={20} className="text-secondary" /> Processing Log
              </h4>

              {isProcessing ? (
                <div className="py-12 flex flex-col items-center">
                  <Loader2 className="animate-spin text-secondary mb-4" size={48} />
                  <p className="font-bold animate-pulse">Analyzing structures...</p>
                </div>
              ) : result ? (
                <div className="space-y-4">
                  <div className="flex items-start gap-3 p-3 bg-white/10 border border-white/20">
                    <CheckCircle2 className="text-green-400 shrink-0" size={24} />
                    <div>
                      <p className="font-bold">Success!</p>
                      <p className="text-sm text-white/60">{result.row_count === -1 ? "Processed (Streaming)" : `${result.row_count} rows cleaned`}</p>
                    </div>
                  </div>

                  <ul className="text-xs space-y-2 opacity-80 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                    {result.fixes.map((f, i) => (
                      <li key={i} className="flex gap-2">
                        <span className="text-secondary">✓</span> {f}
                      </li>
                    ))}
                  </ul>

                  <a
                    href={`${API_BASE}${result.output_url}`}
                    className="block w-full py-4 bg-secondary text-slate-900 font-black text-center border-2 border-white shadow-[4px_4px_0px_0px_rgba(255,255,255,1)] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(255,255,255,1)] transition-all flex items-center justify-center gap-2"
                  >
                    <Download size={20} /> DOWNLOAD CSV
                  </a>
                </div>
              ) : error ? (
                <div className="flex items-start gap-3 p-4 bg-red-500/20 border border-red-500/50 text-red-100">
                  <AlertCircle className="shrink-0" size={24} />
                  <div>
                    <p className="font-bold">Process Failed</p>
                    <p className="text-sm opacity-80">{error}</p>
                  </div>
                </div>
              ) : (
                <div className="py-12 text-center opacity-40">
                  <Loader2 size={48} className="mx-auto mb-4 opacity-20" />
                  <p className="font-medium">Ready for input</p>
                </div>
              )}
            </div>

            <div className="block-card p-6 bg-white">
              <h4 className="text-sm font-bold uppercase tracking-widest text-text-muted mb-4 border-b border-slate-100 pb-2">
                System Stats
              </h4>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-bold">Fast Mode</span>
                  <span className="px-2 py-1 bg-green-100 text-green-700 text-[10px] font-black uppercase">Active</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-bold">BigQuery Ready</span>
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 text-[10px] font-black uppercase">Verified</span>
                </div>
                <div className="pt-4 border-t border-slate-100">
                  <p className="text-[10px] text-text-muted leading-relaxed">
                    Powered by Antigravity core fixers. Replaces headers, fixes timestamps, and repairs column counts for seamless ETL imports.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
