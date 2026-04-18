# setup-dev.ps1
# Windows setup script for Propex

Write-Host "--- Propex Development Setup ---" -ForegroundColor Cyan

# 1. Check for Docker
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found. Please install Docker Desktop."
    exit 1
}

# 2. Check for Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found. Please install Python 3.11+."
    exit 1
}

# 3. Check for Node/npm
if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js/npm not found. Please install Node.js 18+."
    exit 1
}

# 4. Start Docker services
Write-Host "Starting Docker services..." -ForegroundColor Green
docker compose up -d

# 5. Install Python dependencies
Write-Host "Installing root Python dependencies..." -ForegroundColor Green
pip install poetry
poetry install

# 6. Install Frontend dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Green
Set-Location apps/web-dashboard
npm install
Set-Location ../..

Write-Host "--- Setup Complete ---" -ForegroundColor Cyan
Write-Host "You can now run 'make dev' to start the environment."
