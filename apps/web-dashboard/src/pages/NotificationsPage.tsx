import { useState, useEffect } from "react";
import { Bell, CheckCircle2, XCircle, RefreshCw, ExternalLink, Loader2 } from "lucide-react";
import { getNotifications, retryNotification, type Notification } from "../lib/api";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [retrying, setRetrying] = useState<number | null>(null);

  const fetchNotifications = () => {
    setLoading(true);
    getNotifications()
      .then(setNotifications)
      .catch(() => setNotifications([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchNotifications(); }, []);

  const handleRetry = async (id: number) => {
    setRetrying(id);
    try {
      await retryNotification(id);
      // Optimistically update the UI
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, failure_reason: "Queued for retry..." } : n));
    } catch {
      // ignore
    } finally {
      setRetrying(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Notification History</h1>
          <p className="text-muted-foreground mt-1">Track all security alerts sent to open-source maintainers.</p>
        </div>
        <button
          onClick={fetchNotifications}
          className="flex items-center gap-2 px-4 py-2 rounded-xl border border-border/50 bg-card text-sm hover:bg-muted transition-colors"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-24 text-muted-foreground">
          <Loader2 size={24} className="animate-spin mr-3" /> Loading notifications...
        </div>
      ) : notifications.length === 0 ? (
        <div className="text-center py-24 flex flex-col items-center gap-3 text-muted-foreground">
          <Bell size={40} className="opacity-20" />
          <p className="text-lg font-medium">No notifications sent yet.</p>
          <p className="text-sm">When the Issue Creator sends GitHub issues, they'll appear here.</p>
        </div>
      ) : (
        <div className="border border-border/40 rounded-2xl overflow-hidden bg-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border/40 bg-muted/30">
                <th className="text-left px-5 py-3.5 font-medium text-muted-foreground">Status</th>
                <th className="text-left px-5 py-3.5 font-medium text-muted-foreground">CVE ID</th>
                <th className="text-left px-5 py-3.5 font-medium text-muted-foreground">Repository</th>
                <th className="text-left px-5 py-3.5 font-medium text-muted-foreground">GitHub Issue</th>
                <th className="text-left px-5 py-3.5 font-medium text-muted-foreground">Detail</th>
                <th className="px-5 py-3.5" />
              </tr>
            </thead>
            <tbody>
              {notifications.map((n) => (
                <tr key={n.id} className="border-b border-border/20 hover:bg-muted/20 transition-colors">
                  <td className="px-5 py-4">
                    {n.success ? (
                      <span className="flex items-center gap-1.5 text-emerald-400">
                        <CheckCircle2 size={15} /> Success
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 text-rose-400">
                        <XCircle size={15} /> Failed
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-4 font-mono text-xs font-semibold">{n.cve_id}</td>
                  <td className="px-5 py-4 text-muted-foreground text-xs truncate max-w-[200px]">
                    {n.repository_url.replace("https://github.com/", "")}
                  </td>
                  <td className="px-5 py-4">
                    {n.github_issue_url ? (
                      <a href={n.github_issue_url} target="_blank" rel="noopener noreferrer"
                         className="flex items-center gap-1 text-primary hover:underline text-xs">
                        View Issue <ExternalLink size={11} />
                      </a>
                    ) : (
                      <span className="text-muted-foreground text-xs">—</span>
                    )}
                  </td>
                  <td className="px-5 py-4 text-xs text-muted-foreground">{n.failure_reason || "—"}</td>
                  <td className="px-5 py-4">
                    {!n.success && (
                      <button
                        onClick={() => handleRetry(n.id)}
                        disabled={retrying === n.id}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/10 text-primary text-xs font-medium hover:bg-primary/20 transition-colors disabled:opacity-50"
                      >
                        {retrying === n.id ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
                        Retry
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
