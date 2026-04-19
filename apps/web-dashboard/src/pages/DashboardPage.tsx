import { useState, useEffect } from "react";
import { ShieldAlert, Package, Globe, AlertTriangle, TrendingUp, Activity, Zap, Sparkles } from "lucide-react";
import { getAffectedRepos, type AffectedRepo } from "../lib/api";

const SEVERITY_COLOR: Record<string, string> = {
  Critical: "bg-rose-500/10 text-rose-400 border-rose-500/30",
  High: "bg-orange-500/10 text-orange-400 border-orange-500/30",
  Medium: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  Low: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
};

function scoreToTier(score: number): string {
  if (score >= 9) return "Critical";
  if (score >= 7) return "High";
  if (score >= 4) return "Medium";
  return "Low";
}

const StatCard = ({ title, value, icon: Icon, trend, color }: any) => (
  <div className="p-6 bg-card border border-border/40 rounded-2xl shadow-sm hover:shadow-lg hover:border-primary/30 transition-all duration-300 group">
    <div className="flex items-center justify-between mb-4">
      <div className={`p-2.5 rounded-xl ${color || "bg-primary/10 text-primary"} transition-transform group-hover:scale-110`}>
        <Icon size={22} />
      </div>
      {trend !== undefined && (
        <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${
          trend > 0 ? "bg-rose-500/10 text-rose-400 border-rose-500/20" :
          trend < 0 ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
          "bg-muted text-muted-foreground border-border"
        }`}>
          {trend > 0 ? "+" : ""}{trend}%
        </span>
      )}
    </div>
    <p className="text-sm text-muted-foreground">{title}</p>
    <h3 className="text-2xl font-bold mt-1 tracking-tight">{value}</h3>
  </div>
);

const ScoreBar = ({ score }: { score: number }) => {
  const tier = scoreToTier(score);
  const colors: Record<string, string> = {
    Critical: "bg-rose-500",
    High: "bg-orange-500",
    Medium: "bg-yellow-500",
    Low: "bg-emerald-500",
  };
  return (
    <div className="flex items-center gap-3 w-full">
      <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${colors[tier]}`} style={{ width: `${(score / 10) * 100}%` }} />
      </div>
      <span className="text-sm font-semibold tabular-nums w-8 text-right">{score.toFixed(1)}</span>
    </div>
  );
};

export default function DashboardPage() {
  const [liveRepos, setLiveRepos] = useState<AffectedRepo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAffectedRepos("CVE-2026-9999", 0, 10)
      .then(setLiveRepos)
      .catch(() => setLiveRepos([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Security Overview</h1>
          <p className="text-muted-foreground mt-1">Monitor vulnerability propagation across your dependency graph in real-time.</p>
        </div>
        <div className="flex items-center gap-3">
          <a 
            href="/remediation" 
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 transition-all shadow-lg shadow-primary/20"
          >
            <Sparkles size={16} />
            Remediation Hub
          </a>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Live
          </div>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard title="Active CVEs" value="1,284" icon={ShieldAlert} trend={12} color="bg-rose-500/10 text-rose-400" />
        <StatCard title="Affected Packages" value="8,432" icon={Package} trend={-3} color="bg-orange-500/10 text-orange-400" />
        <StatCard title="Monitored Repos" value="452" icon={Globe} trend={5} color="bg-blue-500/10 text-blue-400" />
        <StatCard title="Critical Findings" value="42" icon={AlertTriangle} trend={0} color="bg-purple-500/10 text-purple-400" />
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Live Feed */}
        <div className="lg:col-span-3 p-6 bg-card border border-border/40 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Activity size={18} className="text-primary" /> Recent Propagation Events
            </h3>
          </div>
          <div className="space-y-4">
            {[
              { cve: "CVE-2026-9999", pkg: "core-dependency-lib@2.4.4", repos: 12, time: "Just now", tier: "Critical" },
              { cve: "CVE-2024-8779", pkg: "express@4.18.2", repos: 143, time: "2m ago", tier: "Critical" },
              { cve: "CVE-2024-6119", pkg: "openssl@3.1.0", repos: 89, time: "11m ago", tier: "High" },
              { cve: "CVE-2024-3094", pkg: "xz-utils@5.6.0", repos: 34, time: "25m ago", tier: "Critical" },
            ].map((item) => (
              <div key={item.cve} className="flex items-center gap-4 p-3 rounded-xl hover:bg-muted/40 transition-colors cursor-pointer">
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${SEVERITY_COLOR[item.tier]}`}>{item.tier}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{item.cve} — <span className="text-muted-foreground font-mono text-xs">{item.pkg}</span></p>
                  <p className="text-xs text-muted-foreground mt-0.5">Propagated to <strong>{item.repos}</strong> repos · {item.time}</p>
                </div>
                <Zap size={14} className="text-muted-foreground shrink-0" />
              </div>
            ))}
          </div>
        </div>

        {/* Scored Repos Live from API */}
        <div className="lg:col-span-2 p-6 bg-card border border-border/40 rounded-2xl shadow-sm">
          <div className="flex items-center gap-2 mb-6">
            <TrendingUp size={18} className="text-primary" />
            <h3 className="text-lg font-semibold">Live Scored Repos</h3>
          </div>
          {loading ? (
            <div className="space-y-3">
              {[1,2,3].map(i => <div key={i} className="h-12 rounded-xl bg-muted animate-pulse" />)}
            </div>
          ) : liveRepos.length === 0 ? (
            <div className="text-sm text-muted-foreground text-center py-12 flex flex-col items-center gap-2">
              <ShieldAlert size={32} className="text-muted-foreground/40" />
              <p>No scored repos yet.<br/>Trigger a CVE to see live results.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {liveRepos.map(repo => (
                <div key={repo.id} className="space-y-1.5">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium truncate max-w-[160px]" title={repo.repository_url}>
                      {repo.repository_url.replace("https://github.com/", "")}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${SEVERITY_COLOR[scoreToTier(repo.propex_score)]}`}>
                      {scoreToTier(repo.propex_score)}
                    </span>
                  </div>
                  <ScoreBar score={repo.propex_score} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Security Health Chart */}
      <div className="p-6 bg-card border border-border/40 rounded-2xl shadow-sm">
        <h3 className="text-lg font-semibold mb-6">Resolution Activity (7-day)</h3>
        <div className="flex items-end gap-2 h-28">
          {[40, 65, 45, 90, 85, 100, 78].map((h, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-2">
              <div
                className="w-full bg-primary/20 hover:bg-primary/50 rounded-t-md transition-all duration-300 cursor-pointer"
                style={{ height: `${h}%` }}
              />
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-3 text-xs text-muted-foreground">
          {["Mon","Tue","Wed","Thu","Fri","Sat","Sun"].map(d => <span key={d}>{d}</span>)}
        </div>
      </div>
    </div>
  );
}
