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

The `deploy.sh` script provides an automated subscription-level deployment with validation. **Content Understanding configuration is a separate manual step** (see step 4 below).

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
# Simple deployment (uses defaults: short-name=wbiq, location=westus)
./deploy.sh

# Specify custom short name (2-5 characters)
./deploy.sh --short-name "myapp"

# Specify location and short name
./deploy.sh --short-name "myapp" --location "eastus"

# Skip validation
./deploy.sh --skip-validation

# Skip confirmation prompt
./deploy.sh --yes
```

The script will:
- ✓ Display a deployment banner with planned resources
- ✓ Ask for confirmation before proceeding (unless --yes flag is used)
- ✓ Validate your Azure authentication
- ✓ Check Bicep template syntax
- ✓ Create the resource group (based on short-name parameter)
- ✓ Deploy all infrastructure (10-15 minutes)
- ✓ Assign necessary RBAC roles for Content Understanding
- ✓ Validate the deployment
- ✓ Display deployment summary with next steps

**Note**: Resource naming uses the pattern `rg-{shortName}-dev`. The default short name is `wbiq` but can be customized with the `--short-name` parameter (2-5 characters).

#### 3. Review Outputs

The script will display:
- Resource group name
- AI Foundry endpoint
- Managed Identity Client ID
- Model deployment names
- Environment variables for your `.env` file
- **Command to run for Content Understanding configuration**

#### 4. Configure Content Understanding (Separate Step)

**Wait 2-3 minutes** after deployment completes for RBAC role assignments to propagate, then run:

```bash
./configure-content-understanding.sh \
  --ai-foundry-endpoint "https://your-account-name.openai.azure.com" \
  --gpt4-deployment "gpt-4.1" \
  --gpt4-mini-deployment "gpt-4.1-mini" \
  --embedding-deployment "text-embedding-3-large"
```

**Note**: The exact command with your endpoint will be displayed at the end of the deployment script output.

**Why separate?** Role assignments need time to propagate through Azure AD. Running this configuration immediately after deployment may result in permission errors.

## 🔧 Configuration & Validation Scripts

### Configure Content Understanding (Required)

**This must be run after the main deployment** (see Quick Start step 4 above).

```bash
# Bash
./configure-content-understanding.sh \
  --ai-foundry-endpoint "https://your-account.openai.azure.com" \
  --gpt4-deployment "gpt-4.1" \
  --gpt4-mini-deployment "gpt-4.1-mini" \
  --embedding-deployment "text-embedding-3-large"
```

**Troubleshooting**: If you get a `PermissionDenied` error:
- Wait 2-3 more minutes for role assignments to propagate
- Verify your user has the "Cognitive Services OpenAI Contributor" role on the AI Foundry account

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

**Default values** (can be passed as parameters to deployment):
- `baseName`: `wbiq` (pass with `--parameters baseName="yourname"`)
- `environmentName`: `dev` (hardcoded in template)
- `resourceGroupName`: `rg-{baseName}-dev` (auto-created)

#### 2. Login to Azure

```bash
# Login to Azure
az login

# Set subscription (if you have multiple)
az account set --subscription "your-subscription-id"
```

#### 3. Deploy Infrastructure

```bash
# Deploy at subscription level (creates resource group automatically)
az deployment sub create \
  --name "wbiq-deployment" \
  --location eastus \
  --template-file main.bicep \
  --parameters main.bicepparam \
  --parameters baseName="wbiq"
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

#### 5. Configure Content Understanding

**Wait 2-3 minutes** for role assignments to propagate, then run:

```bash
./configure-content-understanding.sh \
  --ai-foundry-endpoint "https://your-account.openai.azure.com" \
  --gpt4-deployment "gpt-4.1" \
  --gpt4-mini-deployment "gpt-4.1-mini" \
  --embedding-deployment "text-embedding-3-large"
```

## 🔍 Validation

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
