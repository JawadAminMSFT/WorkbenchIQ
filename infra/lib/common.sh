#!/usr/bin/env bash

# Common functions library for Azure AI Foundry deployment scripts

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Output functions
write_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

write_error() {
    echo -e "${RED}✗ $1${NC}" >&2
}

write_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

write_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

write_header() {
    echo ""
    echo -e "${CYAN}===================================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}===================================================================${NC}"
    echo ""
}

# Azure authentication check
check_azure_auth() {
    if ! az account show &>/dev/null; then
        write_error "Not logged in to Azure. Please run 'az login'"
        return 1
    fi
    return 0
}

# Get Azure access token
get_access_token() {
    local resource="${1:-https://cognitiveservices.azure.com}"
    local token
    
    token=$(az account get-access-token --resource "$resource" --query accessToken -o tsv 2>/dev/null)
    if [ -z "$token" ]; then
        write_error "Failed to obtain access token for resource: $resource"
        return 1
    fi
    
    echo "$token"
    return 0
}

# Check required commands
require_command() {
    if ! command -v "$1" &>/dev/null; then
        write_error "Required command not found: $1"
        return 1
    fi
    return 0
}

# JSON validation
validate_json() {
    echo "$1" | jq empty 2>/dev/null
    return $?
}
