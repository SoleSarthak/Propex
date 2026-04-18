import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate } from "k6/metrics";

// --- Custom Metrics ---
const apiLatency = new Trend("api_latency", true);
const errorRate = new Rate("error_rate");

// --- Test Config: 100 concurrent users, ramp up over 2 min ---
export const options = {
  stages: [
    { duration: "30s", target: 25 },   // Ramp up to 25 users
    { duration: "1m", target: 100 },   // Ramp up to 100 users
    { duration: "2m", target: 100 },   // Hold 100 concurrent users
    { duration: "30s", target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ["p(95)<500"],  // P95 must be < 500ms
    error_rate: ["rate<0.01"],         // Error rate < 1%
  },
};

const BASE_URL = __ENV.API_URL || "http://localhost:8006";

const ENDPOINTS = [
  { name: "health", url: `${BASE_URL}/health` },
  { name: "affected_repos", url: `${BASE_URL}/api/v1/cves/CVE-2024-1234/affected-repos?limit=50` },
  { name: "notifications", url: `${BASE_URL}/api/v1/notifications?limit=50` },
  { name: "opt_out_list", url: `${BASE_URL}/opt-out` },
];

export default function () {
  const endpoint = ENDPOINTS[Math.floor(Math.random() * ENDPOINTS.length)];

  const start = Date.now();
  const res = http.get(endpoint.url, {
    tags: { name: endpoint.name },
    timeout: "5s",
  });
  const duration = Date.now() - start;

  apiLatency.add(duration, { endpoint: endpoint.name });

  const ok = check(res, {
    "status is 200": (r) => r.status === 200,
    "response time < 500ms": (r) => r.timings.duration < 500,
  });

  errorRate.add(!ok);
  sleep(0.5 + Math.random() * 0.5);
}
