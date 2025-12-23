// ======================================================================================
// Main deployment template for Azure AI Foundry v2 with Content Understanding
// ======================================================================================
// This template orchestrates the deployment of:
// - Resource Group creation
// - Phase 1: Foundation resources (Managed Identity, Storage, Key Vault)
// - Phase 2: AI Foundry Account and Project
// - Phase 3: Model Deployments (GPT-4.1, GPT-4.1-mini, text-embedding-3-large)
// Note: Phase 4 (Content Understanding config) requires post-deployment script
// ======================================================================================

targetScope = 'subscription'

// ======================================================================================
// PARAMETERS
// ======================================================================================

@description('Azure region for resource deployment')
param location string = 'westus'

@description('Short name used as prefix for all resources (2-5 characters)')
@minLength(2)
@maxLength(5)
param baseName string = 'wbiq'

@description('Object ID of the user running the deployment (optional, for Content Understanding permissions)')
param deployerObjectId string = ''

// ======================================================================================
// VARIABLES
// ======================================================================================
var environmentName = 'dev'
var resourceGroupName = 'rg-${baseName}-${environmentName}'
var resourcePrefix = '${baseName}-${environmentName}'
var uniqueSuffix = uniqueString(subscription().id, baseName)

var tags = {
  Environment: environmentName
  Purpose: 'AI-Foundry-Content-Understanding'
  ManagedBy: 'Bicep'
}

// ======================================================================================
// RESOURCE GROUP
// ======================================================================================

@description('Resource group for all WorkbenchIQ resources')
resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// Resource names
var managedIdentityName = '${resourcePrefix}-identity'
var storageAccountName = toLower('${take(baseName, 5)}${take(uniqueSuffix, 5)}st')
var keyVaultName = '${take(baseName, 5)}-${take(uniqueSuffix, 5)}-kv'
var aiFoundryAccountName = '${take(baseName, 5)}-${environmentName}-ai'
var aiFoundryProjectName = '${take(baseName, 5)}-${take(environmentName, 1)}-prj'

// Model deployment names
var gpt41DeploymentName = 'gpt-4.1'
var gpt41MiniDeploymentName = 'gpt-4.1-mini'
var textEmbedding3LargeDeploymentName = 'text-embedding-3-large'

// ======================================================================================
// PHASE 1: FOUNDATION RESOURCES
// ======================================================================================

@description('User-assigned managed identity for secure resource access')
module managedIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.3' = {
  name: 'deploy-managed-identity'
  scope: resourceGroup
  params: {
    name: managedIdentityName
    location: location
    tags: tags
  }
}

@description('Storage account for AI Foundry agent services')
module storageAccount 'br/public:avm/res/storage/storage-account:0.30.0' = {
  name: 'deploy-storage-account'
  scope: resourceGroup
  params: {
    name: storageAccountName
    location: location
    tags: tags
    kind: 'StorageV2'
    skuName: 'Standard_LRS'
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

@description('Key Vault for storing application secrets')
module keyVault 'br/public:avm/res/key-vault/vault:0.13.3' = {
  name: 'deploy-key-vault'
  scope: resourceGroup
  params: {
    name: keyVaultName
    location: location
    tags: tags
    sku: 'standard'
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// ======================================================================================
// PHASE 2: AI FOUNDRY ACCOUNT AND PROJECT
// ======================================================================================

@description('AI Foundry account with project and model deployments')
module aiFoundry 'br/public:avm/ptn/ai-ml/ai-foundry:0.6.0' = {
  name: 'deploy-ai-foundry'
  scope: resourceGroup
  params: {
    baseName: resourcePrefix
    location: location
    tags: tags
    aiFoundryConfiguration: {
      accountName: aiFoundryAccountName
      sku: 'S0'
      allowProjectManagement: true
      createCapabilityHosts: true
      disableLocalAuth: false
      project: {
        name: aiFoundryProjectName
        displayName: 'Content Understanding Project'
        desc: 'AI Foundry project for Content Understanding workloads'
      }
      roleAssignments: concat([
        {
          principalId: managedIdentity.outputs.principalId
          roleDefinitionIdOrName: 'Cognitive Services User'
          principalType: 'ServicePrincipal'
        }
      ], !empty(deployerObjectId) ? [{
        principalId: deployerObjectId
        roleDefinitionIdOrName: 'Cognitive Services OpenAI Contributor'
        principalType: 'User'
      }] : [])
    }
    aiModelDeployments: [
      {
        name: gpt41DeploymentName
        model: {
          format: 'OpenAI'
          name: 'gpt-4.1'
          version: '2025-04-14'
        }
        sku: {
          name: 'GlobalStandard'
          capacity: 10
        }
      }
      {
        name: gpt41MiniDeploymentName
        model: {
          format: 'OpenAI'
          name: 'gpt-4.1-mini'
          version: '2025-04-14'
        }
        sku: {
          name: 'GlobalStandard'
          capacity: 10
        }
      }
      {
        name: textEmbedding3LargeDeploymentName
        model: {
          format: 'OpenAI'
          name: 'text-embedding-3-large'
          version: '1'
        }
        sku: {
          name: 'GlobalStandard'
          capacity: 10
        }
      }
    ]
    includeAssociatedResources: false // We're managing Storage and Key Vault separately
  }
  dependsOn: [
    storageAccount
    keyVault
  ]
}

// ======================================================================================
// OUTPUTS
// ======================================================================================

@description('Resource group information')
output resourceGroupName string = resourceGroup.name
output resourceGroupLocation string = resourceGroup.location

@description('Resource IDs and configuration values for application use')
output aiFoundryAccountName string = aiFoundry.outputs.aiServicesName
output aiFoundryAccountEndpoint string = 'https://${aiFoundry.outputs.aiServicesName}.openai.azure.com'
output aiProjectName string = aiFoundry.outputs.aiProjectName

output managedIdentityPrincipalId string = managedIdentity.outputs.principalId
output managedIdentityClientId string = managedIdentity.outputs.clientId
output managedIdentityResourceId string = managedIdentity.outputs.resourceId

output storageAccountName string = storageAccount.outputs.name
output storageAccountResourceId string = storageAccount.outputs.resourceId

output keyVaultName string = keyVault.outputs.name
output keyVaultUri string = keyVault.outputs.uri
output keyVaultResourceId string = keyVault.outputs.resourceId

@description('Model deployment names for Content Understanding configuration')
output modelDeployments object = {
  'gpt-4.1': gpt41DeploymentName
  'gpt-4.1-mini': gpt41MiniDeploymentName
  'text-embedding-3-large': textEmbedding3LargeDeploymentName
}

@description('Environment configuration for application .env file')
output environmentConfig object = {
  AZURE_AI_FOUNDRY_ENDPOINT: 'https://${aiFoundry.outputs.aiServicesName}.openai.azure.com'
  AZURE_AI_PROJECT_NAME: aiFoundry.outputs.aiProjectName
  AZURE_MANAGED_IDENTITY_CLIENT_ID: managedIdentity.outputs.clientId
  AZURE_STORAGE_ACCOUNT_NAME: storageAccount.outputs.name
  AZURE_KEY_VAULT_NAME: keyVault.outputs.name
  GPT_41_DEPLOYMENT_NAME: gpt41DeploymentName
  GPT_41_MINI_DEPLOYMENT_NAME: gpt41MiniDeploymentName
  TEXT_EMBEDDING_DEPLOYMENT_NAME: textEmbedding3LargeDeploymentName
}
