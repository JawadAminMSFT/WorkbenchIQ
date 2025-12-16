#Requires -Version 7.0
#Requires -Modules Az.Accounts

<#
.SYNOPSIS
    Configures Azure AI Foundry Content Understanding default model mappings.

.DESCRIPTION
    This script configures the Content Understanding service with default model deployments
    for document processing, OCR, and embedding operations. It replicates the configuration
    from setup_content_understanding.py using PowerShell and Azure REST API.

.PARAMETER AiFoundryEndpoint
    The AI Foundry account endpoint (e.g., https://your-account.openai.azure.com/)

.PARAMETER ModelDeployments
    Hashtable containing model deployment names:
    @{
        'gpt-4.1' = 'gpt-4.1'
        'gpt-4.1-mini' = 'gpt-4.1-mini'
        'text-embedding-3-large' = 'text-embedding-3-large'
    }

.PARAMETER ApiVersion
    Content Understanding API version (default: 2025-11-01)

.EXAMPLE
    .\configure-content-understanding.ps1 `
        -AiFoundryEndpoint "https://wbiq-dev-aifoundry.openai.azure.com/" `
        -ModelDeployments @{'gpt-4.1'='gpt-4.1'; 'gpt-4.1-mini'='gpt-4.1-mini'; 'text-embedding-3-large'='text-embedding-3-large'}
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$AiFoundryEndpoint,

    [Parameter(Mandatory = $true)]
    [hashtable]$ModelDeployments,

    [Parameter(Mandatory = $false)]
    [string]$ApiVersion = "2025-11-01"
)

# ======================================================================================
# SCRIPT INITIALIZATION
# ======================================================================================

$ErrorActionPreference = "Stop"
$WarningPreference = "Continue"
$InformationPreference = "Continue"

# ======================================================================================
# FUNCTIONS
# ======================================================================================

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

function Get-AzureAccessToken {
    param([string]$Resource = "https://cognitiveservices.azure.com")
    
    try {
        $context = Get-AzContext
        if (-not $context) {
            throw "Not authenticated to Azure. Run Connect-AzAccount first."
        }
        
        $token = Get-AzAccessToken -ResourceUrl $Resource
        return $token.Token
    } catch {
        Write-Error-Message "Failed to obtain Azure access token: $_"
        throw
    }
}

# ======================================================================================
# VALIDATION
# ======================================================================================

Write-Information "Validating configuration parameters..."

# Normalize endpoint (ensure trailing slash)
if (-not $AiFoundryEndpoint.EndsWith("/")) {
    $AiFoundryEndpoint = "$AiFoundryEndpoint/"
}

# Validate model deployments
$requiredModels = @('gpt-4.1', 'gpt-4.1-mini', 'text-embedding-3-large')
foreach ($model in $requiredModels) {
    if (-not $ModelDeployments.ContainsKey($model)) {
        Write-Error-Message "Missing required model deployment: $model"
        exit 1
    }
}

Write-Success "Configuration parameters validated"

# ======================================================================================
# BUILD CONFIGURATION PAYLOAD
# ======================================================================================

Write-Information "Building Content Understanding configuration payload..."

# Build the configuration object matching setup_content_understanding.py
$config = @{
    modelDeployments = @{
        documentProcessing = $ModelDeployments['gpt-4.1']
        ocr = $ModelDeployments['gpt-4.1-mini']
        embedding = $ModelDeployments['text-embedding-3-large']
    }
}

$jsonPayload = $config | ConvertTo-Json -Depth 10 -Compress

Write-Host "Configuration payload:" -ForegroundColor Cyan
Write-Host $jsonPayload -ForegroundColor White

# ======================================================================================
# CONFIGURE CONTENT UNDERSTANDING
# ======================================================================================

Write-Information "Configuring Content Understanding defaults..."

try {
    # Get Azure AD access token
    Write-Information "Obtaining Azure AD access token..."
    $accessToken = Get-AzureAccessToken
    Write-Success "Access token obtained"

    # Build request URL
    $configUrl = "${AiFoundryEndpoint}contentunderstanding/defaults?api-version=$ApiVersion"
    Write-Information "Configuration URL: $configUrl"

    # Prepare headers
    $headers = @{
        "Authorization" = "Bearer $accessToken"
        "Content-Type" = "application/json"
    }

    # Send PATCH request to configure defaults
    Write-Information "Sending configuration request..."
    $response = Invoke-RestMethod `
        -Uri $configUrl `
        -Method PATCH `
        -Headers $headers `
        -Body $jsonPayload `
        -ErrorAction Stop

    Write-Success "Content Understanding defaults configured successfully"
    
    # Display response
    Write-Host "`nConfiguration Response:" -ForegroundColor Cyan
    Write-Host ($response | ConvertTo-Json -Depth 10) -ForegroundColor White

} catch {
    Write-Error-Message "Failed to configure Content Understanding: $_"
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $statusDescription = $_.Exception.Response.StatusDescription
        Write-Host "HTTP Status: $statusCode - $statusDescription" -ForegroundColor Red
        
        # Try to read error response body
        try {
            $streamReader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
            $errorBody = $streamReader.ReadToEnd()
            Write-Host "Error Details: $errorBody" -ForegroundColor Red
        } catch {
            # Ignore if we can't read the error body
        }
    }
    
    exit 1
}

# ======================================================================================
# VERIFY CONFIGURATION
# ======================================================================================

Write-Information "`nVerifying configuration..."

try {
    # Send GET request to verify defaults
    $verifyUrl = "${AiFoundryEndpoint}contentunderstanding/defaults?api-version=$ApiVersion"
    $verifyResponse = Invoke-RestMethod `
        -Uri $verifyUrl `
        -Method GET `
        -Headers $headers `
        -ErrorAction Stop

    Write-Success "Configuration verified successfully"
    
    Write-Host "`nCurrent Configuration:" -ForegroundColor Cyan
    Write-Host "  Document Processing: $($verifyResponse.modelDeployments.documentProcessing)" -ForegroundColor White
    Write-Host "  OCR: $($verifyResponse.modelDeployments.ocr)" -ForegroundColor White
    Write-Host "  Embedding: $($verifyResponse.modelDeployments.embedding)" -ForegroundColor White

    # Validate configuration matches
    $isValid = $true
    if ($verifyResponse.modelDeployments.documentProcessing -ne $ModelDeployments['gpt-4.1']) {
        Write-Warning-Message "Document Processing model mismatch"
        $isValid = $false
    }
    if ($verifyResponse.modelDeployments.ocr -ne $ModelDeployments['gpt-4.1-mini']) {
        Write-Warning-Message "OCR model mismatch"
        $isValid = $false
    }
    if ($verifyResponse.modelDeployments.embedding -ne $ModelDeployments['text-embedding-3-large']) {
        Write-Warning-Message "Embedding model mismatch"
        $isValid = $false
    }

    if ($isValid) {
        Write-Success "`nAll model deployments configured correctly!"
        exit 0
    } else {
        Write-Warning-Message "`nSome model deployments don't match expected configuration"
        exit 1
    }

} catch {
    Write-Warning-Message "Failed to verify configuration: $_"
    Write-Warning-Message "Configuration may have been applied but verification failed"
    exit 1
}
