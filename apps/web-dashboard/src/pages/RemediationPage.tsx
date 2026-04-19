import { useState } from "react";
import { Sparkles, GitPullRequest, CheckCircle2, AlertCircle, ArrowRight, Code, Terminal, Bot } from "lucide-react";

export default function RemediationPage() {
  const [isCreating, setIsCreating] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleCreateIssue = () => {
    setIsCreating(true);
    // Simulate API call
    setTimeout(() => {
      setIsCreating(false);
      setIsSuccess(true);
    }, 2000);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div>
        <div className="flex items-center gap-2 text-primary mb-2">
          <Sparkles size={16} />
          <span className="text-xs font-bold uppercase tracking-wider">AI Remediation Hub</span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight">Vulnerability Fix Center</h1>
        <p className="text-muted-foreground mt-1">Gemini AI has analyzed 12 propagation paths and drafted a consolidated patch.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Patch Content */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-card border border-border/40 rounded-2xl overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-border/40 bg-muted/30 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Code size={18} className="text-primary" />
                <span className="font-mono text-sm font-medium">patch_v2.4.5_security_fix.diff</span>
              </div>
              <span className="text-xs text-muted-foreground font-mono">Target: core-dependency-lib</span>
            </div>
            <div className="p-6 font-mono text-sm overflow-x-auto bg-slate-950 text-slate-300">
              <div className="flex gap-4">
                <span className="text-slate-600 select-none">124</span>
                <span className="text-slate-400">  async function processInput(data) {"{"}</span>
              </div>
              <div className="flex gap-4 bg-rose-500/10 -mx-6 px-6">
                <span className="text-rose-500 select-none">-</span>
                <span className="text-rose-400">    const result = eval(data);</span>
              </div>
              <div className="flex gap-4 bg-emerald-500/10 -mx-6 px-6">
                <span className="text-emerald-500 select-none">+</span>
                <span className="text-emerald-400">    const result = JSON.parse(data); // Sanitized via Propex Policy</span>
              </div>
              <div className="flex gap-4">
                <span className="text-slate-600 select-none">126</span>
                <span className="text-slate-400">    return result;</span>
              </div>
              <div className="flex gap-4">
                <span className="text-slate-600 select-none">127</span>
                <span className="text-slate-400">  {"}"}</span>
              </div>
            </div>
          </div>

          <div className="bg-primary/5 border border-primary/20 rounded-2xl p-6">
            <div className="flex gap-4">
              <div className="p-3 rounded-xl bg-primary/10 text-primary h-fit">
                <Bot size={24} />
              </div>
              <div className="space-y-3">
                <h3 className="text-lg font-semibold">Gemini AI Analysis</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  "The vulnerability in <code className="bg-muted px-1 rounded text-primary">core-dependency-lib</code> is caused by unsanitized input reaching an <code className="bg-muted px-1 rounded text-primary">eval()</code> statement. This patch replaces it with a secure JSON parser, which is compatible with all downstream dependents detected in your graph (express, requests, and 8 others)."
                </p>
                <div className="flex flex-wrap gap-2 pt-2">
                  <span className="text-[10px] font-bold bg-white/50 border border-primary/10 px-2 py-0.5 rounded text-primary">No Breaking Changes</span>
                  <span className="text-[10px] font-bold bg-white/50 border border-primary/10 px-2 py-0.5 rounded text-primary">High Confidence (98%)</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Sidebar */}
        <div className="space-y-6">
          <div className="bg-card border border-border/40 rounded-2xl p-6 shadow-sm">
            <h3 className="font-semibold mb-4">Automation Hub</h3>
            <div className="space-y-4">
              <button 
                onClick={handleCreateIssue}
                disabled={isCreating || isSuccess}
                className={`w-full flex items-center justify-center gap-2 py-3 rounded-xl font-medium transition-all ${
                  isSuccess 
                    ? "bg-emerald-500 text-white" 
                    : "bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg shadow-primary/20"
                }`}
              >
                {isCreating ? (
                  <Terminal className="animate-spin" size={18} />
                ) : isSuccess ? (
                  <CheckCircle2 size={18} />
                ) : (
                  <GitPullRequest size={18} />
                )}
                {isCreating ? "Connecting..." : isSuccess ? "Issue Created!" : "Open GitHub Pull Request"}
              </button>
              
              <button className="w-full flex items-center justify-center gap-2 py-3 rounded-xl border border-border bg-card hover:bg-muted transition-colors font-medium">
                <AlertCircle size={18} />
                Flag for Review
              </button>
            </div>
            
            <div className="mt-8 pt-6 border-t border-border/40">
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-4">Downstream Impact</h4>
              <div className="space-y-3">
                {[
                  { name: "Propex-Backend", status: "Critical" },
                  { name: "Auth-Service", status: "High" },
                  { name: "Payment-Gateway", status: "Medium" },
                ].map(item => (
                  <div key={item.name} className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{item.name}</span>
                    <ArrowRight size={12} className="text-muted-foreground/30" />
                    <span className="font-medium text-emerald-500">Fix Ready</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
