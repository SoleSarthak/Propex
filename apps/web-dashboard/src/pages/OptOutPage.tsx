import { useState, useEffect } from "react";
import { ShieldOff, Trash2, Plus, Loader2, Globe } from "lucide-react";
import { listOptOuts, registerOptOut, removeOptOut } from "../lib/api";

export default function OptOutPage() {
  const [repos, setRepos] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);

  const fetchOptOuts = () => {
    listOptOuts()
      .then(data => setRepos(data.opted_out_repositories))
      .catch(() => setRepos([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchOptOuts(); }, []);

  const handleAdd = async () => {
    if (!input.trim()) return;
    setSubmitting(true);
    try {
      await registerOptOut(input.trim());
      setRepos(prev => [...prev, input.trim()]);
      setInput("");
    } catch {
      // Could show a toast here
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemove = async (repoUrl: string) => {
    setRemoving(repoUrl);
    try {
      await removeOptOut(repoUrl);
      setRepos(prev => prev.filter(r => r !== repoUrl));
    } catch {
      // ignore
    } finally {
      setRemoving(null);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Opt-Out Registry</h1>
        <p className="text-muted-foreground mt-1">
          Repositories listed here will never receive automated security issue notifications from Propex.
        </p>
      </div>

      {/* Add Form */}
      <div className="p-6 bg-card border border-border/40 rounded-2xl space-y-4">
        <h3 className="font-semibold flex items-center gap-2"><ShieldOff size={16} /> Add Repository</h3>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Globe size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="https://github.com/owner/repo"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleAdd()}
              className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-border/50 bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition"
            />
          </div>
          <button
            onClick={handleAdd}
            disabled={submitting || !input.trim()}
            className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:bg-primary/90 transition disabled:opacity-50"
          >
            {submitting ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
            Opt Out
          </button>
        </div>
      </div>

      {/* List */}
      <div className="border border-border/40 rounded-2xl overflow-hidden bg-card">
        <div className="px-5 py-3.5 border-b border-border/40 bg-muted/20 flex items-center justify-between">
          <span className="text-sm font-medium text-muted-foreground">Opted-Out Repositories</span>
          <span className="text-xs bg-muted px-2 py-0.5 rounded-full">{repos.length}</span>
        </div>
        {loading ? (
          <div className="flex justify-center py-12 text-muted-foreground">
            <Loader2 size={20} className="animate-spin" />
          </div>
        ) : repos.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">
            <ShieldOff size={32} className="mx-auto mb-3 opacity-20" />
            <p className="text-sm">No repositories opted out yet.</p>
          </div>
        ) : (
          <ul className="divide-y divide-border/20">
            {repos.map(repo => (
              <li key={repo} className="flex items-center justify-between px-5 py-4 hover:bg-muted/20 transition-colors">
                <span className="text-sm text-muted-foreground font-mono">{repo}</span>
                <button
                  onClick={() => handleRemove(repo)}
                  disabled={removing === repo}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-rose-400 hover:bg-rose-500/10 text-xs font-medium transition-colors disabled:opacity-50"
                >
                  {removing === repo ? <Loader2 size={12} className="animate-spin" /> : <Trash2 size={12} />}
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
