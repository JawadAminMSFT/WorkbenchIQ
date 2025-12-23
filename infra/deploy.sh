#!/usr/bin/env bash

# ======================================================================================
# deploy.sh
# ======================================================================================
# SYNOPSIS
#     Deploys Workbench IQ infrastructure.
#
# DESCRIPTION
#     This script orchestrates the complete deployment process:
#     - Phase 1-3: Deploys Bicep templates (Foundation, AI Foundry, Models)
#     - Phase 4: Configures Content Understanding default model mappings
#     - Phase 5: Validates the deployment
#     
#     The Bicep template creates the resource group automatically based on the
#     baseName and environmentName variables (default: rg-wbiq-dev).
#
# PARAMETERS
#     --location <region>              Azure region for deployment (default: westus)
#     --template-file <path>           Path to main Bicep template (default: ./main.bicep)
#     --parameter-file <path>          Path to Bicep parameters (default: ./main.bicepparam)
#     --skip-validation                Skip post-deployment validation
#     --skip-configuration             Skip Content Understanding configuration
#     --yes                            Skip confirmation prompt
#
# EXAMPLE
#     ./deploy.sh
#     ./deploy.sh --location "westus"
#     ./deploy.sh --location "eastus" --skip-validation
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

# Script paths
CONFIG_SCRIPT="$SCRIPT_DIR/configure-content-understanding.sh"
VALIDATE_SCRIPT="$SCRIPT_DIR/validate-deployment.sh"

# Default parameters
LOCATION="westus"
SHORT_NAME="wbiq"
TEMPLATE_FILE="$SCRIPT_DIR/main.bicep"
PARAMETER_FILE="$SCRIPT_DIR/main.bicepparam"
SKIP_VALIDATION=false
YES=false

# ======================================================================================
# PARAMETER PARSING
# ======================================================================================

show_usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Deploys Workbench IQ infrastructure.

Options:
    --location <region>              Azure region for deployment (default: westus)
    --short-name <name>              Short name for resource prefix, 2-5 characters (default: wbiq)
    --template-file <path>           Path to main Bicep template (default: ./main.bicep)
    --parameter-file <path>          Path to Bicep parameters (default: ./main.bicepparam)
    --skip-validation                Skip post-deployment validation
    --yes                            Skip confirmation prompt
    --help                           Show this help message

Example:
    $(basename "$0")
    $(basename "$0") --location "westus" --short-name "myapp"
    $(basename "$0") --location "eastus" --skip-validation
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --location)
            LOCATION="$2"
            shift 2
            ;;
        --short-name)
            SHORT_NAME="$2"
            shift 2
            ;;
        --template-file)
            TEMPLATE_FILE="$2"
            shift 2
            ;;
        --parameter-file)
            PARAMETER_FILE="$2"
            shift 2
            ;;
        --skip-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        --yes)
            YES=true
            shift
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
# STARTUP BANNER
# ======================================================================================

clear
echo ""
echo -e "${CYAN}========================================================================${NC}"
echo -e "${CYAN}   Workbench IQ - Deployment Script   ${NC}"
echo -e "${CYAN}========================================================================${NC}"
echo ""
echo -e "${NC}This script will deploy:${NC}"
echo -e "  ${NC}• Resource Group${NC}"
echo -e "  ${NC}• Managed Identity${NC}"
echo -e "  ${NC}• Storage Account${NC}"
echo -e "  ${NC}• Key Vault${NC}"
echo -e "  ${NC}• AI Foundry Account & Project${NC}"
echo -e "  ${NC}• Model Deployments (GPT-4o, GPT-4o-mini, Text-Embedding)${NC}"
echo ""

# ======================================================================================
# PARAMETER VALIDATION
# ======================================================================================

echo -e "${CYAN}Deployment Configuration:${NC}"
echo -e "  Short Name: ${NC}$SHORT_NAME${NC}"
echo -e "  Location: ${NC}$LOCATION${NC}"
echo -e "  Template: ${NC}$TEMPLATE_FILE${NC}"
echo -e "  Parameters: ${NC}$PARAMETER_FILE${NC}"
echo ""
echo -e "  ${NC}Note: Resource group name will be: rg-$SHORT_NAME-dev${NC}"
echo ""

if [ "$YES" = false ]; then
    read -r -p "Proceed with deployment? (Y/n): " confirmation
    if [[ "$confirmation" =~ ^[Nn]$ ]]; then
        echo -e "${YELLOW}Deployment cancelled by user${NC}"
        exit 0
    fi
fi

# ======================================================================================
# PRE-DEPLOYMENT CHECKS
# ======================================================================================

write_header "Pre-Deployment Checks"

# Check required commands
require_command "az" || exit 1
require_command "jq" || exit 1
require_command "bicep" || exit 1

# Check Azure authentication
write_info "Checking Azure authentication..."
check_azure_auth || exit 1

ACCOUNT_INFO=$(az account show)
ACCOUNT_ID=$(echo "$ACCOUNT_INFO" | jq -r '.user.name')
SUBSCRIPTION_NAME=$(echo "$ACCOUNT_INFO" | jq -r '.name')
SUBSCRIPTION_ID=$(echo "$ACCOUNT_INFO" | jq -r '.id')

write_success "Logged in as: $ACCOUNT_ID"
write_success "Subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"

# Check template files exist
if [ ! -f "$TEMPLATE_FILE" ]; then
    write_error "Template file not found: $TEMPLATE_FILE"
    exit 1
fi
write_success "Found template file: $TEMPLATE_FILE"

if [ ! -f "$PARAMETER_FILE" ]; then
    write_error "Parameter file not found: $PARAMETER_FILE"
    exit 1
fi
write_success "Found parameter file: $PARAMETER_FILE"

# Validate Bicep template
write_info "Validating Bicep template..."
if bicep build "$TEMPLATE_FILE" --stdout --no-restore &>/dev/null; then
    write_success "Bicep template is valid"
else
    write_error "Bicep build failed. Please fix errors and retry."
    bicep build "$TEMPLATE_FILE" --stdout --no-restore
    exit 1
fi

# ======================================================================================
# PHASE 1-3: BICEP DEPLOYMENT
# ======================================================================================

write_header "Phase 1-3: Deploying Infrastructure (Foundation, AI Foundry, Models)"

DEPLOYMENT_NAME="aifoundry-cu-$(date +%Y%m%d%H%M%S)"

write_info "Starting subscription-level deployment: $DEPLOYMENT_NAME"
write_info "This may take 10-15 minutes..."

# Get current user's object ID for role assignment
DEPLOYER_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv 2>/dev/null || echo "")
if [ -n "$DEPLOYER_OBJECT_ID" ]; then
    write_info "Detected deployer object ID: $DEPLOYER_OBJECT_ID"
fi

# Suppress Bicep CLI installation messages by setting environment variable
export AZURE_BICEP_USE_BINARY_FROM_PATH=true

# Run deployment and capture output, filtering out non-JSON lines
DEPLOYMENT_RAW_OUTPUT=$(az deployment sub create \
    --name "$DEPLOYMENT_NAME" \
    --location "$LOCATION" \
    --template-file "$TEMPLATE_FILE" \
    --parameters "$PARAMETER_FILE" \
    --parameters baseName="$SHORT_NAME" \
    --parameters deployerObjectId="$DEPLOYER_OBJECT_ID" \
    --query '{provisioningState: properties.provisioningState, outputs: properties.outputs}' \
    --only-show-errors \
    -o json 2>&1)

DEPLOYMENT_EXIT_CODE=$?

# Extract only the JSON part (starts with '{' or '[')
DEPLOYMENT_OUTPUT=$(echo "$DEPLOYMENT_RAW_OUTPUT" | sed -n '/^[{[]/,$p')

if [ $DEPLOYMENT_EXIT_CODE -ne 0 ]; then
    write_error "Deployment failed"
    echo "$DEPLOYMENT_RAW_OUTPUT"
    exit 1
fi

PROVISIONING_STATE=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.provisioningState')

if [ "$PROVISIONING_STATE" == "Succeeded" ]; then
    write_success "Bicep deployment completed successfully"
    
    # Extract outputs
    OUTPUTS=$(echo "$DEPLOYMENT_OUTPUT" | jq '.outputs')
    RESOURCE_GROUP_NAME=$(echo "$OUTPUTS" | jq -r '.resourceGroupName.value')
    AI_FOUNDRY_ACCOUNT_NAME=$(echo "$OUTPUTS" | jq -r '.aiFoundryAccountName.value')
    AI_FOUNDRY_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.aiFoundryAccountEndpoint.value')
    MANAGED_IDENTITY_CLIENT_ID=$(echo "$OUTPUTS" | jq -r '.managedIdentityClientId.value')
    MODEL_DEPLOYMENTS=$(echo "$OUTPUTS" | jq -r '.modelDeployments.value')
    ENVIRONMENT_CONFIG=$(echo "$OUTPUTS" | jq -r '.environmentConfig.value')
    
    echo ""
    echo -e "${CYAN}Deployment Outputs:${NC}"
    echo "$OUTPUTS" | jq -r 'to_entries | .[] | "  \(.key): \(.value.value)"'
else
    write_error "Deployment failed with state: $PROVISIONING_STATE"
    exit 1
fi

# ======================================================================================
# PHASE 4: CONTENT UNDERSTANDING CONFIGURATION (SKIPPED)
# ======================================================================================

# Content Understanding configuration is now a separate manual step
# This allows role assignments time to propagate before configuration
write_info "Skipping Content Understanding configuration (run separately)"
write_info "Role assignments may need a few minutes to propagate"

# ======================================================================================
# PHASE 5: VALIDATION
# ======================================================================================

if [ "$SKIP_VALIDATION" = false ]; then
    write_header "Phase 5: Validating Deployment"
    
    if [ ! -f "$VALIDATE_SCRIPT" ]; then
        write_warning "Validation script not found: $VALIDATE_SCRIPT"
        write_warning "Skipping validation"
    else
        write_info "Running deployment validation..."
        
        if bash "$VALIDATE_SCRIPT" \
            --resource-group "$RESOURCE_GROUP_NAME" \
            --ai-foundry-account "$AI_FOUNDRY_ACCOUNT_NAME"; then
            write_success "Validation passed"
        else
            EXIT_CODE=$?
            if [ $EXIT_CODE -eq 0 ]; then
                write_success "Validation passed"
            else
                write_warning "Validation completed with warnings"
            fi
        fi
    fi
else
    write_info "Skipping validation (--skip-validation flag set)"
fi

# ======================================================================================
# DEPLOYMENT SUMMARY
# ======================================================================================

write_header "Deployment Summary"

echo -e "${NC}Resource Group: ${NC}$RESOURCE_GROUP_NAME${NC}"
echo -e "${NC}AI Foundry Account: ${NC}$AI_FOUNDRY_ACCOUNT_NAME${NC}"
echo -e "${NC}Endpoint: ${NC}$AI_FOUNDRY_ENDPOINT${NC}"
echo -e "${NC}Managed Identity Client ID: ${NC}$MANAGED_IDENTITY_CLIENT_ID${NC}"

echo ""
echo -e "${CYAN}Model Deployments:${NC}"
echo "$MODEL_DEPLOYMENTS" | jq -r 'to_entries | .[] | "  - \(.key): \(.value)"'

echo ""
echo -e "${CYAN}Environment Configuration:${NC}"
echo "$ENVIRONMENT_CONFIG" | jq -r 'to_entries | .[] | "  \(.key)=\(.value)"'

echo ""
write_success "Deployment completed successfully!"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "${NC}1. Wait 2-3 minutes for role assignments to propagate${NC}"
echo -e "${NC}2. Configure Content Understanding by running:${NC}"
echo -e "${CYAN}   ./configure-content-understanding.sh \\${NC}"
echo -e "${CYAN}     --ai-foundry-endpoint \"$AI_FOUNDRY_ENDPOINT\" \\${NC}"
echo -e "${CYAN}     --gpt4-deployment \"gpt-4.1\" \\${NC}"
echo -e "${CYAN}     --gpt4-mini-deployment \"gpt-4.1-mini\" \\${NC}"
echo -e "${CYAN}     --embedding-deployment \"text-embedding-3-large\"${NC}"
echo -e "${NC}3. Update your .env file with the environment configuration above${NC}"
echo -e "${NC}4. Review the deployment validation results${NC}"

exit 0
