import React, { useState, useRef } from "react";
import { Upload, FileText, CheckCircle2, AlertTriangle, Loader2, ShieldCheck, X } from "lucide-react";

export const FileUploadScanner = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [status, setStatus] = useState<"idle" | "scanning" | "result">("idle");
  const [fileName, setFileName] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => setIsDragging(false);

  const [scanResult, setScanResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (file: File) => {
    setFileName(file.name);
    setStatus("scanning");
    setError(null);
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8006/api/v1/security/scan-file", {
        method: "POST",
        body: formData,
      });
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Scan failed");
      }
      
      const result = await response.json();
      setScanResult(result);
      setStatus("result");
    } catch (err: any) {
      console.error(err);
      setError(err.message);
      setStatus("idle");
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const reset = () => {
    setStatus("idle");
    setFileName("");
    setScanResult(null);
    setError(null);
  };

  return (
    <div className="bg-card border border-border/40 rounded-2xl p-6 shadow-sm relative overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold flex items-center gap-2">
          <Upload size={18} className="text-primary" /> Live VirusTotal Scan
        </h3>
        {status !== "idle" && (
          <button onClick={reset} className="text-muted-foreground hover:text-foreground">
            <X size={16} />
          </button>
        )}
      </div>

      {error && (
        <div className="p-3 mb-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs flex items-center gap-2">
          <AlertTriangle size={14} /> {error}
        </div>
      )}

      {status === "idle" && (
        <div
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center gap-3 cursor-pointer transition-all duration-300 ${
            isDragging ? "border-primary bg-primary/5 scale-[0.98]" : "border-border/60 hover:border-primary/40 hover:bg-muted/50"
          }`}
        >
          <input 
            type="file" 
            ref={fileInputRef} 
            className="hidden" 
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            accept=".json,.txt,.xml,.yml,.com,.exe"
          />
          <div className="p-3 rounded-full bg-primary/10 text-primary">
            <FileText size={24} />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium">Drop any file to scan</p>
            <p className="text-xs text-muted-foreground mt-1">Real-time analysis via VirusTotal API</p>
          </div>
        </div>
      )}

      {status === "scanning" && (
        <div className="py-10 flex flex-col items-center justify-center gap-4 animate-in fade-in zoom-in duration-300">
          <div className="relative">
            <Loader2 size={48} className="text-primary animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center">
              <ShieldCheck size={20} className="text-primary" />
            </div>
          </div>
          <div className="text-center">
            <p className="text-sm font-bold tracking-tight">Analyzing {fileName}...</p>
            <p className="text-xs text-muted-foreground mt-1">Hashing and checking VirusTotal Global Intel</p>
          </div>
        </div>
      )}

      {status === "result" && scanResult && (
        <div className="animate-in slide-in-from-bottom-2 duration-500">
          <div className={`p-4 rounded-xl mb-4 border ${
            scanResult.detected 
              ? "bg-rose-500/10 border-rose-500/20" 
              : "bg-emerald-500/10 border-emerald-500/20"
          }`}>
            <div className="flex gap-3">
              {scanResult.detected ? (
                <AlertTriangle className="text-rose-500 shrink-0" size={20} />
              ) : (
                <ShieldCheck className="text-emerald-500 shrink-0" size={20} />
              )}
              <div>
                <p className={`text-sm font-bold ${scanResult.detected ? "text-rose-500" : "text-emerald-500"}`}>
                  {scanResult.detected ? "Malicious Content Detected!" : "No Threats Found"}
                </p>
                <p className="text-xs opacity-80 mt-1">
                  {scanResult.detected 
                    ? `VirusTotal flagged this file with ${scanResult.malicious_count} detections.` 
                    : "This file fingerprint is recognized as safe by VirusTotal."}
                </p>
              </div>
            </div>
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border border-border/40 text-xs">
              <span className="font-mono text-[10px] truncate max-w-[200px]" title={scanResult.hash}>{scanResult.hash}</span>
              <span className={`font-bold ${scanResult.detected ? "text-rose-500" : "text-emerald-500"}`}>
                {scanResult.detected ? "DANGEROUS" : "SECURE"}
              </span>
            </div>

            {/* VirusTotal Intel Section */}
            <div className="p-4 rounded-xl border border-border/40 bg-muted/30 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-1">
                  <ShieldCheck size={12} className={scanResult.detected ? "text-rose-500" : "text-emerald-500"} /> 
                  VirusTotal Live Intel
                </span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  scanResult.detected ? "bg-rose-500 text-white" : "bg-emerald-500 text-white"
                }`}>
                  {scanResult.malicious_count || 0} / {scanResult.total_engines || 0} Engines
                </span>
              </div>
              
              {scanResult.detected && scanResult.details && (
                <div className="space-y-1.5 border-t border-border/20 pt-2">
                  {Object.entries(scanResult.details)
                    .filter(([_, r]: any) => r.category === "malicious")
                    .slice(0, 3)
                    .map(([engine, result]: any) => (
                      <div key={engine} className="flex items-center justify-between text-[10px]">
                        <span className="text-muted-foreground">{engine}</span>
                        <span className="font-mono text-rose-400">{result.result}</span>
                      </div>
                    ))}
                </div>
              )}
            </div>

            {scanResult.detected && (
              <a 
                href="/remediation" 
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:opacity-90 transition-opacity shadow-lg shadow-primary/20"
              >
                Get AI Antidote
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
