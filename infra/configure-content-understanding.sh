#!/usr/bin/env bash

# ======================================================================================
# configure-content-understanding.sh
# ======================================================================================
# SYNOPSIS
#     Configures Azure AI Foundry Content Understanding default model mappings.
#
# DESCRIPTION
#     This script configures the Content Understanding service with default model 
#     deployments for document processing, OCR, and embedding operations. It replicates
#     the configuration from setup_content_understanding.py using Bash and Azure REST API.
#
# PARAMETERS
#     --ai-foundry-endpoint <url>     AI Foundry account endpoint (required)
#     --gpt4-deployment <name>        GPT-4 deployment name (required)
#     --gpt4-mini-deployment <name>   GPT-4 mini deployment name (required)
#     --embedding-deployment <name>   Embedding deployment name (required)
#     --api-version <version>         Content Understanding API version (optional, default: 2025-11-01)
#
# EXAMPLE
#     ./configure-content-understanding.sh \
#         --ai-foundry-endpoint "https://wbiq-dev-aifoundry.openai.azure.com/" \
#         --gpt4-deployment "gpt-4.1" \
#         --gpt4-mini-deployment "gpt-4.1-mini" \
#         --embedding-deployment "text-embedding-3-large"
# ======================================================================================

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source common functions
if [ -f "$SCRIPT_DIR/lib/common.sh" ]; then
    # shellcheck source=lib/common.sh
    source "$SCRIPT_DIR/lib/common.sh"
else
    echo "Error: common.sh library not found at $SCRIPT_DIR/lib/common.sh" >&2
    exit 1
fi

# Default values
API_VERSION="2025-11-01"
AI_FOUNDRY_ENDPOINT=""
GPT4_DEPLOYMENT=""
GPT4_MINI_DEPLOYMENT=""
EMBEDDING_DEPLOYMENT=""

# ======================================================================================
# PARAMETER PARSING
# ======================================================================================

show_usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Configures Azure AI Foundry Content Understanding default model mappings.

Required Options:
    --ai-foundry-endpoint <url>     AI Foundry account endpoint
    --gpt4-deployment <name>        GPT-4 deployment name
    --gpt4-mini-deployment <name>   GPT-4 mini deployment name
    --embedding-deployment <name>   Embedding deployment name

Optional:
    --api-version <version>         API version (default: 2025-11-01)
    --help                          Show this help message

Example:
    $(basename "$0") \\
        --ai-foundry-endpoint "https://wbiq-dev-aifoundry.openai.azure.com/" \\
        --gpt4-deployment "gpt-4.1" \\
        --gpt4-mini-deployment "gpt-4.1-mini" \\
        --embedding-deployment "text-embedding-3-large"
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --ai-foundry-endpoint)
            AI_FOUNDRY_ENDPOINT="$2"
            shift 2
            ;;
        --gpt4-deployment)
            GPT4_DEPLOYMENT="$2"
            shift 2
            ;;
        --gpt4-mini-deployment)
            GPT4_MINI_DEPLOYMENT="$2"
            shift 2
            ;;
        --embedding-deployment)
            EMBEDDING_DEPLOYMENT="$2"
            shift 2
            ;;
        --api-version)
            API_VERSION="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            show_usage
            exit 1
            ;;
    esac
done

# ======================================================================================
# VALIDATION
# ======================================================================================

write_info "Validating configuration parameters..."

# Validate required parameters
if [ -z "$AI_FOUNDRY_ENDPOINT" ]; then
    write_error "Missing required parameter: --ai-foundry-endpoint"
    exit 1
fi

if [ -z "$GPT4_DEPLOYMENT" ]; then
    write_error "Missing required parameter: --gpt4-deployment"
    exit 1
fi

if [ -z "$GPT4_MINI_DEPLOYMENT" ]; then
    write_error "Missing required parameter: --gpt4-mini-deployment"
    exit 1
fi

if [ -z "$EMBEDDING_DEPLOYMENT" ]; then
    write_error "Missing required parameter: --embedding-deployment"
    exit 1
fi

# Check required commands
require_command "az" || exit 1
require_command "jq" || exit 1
require_command "curl" || exit 1

# Check Azure authentication
check_azure_auth || exit 1

# Normalize endpoint (ensure trailing slash)
if [[ ! "$AI_FOUNDRY_ENDPOINT" =~ /$ ]]; then
    AI_FOUNDRY_ENDPOINT="${AI_FOUNDRY_ENDPOINT}/"
fi

write_success "Configuration parameters validated"

# ======================================================================================
# BUILD CONFIGURATION PAYLOAD
# ======================================================================================

write_info "Building Content Understanding configuration payload..."

# Build the configuration object matching setup_content_understanding.py
CONFIG_JSON=$(jq -n \
    --arg doc_processing "$GPT4_DEPLOYMENT" \
    --arg ocr "$GPT4_MINI_DEPLOYMENT" \
    --arg embedding "$EMBEDDING_DEPLOYMENT" \
    '{
        modelDeployments: {
            documentProcessing: $doc_processing,
            ocr: $ocr,
            embedding: $embedding
        }
    }')

echo -e "${CYAN}Configuration payload:${NC}"
echo -e "${NC}$CONFIG_JSON${NC}"

# ======================================================================================
# CONFIGURE CONTENT UNDERSTANDING
# ======================================================================================

write_info "Configuring Content Understanding defaults..."

# Get Azure AD access token
write_info "Obtaining Azure AD access token..."
ACCESS_TOKEN=$(get_access_token "https://cognitiveservices.azure.com")
if [ $? -ne 0 ]; then
    write_error "Failed to obtain access token"
    exit 1
fi
write_success "Access token obtained"

# Build request URL
CONFIG_URL="${AI_FOUNDRY_ENDPOINT}contentunderstanding/defaults?api-version=$API_VERSION"
write_info "Configuration URL: $CONFIG_URL"

# Send PATCH request to configure defaults
write_info "Sending configuration request..."
HTTP_RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH "$CONFIG_URL" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$CONFIG_JSON")

HTTP_CODE=$(echo "$HTTP_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$HTTP_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
    write_success "Content Understanding defaults configured successfully"
    
    echo ""
    echo -e "${CYAN}Configuration Response:${NC}"
    echo "$RESPONSE_BODY" | jq '.'
else
    write_error "Failed to configure Content Understanding"
    write_error "HTTP Status: $HTTP_CODE"
    echo -e "${RED}Error Details:${NC}"
    echo "$RESPONSE_BODY" | jq '.' 2>/dev/null || echo "$RESPONSE_BODY"
    exit 1
fi

# ======================================================================================
# VERIFY CONFIGURATION
# ======================================================================================

write_info ""
write_info "Verifying configuration..."

# Send GET request to verify defaults
VERIFY_URL="${AI_FOUNDRY_ENDPOINT}contentunderstanding/defaults?api-version=$API_VERSION"
VERIFY_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$VERIFY_URL" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

VERIFY_HTTP_CODE=$(echo "$VERIFY_RESPONSE" | tail -n1)
VERIFY_BODY=$(echo "$VERIFY_RESPONSE" | head -n-1)

if [ "$VERIFY_HTTP_CODE" -ge 200 ] && [ "$VERIFY_HTTP_CODE" -lt 300 ]; then
    write_success "Configuration verified successfully"
    
    # Extract configured values
    DOC_PROCESSING=$(echo "$VERIFY_BODY" | jq -r '.modelDeployments.documentProcessing')
    OCR=$(echo "$VERIFY_BODY" | jq -r '.modelDeployments.ocr')
    EMBEDDING=$(echo "$VERIFY_BODY" | jq -r '.modelDeployments.embedding')
    
    echo ""
    echo -e "${CYAN}Current Configuration:${NC}"
    echo -e "  Document Processing: ${NC}$DOC_PROCESSING${NC}"
    echo -e "  OCR: ${NC}$OCR${NC}"
    echo -e "  Embedding: ${NC}$EMBEDDING${NC}"
    
    # Validate configuration matches
    IS_VALID=true
    
    if [ "$DOC_PROCESSING" != "$GPT4_DEPLOYMENT" ]; then
        write_warning "Document Processing model mismatch"
        IS_VALID=false
    fi
    
    if [ "$OCR" != "$GPT4_MINI_DEPLOYMENT" ]; then
        write_warning "OCR model mismatch"
        IS_VALID=false
    fi
    
    if [ "$EMBEDDING" != "$EMBEDDING_DEPLOYMENT" ]; then
        write_warning "Embedding model mismatch"
        IS_VALID=false
    fi
    
    if [ "$IS_VALID" = true ]; then
        echo ""
        write_success "All model deployments configured correctly!"
        exit 0
    else
        echo ""
        write_warning "Some model deployments don't match expected configuration"
        exit 1
    fi
else
    write_warning "Failed to verify configuration: HTTP $VERIFY_HTTP_CODE"
    write_warning "Configuration may have been applied but verification failed"
    exit 1
fi
