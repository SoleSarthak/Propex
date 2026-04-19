# Propex Live Demo Simulation Script
# Run this to trigger a real-time vulnerability ingestion

$cveData = @{
    id = "CVE-2026-9999"
    sourceIdentifier = "nvd@nist.gov"
    published = "2026-04-19T10:00:00.000"
    lastModified = "2026-04-19T10:00:00.000"
    vulnStatus = "Analyzed"
    descriptions = @(
        @{
            lang = "en"
            value = "CRITICAL: Remote Code Execution vulnerability in core-dependency-lib affecting all versions prior to 2.4.5."
        }
    )
    metrics = @{
        cvssMetricV31 = @(
            @{
                cvssData = @{
                    version = "3.1"
                    vectorString = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
                    baseScore = 9.8
                    baseSeverity = "CRITICAL"
                }
            }
        )
    }
} | ConvertTo-Json -Depth 10

Write-Host "Triggering Live CVE Ingestion for CVE-2026-9999..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/ingest" -Method Post -Body $cveData -ContentType "application/json"
    Write-Host "Success! System is now processing the vulnerability." -ForegroundColor Green
    Write-Host "Check Redpanda Console (localhost:8080) and Neo4j (localhost:7474) for updates." -ForegroundColor Yellow
} catch {
    Write-Host "Error: Could not connect to CVE Ingestion service. Is it running on port 8000?" -ForegroundColor Red
}
