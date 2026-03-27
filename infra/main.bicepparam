using './main.bicep'

// ======================================================================================
// Parameters for Azure AI Foundry v2 with Content Understanding deployment
// ======================================================================================
// Note: baseName, environmentName, and tags are now defined in main.bicep as variables
// Only location is configurable as a parameter
// ======================================================================================

// Azure region for deployment (defaults to 'eastus' if not specified)
param location = 'westus'
