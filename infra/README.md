# Azure AI Foundry v2 with Content Understanding - Bicep Deployment

This directory contains Bicep Infrastructure as Code templates to deploy Azure AI Foundry v2 with Content Understanding service.

## 📋 Prerequisites

1. **Azure Subscription** with sufficient permissions:
   - Contributor role at subscription level (for resource group creation)
   - User Access Administrator role (for RBAC assignments)

2. **Required Tools:**
   - Azure CLI (version 2.56.0 or later) - [Install](https://learn.microsoft.com/cli/azure/install-azure-cli)
   - Bicep CLI (included with Azure CLI)
   - jq (version 1.6+) - For JSON processing in bash scripts
   - curl - For REST API calls (standard with most Linux distributions)

3. **Quotas:**
   - Cognitive Services (S0 SKU)
   - Storage Accounts
   - Key Vault

## 🏗️ Architecture

The deployment creates:

- **Resource Group**: `rg-wbiq-dev` (automatically created)
- **Managed Identity**: User-assigned identity for secure authentication
- **Storage Account**: Azure Storage for AI agent data (Standard_LRS)
- **Key Vault**: Secure storage for application secrets
- **AI Foundry Account**: Azure Cognitive Services (S0 SKU)
- **AI Foundry Project**: Content Understanding workspace
- **Model Deployments**:
  - GPT-4.1 (GlobalStandard, capacity: 10)
  - GPT-4.1-mini (GlobalStandard, capacity: 10)
  - Text-Embedding-3-Large (Standard, capacity: 10)

## 📁 Files

```
infra/
├── main.bicep                          # Main template (subscription scope)
├── main.bicepparam                     # Parameters (location only)
├── deploy.sh                           # Deployment orchestration script
├── configure-content-understanding.sh  # Content Understanding configuration
├── validate-deployment.sh              # Deployment validation script
├── lib/
│   └── common.sh                       # Common bash functions library
└── README.md                           # This file
```

## 🚀 Quick Start

### Deployment Script

The `deploy.sh` script provides an automated subscription-level deployment with validation and configuration.

#### 1. Login to Azure

```bash
# Login to Azure
az login

# Set subscription (if you have multiple)
az account set --subscription "your-subscription-id"

# Verify context
az account show
```

#### 2. Run Deployment

```bash
# Simple deployment (uses defaults: location=westus, resource group=rg-wbiq-dev)
./deploy.sh

# Specify location
./deploy.sh --location "westus"

# Skip validation
./deploy.sh --location "eastus" --skip-validation

# Skip confirmation prompt
./deploy.sh --yes
```

The script will:
- ✓ Display a deployment banner with planned resources
- ✓ Ask for confirmation before proceeding (unless --yes flag is used)
- ✓ Validate your Azure authentication
- ✓ Check Bicep template syntax
- ✓ Create the resource group (automatically based on template variables)
- ✓ Deploy all infrastructure (10-15 minutes)
- ✓ Configure Content Understanding defaults
- ✓ Validate the deployment
- ✓ Display deployment summary with endpoints and configuration

**Note**: The resource group name (`rg-wbiq-dev`) is defined in the Bicep template variables. To customize it, edit the `baseName` and `environmentName` variables in [main.bicep](main.bicep).

#### 3. Review Outputs

The script will display:
- Resource group name
- AI Foundry endpoint
- Managed Identity Client ID
- Model deployment names
- Environment variables for your `.env` file

## 🔧 Manual Configuration Scripts

If you need to run configuration or validation independently:

### Configure Content Understanding

```bash
# Bash
./configure-content-understanding.sh \
  --ai-foundry-endpoint "https://your-account.openai.azure.com/" \
  --gpt4-deployment "gpt-4.1" \
  --gpt4-mini-deployment "gpt-4.1-mini" \
  --embedding-deployment "text-embedding-3-large"

# PowerShell (Windows)
.\configure-content-understanding.ps1 `
  -AiFoundryEndpoint "https://your-account.openai.azure.com/" `
  -ModelDeployments @{'gpt-4.1'='gpt-4.1'; 'gpt-4.1-mini'='gpt-4.1-mini'; 'text-embedding-3-large'='text-embedding-3-large'}
```

### Validate Deployment

```bash
./validate-deployment.sh \
  --resource-group "rg-aifoundry-dev" \
  --ai-foundry-account "wbiq-dev-aifoundry"

# With JSON output
./validate-deployment.sh \
  --resource-group "rg-aifoundry-dev" \
  --ai-foundry-account "wbiq-dev-aifoundry" \
  --json-output validation-report.json
```

## Azure CLI (Manual Deployment)

#### 1. Configure Location (Optional)

Edit [main.bicepparam](main.bicepparam):

```bicep
param location = 'eastus'  // Change to your preferred region
```

**Default values** (edit [main.bicep](main.bicep) to customize):
- `baseName`: `wbiq`
- `environmentName`: `dev`
- `resourceGroupName`: `rg-wbiq-dev` (auto-created)

#### 2. Login to Azure

```bash
# Login to Azure
./configure-content-understanding.sh \
  --ai-foundry-endpoint "https://your-account.openai.azure.com/" \
  --gpt4-deployment "gpt-4.1" \
  --gpt4-mini-deployment "gpt-4.1-mini" \
  --embedding-deployment "text-embedding-3-large"
```bash
# Deploy at subscription level (creates resource group automatically)
az deployment sub create \
  --name "wbiq-deployment" \
  --location eastus \
  --template-file main.bicep \
  --parameters main.bicepparam
```

#### 4. Get Deployment Outputs

```bash
# Get deployment outputs
az deployment sub show \
  --name "wbiq-deployment" \
  --query properties.outputs

# Get specific values
az deployment sub show \
  --name "wbiq-deployment" \
  --query properties.outputs.aiFoundryAccountName.value -o tsv
```

Update your `.env` file with the output values.

## � Validation

```bash
# Restore and validate Bicep template
bicep restore main.bicep
bicep build main.bicep --stdout --no-restore

# Format and lint
bicep format main.bicep
bicep lint main.bicep

# What-if deployment (preview changes)
az 🔍eployment sub what-if \
  --location eastus \
  --template-file main.bicep \
  --parameters main.bicepparam
```

## 🧪 Testing

Test the Content Understanding endpoint:

```bash
# Get access token
TOKEN=$(az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv)

# Get AI Foundry endpoint
ENDPOINT=$(az deployment sub show \
  --name "wbiq-deployment" \
  --query properties.outputs.aiFoundryAccountName.value -o tsv)

# Test configuration endpoint
curl -H "Authorization: Bearer $TOKEN" \
  "https://${ENDPOINT}.openai.azure.com/contentunderstanding/defaults?api-version=2025-11-01"
```

## 🔧 Troubleshooting

### Prerequisites Issues

**Missing jq:**
```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq

# RHEL/CentOS
sudo yum install jq
```

**Missing Azure CLI:**
```bash
# Install Azure CLI on Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# macOS
brew install azure-cli
```

**Azure CLI not logged in:**
```bash
az login
az account show
```

### Common Issues

**Quota exceeded:**
```bash
az vm list-usage --location eastus --output table
```

**Permission denied:**
- Ensure you have Contributor role at subscription level
- Verify: `az role assignment list --assignee $(az account show --query user.name -o tsv)`

**Region unavailable:**
```bash
# Check AI Foundry availability
az provider show --namespace Microsoft.CognitiveServices \
  --query "resourceTypes[?resourceType=='accounts'].locations" -o table
```

**Deployment failed:**
```bash
# View deployment errors
az deployment sub show --name "wbiq-deployment" --query properties.error

# View operation details
az deployment operation sub list --name "wbiq-deployment"
```

## 📚 Resources

- [Azure AI Foundry](https://learn.microsoft.com/azure/ai-services/ai-services-foundry)
- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Azure Verified Modules](https://azure.github.io/Azure-Verified-Modules/)

## 🔐 Security

- **Managed Identity**: Azure AD authentication (no keys)
- **Key Vault**: RBAC-based secret access
- **Storage**: Public access disabled, TLS 1.2 enforced
- **Network**: Public access enabled (configure network rules as needed)

## 💰 Cost

- AI Foundry: Pay-per-use
- Model Deployments: Pay-per-token
- Storage (Standard_LRS): ~$0.02/GB/month
- Key Vault: ~$0.03/10k operations
- Managed Identity: Free

Monitor costs: `az consumption usage list`

## 🤝 Contributing

See:
- `docs/infra/bicep-planning-files/INFRA.ai-foundry-content-understanding.md`
- `.github/instructions/bicep-code-best-practices.instructions.md`
