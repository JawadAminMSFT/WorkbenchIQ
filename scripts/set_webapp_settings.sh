#!/bin/bash

# Script to set Azure Web App settings from .env file
# Usage: ./set_webapp_settings.sh -g <resource-group> -n <webapp-name> [-e <env-file>]

set -e

# Default values
ENV_FILE=".env"
RESOURCE_GROUP=""
WEBAPP_NAME=""

# Parse command line arguments
while getopts "g:n:e:h" opt; do
    case $opt in
        g) RESOURCE_GROUP="$OPTARG" ;;
        n) WEBAPP_NAME="$OPTARG" ;;
        e) ENV_FILE="$OPTARG" ;;
        h)
            echo "Usage: $0 -g <resource-group> -n <webapp-name> [-e <env-file>]"
            echo ""
            echo "Options:"
            echo "  -g    Azure resource group name (required)"
            echo "  -n    Azure web app name (required)"
            echo "  -e    Path to .env file (default: .env)"
            echo "  -h    Show this help message"
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$RESOURCE_GROUP" ] || [ -z "$WEBAPP_NAME" ]; then
    echo "Error: Resource group (-g) and web app name (-n) are required."
    echo "Usage: $0 -g <resource-group> -n <webapp-name> [-e <env-file>]"
    exit 1
fi

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file '$ENV_FILE' not found."
    exit 1
fi

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo "Error: Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

echo "=========================================="
echo "Azure Web App Settings Deployment"
echo "=========================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "Web App Name:   $WEBAPP_NAME"
echo "Env File:       $ENV_FILE"
echo "=========================================="

# Build the settings array
SETTINGS=()

while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    if [[ -z "$line" ]] || [[ "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Remove leading/trailing whitespace
    line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    
    # Skip if line doesn't contain '='
    if [[ ! "$line" =~ = ]]; then
        continue
    fi
    
    # Extract key and value
    key=$(echo "$line" | cut -d'=' -f1)
    value=$(echo "$line" | cut -d'=' -f2-)
    
    # Skip empty keys
    if [ -z "$key" ]; then
        continue
    fi
    
    # Add to settings array
    SETTINGS+=("$key=$value")
    echo "  Setting: $key"
    
done < "$ENV_FILE"

# Check if we have any settings to apply
if [ ${#SETTINGS[@]} -eq 0 ]; then
    echo "No settings found in $ENV_FILE"
    exit 0
fi

echo ""
echo "Applying ${#SETTINGS[@]} settings to web app..."
echo ""

# Apply settings using Azure CLI
az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$WEBAPP_NAME" \
    --settings "${SETTINGS[@]}" \
    --output table

echo ""
echo "=========================================="
echo "Settings applied successfully!"
echo "=========================================="
