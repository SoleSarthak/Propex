// Central API client — connects to the API Gateway at port 8006
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8006";

export interface AffectedRepo {
  id: number;
  cve_id: string;
  repository_url: string;
  target_package: string;
  dependency_depth: number;
  context_type: string;
  popularity_stars: number;
  download_count: number;
  propex_score: number;
  maintainer_status: string;
}

export interface Notification {
  id: number;
  cve_id: string;
  repository_url: string;
  github_issue_url: string | null;
  success: boolean;
  failure_reason: string | null;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

// --- Scoring endpoints ---
export const getAffectedRepos = (cveId: string, skip = 0, limit = 50) =>
  apiFetch<AffectedRepo[]>(`/api/v1/cves/${cveId}/affected-repos?skip=${skip}&limit=${limit}`);

export const getRepoVulnerabilities = (owner: string, name: string) =>
  apiFetch<AffectedRepo[]>(`/api/v1/repos/${owner}/${name}/vulnerabilities`);

export const patchMaintainerStatus = (owner: string, name: string, cveId: string, status: string) =>
  apiFetch<{ message: string }>(`/api/v1/repos/${owner}/${name}/vulnerabilities/${cveId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });

// --- Notification endpoints ---
export const getNotifications = (skip = 0, limit = 50) =>
  apiFetch<Notification[]>(`/api/v1/notifications?skip=${skip}&limit=${limit}`);

export const retryNotification = (id: number) =>
  apiFetch<{ message: string }>(`/api/v1/notifications/${id}/retry`, { method: "POST" });

// --- Opt-out endpoints ---
export const registerOptOut = (repoUrl: string) =>
  apiFetch<{ message: string }>("/opt-out", {
    method: "POST",
    body: JSON.stringify({ repository_url: repoUrl }),
  });

export const removeOptOut = (repoUrl: string) =>
  apiFetch<{ message: string }>(`/opt-out?repository_url=${encodeURIComponent(repoUrl)}`, {
    method: "DELETE",
  });

export const listOptOuts = () =>
  apiFetch<{ opted_out_repositories: string[]; count: number }>("/opt-out");
