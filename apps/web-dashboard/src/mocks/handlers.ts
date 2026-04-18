import { http, HttpResponse } from 'msw'

export const handlers = [
  // Mock CVE list endpoint
  http.get('/api/v1/cves', () => {
    return HttpResponse.json([
      {
        id: 'CVE-2024-1234',
        severity: 'Critical',
        status: 'Propagating',
        description: 'Sample vulnerability in @fastify/core',
        published_at: new Date().toISOString()
      }
    ])
  }),

  // Mock stats endpoint
  http.get('/api/v1/stats', () => {
    return HttpResponse.json({
      active_cves: 1284,
      affected_packages: 8432,
      monitored_repos: 452,
      critical_risks: 42
    })
  })
]
