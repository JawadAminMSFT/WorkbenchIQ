---
goal: Deploy Azure AI Foundry v2 with Content Understanding and Required Model Deployments
---

# Introduction

This implementation plan outlines the deployment of Azure AI Foundry v2 (Microsoft.CognitiveServices/accounts kind AIServices) with a project configured for Content Understanding. The deployment includes three required model deployments (GPT-4.1, GPT-4.1-mini, text-embedding-3-large) and configures Content Understanding with default model mappings to enable prebuilt analyzers. Supporting resources include Azure Storage, Azure Key Vault, and managed identity for secure access.

## Resources

### aiFoundryAccount

```yaml
name: aiFoundryAccount
kind: AVM
avmModule: br/public:avm/ptn/ai-ml/ai-foundry:0.6.0

purpose: Azure AI Foundry account (formerly AI Services) that hosts the project, model deployments, and Content Understanding service
dependsOn: []

parameters:
  required:
    - name: baseName
      type: string
      description: Base name for resource naming convention
      example: wbiq

  optional:
    - name: location
      type: string
      description: Azure region for deployment
      default: eastus

    - name: aiFoundryConfiguration
      type: object
      description: Configuration for AI Foundry account including SKU, networking, and project settings
      default: 
        sku: S0
        kind: AIServices
        disableLocalAuth: false
        allowProjectManagement: true
        createCapabilityHosts: true

    - name: aiModelDeployments
      type: array
      description: Array of model deployment definitions for GPT-4.1, GPT-4.1-mini, and text-embedding-3-large
      default: []

    - name: includeAssociatedResources
      type: bool
      description: Whether to create associated resources like Storage and Key Vault
      default: true

    - name: storageAccountConfiguration
      type: object
      description: Configuration for Storage Account used by agent services
      default: {}

    - name: keyVaultConfiguration
      type: object
      description: Configuration for Key Vault to store secrets
      default: {}

outputs:
  - name: aiFoundryAccountResourceId
    type: string
    description: Resource ID of the AI Foundry account

  - name: aiFoundryAccountEndpoint
    type: string
    description: Endpoint URL for the AI Foundry account

  - name: aiFoundryAccountName
    type: string
    description: Name of the AI Foundry account

  - name: aiProjectResourceId
    type: string
    description: Resource ID of the AI Foundry project

  - name: modelDeploymentNames
    type: object
    description: Map of model names to deployment names

references:
  docs: https://learn.microsoft.com/en-us/azure/ai-foundry/
  avm: https://github.com/Azure/bicep-registry-modules/tree/avm/ptn/ai-ml/ai-foundry/0.6.0/avm/ptn/ai-ml/ai-foundry/README.md
```

### gpt41ModelDeployment

```yaml
name: gpt41ModelDeployment
kind: Raw
type: Microsoft.CognitiveServices/accounts/deployments@2025-06-01

purpose: Serverless API deployment for GPT-4.1 model used by Content Understanding for general analysis tasks
dependsOn: [aiFoundryAccount]

parameters:
  required:
    - name: accountName
      type: string
      description: Name of the parent AI Foundry account
      example: wbiq-aifoundry

    - name: deploymentName
      type: string
      description: Name for the GPT-4.1 deployment
      example: gpt-4.1

    - name: modelFormat
      type: string
      description: Model format (OpenAI for Azure OpenAI models)
      example: OpenAI

    - name: modelName
      type: string
      description: Model name from catalog
      example: gpt-4.1

    - name: modelVersion
      type: string
      description: Version of the model to deploy
      example: latest

  optional:
    - name: sku
      type: object
      description: SKU configuration for deployment
      default: 
        name: GlobalStandard
        capacity: 1

    - name: raiPolicyName
      type: string
      description: Responsible AI policy name for content filtering
      default: Microsoft.Default

outputs:
  - name: deploymentId
    type: string
    description: Resource ID of the deployment

  - name: deploymentEndpoint
    type: string
    description: Endpoint for the model deployment

references:
  docs: https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/create-model-deployments
```

### gpt41MiniModelDeployment

```yaml
name: gpt41MiniModelDeployment
kind: Raw
type: Microsoft.CognitiveServices/accounts/deployments@2025-06-01

purpose: Serverless API deployment for GPT-4.1-mini model used by Content Understanding for RAG analyzers like documentSearch
dependsOn: [aiFoundryAccount]

parameters:
  required:
    - name: accountName
      type: string
      description: Name of the parent AI Foundry account
      example: wbiq-aifoundry

    - name: deploymentName
      type: string
      description: Name for the GPT-4.1-mini deployment
      example: gpt-4.1-mini

    - name: modelFormat
      type: string
      description: Model format (OpenAI for Azure OpenAI models)
      example: OpenAI

    - name: modelName
      type: string
      description: Model name from catalog
      example: gpt-4.1-mini

    - name: modelVersion
      type: string
      description: Version of the model to deploy
      example: latest

  optional:
    - name: sku
      type: object
      description: SKU configuration for deployment
      default: 
        name: GlobalStandard
        capacity: 1

    - name: raiPolicyName
      type: string
      description: Responsible AI policy name for content filtering
      default: Microsoft.Default

outputs:
  - name: deploymentId
    type: string
    description: Resource ID of the deployment

  - name: deploymentEndpoint
    type: string
    description: Endpoint for the model deployment

references:
  docs: https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/create-model-deployments
```

### textEmbedding3LargeDeployment

```yaml
name: textEmbedding3LargeDeployment
kind: Raw
type: Microsoft.CognitiveServices/accounts/deployments@2025-06-01

purpose: Serverless API deployment for text-embedding-3-large model used for embeddings in Content Understanding
dependsOn: [aiFoundryAccount]

parameters:
  required:
    - name: accountName
      type: string
      description: Name of the parent AI Foundry account
      example: wbiq-aifoundry

    - name: deploymentName
      type: string
      description: Name for the text-embedding-3-large deployment
      example: text-embedding-3-large

    - name: modelFormat
      type: string
      description: Model format (OpenAI for Azure OpenAI models)
      example: OpenAI

    - name: modelName
      type: string
      description: Model name from catalog
      example: text-embedding-3-large

    - name: modelVersion
      type: string
      description: Version of the model to deploy
      example: latest

  optional:
    - name: sku
      type: object
      description: SKU configuration for deployment
      default: 
        name: GlobalStandard
        capacity: 1

outputs:
  - name: deploymentId
    type: string
    description: Resource ID of the deployment

  - name: deploymentEndpoint
    type: string
    description: Endpoint for the model deployment

references:
  docs: https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/create-model-deployments
```

### contentUnderstandingDefaults

```yaml
name: contentUnderstandingDefaults
kind: Raw
type: N/A - Deployed via REST API (PATCH request)

purpose: Configure default model deployment mappings for Content Understanding to enable prebuilt analyzers without specifying models in each request
dependsOn: [gpt41ModelDeployment, gpt41MiniModelDeployment, textEmbedding3LargeDeployment]

parameters:
  required:
    - name: endpoint
      type: string
      description: AI Foundry account endpoint URL
      example: https://wbiq-aifoundry.cognitiveservices.azure.com

    - name: modelDeployments
      type: object
      description: Mapping of model names to deployment names
      example:
        gpt-4.1: gpt-4.1
        gpt-4.1-mini: gpt-4.1-mini
        text-embedding-3-large: text-embedding-3-large

    - name: apiVersion
      type: string
      description: Content Understanding API version
      example: 2025-11-01

  optional:
    - name: useAzureAd
      type: bool
      description: Whether to use Azure AD authentication instead of API key
      default: true

outputs:
  - name: configuredModels
    type: object
    description: Confirmed model deployment mappings

references:
  docs: https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/concepts/models-deployments
```

### managedIdentity

```yaml
name: managedIdentity
kind: AVM
avmModule: br/public:avm/res/managed-identity/user-assigned-identity:0.4.3

purpose: User-assigned managed identity for secure access to Azure resources without storing credentials
dependsOn: []

parameters:
  required:
    - name: name
      type: string
      description: Name of the managed identity
      example: wbiq-identity

  optional:
    - name: location
      type: string
      description: Azure region for the identity
      default: eastus

outputs:
  - name: principalId
    type: string
    description: Principal ID of the managed identity for role assignments

  - name: resourceId
    type: string
    description: Resource ID of the managed identity

  - name: clientId
    type: string
    description: Client ID of the managed identity

references:
  docs: https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/
  avm: https://github.com/Azure/bicep-registry-modules/tree/avm/res/managed-identity/user-assigned-identity/0.4.3
```

### storageAccount

```yaml
name: storageAccount
kind: AVM
avmModule: br/public:avm/res/storage/storage-account:0.30.0

purpose: Storage account for AI Foundry agent services to store threads, messages, and files
dependsOn: []

parameters:
  required:
    - name: name
      type: string
      description: Storage account name (must be globally unique, 3-24 characters, lowercase letters and numbers)
      example: wbiqstorage

  optional:
    - name: location
      type: string
      description: Azure region for the storage account
      default: eastus

    - name: skuName
      type: string
      description: Storage account SKU
      default: Standard_LRS

    - name: kind
      type: string
      description: Storage account kind
      default: StorageV2

    - name: accessTier
      type: string
      description: Access tier for blob storage
      default: Hot

    - name: minimumTlsVersion
      type: string
      description: Minimum TLS version
      default: TLS1_2

    - name: allowBlobPublicAccess
      type: bool
      description: Whether to allow public access to blobs
      default: false

outputs:
  - name: resourceId
    type: string
    description: Resource ID of the storage account

  - name: name
    type: string
    description: Name of the storage account

  - name: primaryEndpoints
    type: object
    description: Primary endpoints for blob, file, queue, and table services

references:
  docs: https://learn.microsoft.com/en-us/azure/storage/common/storage-account-overview
  avm: https://github.com/Azure/bicep-registry-modules/tree/avm/res/storage/storage-account/0.30.0
```

### keyVault

```yaml
name: keyVault
kind: AVM
avmModule: br/public:avm/res/key-vault/vault:0.13.3

purpose: Key Vault for storing secrets, keys, and certificates used by the AI application
dependsOn: []

parameters:
  required:
    - name: name
      type: string
      description: Key Vault name (must be globally unique, 3-24 characters, alphanumeric and hyphens)
      example: wbiq-kv

  optional:
    - name: location
      type: string
      description: Azure region for Key Vault
      default: eastus

    - name: sku
      type: string
      description: Key Vault SKU
      default: standard

    - name: enableRbacAuthorization
      type: bool
      description: Use RBAC for authorization instead of access policies
      default: true

    - name: enableSoftDelete
      type: bool
      description: Enable soft delete for recovery
      default: true

    - name: softDeleteRetentionInDays
      type: int
      description: Days to retain soft-deleted items
      default: 90

    - name: networkAcls
      type: object
      description: Network ACL configuration
      default:
        defaultAction: Allow

outputs:
  - name: resourceId
    type: string
    description: Resource ID of the Key Vault

  - name: name
    type: string
    description: Name of the Key Vault

  - name: uri
    type: string
    description: URI of the Key Vault

references:
  docs: https://learn.microsoft.com/en-us/azure/key-vault/general/overview
  avm: https://github.com/Azure/bicep-registry-modules/tree/avm/res/key-vault/vault/0.13.3
```

### roleAssignmentCognitiveServicesUser

```yaml
name: roleAssignmentCognitiveServicesUser
kind: Raw
type: Microsoft.Authorization/roleAssignments@2022-04-01

purpose: Assign Cognitive Services User role to managed identity for AI Foundry access
dependsOn: [managedIdentity, aiFoundryAccount]

parameters:
  required:
    - name: principalId
      type: string
      description: Principal ID of the managed identity
      example: <managed-identity-principal-id>

    - name: roleDefinitionId
      type: string
      description: Role definition ID for Cognitive Services User
      example: /subscriptions/{subscriptionId}/providers/Microsoft.Authorization/roleDefinitions/a97b65f3-24c7-4388-baec-2e87135dc908

    - name: scope
      type: string
      description: Scope for the role assignment (AI Foundry account resource ID)
      example: /subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/providers/Microsoft.CognitiveServices/accounts/{accountName}

outputs:
  - name: roleAssignmentId
    type: string
    description: Resource ID of the role assignment

references:
  docs: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#cognitive-services-user
```

### roleAssignmentStorageBlobDataContributor

```yaml
name: roleAssignmentStorageBlobDataContributor
kind: Raw
type: Microsoft.Authorization/roleAssignments@2022-04-01

purpose: Assign Storage Blob Data Contributor role to AI Foundry for accessing storage
dependsOn: [managedIdentity, storageAccount, aiFoundryAccount]

parameters:
  required:
    - name: principalId
      type: string
      description: Principal ID of the AI Foundry account system-assigned managed identity
      example: <ai-foundry-principal-id>

    - name: roleDefinitionId
      type: string
      description: Role definition ID for Storage Blob Data Contributor
      example: /subscriptions/{subscriptionId}/providers/Microsoft.Authorization/roleDefinitions/ba92f5b4-2d11-453d-a403-e96b0029c9fe

    - name: scope
      type: string
      description: Scope for the role assignment (Storage account resource ID)
      example: /subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/providers/Microsoft.Storage/storageAccounts/{storageAccountName}

outputs:
  - name: roleAssignmentId
    type: string
    description: Resource ID of the role assignment

references:
  docs: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#storage-blob-data-contributor
```

### roleAssignmentKeyVaultSecretsUser

```yaml
name: roleAssignmentKeyVaultSecretsUser
kind: Raw
type: Microsoft.Authorization/roleAssignments@2022-04-01

purpose: Assign Key Vault Secrets User role to managed identity for secret access
dependsOn: [managedIdentity, keyVault]

parameters:
  required:
    - name: principalId
      type: string
      description: Principal ID of the managed identity
      example: <managed-identity-principal-id>

    - name: roleDefinitionId
      type: string
      description: Role definition ID for Key Vault Secrets User
      example: /subscriptions/{subscriptionId}/providers/Microsoft.Authorization/roleDefinitions/4633458b-17de-408a-b874-0445c86b69e6

    - name: scope
      type: string
      description: Scope for the role assignment (Key Vault resource ID)
      example: /subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/providers/Microsoft.KeyVault/vaults/{keyVaultName}

outputs:
  - name: roleAssignmentId
    type: string
    description: Resource ID of the role assignment

references:
  docs: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#key-vault-secrets-user
```

# Implementation Plan

The implementation follows a phased approach to ensure dependencies are met and resources are deployed in the correct order. The plan uses Azure Verified Modules (AVM) where available for production-ready, well-tested deployments.

## Phase 1 — Foundation Resources

**Objective:** Deploy core infrastructure resources that other services depend on (managed identity, storage, and Key Vault)

This phase establishes the security and storage foundation for the AI Foundry deployment. The managed identity enables secure, credential-free authentication, while storage and Key Vault provide data persistence and secret management.

- IMPLEMENT-GOAL-001: Deploy foundational Azure resources for identity, storage, and secrets management

| Task     | Description                                                                 | Action                                                |
| -------- | --------------------------------------------------------------------------- | ----------------------------------------------------- |
| TASK-001 | Create user-assigned managed identity for secure resource access           | Deploy using AVM module avm/res/managed-identity     |
| TASK-002 | Create Azure Storage Account for AI agent service data                     | Deploy using AVM module avm/res/storage              |
| TASK-003 | Create Azure Key Vault for application secrets                             | Deploy using AVM module avm/res/key-vault            |
| TASK-004 | Configure RBAC assignments for managed identity to access Key Vault        | Create role assignment for Key Vault Secrets User    |
| TASK-005 | Validate managed identity, storage, and Key Vault deployment and access    | Test managed identity access to storage and Key Vault|

## Phase 2 — AI Foundry Account and Project

**Objective:** Deploy Azure AI Foundry v2 account with a project for Content Understanding workloads

This phase deploys the core AI Foundry infrastructure using the Azure Verified Module pattern, which includes the account, project, and associated resources. The AVM handles complex configurations like networking, capability hosts, and project management automatically.

- IMPLEMENT-GOAL-002: Deploy AI Foundry account and project with proper configuration

| Task     | Description                                                                 | Action                                                |
| -------- | --------------------------------------------------------------------------- | ----------------------------------------------------- |
| TASK-006 | Deploy AI Foundry account using AVM pattern module                         | Use br/public:avm/ptn/ai-ml/ai-foundry:0.6.0         |
| TASK-007 | Configure AI Foundry with SKU S0, disableLocalAuth=false                   | Set aiFoundryConfiguration parameters                 |
| TASK-008 | Enable project management and capability hosts                             | Set createCapabilityHosts=true, allowProjectManagement=true |
| TASK-009 | Link Storage Account and Key Vault to AI Foundry                           | Configure includeAssociatedResources parameters      |
| TASK-010 | Create AI Foundry project under the account                               | Configure aiFoundryConfiguration.project properties  |
| TASK-011 | Assign Cognitive Services User role to managed identity                    | Create role assignment at AI Foundry account scope   |
| TASK-012 | Assign Storage Blob Data Contributor to AI Foundry system identity         | Create role assignment at Storage Account scope      |
| TASK-013 | Validate AI Foundry account and project are operational                    | Test endpoint connectivity and authentication        |

## Phase 3 — Model Deployments

**Objective:** Deploy required AI models (GPT-4.1, GPT-4.1-mini, text-embedding-3-large) as serverless deployments

This phase creates serverless API deployments for the three models required by Content Understanding. Serverless deployments provide automatic scaling, pay-per-use pricing, and don't require provisioned capacity.

- IMPLEMENT-GOAL-003: Deploy AI model endpoints for Content Understanding

| Task     | Description                                                                 | Action                                                |
| -------- | --------------------------------------------------------------------------- | ----------------------------------------------------- |
| TASK-014 | Deploy GPT-4.1 model with GlobalStandard SKU                               | Create Microsoft.CognitiveServices/accounts/deployments |
| TASK-015 | Configure GPT-4.1 deployment with model format OpenAI, latest version      | Set deployment properties and SKU                     |
| TASK-016 | Apply Microsoft.Default RAI policy for content filtering on GPT-4.1        | Configure raiPolicyName parameter                     |
| TASK-017 | Deploy GPT-4.1-mini model with GlobalStandard SKU                          | Create Microsoft.CognitiveServices/accounts/deployments |
| TASK-018 | Configure GPT-4.1-mini with model format OpenAI, latest version            | Set deployment properties and SKU                     |
| TASK-019 | Apply Microsoft.Default RAI policy for content filtering on GPT-4.1-mini   | Configure raiPolicyName parameter                     |
| TASK-020 | Deploy text-embedding-3-large model with GlobalStandard SKU                | Create Microsoft.CognitiveServices/accounts/deployments |
| TASK-021 | Configure text-embedding-3-large with model format OpenAI, latest version  | Set deployment properties and SKU                     |
| TASK-022 | Capture deployment names for each model                                    | Store outputs for Content Understanding configuration|
| TASK-023 | Validate all three model deployments are ready                             | Test model endpoints with sample requests            |

## Phase 4 — Content Understanding Configuration

**Objective:** Configure Content Understanding default model mappings to enable prebuilt analyzers

This phase configures the Content Understanding service with default model deployment mappings using a PATCH REST API request. This configuration enables prebuilt analyzers (like receipt, invoice, documentSearch) to work without specifying models in each analyze request.

- IMPLEMENT-GOAL-004: Configure Content Understanding with default model deployment mappings

| Task     | Description                                                                 | Action                                                |
| -------- | --------------------------------------------------------------------------- | ----------------------------------------------------- |
| TASK-024 | Implement deployment script or Azure CLI command for configuration         | Create script similar to setup_content_understanding.py |
| TASK-025 | Authenticate to Content Understanding API using Azure AD credential        | Use DefaultAzureCredential for authentication        |
| TASK-026 | Execute PATCH request to /contentunderstanding/defaults endpoint           | Set API version 2025-11-01                           |
| TASK-027 | Map gpt-4.1 model to deployment name                                       | Add to modelDeployments dictionary                   |
| TASK-028 | Map gpt-4.1-mini model to deployment name                                  | Add to modelDeployments dictionary                   |
| TASK-029 | Map text-embedding-3-large model to deployment name                        | Add to modelDeployments dictionary                   |
| TASK-030 | Verify configuration was applied successfully                              | GET /contentunderstanding/defaults to confirm        |
| TASK-031 | Test prebuilt analyzer without specifying modelDeployments                 | Call analyze API with prebuilt analyzer ID           |
| TASK-032 | Document configuration for application reference                           | Update application .env or configuration files       |

## Phase 5 — Validation and Documentation

**Objective:** Validate the complete deployment and document configuration for application use

This final phase ensures all components are working together correctly and provides documentation for developers to integrate Content Understanding into the application.

- IMPLEMENT-GOAL-005: Validate deployment and create integration documentation

| Task     | Description                                                                 | Action                                                |
| -------- | --------------------------------------------------------------------------- | ----------------------------------------------------- |
| TASK-033 | Test end-to-end Content Understanding workflow                             | Submit document for analysis using prebuilt analyzer |
| TASK-034 | Verify token consumption is tracked correctly                              | Check usage property in analyze response             |
| TASK-035 | Validate managed identity can access all required resources                | Test identity access to Storage, Key Vault, AI Foundry |
| TASK-036 | Document AI Foundry endpoint URL for application configuration             | Add to .env.example and deployment docs              |
| TASK-037 | Document model deployment names for application reference                  | Add to configuration documentation                   |
| TASK-038 | Create operational runbook for monitoring and maintenance                  | Document metrics to monitor, scaling considerations  |
| TASK-039 | Document cost estimation based on expected usage                           | Calculate costs for model usage, storage, services   |
| TASK-040 | Validate security posture and compliance requirements                      | Review RBAC, network security, data encryption       |

# High-level Design

## Architecture Overview

The solution deploys a comprehensive Azure AI Foundry v2 environment optimized for Content Understanding workloads. The architecture follows Azure best practices for security, scalability, and cost optimization.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Azure AI Foundry v2 Architecture                                           │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Application Layer                                                      │ │
│  │  ┌──────────────────┐                                                  │ │
│  │  │  Python App      │───────────────┐                                  │ │
│  │  │  (FastAPI)       │               │                                  │ │
│  │  └──────────────────┘               │                                  │ │
│  └────────────────────────┬─────────────┼──────────────────────────────────┘ │
│                           │             │                                    │
│                           │ Azure AD    │ API Calls                          │
│                           │ Auth        │                                    │
│  ┌────────────────────────▼─────────────▼──────────────────────────────────┐ │
│  │  AI Foundry Account (Microsoft.CognitiveServices/accounts)              │ │
│  │  Kind: AIServices, SKU: S0                                              │ │
│  │                                                                          │ │
│  │  ┌────────────────────────────────────────────────────────────────────┐ │ │
│  │  │  AI Foundry Project                                                 │ │ │
│  │  │  (Microsoft.CognitiveServices/accounts/projects)                    │ │ │
│  │  │                                                                      │ │ │
│  │  │  ┌───────────────────────────────────────────────────────────────┐ │ │ │
│  │  │  │  Content Understanding Service                                 │ │ │ │
│  │  │  │  API Version: 2025-11-01                                       │ │ │ │
│  │  │  │                                                                 │ │ │ │
│  │  │  │  Default Model Mappings:                                       │ │ │ │
│  │  │  │  • gpt-4.1 → gpt-4.1                                          │ │ │ │
│  │  │  │  • gpt-4.1-mini → gpt-4.1-mini                                │ │ │ │
│  │  │  │  • text-embedding-3-large → text-embedding-3-large            │ │ │ │
│  │  │  └───────────────────────────────────────────────────────────────┘ │ │ │
│  │  └────────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                          │ │
│  │  Model Deployments (Serverless API):                                    │ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐   │ │
│  │  │ GPT-4.1          │  │ GPT-4.1-mini     │  │ text-embedding-    │   │ │
│  │  │ GlobalStandard   │  │ GlobalStandard   │  │ 3-large            │   │ │
│  │  │ OpenAI Format    │  │ OpenAI Format    │  │ GlobalStandard     │   │ │
│  │  └──────────────────┘  └──────────────────┘  └────────────────────┘   │ │
│  └────────────────────────┬──────────────────────────────────────────────┘ │
│                           │                                                 │
│                           │ Uses (System Managed Identity)                  │
│                           │                                                 │
│  ┌────────────────────────▼──────────────────────────────────────────────┐ │
│  │  Supporting Resources                                                  │ │
│  │                                                                        │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐ │ │
│  │  │ Storage Account │  │ Key Vault       │  │ User Assigned       │ │ │
│  │  │ (Agent Data)    │  │ (Secrets)       │  │ Managed Identity    │ │ │
│  │  │                 │  │                 │  │                      │ │ │
│  │  │ • Threads       │  │ • API Keys      │  │ • App Auth          │ │ │
│  │  │ • Messages      │  │ • Conn Strings  │  │ • Resource Access   │ │ │
│  │  │ • Files         │  │                 │  │                      │ │ │
│  │  └─────────────────┘  └─────────────────┘  └──────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Security:                                                                   │
│  • Azure AD Authentication (DefaultAzureCredential)                          │
│  • RBAC: Cognitive Services User, Storage Blob Data Contributor,            │
│  •       Key Vault Secrets User                                             │
│  • Managed Identities for secure access without credentials                 │
│  • Content filtering via Microsoft.Default RAI policy                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

1. **Azure Verified Modules (AVM)**: Leverages the official AI Foundry AVM pattern module (version 0.6.0) for production-ready, well-tested infrastructure deployment with built-in best practices.

2. **Serverless Model Deployments**: Uses GlobalStandard SKU for serverless API deployments, providing automatic scaling, pay-per-use pricing, and no capacity provisioning requirements.

3. **Content Understanding Default Mappings**: Configures default model deployment mappings at the resource level, eliminating the need to specify models in each analyze request and simplifying application code.

4. **Managed Identity**: Implements user-assigned managed identity for application authentication and system-assigned identity for AI Foundry, enabling secure, credential-free access to Azure resources.

5. **Resource Naming**: Follows Azure naming conventions with consistent prefix (baseName parameter) and resource type suffixes for clear resource identification.

6. **Security Posture**: 
   - Disables local authentication in favor of Azure AD (can be adjusted based on requirements)
   - Implements RBAC with least-privilege access
   - Enables soft delete on Key Vault for recovery
   - Uses TLS 1.2 minimum for all connections
   - Applies Microsoft.Default RAI policy for responsible AI content filtering

7. **Cost Optimization**:
   - Serverless deployments only charge for actual usage
   - Standard_LRS storage for cost-effective redundancy
   - Standard Key Vault SKU (can upgrade to Premium if HSM required)
   - S0 SKU for AI Foundry account (production-ready tier)

8. **Supported Regions**: Content Understanding is only available in specific regions. Verify region support before deployment: https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/language-region-support

9. **API Version**: Uses Content Understanding API version 2025-11-01 for the latest features and stability.

10. **Integration Pattern**: The deployment script should be adapted from setup_content_understanding.py to execute as part of the infrastructure deployment, using Azure CLI or deployment script resource for automation.

## Dependencies and Constraints

**Dependencies:**
- Azure subscription with Cognitive Services resource provider registered
- Sufficient quota for AI model deployments in target region
- Azure CLI or PowerShell for deployment
- Bicep CLI version 0.4.x or later

**Constraints:**
- AI Foundry and Content Understanding are only available in select Azure regions
- Model deployments require capacity availability in the region
- Serverless API deployments have per-region quotas
- Content Understanding defaults configuration requires REST API call (not available in Bicep)
- Maximum 2 MB file size for Content Understanding analyze requests

**Migration Notes:**
- If migrating from hub-based AI projects, follow Microsoft's migration guide
- Existing Azure OpenAI resources can be connected for continued access to deployments
- No downtime migration path available; plan for parallel deployment and cutover
