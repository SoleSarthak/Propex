import { useState } from "react";
import { Search, Filter, ExternalLink, ChevronDown } from "lucide-react";

const MOCK_CVES = [
  { id: "CVE-2024-8779", severity: "Critical", score: 9.8, package: "express", ecosystem: "npm", repos: 143, date: "2024-04-01" },
  { id: "CVE-2024-6119", severity: "High", score: 8.2, package: "openssl", ecosystem: "npm", repos: 89, date: "2024-03-28" },
  { id: "CVE-2024-3094", severity: "Critical", score: 10.0, package: "xz-utils", ecosystem: "pypi", repos: 34, date: "2024-03-29" },
  { id: "CVE-2024-1234", severity: "High", score: 7.5, package: "requests", ecosystem: "pypi", repos: 512, date: "2024-03-15" },
  { id: "CVE-2024-9999", severity: "Medium", score: 5.4, package: "log4j-core", ecosystem: "maven", repos: 201, date: "2024-02-10" },
  { id: "CVE-2023-4863", severity: "Critical", score: 9.6, package: "libwebp", ecosystem: "npm", repos: 67, date: "2023-09-12" },
];

const SEVERITY_STYLE: Record<string, string> = {
  Critical: "bg-rose-500/10 text-rose-400 border-rose-500/30",
  High: "bg-orange-500/10 text-orange-400 border-orange-500/30",
  Medium: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  Low: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
};

const ECOSYSTEM_STYLE: Record<string, string> = {
  npm: "bg-green-500/10 text-green-400",
  pypi: "bg-blue-500/10 text-blue-400",
  maven: "bg-red-500/10 text-red-400",
};

export default function CveListPage() {
  const [search, setSearch] = useState("");
  const [ecosystem, setEcosystem] = useState("all");
  const [severity, setSeverity] = useState("all");

  const filtered = MOCK_CVES.filter(c => {
    const matchSearch = c.id.toLowerCase().includes(search.toLowerCase()) || c.package.toLowerCase().includes(search.toLowerCase());
    const matchEco = ecosystem === "all" || c.ecosystem === ecosystem;
    const matchSev = severity === "all" || c.severity.toLowerCase() === severity;
    return matchSearch && matchEco && matchSev;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">CVE Explorer</h1>
        <p className="text-muted-foreground mt-1">Browse and filter all tracked vulnerabilities across ecosystems.</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search CVE ID or package..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-border/50 bg-card text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition"
          />
        </div>
        <div className="relative">
          <select
            value={ecosystem}
            onChange={e => setEcosystem(e.target.value)}
            className="appearance-none pl-4 pr-10 py-2.5 rounded-xl border border-border/50 bg-card text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 cursor-pointer"
          >
            <option value="all">All Ecosystems</option>
            <option value="npm">npm</option>
            <option value="pypi">PyPI</option>
            <option value="maven">Maven</option>
          </select>
          <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
        </div>
        <div className="relative">
          <select
            value={severity}
            onChange={e => setSeverity(e.target.value)}
            className="appearance-none pl-4 pr-10 py-2.5 rounded-xl border border-border/50 bg-card text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 cursor-pointer"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
        </div>
      </div>

      {/* Table */}
      <div className="border border-border/40 rounded-2xl overflow-hidden bg-card">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border/40 bg-muted/30">
              <th className="text-left px-5 py-3.5 font-medium text-muted-foreground">CVE ID</th>
              <th className="text-left px-5 py-3.5 font-medium text-muted-foreground">Package</th>
              <th className="text-left px-5 py-3.5 font-medium text-muted-foreground">Ecosystem</th>
              <th className="text-left px-5 py-3.5 font-medium text-muted-foreground">Severity</th>
              <th className="text-left px-5 py-3.5 font-medium text-muted-foreground">CVSS</th>
              <th className="text-left px-5 py-3.5 font-medium text-muted-foreground">Affected Repos</th>
              <th className="text-left px-5 py-3.5 font-medium text-muted-foreground">Date</th>
              <th className="px-5 py-3.5" />
            </tr>
          </thead>
          <tbody>
            {filtered.map((cve, i) => (
              <tr key={cve.id} className={`border-b border-border/20 hover:bg-muted/20 transition-colors ${i % 2 === 0 ? "" : "bg-muted/5"}`}>
                <td className="px-5 py-4 font-mono text-xs font-semibold">{cve.id}</td>
                <td className="px-5 py-4 font-medium">{cve.package}</td>
                <td className="px-5 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${ECOSYSTEM_STYLE[cve.ecosystem]}`}>{cve.ecosystem}</span>
                </td>
                <td className="px-5 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${SEVERITY_STYLE[cve.severity]}`}>{cve.severity}</span>
                </td>
                <td className="px-5 py-4 font-semibold tabular-nums">{cve.score}</td>
                <td className="px-5 py-4">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 rounded-full bg-muted overflow-hidden">
                      <div className="h-full bg-primary/60 rounded-full" style={{ width: `${Math.min(100, (cve.repos / 600) * 100)}%` }} />
                    </div>
                    <span className="tabular-nums text-muted-foreground">{cve.repos}</span>
                  </div>
                </td>
                <td className="px-5 py-4 text-muted-foreground">{cve.date}</td>
                <td className="px-5 py-4">
                  <button className="p-1.5 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground">
                    <ExternalLink size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center py-16 text-muted-foreground">
            <Filter size={32} className="mx-auto mb-3 opacity-30" />
            <p>No CVEs match your filters.</p>
          </div>
        )}
      </div>
    </div>
  );
}
