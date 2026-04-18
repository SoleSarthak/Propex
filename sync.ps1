# Git Sync Script
Write-Host "Syncing with remote repository..." -ForegroundColor Cyan

# 1. Pull latest changes
Write-Host "Pulling latest changes..." -ForegroundColor Yellow
git pull origin main

# 2. Add all changes
Write-Host "Staging changes..." -ForegroundColor Yellow
git add .

# 3. Commit
$commitMsg = "Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Committing with message: $commitMsg" -ForegroundColor Yellow
git commit -m "$commitMsg"

# 4. Push
Write-Host "Pushing to remote..." -ForegroundColor Green
git push origin main

Write-Host "Done!" -ForegroundColor Cyan
