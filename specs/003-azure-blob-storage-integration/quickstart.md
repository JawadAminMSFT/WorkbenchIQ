# Quickstart: Azure Blob Storage Integration

**Feature**: 003-azure-blob-storage-integration  
**Date**: 2025-12-08

## Overview

This guide explains how to configure WorkbenchIQ to use Azure Blob Storage instead of local filesystem storage.

## Prerequisites

- Azure subscription with a Storage Account
- Storage account access keys (found in Azure Portal → Storage Account → Access keys)
- WorkbenchIQ backend running

## Configuration

### Option 1: Local Storage (Default)

No configuration needed. The application uses local filesystem storage by default.

```bash
# These are the defaults - no action required
# STORAGE_BACKEND=local
# UW_APP_STORAGE_ROOT=data
```

### Option 2: Azure Blob Storage

Set the following environment variables:

```bash
# Required
export STORAGE_BACKEND=azure_blob
export AZURE_STORAGE_ACCOUNT_NAME=your_storage_account_name
export AZURE_STORAGE_ACCOUNT_KEY=your_storage_account_key

# Optional (defaults shown)
export AZURE_STORAGE_CONTAINER_NAME=workbenchiq-data
```

### Using .env File

Add to your `.env` file:

```env
STORAGE_BACKEND=azure_blob
AZURE_STORAGE_ACCOUNT_NAME=mystorageaccount
AZURE_STORAGE_ACCOUNT_KEY=abc123...base64key...==
AZURE_STORAGE_CONTAINER_NAME=workbenchiq-data
```

## Verification

### 1. Check Configuration at Startup

When the application starts, it validates the storage configuration. Look for:

```
INFO: Storage backend: azure_blob
INFO: Storage container: workbenchiq-data
```

If configuration is invalid:
```
ERROR: AZURE_STORAGE_ACCOUNT_NAME is not set (required when STORAGE_BACKEND=azure_blob)
```

### 2. Test File Upload

Upload a test document through the UI or API:

```bash
curl -X POST "http://localhost:8000/applications" \
  -F "files=@test-document.pdf" \
  -F "external_reference=test-001"
```

### 3. Verify in Azure Portal

1. Go to Azure Portal → Your Storage Account
2. Navigate to Containers → `workbenchiq-data`
3. Browse to `applications/{app_id}/files/`
4. Confirm uploaded file appears

## Troubleshooting

### "Storage authentication failed"

- Verify `AZURE_STORAGE_ACCOUNT_KEY` is correct
- Check key hasn't been rotated in Azure Portal
- Ensure no extra whitespace in environment variable

### "Container creation failed"

- Verify `AZURE_STORAGE_CONTAINER_NAME` follows naming rules:
  - 3-63 characters
  - Lowercase letters, numbers, and hyphens only
  - Cannot start or end with hyphen
  - No consecutive hyphens

### "Storage operation timed out"

- Default timeout is 30 seconds per operation
- Large files (>50MB) may need network optimization
- Check Azure Storage Account network settings (firewall rules)

### "Application not found" after switching backends

- Data is NOT migrated between backends
- When switching from local to Azure Blob, existing local applications are not accessible
- Upload new documents to populate Azure Blob Storage

## Azure Storage Account Setup (if needed)

### Create Storage Account (Azure CLI)

```bash
# Create resource group
az group create --name workbenchiq-rg --location eastus

# Create storage account
az storage account create \
  --name workbenchiqstorage \
  --resource-group workbenchiq-rg \
  --location eastus \
  --sku Standard_LRS

# Get access key
az storage account keys list \
  --account-name workbenchiqstorage \
  --resource-group workbenchiq-rg \
  --query '[0].value' -o tsv
```

### Create Storage Account (Azure Portal)

1. Go to Azure Portal → Create a resource → Storage account
2. Fill in:
   - **Resource group**: Create new or select existing
   - **Storage account name**: Unique name (3-24 lowercase letters/numbers)
   - **Region**: Select closest region
   - **Performance**: Standard
   - **Redundancy**: LRS (for development) or GRS (for production)
3. Click Review + create → Create
4. After deployment, go to Access keys and copy Key1

## Security Recommendations

### Production Deployments

1. **Use Azure Key Vault**: Store storage keys in Key Vault instead of environment variables
2. **Enable HTTPS only**: In storage account settings, require secure transfer
3. **Network restrictions**: Configure firewall to allow only your application's IP/VNet
4. **Key rotation**: Implement key rotation schedule

### Development

- Use `.env` file (not committed to source control)
- Consider using Azure Storage Emulator (Azurite) for local development

## Next Steps

- [Full API Documentation](../../README.md)
- [Azure Blob Storage Documentation](https://learn.microsoft.com/en-us/azure/storage/blobs/)
- [Storage Retry Policies](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-retry-policy-python)
