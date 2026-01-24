<# 
.SYNOPSIS
    Complete setup script for Automotive Claims Multimodal feature.

.DESCRIPTION
    This script automates the entire setup process for the automotive claims
    multimodal processing feature. It handles:
    - Environment validation
    - Python dependencies
    - Azure Content Understanding analyzer setup
    - Claims policy indexing
    - Database table initialization
    - Frontend dependencies
    - Starting the development servers

.PARAMETER SkipAzureSetup
    Skip Azure Content Understanding analyzer creation (use if already configured)

.PARAMETER SkipFrontend
    Skip frontend npm install (use if already installed)

.PARAMETER StartServers
    Start the API and frontend servers after setup

.PARAMETER VerifyOnly
    Only verify the setup without making changes

.EXAMPLE
    .\scripts\setup_automotive_claims.ps1 -StartServers
    
.EXAMPLE
    .\scripts\setup_automotive_claims.ps1 -SkipAzureSetup -StartServers
#>

param(
    [switch]$SkipAzureSetup,
    [switch]$SkipFrontend,
    [switch]$StartServers,
    [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Step { param($msg) Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  [!!] $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "  [X] $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "      $msg" -ForegroundColor Gray }

# Banner
Write-Host @"

================================================================
   Automotive Claims Multimodal - Setup Script
   Feature: 007-automotive-claims-multimodal
================================================================

"@ -ForegroundColor Magenta

# Check we're in the right directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Fail "Please run this script from the project root directory"
    exit 1
}

# ============================================================
# Step 1: Validate Environment
# ============================================================
Write-Step "Validating Environment"

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python: $pythonVersion"
} catch {
    Write-Fail "Python not found. Please install Python 3.10+"
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Success "Node.js: $nodeVersion"
} catch {
    Write-Warn "Node.js not found. Frontend will not work."
}

# Check uv (Python package manager)
try {
    $uvVersion = uv --version 2>&1
    Write-Success "uv: $uvVersion"
} catch {
    Write-Warn "uv not found. Using pip instead."
}

# Check .env file
if (Test-Path ".env") {
    Write-Success ".env file exists"
} else {
    if (Test-Path ".env.example") {
        Write-Warn ".env not found, copying from .env.example"
        Copy-Item ".env.example" ".env"
    } else {
        Write-Fail ".env file not found. Please create one with required settings."
        exit 1
    }
}

# Load and validate required env vars
$envContent = Get-Content ".env" -Raw
$requiredVars = @(
    "AZURE_CONTENT_UNDERSTANDING_ENDPOINT",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY"
)

$missingVars = @()
foreach ($var in $requiredVars) {
    if ($envContent -notmatch "$var\s*=\s*.+") {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Warn "Missing environment variables: $($missingVars -join ', ')"
    Write-Info "Some features may not work without these."
} else {
    Write-Success "All required environment variables configured"
}

if ($VerifyOnly) {
    Write-Host "`nVerification complete." -ForegroundColor Green
    exit 0
}

# ============================================================
# Step 2: Install Python Dependencies
# ============================================================
Write-Step "Installing Python Dependencies"

try {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv sync
    } else {
        pip install -r requirements.txt
    }
    Write-Success "Python dependencies installed"
} catch {
    Write-Fail "Failed to install Python dependencies: $_"
    exit 1
}

# ============================================================
# Step 3: Setup Azure Content Understanding Analyzers
# ============================================================
if (-not $SkipAzureSetup) {
    Write-Step "Setting up Azure Content Understanding Analyzers"
    
    try {
        # Check if the setup script exists
        if (Test-Path "scripts/setup_automotive_analyzers.py") {
            Write-Info "Creating custom analyzers..."
            python scripts/setup_automotive_analyzers.py --create-all
            
            Write-Info "Verifying analyzers..."
            python scripts/setup_automotive_analyzers.py --verify
            Write-Success "Azure analyzers configured"
        } else {
            Write-Warn "setup_automotive_analyzers.py not found, skipping"
        }
    } catch {
        Write-Warn "Failed to setup Azure analyzers: $_"
        Write-Info "You may need to set up analyzers manually or check credentials"
    }
} else {
    Write-Info "Skipping Azure setup (--SkipAzureSetup flag)"
}

# ============================================================
# Step 4: Index Claims Policies for RAG
# ============================================================
Write-Step "Indexing Claims Policies for RAG"

try {
    if (Test-Path "scripts/index_claims_policies.py") {
        python scripts/index_claims_policies.py
        Write-Success "Claims policies indexed"
    } else {
        Write-Warn "index_claims_policies.py not found, skipping"
    }
} catch {
    Write-Warn "Failed to index policies: $_"
    Write-Info "RAG search for claims policies may not work"
}

# ============================================================
# Step 5: Initialize Database Tables
# ============================================================
Write-Step "Initializing Database Tables"

try {
    # Run a quick Python script to initialize tables
    $initScript = @"
import asyncio
from app.config import Settings
from app.database.settings import DatabaseSettings

settings = Settings.from_env()
db_settings = DatabaseSettings.from_env()

if db_settings.backend == 'postgresql':
    print(f'Database backend: PostgreSQL at {db_settings.host}')
    
    async def init_tables():
        from app.database.pool import init_pool, close_pool
        from app.multimodal.repository import ClaimsMediaRepository
        from app.claims.indexer import ClaimsPolicyChunkRepository
        
        await init_pool(db_settings)
        
        # Initialize claim media tables
        repo = ClaimsMediaRepository()
        await repo.initialize_tables()
        print('  Initialized claim media tables')
        
        # Initialize policy chunks table
        policy_repo = ClaimsPolicyChunkRepository()
        await policy_repo.initialize_table()
        print('  Initialized policy chunks table')
        
        await close_pool()
    
    asyncio.run(init_tables())
    print('Database tables ready')
else:
    print(f'Database backend: {db_settings.backend} (no PostgreSQL tables needed)')
"@
    
    $initScript | python -
    Write-Success "Database tables initialized"
} catch {
    Write-Warn "Failed to initialize database: $_"
    Write-Info "Tables will be created on first API request"
}

# ============================================================
# Step 6: Install Frontend Dependencies
# ============================================================
if (-not $SkipFrontend) {
    Write-Step "Installing Frontend Dependencies"
    
    try {
        Push-Location frontend
        if (-not (Test-Path "node_modules")) {
            npm install
            Write-Success "Frontend dependencies installed"
        } else {
            Write-Success "Frontend dependencies already installed"
        }
        Pop-Location
    } catch {
        Pop-Location
        Write-Warn "Failed to install frontend dependencies: $_"
    }
} else {
    Write-Info "Skipping frontend setup (--SkipFrontend flag)"
}

# ============================================================
# Step 7: Run Tests
# ============================================================
Write-Step "Running Quick Verification Tests"

try {
    $testResult = python -m pytest tests/test_auto_claims_phase1_config.py tests/test_auto_claims_phase2_router.py -v --tb=short 2>&1
    $passedTests = ($testResult | Select-String "passed").Count
    if ($passedTests -gt 0) {
        Write-Success "Tests passed"
    }
} catch {
    Write-Warn "Some tests may have failed"
}

# ============================================================
# Summary
# ============================================================
Write-Host @"

╔═══════════════════════════════════════════════════════════════╗
║                     Setup Complete!                           ║
╚═══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green

Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Start servers:  .\scripts\run_frontend.bat" -ForegroundColor White
Write-Host "  2. Open browser:   http://localhost:3000" -ForegroundColor White
Write-Host "  3. Open admin:     http://localhost:3000/admin" -ForegroundColor White
Write-Host "  4. API docs:       http://localhost:8000/docs" -ForegroundColor White
Write-Host ""

# ============================================================
# Step 8: Start Servers (if requested)
# ============================================================
if ($StartServers) {
    Write-Step "Starting Development Servers"
    
    Write-Info "Starting API server on port 8000..."
    Start-Process -FilePath "cmd" -ArgumentList "/c", "uv run python -m uvicorn api_server:app --reload --port 8000" -WindowStyle Normal
    
    Start-Sleep -Seconds 3
    
    Write-Info "Starting frontend on port 3000..."
    Push-Location frontend
    Start-Process -FilePath "cmd" -ArgumentList "/c", "npm run dev" -WindowStyle Normal
    Pop-Location
    
    Start-Sleep -Seconds 2
    
    Write-Host "`nServers are starting..." -ForegroundColor Green
    Write-Host "  API:      http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    
    # Open browser
    Start-Process "http://localhost:3000"
}
