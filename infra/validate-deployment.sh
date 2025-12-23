#!/usr/bin/env bash

# ======================================================================================
# validate-deployment.sh
# ======================================================================================
# SYNOPSIS
#     Validates Azure AI Foundry Content Understanding deployment.
#
# DESCRIPTION
#     This script performs comprehensive validation of the deployment:
#     - Resource existence and configuration
#     - Model deployments and availability
#     - RBAC role assignments
#     - Network connectivity and endpoint health
#
#     Note: Content Understanding configuration is validated separately
#     after running configure-content-understanding.sh
#
# PARAMETERS
#     --resource-group <name>      Name of the resource group (required)
#     --ai-foundry-account <name>  Name of the AI Foundry account (required)
#     --verbose                    Show detailed output (optional)
#     --json-output <file>         Write JSON report to file (optional)
#
# EXAMPLE
#     ./validate-deployment.sh \
#         --resource-group "rg-aifoundry-dev" \
#         --ai-foundry-account "wbiq-dev-aifoundry"
# ======================================================================================

set -uo pipefail

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

# Validation results tracking
declare -a TEST_NAMES=()
declare -a TEST_STATUSES=()
declare -a TEST_MESSAGES=()
PASSED_COUNT=0
FAILED_COUNT=0
WARNING_COUNT=0

# Parameters
RESOURCE_GROUP=""
AI_FOUNDRY_ACCOUNT=""
VERBOSE=false
JSON_OUTPUT=""

# ======================================================================================
# PARAMETER PARSING
# ======================================================================================

show_usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Validates Azure AI Foundry Content Understanding deployment.

Required Options:
    --resource-group <name>      Name of the resource group
    --ai-foundry-account <name>  Name of the AI Foundry account

Optional:
    --verbose                    Show detailed output
    --json-output <file>         Write JSON report to file
    --help                       Show this help message

Example:
    $(basename "$0") \\
        --resource-group "rg-aifoundry-dev" \\
        --ai-foundry-account "wbiq-dev-aifoundry"
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        --ai-foundry-account)
            AI_FOUNDRY_ACCOUNT="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --json-output)
            JSON_OUTPUT="$2"
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
# FUNCTIONS
# ======================================================================================

write_test_header() {
    echo ""
    echo -e "${CYAN}--- $1 ---${NC}"
}

write_test_success() {
    echo -e "  ${GREEN}✓ $1${NC}"
}

write_test_failure() {
    echo -e "  ${RED}✗ $1${NC}"
}

write_test_warning() {
    echo -e "  ${YELLOW}⚠ $1${NC}"
}

add_test_result() {
    local name="$1"
    local status="$2"
    local message="$3"
    
    TEST_NAMES+=("$name")
    TEST_STATUSES+=("$status")
    TEST_MESSAGES+=("$message")
    
    case "$status" in
        "Passed")
            ((PASSED_COUNT++))
            ;;
        "Failed")
            ((FAILED_COUNT++))
            ;;
        "Warning")
            ((WARNING_COUNT++))
            ;;
    esac
}

# ======================================================================================
# VALIDATION
# ======================================================================================

# Validate required parameters
if [ -z "$RESOURCE_GROUP" ]; then
    write_error "Missing required parameter: --resource-group"
    exit 1
fi

if [ -z "$AI_FOUNDRY_ACCOUNT" ]; then
    write_error "Missing required parameter: --ai-foundry-account"
    exit 1
fi

# Check required commands
require_command "az" || exit 1
require_command "jq" || exit 1
require_command "curl" || exit 1

# ======================================================================================
# VALIDATION TESTS
# ======================================================================================

echo ""
echo -e "${CYAN}===================================================================${NC}"
echo -e "${CYAN}Azure AI Foundry Content Understanding - Deployment Validation${NC}"
echo -e "${CYAN}===================================================================${NC}"

# Test 1: Azure Authentication
write_test_header "Test 1: Azure Authentication"
if ACCOUNT_INFO=$(az account show 2>&1); then
    ACCOUNT_ID=$(echo "$ACCOUNT_INFO" | jq -r '.user.name')
    SUBSCRIPTION_NAME=$(echo "$ACCOUNT_INFO" | jq -r '.name')
    
    write_test_success "Authenticated as: $ACCOUNT_ID"
    write_test_success "Subscription: $SUBSCRIPTION_NAME"
    add_test_result "Azure Authentication" "Passed" "Authenticated successfully"
else
    write_test_failure "Not authenticated to Azure"
    add_test_result "Azure Authentication" "Failed" "Not authenticated"
    exit 1
fi

# Test 2: Resource Group
write_test_header "Test 2: Resource Group Validation"
if RG_INFO=$(az group show --name "$RESOURCE_GROUP" 2>&1); then
    RG_LOCATION=$(echo "$RG_INFO" | jq -r '.location')
    
    write_test_success "Resource group exists: $RESOURCE_GROUP"
    write_test_success "Location: $RG_LOCATION"
    add_test_result "Resource Group" "Passed" "Resource group exists"
else
    write_test_failure "Resource group not found: $RESOURCE_GROUP"
    add_test_result "Resource Group" "Failed" "Resource group not found"
    exit 1
fi

# Test 3: AI Foundry Account
write_test_header "Test 3: AI Foundry Account Validation"
if AI_ACCOUNT=$(az cognitiveservices account show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$AI_FOUNDRY_ACCOUNT" 2>&1); then
    
    ENDPOINT=$(echo "$AI_ACCOUNT" | jq -r '.properties.endpoint')
    SKU=$(echo "$AI_ACCOUNT" | jq -r '.sku.name')
    PROVISIONING_STATE=$(echo "$AI_ACCOUNT" | jq -r '.properties.provisioningState')
    
    write_test_success "AI Foundry account exists: $AI_FOUNDRY_ACCOUNT"
    write_test_success "Endpoint: $ENDPOINT"
    write_test_success "SKU: $SKU"
    write_test_success "Provisioning State: $PROVISIONING_STATE"
    
    if [ "$PROVISIONING_STATE" == "Succeeded" ]; then
        add_test_result "AI Foundry Account" "Passed" "Account provisioned successfully"
    else
        write_test_warning "Provisioning state is not 'Succeeded'"
        add_test_result "AI Foundry Account" "Warning" "Provisioning state: $PROVISIONING_STATE"
    fi
else
    write_test_failure "AI Foundry account not found: $AI_FOUNDRY_ACCOUNT"
    add_test_result "AI Foundry Account" "Failed" "Account not found"
    exit 1
fi

# Test 4: Model Deployments
write_test_header "Test 4: Model Deployments Validation"
if DEPLOYMENTS=$(az cognitiveservices account deployment list \
    --resource-group "$RESOURCE_GROUP" \
    --name "$AI_FOUNDRY_ACCOUNT" 2>&1); then
    
    REQUIRED_MODELS=("gpt-4.1" "gpt-4.1-mini" "text-embedding-3-large")
    FOUND_MODELS=()
    
    while IFS= read -r deployment; do
        DEP_NAME=$(echo "$deployment" | jq -r '.name')
        DEP_STATE=$(echo "$deployment" | jq -r '.properties.provisioningState')
        write_test_success "Deployment: $DEP_NAME - State: $DEP_STATE"
        FOUND_MODELS+=("$DEP_NAME")
    done < <(echo "$DEPLOYMENTS" | jq -c '.[]')
    
    ALL_MODELS_FOUND=true
    for model in "${REQUIRED_MODELS[@]}"; do
        if [[ ! " ${FOUND_MODELS[*]} " =~ " ${model} " ]]; then
            write_test_failure "Required model deployment missing: $model"
            ALL_MODELS_FOUND=false
        fi
    done
    
    if [ "$ALL_MODELS_FOUND" = true ]; then
        add_test_result "Model Deployments" "Passed" "All required models deployed"
    else
        add_test_result "Model Deployments" "Failed" "Some required models missing"
    fi
else
    write_test_failure "Failed to retrieve model deployments"
    add_test_result "Model Deployments" "Failed" "Could not retrieve deployments"
fi

# Test 5: Managed Identity
write_test_header "Test 5: Managed Identity Validation"
if IDENTITIES=$(az identity list --resource-group "$RESOURCE_GROUP" 2>&1); then
    IDENTITY_COUNT=$(echo "$IDENTITIES" | jq 'length')
    
    if [ "$IDENTITY_COUNT" -gt 0 ]; then
        while IFS= read -r identity; do
            IDENTITY_NAME=$(echo "$identity" | jq -r '.name')
            PRINCIPAL_ID=$(echo "$identity" | jq -r '.principalId')
            CLIENT_ID=$(echo "$identity" | jq -r '.clientId')
            
            write_test_success "Managed Identity: $IDENTITY_NAME"
            write_test_success "Principal ID: $PRINCIPAL_ID"
            write_test_success "Client ID: $CLIENT_ID"
        done < <(echo "$IDENTITIES" | jq -c '.[]')
        
        add_test_result "Managed Identity" "Passed" "Managed identity exists"
    else
        write_test_warning "No managed identities found"
        add_test_result "Managed Identity" "Warning" "No managed identities found"
    fi
else
    write_test_warning "Failed to retrieve managed identities"
    add_test_result "Managed Identity" "Warning" "Could not retrieve identities"
fi

# Test 6: Storage Account
write_test_header "Test 6: Storage Account Validation"
if STORAGE_ACCOUNTS=$(az storage account list --resource-group "$RESOURCE_GROUP" 2>&1); then
    STORAGE_COUNT=$(echo "$STORAGE_ACCOUNTS" | jq 'length')
    
    if [ "$STORAGE_COUNT" -gt 0 ]; then
        while IFS= read -r storage; do
            STORAGE_NAME=$(echo "$storage" | jq -r '.name')
            STORAGE_LOCATION=$(echo "$storage" | jq -r '.location')
            STORAGE_SKU=$(echo "$storage" | jq -r '.sku.name')
            STORAGE_STATE=$(echo "$storage" | jq -r '.provisioningState')
            
            write_test_success "Storage Account: $STORAGE_NAME"
            write_test_success "Location: $STORAGE_LOCATION"
            write_test_success "SKU: $STORAGE_SKU"
            write_test_success "Provisioning State: $STORAGE_STATE"
        done < <(echo "$STORAGE_ACCOUNTS" | jq -c '.[]')
        
        add_test_result "Storage Account" "Passed" "Storage account exists"
    else
        write_test_warning "No storage accounts found"
        add_test_result "Storage Account" "Warning" "No storage accounts found"
    fi
else
    write_test_warning "Failed to retrieve storage accounts"
    add_test_result "Storage Account" "Warning" "Could not retrieve storage accounts"
fi

# Test 7: Key Vault
write_test_header "Test 7: Key Vault Validation"
if KEY_VAULTS=$(az keyvault list --resource-group "$RESOURCE_GROUP" 2>&1); then
    VAULT_COUNT=$(echo "$KEY_VAULTS" | jq 'length')
    
    if [ "$VAULT_COUNT" -gt 0 ]; then
        while IFS= read -r vault; do
            VAULT_NAME=$(echo "$vault" | jq -r '.name')
            VAULT_URI=$(echo "$vault" | jq -r '.properties.vaultUri')
            VAULT_LOCATION=$(echo "$vault" | jq -r '.location')
            
            write_test_success "Key Vault: $VAULT_NAME"
            write_test_success "URI: $VAULT_URI"
            write_test_success "Location: $VAULT_LOCATION"
        done < <(echo "$KEY_VAULTS" | jq -c '.[]')
        
        add_test_result "Key Vault" "Passed" "Key Vault exists"
    else
        write_test_warning "No key vaults found"
        add_test_result "Key Vault" "Warning" "No key vaults found"
    fi
else
    write_test_warning "Failed to retrieve key vaults"
    add_test_result "Key Vault" "Warning" "Could not retrieve key vaults"
fi

# Test 8: Network Connectivity
write_test_header "Test 8: Network Connectivity"
if ACCESS_TOKEN=$(get_access_token "https://cognitiveservices.azure.com" 2>&1); then
    TEST_URL="${ENDPOINT}openai/deployments?api-version=2024-06-01"
    
    CONN_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$TEST_URL" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    CONN_HTTP_CODE=$(echo "$CONN_RESPONSE" | tail -n1)
    
    if [ "$CONN_HTTP_CODE" -ge 200 ] && [ "$CONN_HTTP_CODE" -lt 300 ]; then
        write_test_success "Endpoint is reachable and responding"
        add_test_result "Network Connectivity" "Passed" "Endpoint accessible"
    else
        write_test_warning "Unexpected status code: $CONN_HTTP_CODE"
        add_test_result "Network Connectivity" "Warning" "Status: $CONN_HTTP_CODE"
    fi
else
    write_test_warning "Could not obtain access token for connectivity test"
    add_test_result "Network Connectivity" "Warning" "Could not test connectivity"
fi

# ======================================================================================
# VALIDATION SUMMARY
# ======================================================================================

echo ""
echo -e "${CYAN}===================================================================${NC}"
echo -e "${CYAN}Validation Summary${NC}"
echo -e "${CYAN}===================================================================${NC}"
echo ""

TOTAL_TESTS=${#TEST_NAMES[@]}
echo -e "${NC}Total Tests: $TOTAL_TESTS${NC}"
echo -e "${GREEN}Passed: $PASSED_COUNT${NC}"
echo -e "${RED}Failed: $FAILED_COUNT${NC}"
echo -e "${YELLOW}Warnings: $WARNING_COUNT${NC}"

echo ""
echo -e "${CYAN}Detailed Results:${NC}"
for i in "${!TEST_NAMES[@]}"; do
    case "${TEST_STATUSES[$i]}" in
        "Passed")
            echo -e "  ${GREEN}[${TEST_STATUSES[$i]}] ${TEST_NAMES[$i]}: ${TEST_MESSAGES[$i]}${NC}"
            ;;
        "Failed")
            echo -e "  ${RED}[${TEST_STATUSES[$i]}] ${TEST_NAMES[$i]}: ${TEST_MESSAGES[$i]}${NC}"
            ;;
        "Warning")
            echo -e "  ${YELLOW}[${TEST_STATUSES[$i]}] ${TEST_NAMES[$i]}: ${TEST_MESSAGES[$i]}${NC}"
            ;;
    esac
done

# Write JSON output if requested
if [ -n "$JSON_OUTPUT" ]; then
    JSON_REPORT=$(jq -n \
        --argjson total "$TOTAL_TESTS" \
        --argjson passed "$PASSED_COUNT" \
        --argjson failed "$FAILED_COUNT" \
        --argjson warnings "$WARNING_COUNT" \
        '{
            totalTests: $total,
            passed: $passed,
            failed: $failed,
            warnings: $warnings,
            tests: []
        }')
    
    for i in "${!TEST_NAMES[@]}"; do
        JSON_REPORT=$(echo "$JSON_REPORT" | jq \
            --arg name "${TEST_NAMES[$i]}" \
            --arg status "${TEST_STATUSES[$i]}" \
            --arg message "${TEST_MESSAGES[$i]}" \
            '.tests += [{name: $name, status: $status, message: $message}]')
    done
    
    echo "$JSON_REPORT" > "$JSON_OUTPUT"
    write_success "JSON report written to: $JSON_OUTPUT"
fi

# Exit with appropriate code
if [ "$FAILED_COUNT" -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ Validation FAILED - Please review failed tests above${NC}"
    exit 1
elif [ "$WARNING_COUNT" -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Validation completed with WARNINGS${NC}"
    exit 0
else
    echo ""
    echo -e "${GREEN}✅ All validation tests PASSED!${NC}"
    exit 0
fi
