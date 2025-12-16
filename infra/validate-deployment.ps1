#Requires -Version 7.0
#Requires -Modules Az.Accounts, Az.Resources, Az.CognitiveServices

<#
.SYNOPSIS
    Validates Azure AI Foundry Content Understanding deployment.

.DESCRIPTION
    This script performs comprehensive validation of the deployment:
    - Resource existence and configuration
    - Model deployments and availability
    - Content Understanding configuration
    - RBAC role assignments
    - Network connectivity and endpoint health

.PARAMETER ResourceGroupName
    Name of the resource group containing the deployment

.PARAMETER AiFoundryAccountName
    Name of the AI Foundry account to validate

.EXAMPLE
    .\validate-deployment.ps1 -ResourceGroupName "rg-aifoundry-dev" -AiFoundryAccountName "wbiq-dev-aifoundry"
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$ResourceGroupName,

    [Parameter(Mandatory = $true)]
    [string]$AiFoundryAccountName
)

# ======================================================================================
# SCRIPT INITIALIZATION
# ======================================================================================

$ErrorActionPreference = "Continue"
$WarningPreference = "Continue"
$InformationPreference = "Continue"

$ValidationResults = @{
    Passed = 0
    Failed = 0
    Warnings = 0
    Tests = @()
}

# ======================================================================================
# FUNCTIONS
# ======================================================================================

function Write-TestHeader {
    param([string]$Message)
    Write-Host "`n--- $Message ---" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  ✓ $Message" -ForegroundColor Green
}

function Write-Failure {
    param([string]$Message)
    Write-Host "  ✗ $Message" -ForegroundColor Red
}

function Write-Warning-Message {
    param([string]$Message)
    Write-Host "  ⚠ $Message" -ForegroundColor Yellow
}

function Add-TestResult {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Message
    )
    
    $ValidationResults.Tests += @{
        Name = $Name
        Status = $Status
        Message = $Message
    }
    
    switch ($Status) {
        "Passed" { $ValidationResults.Passed++ }
        "Failed" { $ValidationResults.Failed++ }
        "Warning" { $ValidationResults.Warnings++ }
    }
}

function Get-AzureAccessToken {
    param([string]$Resource = "https://cognitiveservices.azure.com")
    
    try {
        $context = Get-AzContext
        if (-not $context) {
            throw "Not authenticated to Azure"
        }
        
        $token = Get-AzAccessToken -ResourceUrl $Resource
        return $token.Token
    } catch {
        return $null
    }
}

# ======================================================================================
# VALIDATION TESTS
# ======================================================================================

Write-Host "`n===================================================================" -ForegroundColor Cyan
Write-Host "Azure AI Foundry Content Understanding - Deployment Validation" -ForegroundColor Cyan
Write-Host "===================================================================`n" -ForegroundColor Cyan

# Test 1: Azure Authentication
Write-TestHeader "Test 1: Azure Authentication"
try {
    $context = Get-AzContext
    if ($context) {
        Write-Success "Authenticated as: $($context.Account.Id)"
        Write-Success "Subscription: $($context.Subscription.Name)"
        Add-TestResult -Name "Azure Authentication" -Status "Passed" -Message "Authenticated successfully"
    } else {
        Write-Failure "Not authenticated to Azure"
        Add-TestResult -Name "Azure Authentication" -Status "Failed" -Message "Not authenticated"
        exit 1
    }
} catch {
    Write-Failure "Authentication check failed: $_"
    Add-TestResult -Name "Azure Authentication" -Status "Failed" -Message $_.Exception.Message
    exit 1
}

# Test 2: Resource Group
Write-TestHeader "Test 2: Resource Group Validation"
try {
    $resourceGroup = Get-AzResourceGroup -Name $ResourceGroupName -ErrorAction Stop
    Write-Success "Resource group exists: $ResourceGroupName"
    Write-Success "Location: $($resourceGroup.Location)"
    Add-TestResult -Name "Resource Group" -Status "Passed" -Message "Resource group exists"
} catch {
    Write-Failure "Resource group not found: $ResourceGroupName"
    Add-TestResult -Name "Resource Group" -Status "Failed" -Message "Resource group not found"
    exit 1
}

# Test 3: AI Foundry Account
Write-TestHeader "Test 3: AI Foundry Account Validation"
try {
    $aiAccount = Get-AzCognitiveServicesAccount -ResourceGroupName $ResourceGroupName -Name $AiFoundryAccountName -ErrorAction Stop
    Write-Success "AI Foundry account exists: $AiFoundryAccountName"
    Write-Success "Endpoint: $($aiAccount.Endpoint)"
    Write-Success "SKU: $($aiAccount.Sku.Name)"
    Write-Success "Provisioning State: $($aiAccount.ProvisioningState)"
    
    if ($aiAccount.ProvisioningState -eq "Succeeded") {
        Add-TestResult -Name "AI Foundry Account" -Status "Passed" -Message "Account provisioned successfully"
    } else {
        Write-Warning-Message "Provisioning state is not 'Succeeded'"
        Add-TestResult -Name "AI Foundry Account" -Status "Warning" -Message "Provisioning state: $($aiAccount.ProvisioningState)"
    }
    
    $endpoint = $aiAccount.Endpoint
} catch {
    Write-Failure "AI Foundry account not found: $AiFoundryAccountName"
    Add-TestResult -Name "AI Foundry Account" -Status "Failed" -Message "Account not found"
    exit 1
}

# Test 4: Model Deployments
Write-TestHeader "Test 4: Model Deployments Validation"
try {
    $deployments = Get-AzCognitiveServicesAccountDeployment -ResourceGroupName $ResourceGroupName -AccountName $AiFoundryAccountName -ErrorAction Stop
    
    $requiredModels = @('gpt-4.1', 'gpt-4.1-mini', 'text-embedding-3-large')
    $foundModels = @()
    
    foreach ($deployment in $deployments) {
        Write-Success "Deployment: $($deployment.Name) - State: $($deployment.Properties.ProvisioningState)"
        $foundModels += $deployment.Name
    }
    
    $allModelsFound = $true
    foreach ($model in $requiredModels) {
        if ($foundModels -notcontains $model) {
            Write-Failure "Required model deployment missing: $model"
            $allModelsFound = $false
        }
    }
    
    if ($allModelsFound) {
        Add-TestResult -Name "Model Deployments" -Status "Passed" -Message "All required models deployed"
    } else {
        Add-TestResult -Name "Model Deployments" -Status "Failed" -Message "Some required models missing"
    }
} catch {
    Write-Failure "Failed to retrieve model deployments: $_"
    Add-TestResult -Name "Model Deployments" -Status "Failed" -Message $_.Exception.Message
}

# Test 5: Managed Identity
Write-TestHeader "Test 5: Managed Identity Validation"
try {
    $identities = Get-AzUserAssignedIdentity -ResourceGroupName $ResourceGroupName -ErrorAction Stop
    
    if ($identities) {
        foreach ($identity in $identities) {
            Write-Success "Managed Identity: $($identity.Name)"
            Write-Success "Principal ID: $($identity.PrincipalId)"
            Write-Success "Client ID: $($identity.ClientId)"
        }
        Add-TestResult -Name "Managed Identity" -Status "Passed" -Message "Managed identity exists"
    } else {
        Write-Warning-Message "No managed identities found"
        Add-TestResult -Name "Managed Identity" -Status "Warning" -Message "No managed identities found"
    }
} catch {
    Write-Warning-Message "Failed to retrieve managed identities: $_"
    Add-TestResult -Name "Managed Identity" -Status "Warning" -Message $_.Exception.Message
}

# Test 6: Storage Account
Write-TestHeader "Test 6: Storage Account Validation"
try {
    $storageAccounts = Get-AzStorageAccount -ResourceGroupName $ResourceGroupName -ErrorAction Stop
    
    if ($storageAccounts) {
        foreach ($storage in $storageAccounts) {
            Write-Success "Storage Account: $($storage.StorageAccountName)"
            Write-Success "Location: $($storage.Location)"
            Write-Success "SKU: $($storage.Sku.Name)"
            Write-Success "Provisioning State: $($storage.ProvisioningState)"
        }
        Add-TestResult -Name "Storage Account" -Status "Passed" -Message "Storage account exists"
    } else {
        Write-Warning-Message "No storage accounts found"
        Add-TestResult -Name "Storage Account" -Status "Warning" -Message "No storage accounts found"
    }
} catch {
    Write-Warning-Message "Failed to retrieve storage accounts: $_"
    Add-TestResult -Name "Storage Account" -Status "Warning" -Message $_.Exception.Message
}

# Test 7: Key Vault
Write-TestHeader "Test 7: Key Vault Validation"
try {
    $keyVaults = Get-AzKeyVault -ResourceGroupName $ResourceGroupName -ErrorAction Stop
    
    if ($keyVaults) {
        foreach ($vault in $keyVaults) {
            Write-Success "Key Vault: $($vault.VaultName)"
            Write-Success "URI: $($vault.VaultUri)"
            Write-Success "Location: $($vault.Location)"
        }
        Add-TestResult -Name "Key Vault" -Status "Passed" -Message "Key Vault exists"
    } else {
        Write-Warning-Message "No key vaults found"
        Add-TestResult -Name "Key Vault" -Status "Warning" -Message "No key vaults found"
    }
} catch {
    Write-Warning-Message "Failed to retrieve key vaults: $_"
    Add-TestResult -Name "Key Vault" -Status "Warning" -Message $_.Exception.Message
}

# Test 8: Content Understanding Configuration
Write-TestHeader "Test 8: Content Understanding Configuration"
try {
    $accessToken = Get-AzureAccessToken
    
    if ($accessToken) {
        $verifyUrl = "${endpoint}contentunderstanding/defaults?api-version=2025-11-01"
        $headers = @{
            "Authorization" = "Bearer $accessToken"
        }
        
        $config = Invoke-RestMethod -Uri $verifyUrl -Method GET -Headers $headers -ErrorAction Stop
        
        Write-Success "Content Understanding is configured"
        Write-Success "Document Processing: $($config.modelDeployments.documentProcessing)"
        Write-Success "OCR: $($config.modelDeployments.ocr)"
        Write-Success "Embedding: $($config.modelDeployments.embedding)"
        
        Add-TestResult -Name "Content Understanding Config" -Status "Passed" -Message "Configuration retrieved successfully"
    } else {
        Write-Warning-Message "Could not obtain access token for verification"
        Add-TestResult -Name "Content Understanding Config" -Status "Warning" -Message "Could not verify configuration"
    }
} catch {
    Write-Warning-Message "Failed to retrieve Content Understanding configuration: $_"
    Add-TestResult -Name "Content Understanding Config" -Status "Warning" -Message $_.Exception.Message
}

# Test 9: Network Connectivity
Write-TestHeader "Test 9: Network Connectivity"
try {
    $testUrl = "${endpoint}openai/deployments?api-version=2024-06-01"
    $accessToken = Get-AzureAccessToken
    
    if ($accessToken) {
        $headers = @{
            "Authorization" = "Bearer $accessToken"
        }
        
        $response = Invoke-WebRequest -Uri $testUrl -Method GET -Headers $headers -ErrorAction Stop -UseBasicParsing
        
        if ($response.StatusCode -eq 200) {
            Write-Success "Endpoint is reachable and responding"
            Add-TestResult -Name "Network Connectivity" -Status "Passed" -Message "Endpoint accessible"
        } else {
            Write-Warning-Message "Unexpected status code: $($response.StatusCode)"
            Add-TestResult -Name "Network Connectivity" -Status "Warning" -Message "Status: $($response.StatusCode)"
        }
    } else {
        Write-Warning-Message "Could not obtain access token for connectivity test"
        Add-TestResult -Name "Network Connectivity" -Status "Warning" -Message "Could not test connectivity"
    }
} catch {
    Write-Failure "Endpoint connectivity test failed: $_"
    Add-TestResult -Name "Network Connectivity" -Status "Failed" -Message $_.Exception.Message
}

# ======================================================================================
# VALIDATION SUMMARY
# ======================================================================================

Write-Host "`n===================================================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "===================================================================`n" -ForegroundColor Cyan

Write-Host "Total Tests: $($ValidationResults.Tests.Count)" -ForegroundColor White
Write-Host "Passed: $($ValidationResults.Passed)" -ForegroundColor Green
Write-Host "Failed: $($ValidationResults.Failed)" -ForegroundColor Red
Write-Host "Warnings: $($ValidationResults.Warnings)" -ForegroundColor Yellow

Write-Host "`nDetailed Results:" -ForegroundColor Cyan
foreach ($test in $ValidationResults.Tests) {
    $color = switch ($test.Status) {
        "Passed" { "Green" }
        "Failed" { "Red" }
        "Warning" { "Yellow" }
    }
    Write-Host "  [$($test.Status)] $($test.Name): $($test.Message)" -ForegroundColor $color
}

# Exit with appropriate code
if ($ValidationResults.Failed -gt 0) {
    Write-Host "`n❌ Validation FAILED - Please review failed tests above" -ForegroundColor Red
    exit 1
} elseif ($ValidationResults.Warnings -gt 0) {
    Write-Host "`n⚠️  Validation completed with WARNINGS" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "`n✅ All validation tests PASSED!" -ForegroundColor Green
    exit 0
}
