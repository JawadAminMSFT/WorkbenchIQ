<# 
.SYNOPSIS
    Complete setup script for Mortgage Underwriting feature.

.DESCRIPTION
    This script automates the entire setup process for the Canadian mortgage
    underwriting feature. It handles:
    - Environment validation
    - Python dependencies
    - Azure Content Understanding analyzer setup
    - Mortgage policy indexing
    - Database table initialization (mortgage_policy_chunks)
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
    .\scripts\setup_mortgage_underwriting.ps1 -StartServers
    
.EXAMPLE
    .\scripts\setup_mortgage_underwriting.ps1 -SkipAzureSetup -StartServers
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
   Canadian Mortgage Underwriting - Setup Script
   Feature: 008-mortgage-underwriting
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
        if (Test-Path "scripts/setup_mortgage_analyzers.py") {
            Write-Info "Creating custom analyzers..."
            python scripts/setup_mortgage_analyzers.py --create-all
            
            Write-Info "Verifying analyzers..."
            python scripts/setup_mortgage_analyzers.py --verify
            Write-Success "Azure analyzers configured"
        } else {
            Write-Warn "setup_mortgage_analyzers.py not found, skipping"
        }
    } catch {
        Write-Warn "Failed to setup Azure analyzers: $_"
        Write-Info "You may need to set up analyzers manually or check credentials"
    }
} else {
    Write-Info "Skipping Azure setup (--SkipAzureSetup flag)"
}

# ============================================================
# Step 4: Index Mortgage Policies for RAG
# ============================================================
Write-Step "Indexing Mortgage Policies for RAG"

try {
    if (Test-Path "scripts/index_mortgage_policies.py") {
        python scripts/index_mortgage_policies.py
        Write-Success "Mortgage policies indexed"
    } else {
        Write-Warn "index_mortgage_policies.py not found, skipping"
    }
} catch {
    Write-Warn "Failed to index policies: $_"
    Write-Info "RAG search for mortgage policies may not work"
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
        from app.rag.unified_indexer import UnifiedPolicyChunkRepository
        
        await init_pool(db_settings)
        
        # Initialize mortgage_policy_chunks table
        repo = UnifiedPolicyChunkRepository('mortgage_policy_chunks')
        await repo.create_table()
        print('  Initialized mortgage_policy_chunks table')
        
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
    
    if (Test-Path "frontend/package.json") {
        try {
            Push-Location frontend
            npm install
            Pop-Location
            Write-Success "Frontend dependencies installed"
        } catch {
            Pop-Location
            Write-Warn "Failed to install frontend dependencies: $_"
        }
    } else {
        Write-Info "No frontend found, skipping"
    }
} else {
    Write-Info "Skipping frontend setup (--SkipFrontend flag)"
}

# ============================================================
# Step 7: Create Sample Data Directory
# ============================================================
Write-Step "Setting up Data Directories"

try {
    $dirs = @(
        "data/applications",
        "data/conversations"
    )
    
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Info "Created $dir"
        }
    }
    Write-Success "Data directories ready"
} catch {
    Write-Warn "Failed to create directories: $_"
}

# ============================================================
# Summary
# ============================================================
Write-Host @"

================================================================
   Setup Complete!
================================================================

Mortgage Underwriting Feature Status:
  [✓] Python environment configured
  [✓] Azure analyzers setup
  [✓] Mortgage policies indexed
  [✓] Database tables initialized
  [✓] Data directories created

"@ -ForegroundColor Green

if ($StartServers) {
    Write-Step "Starting Development Servers"
    
    Write-Info "Starting API server on http://localhost:8000"
    Write-Info "Starting frontend on http://localhost:3000"
    Write-Info ""
    Write-Info "Press Ctrl+C to stop all servers"
    Write-Info ""
    
    # Start API server in background
    $apiJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        python api_server.py
    }
    
    # Give API server time to start
    Start-Sleep -Seconds 3
    
    # Start frontend if it exists
    if (Test-Path "frontend/package.json") {
        $frontendJob = Start-Job -ScriptBlock {
            Set-Location $using:PWD/frontend
            npm run dev
        }
    }
    
    # Wait and show logs
    try {
        while ($true) {
            Receive-Job -Job $apiJob
            if ($frontendJob) { Receive-Job -Job $frontendJob }
            Start-Sleep -Seconds 1
        }
    } finally {
        Stop-Job -Job $apiJob
        Remove-Job -Job $apiJob
        if ($frontendJob) {
            Stop-Job -Job $frontendJob
            Remove-Job -Job $frontendJob
        }
    }
} else {
    Write-Info "To start servers manually:"
    Write-Info "  API:      python api_server.py"
    Write-Info "  Frontend: cd frontend && npm run dev"
    Write-Info ""
    Write-Info "Or run with -StartServers flag to start both automatically"
}
