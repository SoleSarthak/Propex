# Propex Live Demo Simulation Script (Fixed Schema)
# Run this to trigger a real-time vulnerability ingestion

$cveData = @{
    cve_id = "CVE-2026-2000"
    source = "nvd"
    published_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    cvss_score = 9.8
    affected_packages = @(
        @{
            ecosystem = "npm"
            name = "core-dependency-lib"
            versions_affected = @("<2.4.5")
            fixed_version = "2.4.5"
        }
    )
    description = "CRITICAL: Remote Code Execution vulnerability in core-dependency-lib affecting all versions prior to 2.4.5."
    raw_data = @{ demo = $true }
} | ConvertTo-Json -Depth 10

Write-Host "Triggering Live CVE Ingestion for CVE-2026-9999..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/ingest" -Method Post -Body $cveData -ContentType "application/json"
    Write-Host "Success! System is now processing the vulnerability." -ForegroundColor Green
    Write-Host "Check Redpanda Console (localhost:8080) and Neo4j (localhost:7474) for updates." -ForegroundColor Yellow
} catch {
    $errMsg = $_.Exception.Message
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $errMsg = $reader.ReadToEnd()
    }
    Write-Host "Error: $errMsg" -ForegroundColor Red
}
