#Requires -Version 7.0
#Requires -Modules Az.Accounts, Az.Resources

<#
.SYNOPSIS
    Deploys Azure AI Foundry v2 with Content Understanding infrastructure.

.DESCRIPTION
    This script orchestrates the complete deployment process:
    - Phase 1-3: Deploys Bicep templates (Foundation, AI Foundry, Models)
    - Phase 4: Configures Content Understanding default model mappings
    - Phase 5: Validates the deployment
    
    The Bicep template creates the resource group automatically based on the
    baseName and environmentName variables (default: rg-wbiq-dev).

.PARAMETER Location
    Azure region for deployment (default: eastus)

.PARAMETER TemplateFile
    Path to the main Bicep template file

.PARAMETER ParameterFile
    Path to the Bicep parameters file

.PARAMETER SkipValidation
    Skip post-deployment validation

.EXAMPLE
    .\deploy.ps1

.EXAMPLE
    .\deploy.ps1 -Location "westus"

.EXAMPLE
    .\deploy.ps1 -Location "eastus" -SkipValidation
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$Location = "westus",

    [Parameter(Mandatory = $false)]
    [string]$TemplateFile = ".\main.bicep",

    [Parameter(Mandatory = $false)]
    [string]$ParameterFile = ".\main.bicepparam",

    [Parameter(Mandatory = $false)]
    [switch]$SkipValidation
)

# ======================================================================================
# SCRIPT INITIALIZATION
# ======================================================================================

$ErrorActionPreference = "Stop"
$WarningPreference = "Continue"
$InformationPreference = "Continue"

$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ConfigScriptPath = Join-Path $ScriptPath "configure-content-understanding.ps1"
$ValidateScriptPath = Join-Path $ScriptPath "validate-deployment.ps1"

# Display startup banner
Clear-Host
Write-Host "`n" -NoNewline
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "   Azure AI Foundry v2 with Content Understanding - Deployment Script   " -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will deploy:" -ForegroundColor White
Write-Host "  • Resource Group" -ForegroundColor Gray
Write-Host "  • Managed Identity" -ForegroundColor Gray
Write-Host "  • Storage Account" -ForegroundColor Gray
Write-Host "  • Key Vault" -ForegroundColor Gray
Write-Host "  • AI Foundry Account & Project" -ForegroundColor Gray
Write-Host "  • Model Deployments (GPT-4o, GPT-4o-mini, Text-Embedding)" -ForegroundColor Gray
Write-Host ""

# ======================================================================================
# FUNCTIONS
# ======================================================================================

function Write-Header {
    param([string]$Message)
    Write-Host "`n===================================================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "===================================================================`n" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error-Message {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Warning-Message {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

# ======================================================================================
# PARAMETER VALIDATION
# ======================================================================================

Write-Host "`nDeployment Configuration:" -ForegroundColor Cyan
Write-Host "  Location: $Location" -ForegroundColor White
Write-Host "  Template: $TemplateFile" -ForegroundColor White
Write-Host "  Parameters: $ParameterFile" -ForegroundColor White
Write-Host ""
Write-Host "  Note: Resource group name will be determined by the Bicep template" -ForegroundColor Gray
Write-Host "        (default: rg-wbiq-dev)" -ForegroundColor Gray
Write-Host ""

$confirmation = Read-Host "Proceed with deployment? (Y/n)"
if ($confirmation -eq 'n' -or $confirmation -eq 'N') {
    Write-Host "Deployment cancelled by user" -ForegroundColor Yellow
    exit 0
}

# ======================================================================================
# PRE-DEPLOYMENT CHECKS
# ======================================================================================

Write-Header "Pre-Deployment Checks"

# Check Azure CLI login
Write-Information "Checking Azure authentication..."
$account = Get-AzContext
if (-not $account) {
    Write-Error-Message "Not logged in to Azure. Please run 'Connect-AzAccount'"
    exit 1
}
Write-Success "Logged in as: $($account.Account.Id)"
Write-Success "Subscription: $($account.Subscription.Name) ($($account.Subscription.Id))"

# Check template files exist
if (-not (Test-Path $TemplateFile)) {
    Write-Error-Message "Template file not found: $TemplateFile"
    exit 1
}
Write-Success "Found template file: $TemplateFile"

if (-not (Test-Path $ParameterFile)) {
    Write-Error-Message "Parameter file not found: $ParameterFile"
    exit 1
}
Write-Success "Found parameter file: $ParameterFile"

# Validate Bicep template
Write-Information "Validating Bicep template..."
try {
    $buildOutput = bicep build $TemplateFile --stdout --no-restore 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Message "Bicep build failed. Please fix errors and retry."
        Write-Host $buildOutput
        exit 1
    }
    Write-Success "Bicep template is valid"
} catch {
    Write-Error-Message "Failed to validate Bicep template: $_"
    exit 1
}

# ======================================================================================
# PHASE 1-3: BICEP DEPLOYMENT
# ======================================================================================

Write-Header "Phase 1-3: Deploying Infrastructure (Foundation, AI Foundry, Models)"

$deploymentName = "aifoundry-cu-$(Get-Date -Format 'yyyyMMddHHmmss')"

Write-Information "Starting subscription-level deployment: $deploymentName"
Write-Information "This may take 10-15 minutes..."

try {
    $deployment = New-AzDeployment `
        -Name $deploymentName `
        -Location $Location `
        -TemplateFile $TemplateFile `
        -TemplateParameterFile $ParameterFile `
        -Verbose

    if ($deployment.ProvisioningState -eq "Succeeded") {
        Write-Success "Bicep deployment completed successfully"
        
        # Extract resource group name from outputs
        $resourceGroupName = $deployment.Outputs.resourceGroupName.Value
        
        # Display outputs
        Write-Host "`nDeployment Outputs:" -ForegroundColor Cyan
        $deployment.Outputs.GetEnumerator() | ForEach-Object {
            Write-Host "  $($_.Key): $($_.Value.Value)" -ForegroundColor White
        }
    } else {
        Write-Error-Message "Deployment failed with state: $($deployment.ProvisioningState)"
        exit 1
    }
} catch {
    Write-Error-Message "Deployment failed: $_"
    Write-Host $_.Exception.Message
    exit 1
}

# ======================================================================================
# PHASE 4: CONTENT UNDERSTANDING CONFIGURATION
# ======================================================================================

Write-Header "Phase 4: Configuring Content Understanding Defaults"

if (-not (Test-Path $ConfigScriptPath)) {
    Write-Warning-Message "Configuration script not found: $ConfigScriptPath"
    Write-Warning-Message "Skipping Content Understanding configuration"
} else {
    Write-Information "Running Content Understanding configuration..."
    
    try {
        # Convert JObject to hashtable for PowerShell script compatibility
        $modelDeploymentsHash = @{}
        $deployment.Outputs.modelDeployments.Value.PSObject.Properties | ForEach-Object {
            $modelDeploymentsHash[$_.Name] = $_.Value
        }
        
        & $ConfigScriptPath `
            -AiFoundryEndpoint $deployment.Outputs.aiFoundryAccountEndpoint.Value `
            -ModelDeployments $modelDeploymentsHash
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Content Understanding configured successfully"
        } else {
            Write-Warning-Message "Content Understanding configuration completed with warnings"
        }
    } catch {
        Write-Error-Message "Content Understanding configuration failed: $_"
        Write-Warning-Message "You can run configure-content-understanding.ps1 manually later"
    }
}

# ======================================================================================
# PHASE 5: VALIDATION
# ======================================================================================

if (-not $SkipValidation) {
    Write-Header "Phase 5: Validating Deployment"
    
    if (-not (Test-Path $ValidateScriptPath)) {
        Write-Warning-Message "Validation script not found: $ValidateScriptPath"
        Write-Warning-Message "Skipping validation"
    } else {
        Write-Information "Running deployment validation..."
        
        try {
            & $ValidateScriptPath `
                -ResourceGroupName $resourceGroupName `
                -AiFoundryAccountName $deployment.Outputs.aiFoundryAccountName.Value
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Validation passed"
            } else {
                Write-Warning-Message "Validation completed with warnings"
            }
        } catch {
            Write-Warning-Message "Validation failed: $_"
        }
    }
} else {
    Write-Information "Skipping validation (use -SkipValidation parameter to enable)"
}

# ======================================================================================
# DEPLOYMENT SUMMARY
# ======================================================================================

Write-Header "Deployment Summary"

Write-Host "Resource Group: $resourceGroupName" -ForegroundColor White
Write-Host "AI Foundry Account: $($deployment.Outputs.aiFoundryAccountName.Value)" -ForegroundColor White
Write-Host "Endpoint: $($deployment.Outputs.aiFoundryAccountEndpoint.Value)" -ForegroundColor White
Write-Host "Managed Identity Client ID: $($deployment.Outputs.managedIdentityClientId.Value)" -ForegroundColor White

Write-Host "`nModel Deployments:" -ForegroundColor Cyan
$deployment.Outputs.modelDeployments.Value.PSObject.Properties | ForEach-Object {
    Write-Host "  - $($_.Name): $($_.Value)" -ForegroundColor White
}

Write-Host "`nEnvironment Configuration:" -ForegroundColor Cyan
$deployment.Outputs.environmentConfig.Value.PSObject.Properties | ForEach-Object {
    Write-Host "  $($_.Name)=$($_.Value)" -ForegroundColor White
}

Write-Success "`nDeployment completed successfully!"
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Update your .env file with the environment configuration above" -ForegroundColor White
Write-Host "2. Test the Content Understanding endpoint using the API" -ForegroundColor White
Write-Host "3. Review the deployment validation results" -ForegroundColor White

exit 0
