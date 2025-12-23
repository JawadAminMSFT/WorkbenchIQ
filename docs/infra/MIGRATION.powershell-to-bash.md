---
goal: Migrate PowerShell scripts to Bash for Linux-based deployments
status: completed
created: 2025-12-23
completed: 2025-12-23
---

# PowerShell to Bash Migration Plan

## Executive Summary

This document outlines the complete migration strategy for converting the three PowerShell scripts under `/infra` to bash equivalents, enabling Linux-native deployment and configuration workflows for the Azure AI Foundry Content Understanding infrastructure.

**Scripts to migrate:**
1. `configure-content-understanding.ps1` - Configures Content Understanding default model mappings
2. `deploy.ps1` - Orchestrates complete Bicep deployment and configuration
3. `validate-deployment.ps1` - Validates deployment health and configuration

## Migration Scope

### In Scope
- Convert PowerShell syntax to bash equivalents
- Replace Azure PowerShell cmdlets with Azure CLI commands
- Maintain identical functionality and validation logic
- Preserve script parameters and configuration options
- Ensure error handling and user feedback mechanisms
- Maintain script exit codes for CI/CD compatibility

### Out of Scope
- Changes to Bicep templates or infrastructure definitions
- Modifications to deployment architecture or resource configurations
- Changes to Content Understanding API contracts
- Pipeline-specific implementations (GitHub Actions, Azure DevOps, etc.)

## Technical Analysis

### Script 1: configure-content-understanding.ps1

**Current Dependencies:**
- PowerShell 7.0+
- Az.Accounts module
- Azure AD authentication via Get-AzAccessToken
- REST API calls via Invoke-RestMethod

**Key Functions:**
1. Parameter validation and normalization
2. Azure access token acquisition (Cognitive Services scope)
3. Build and send PATCH request to Content Understanding API
4. Verify configuration with GET request
5. Compare and validate configured vs expected models

**Bash Equivalents:**
- `Get-AzContext` → `az account show`
- `Get-AzAccessToken` → `az account get-access-token --resource https://cognitiveservices.azure.com`
- `Invoke-RestMethod` → `curl` with appropriate headers and JSON payloads
- Hashtable → Bash associative arrays or JSON manipulation with `jq`
- ConvertTo-Json → `jq` for JSON formatting

### Script 2: deploy.ps1

**Current Dependencies:**
- PowerShell 7.0+
- Az.Accounts, Az.Resources modules
- Bicep CLI for template validation
- Dependency on configure-content-understanding.ps1 and validate-deployment.ps1

**Key Functions:**
1. Interactive confirmation prompts
2. Azure subscription validation
3. Bicep template build and validation
4. Subscription-level deployment via New-AzDeployment
5. Output extraction and parsing
6. Orchestration of configuration and validation scripts

**Bash Equivalents:**
- `Get-AzContext` → `az account show`
- `New-AzDeployment` → `az deployment sub create`
- `bicep build` → Same command (Bicep CLI is cross-platform)
- Script execution → Source/call bash scripts with parameters
- Object property access → `jq` for JSON parsing from az CLI output

### Script 3: validate-deployment.ps1

**Current Dependencies:**
- PowerShell 7.0+
- Az.Accounts, Az.Resources, Az.CognitiveServices modules
- Complex validation state tracking
- Multiple resource type queries

**Key Functions:**
1. Test result tracking and reporting
2. Resource group validation
3. AI Foundry account verification
4. Model deployment enumeration
5. Managed identity, storage, and Key Vault checks
6. Content Understanding configuration verification
7. Network connectivity testing
8. Summary report generation

**Bash Equivalents:**
- `Get-AzResourceGroup` → `az group show`
- `Get-AzCognitiveServicesAccount` → `az cognitiveservices account show`
- `Get-AzCognitiveServicesAccountDeployment` → `az cognitiveservices account deployment list`
- `Get-AzUserAssignedIdentity` → `az identity list`
- `Get-AzStorageAccount` → `az storage account list`
- `Get-AzKeyVault` → `az keyvault list`
- Result tracking → Bash arrays or file-based state

## Implementation Plan

### Phase 1 - Setup and Prerequisites

**Objective:** Establish migration environment and document requirements

| Task       | Description                                                           | Action                                      |
|------------|-----------------------------------------------------------------------|---------------------------------------------|
| TASK-001   | Document Azure CLI version requirements                               | Add to README.md (minimum: Azure CLI 2.56+) |
| TASK-002   | Document required Azure CLI extensions                                | None required for this migration            |
| TASK-003   | Document jq requirement for JSON processing                           | Add to README.md (version 1.6+)             |
| TASK-004   | Document curl requirement for REST API calls                          | Add to README.md (standard with most Linux) |
| TASK-005   | Create bash script template with common functions                     | Create `infra/lib/common.sh`                |
| TASK-006   | Document testing approach and validation criteria                     | Create test checklist in this file          |

### Phase 2 - Migrate configure-content-understanding.ps1

**Objective:** Create `configure-content-understanding.sh` with full functionality parity

**Dependencies:** Phase 1 complete

| Task       | Description                                                           | Action                                          |
|------------|-----------------------------------------------------------------------|-------------------------------------------------|
| TASK-007   | Create script header with usage documentation                         | Add shebang, description, and parameters        |
| TASK-008   | Implement parameter parsing using getopts                             | Parse --ai-foundry-endpoint and model flags     |
| TASK-009   | Implement Azure authentication check                                  | Use `az account show` with error handling       |
| TASK-010   | Implement access token acquisition function                           | Use `az account get-access-token`               |
| TASK-011   | Implement JSON payload construction                                   | Use `jq` to build configuration object          |
| TASK-012   | Implement PATCH request to configure defaults                         | Use `curl` with proper headers and error checks |
| TASK-013   | Implement GET request to verify configuration                         | Use `curl` to retrieve current configuration    |
| TASK-014   | Implement configuration comparison logic                              | Use `jq` to compare expected vs actual          |
| TASK-015   | Add colored output functions (success, error, warning)                | Use ANSI color codes with tput fallback         |
| TASK-016   | Add comprehensive error handling and exit codes                       | Set -e, trap, and explicit exit codes           |
| TASK-017   | Test script with valid deployment                                     | Run against existing infrastructure             |
| TASK-018   | Test script with invalid parameters                                   | Verify error handling and messages              |

### Phase 3 - Migrate validate-deployment.ps1

**Objective:** Create `validate-deployment.sh` with comprehensive validation

**Dependencies:** Phase 1 complete

| Task       | Description                                                           | Action                                             |
|------------|-----------------------------------------------------------------------|----------------------------------------------------|
| TASK-019   | Create script header with usage documentation                         | Add shebang, description, and parameters           |
| TASK-020   | Implement parameter parsing (resource group, account name)            | Use getopts with required parameter validation     |
| TASK-021   | Create test result tracking data structure                            | Use associative arrays or parallel indexed arrays  |
| TASK-022   | Implement test result recording functions                             | Functions to add passed/failed/warning results     |
| TASK-023   | Implement Test 1: Azure authentication check                          | Use `az account show`                              |
| TASK-024   | Implement Test 2: Resource group validation                           | Use `az group show`                                |
| TASK-025   | Implement Test 3: AI Foundry account validation                       | Use `az cognitiveservices account show`            |
| TASK-026   | Implement Test 4: Model deployments validation                        | Use `az cognitiveservices account deployment list` |
| TASK-027   | Implement Test 5: Managed identity validation                         | Use `az identity list --resource-group`            |
| TASK-028   | Implement Test 6: Storage account validation                          | Use `az storage account list --resource-group`     |
| TASK-029   | Implement Test 7: Key Vault validation                                | Use `az keyvault list --resource-group`            |
| TASK-030   | Implement Test 8: Content Understanding config verification           | Use `curl` to call defaults API                    |
| TASK-031   | Implement Test 9: Network connectivity testing                        | Use `curl` to test endpoint accessibility          |
| TASK-032   | Implement validation summary report generation                        | Format and display results with colors             |
| TASK-033   | Implement proper exit code based on results                           | Exit 0 (pass), 1 (fail)                            |
| TASK-034   | Test script with healthy deployment                                   | Verify all tests pass                              |
| TASK-035   | Test script with missing resources                                    | Verify appropriate failures are detected           |

### Phase 4 - Migrate deploy.ps1

**Objective:** Create `deploy.sh` orchestrating the complete deployment flow

**Dependencies:** Phase 2 and Phase 3 complete

| Task       | Description                                                           | Action                                          |
|------------|-----------------------------------------------------------------------|-------------------------------------------------|
| TASK-036   | Create script header with usage documentation                         | Add shebang, description, and parameters        |
| TASK-037   | Implement parameter parsing with defaults                             | Parse --location, --template-file, etc.         |
| TASK-038   | Implement deployment banner and user confirmation                     | Use echo with colors, read for confirmation     |
| TASK-039   | Implement Azure authentication check                                  | Use `az account show`                           |
| TASK-040   | Implement template file existence checks                              | Use `[ -f ]` tests                              |
| TASK-041   | Implement Bicep template build validation                             | Use `bicep build` with error capture            |
| TASK-042   | Implement subscription-level deployment                               | Use `az deployment sub create`                  |
| TASK-043   | Implement deployment output extraction                                | Use `jq` to parse outputs from deployment JSON  |
| TASK-044   | Implement model deployment hash conversion                            | Convert JSON to bash parameters for config      |
| TASK-045   | Implement configure-content-understanding.sh invocation               | Call bash script with appropriate parameters    |
| TASK-046   | Implement validate-deployment.sh invocation                           | Call validation script with extracted outputs   |
| TASK-047   | Implement deployment summary display                                  | Format and display key outputs                  |
| TASK-048   | Implement comprehensive error handling                                | Trap errors, provide cleanup if needed          |
| TASK-049   | Test complete deployment flow                                         | Run full deployment in test subscription        |
| TASK-050   | Test error scenarios (failed deployment, missing files)               | Verify proper error handling                    |

### Phase 5 - Documentation and Cleanup

**Objective:** Update documentation and provide migration guidance

| Task       | Description                                                           | Action                                    |
|------------|-----------------------------------------------------------------------|-------------------------------------------|
| TASK-051   | Update infra/README.md with bash script usage                         | Replace PowerShell examples with bash     |
| TASK-052   | Add prerequisites section for Linux environments                      | List Azure CLI, jq, curl, bicep           |
| TASK-053   | Add troubleshooting section for common issues                         | Document authentication, permission issues|
| TASK-054   | Create migration guide for users transitioning                        | Document parameter differences            |
| TASK-055   | Archive or remove PowerShell scripts                                  | Move to `infra/archive/` or delete        |
| TASK-056   | Update root README.md deployment instructions                         | Reference new bash scripts                |
| TASK-057   | Verify all .sh files have execute permissions                         | Run `chmod +x infra/*.sh`                 |
| TASK-058   | Create CI/CD workflow example using bash scripts                      | Add GitHub Actions or GitLab CI example   |

## Technical Design Specifications

### Common Functions Library (`infra/lib/common.sh`)

```bash
#!/usr/bin/env bash

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
```

### Script 1: configure-content-understanding.sh

**Key Design Decisions:**
- Use long-form parameters (--ai-foundry-endpoint, --gpt4-deployment, etc.)
- Validate required parameters early with explicit error messages
- Use `jq` for all JSON manipulation to ensure correctness
- Implement retry logic for REST API calls (similar to PowerShell)
- Maintain same API version as PowerShell script

**Parameter Structure:**
```bash
--ai-foundry-endpoint <url>     # Required
--gpt4-deployment <name>        # Required
--gpt4-mini-deployment <name>   # Required
--embedding-deployment <name>   # Required
--api-version <version>         # Optional, default: 2025-11-01
```

### Script 2: deploy.sh

**Key Design Decisions:**
- Use `az deployment sub create` for subscription-level deployments
- Parse deployment outputs using `jq` with proper error handling
- Call other bash scripts using `source` or direct execution
- Implement same interactive confirmation as PowerShell version
- Provide skip flags for configuration and validation phases

**Parameter Structure:**
```bash
--location <region>                  # Optional, default: westus
--template-file <path>               # Optional, default: ./main.bicep
--parameter-file <path>              # Optional, default: ./main.bicepparam
--skip-validation                    # Optional flag
--skip-configuration                 # Optional flag
--yes                                # Skip confirmation prompt
```

### Script 3: validate-deployment.sh

**Key Design Decisions:**
- Use indexed arrays for test tracking (names, statuses, messages)
- Implement each test as a separate function for modularity
- Provide verbose mode for detailed output
- Generate structured JSON output option for CI/CD integration
- Exit with code 0 for pass/warnings, 1 for failures

**Parameter Structure:**
```bash
--resource-group <name>           # Required
--ai-foundry-account <name>       # Required
--verbose                         # Optional, show detailed output
--json-output <file>              # Optional, write JSON report
```

## Testing Strategy

### Unit Testing
- Test each script independently with mock Azure resources
- Verify parameter validation and error handling
- Test edge cases (empty parameters, invalid JSON, network failures)

### Integration Testing
- Deploy to test subscription using bash scripts
- Verify resource creation and configuration
- Run validation script to confirm deployment health

### Regression Testing
- Compare outputs of PowerShell vs bash scripts
- Ensure identical deployment results
- Verify exit codes match for success/failure scenarios

### Test Checklist

#### configure-content-understanding.sh
- [ ] Script executes with valid parameters
- [ ] Script fails gracefully with missing parameters
- [ ] Script validates Azure authentication
- [ ] Script obtains access token successfully
- [ ] Script sends correct JSON payload to API
- [ ] Script verifies configuration correctly
- [ ] Script detects mismatched configuration
- [ ] Exit codes match PowerShell behavior

#### deploy.sh
- [ ] Script shows deployment banner and prompts
- [ ] Script validates template files exist
- [ ] Script validates Bicep syntax
- [ ] Script executes subscription deployment
- [ ] Script extracts outputs correctly
- [ ] Script calls configuration script
- [ ] Script calls validation script
- [ ] Script displays deployment summary
- [ ] Exit codes match PowerShell behavior

#### validate-deployment.sh
- [ ] Script validates all required parameters
- [ ] Script tracks test results correctly
- [ ] All 9 tests execute successfully
- [ ] Failed tests are reported correctly
- [ ] Warnings are displayed appropriately
- [ ] Summary report is accurate
- [ ] Exit codes match PowerShell behavior
- [ ] JSON output option works correctly

## Risk Assessment

### Low Risk
- Bash syntax conversion (well-documented patterns)
- Azure CLI command substitution (straightforward mappings)
- File operations and path handling

### Medium Risk
- JSON parsing complexity with `jq` (requires testing)
- Error handling differences between PowerShell and bash
- String manipulation for URL normalization

### High Risk
- REST API authentication token handling (security-sensitive)
- Concurrent script execution and state management
- Cross-platform compatibility (different bash versions)

## Mitigation Strategies

1. **JSON Handling**: Use `jq` with explicit error checking on all operations
2. **Error Handling**: Use `set -euo pipefail` and trap for robust error handling
3. **Token Security**: Never log tokens, use secure temporary files if needed
4. **Testing**: Comprehensive testing in isolated environment before production use
5. **Documentation**: Provide clear examples and troubleshooting guides

## Success Criteria

- [ ] All three bash scripts execute successfully on Linux
- [ ] Deployment completes without errors using bash scripts
- [ ] Validation reports match PowerShell validation results
- [ ] Content Understanding configuration is applied correctly
- [ ] Documentation is updated and clear
- [ ] Team members can use bash scripts without PowerShell knowledge
- [ ] CI/CD pipelines can integrate bash scripts

## Timeline Estimate

| Phase   | Estimated Duration | Dependencies    |
|---------|-------------------|-----------------|
| Phase 1 | 2-4 hours         | None            |
| Phase 2 | 4-6 hours         | Phase 1         |
| Phase 3 | 6-8 hours         | Phase 1         |
| Phase 4 | 4-6 hours         | Phase 2, 3      |
| Phase 5 | 2-3 hours         | Phase 4         |
| **Total** | **18-27 hours** | Sequential      |

## Post-Migration Tasks

1. Update CI/CD pipelines to use bash scripts
2. Train team members on new script usage
3. Monitor first few deployments for issues
4. Collect feedback and iterate on improvements
5. Consider adding shell completion scripts for better UX

## References

### Azure CLI Documentation
- [az deployment sub create](https://learn.microsoft.com/cli/azure/deployment/sub)
- [az cognitiveservices account](https://learn.microsoft.com/cli/azure/cognitiveservices/account)
- [az account get-access-token](https://learn.microsoft.com/cli/azure/account#az-account-get-access-token)

### Tools Documentation
- [jq Manual](https://stedolan.github.io/jq/manual/)
- [Bash Reference Manual](https://www.gnu.org/software/bash/manual/)
- [Azure REST API Reference](https://learn.microsoft.com/rest/api/azure/)

### Related Files
- `/infra/main.bicep` - Main infrastructure template
- `/infra/main.bicepparam` - Deployment parameters
- `/infra/README.md` - Infrastructure documentation

## Appendix A: Command Mapping Reference

| PowerShell Cmdlet | Bash/Azure CLI Equivalent |
|-------------------|---------------------------|
| `Get-AzContext` | `az account show` |
| `Get-AzAccessToken -ResourceUrl <url>` | `az account get-access-token --resource <url>` |
| `New-AzDeployment` | `az deployment sub create` |
| `Get-AzResourceGroup` | `az group show` |
| `Get-AzCognitiveServicesAccount` | `az cognitiveservices account show` |
| `Get-AzCognitiveServicesAccountDeployment` | `az cognitiveservices account deployment list` |
| `Get-AzUserAssignedIdentity` | `az identity list` |
| `Get-AzStorageAccount` | `az storage account list` |
| `Get-AzKeyVault` | `az keyvault list` |
| `Invoke-RestMethod` | `curl` with appropriate flags |
| `ConvertTo-Json` | `jq` |
| `ConvertFrom-Json` | `jq -r` |

## Appendix B: Error Handling Patterns

### PowerShell Pattern
```powershell
try {
    $result = Some-Command
    if ($result.Status -eq "Success") {
        Write-Success "Operation completed"
    }
} catch {
    Write-Error "Operation failed: $_"
    exit 1
}
```

### Bash Equivalent
```bash
set -euo pipefail

if result=$(az some-command 2>&1); then
    if echo "$result" | jq -e '.status == "Success"' >/dev/null; then
        write_success "Operation completed"
    fi
else
    write_error "Operation failed: $result"
    exit 1
fi
```

## Appendix C: JSON Processing Examples

### Extract deployment outputs
```bash
# Get all outputs as JSON
outputs=$(az deployment sub show \
    --name "$deployment_name" \
    --query properties.outputs \
    -o json)

# Extract specific values
endpoint=$(echo "$outputs" | jq -r '.aiFoundryAccountEndpoint.value')
resource_group=$(echo "$outputs" | jq -r '.resourceGroupName.value')

# Extract model deployments object
model_deployments=$(echo "$outputs" | jq -r '.modelDeployments.value')
gpt4_deployment=$(echo "$model_deployments" | jq -r '.["gpt-4.1"]')
```

### Build configuration JSON
```bash
config=$(jq -n \
    --arg doc_processing "$gpt4_deployment" \
    --arg ocr "$gpt4_mini_deployment" \
    --arg embedding "$embedding_deployment" \
    '{
        modelDeployments: {
            documentProcessing: $doc_processing,
            ocr: $ocr,
            embedding: $embedding
        }
    }')
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-23  
**Maintainer:** Infrastructure Team
---
goal: Migrate PowerShell scripts to Bash for Linux-based deployments
status: planned
created: 2025-12-23
---

# PowerShell to Bash Migration Plan

## Executive Summary

This document outlines the complete migration strategy for converting the three PowerShell scripts under `/infra` to bash equivalents, enabling Linux-native deployment and configuration workflows for the Azure AI Foundry Content Understanding infrastructure.

**Scripts to migrate:**
1. `configure-content-understanding.ps1` - Configures Content Understanding default model mappings
2. `deploy.ps1` - Orchestrates complete Bicep deployment and configuration
3. `validate-deployment.ps1` - Validates deployment health and configuration

## Migration Scope

### In Scope
- Convert PowerShell syntax to bash equivalents
- Replace Azure PowerShell cmdlets with Azure CLI commands
- Maintain identical functionality and validation logic
- Preserve script parameters and configuration options
- Ensure error handling and user feedback mechanisms
- Maintain script exit codes for CI/CD compatibility

### Out of Scope
- Changes to Bicep templates or infrastructure definitions
- Modifications to deployment architecture or resource configurations
- Changes to Content Understanding API contracts
- Pipeline-specific implementations (GitHub Actions, Azure DevOps, etc.)

## Technical Analysis

### Script 1: configure-content-understanding.ps1

**Current Dependencies:**
- PowerShell 7.0+
- Az.Accounts module
- Azure AD authentication via Get-AzAccessToken
- REST API calls via Invoke-RestMethod

**Key Functions:**
1. Parameter validation and normalization
2. Azure access token acquisition (Cognitive Services scope)
3. Build and send PATCH request to Content Understanding API
4. Verify configuration with GET request
5. Compare and validate configured vs expected models

**Bash Equivalents:**
- `Get-AzContext` → `az account show`
- `Get-AzAccessToken` → `az account get-access-token --resource https://cognitiveservices.azure.com`
- `Invoke-RestMethod` → `curl` with appropriate headers and JSON payloads
- Hashtable → Bash associative arrays or JSON manipulation with `jq`
- ConvertTo-Json → `jq` for JSON formatting

### Script 2: deploy.ps1

**Current Dependencies:**
- PowerShell 7.0+
- Az.Accounts, Az.Resources modules
- Bicep CLI for template validation
- Dependency on configure-content-understanding.ps1 and validate-deployment.ps1

**Key Functions:**
1. Interactive confirmation prompts
2. Azure subscription validation
3. Bicep template build and validation
4. Subscription-level deployment via New-AzDeployment
5. Output extraction and parsing
6. Orchestration of configuration and validation scripts

**Bash Equivalents:**
- `Get-AzContext` → `az account show`
- `New-AzDeployment` → `az deployment sub create`
- `bicep build` → Same command (Bicep CLI is cross-platform)
- Script execution → Source/call bash scripts with parameters
- Object property access → `jq` for JSON parsing from az CLI output

### Script 3: validate-deployment.ps1

**Current Dependencies:**
- PowerShell 7.0+
- Az.Accounts, Az.Resources, Az.CognitiveServices modules
- Complex validation state tracking
- Multiple resource type queries

**Key Functions:**
1. Test result tracking and reporting
2. Resource group validation
3. AI Foundry account verification
4. Model deployment enumeration
5. Managed identity, storage, and Key Vault checks
6. Content Understanding configuration verification
7. Network connectivity testing
8. Summary report generation

**Bash Equivalents:**
- `Get-AzResourceGroup` → `az group show`
- `Get-AzCognitiveServicesAccount` → `az cognitiveservices account show`
- `Get-AzCognitiveServicesAccountDeployment` → `az cognitiveservices account deployment list`
- `Get-AzUserAssignedIdentity` → `az identity list`
- `Get-AzStorageAccount` → `az storage account list`
- `Get-AzKeyVault` → `az keyvault list`
- Result tracking → Bash arrays or file-based state

## Implementation Plan

### Phase 1 - Setup and Prerequisites

**Objective:** Establish migration environment and document requirements

| Task       | Description                                                           | Action                                      |
|------------|-----------------------------------------------------------------------|---------------------------------------------|
| TASK-001   | Document Azure CLI version requirements                               | Add to README.md (minimum: Azure CLI 2.56+) |
| TASK-002   | Document required Azure CLI extensions                                | None required for this migration            |
| TASK-003   | Document jq requirement for JSON processing                           | Add to README.md (version 1.6+)             |
| TASK-004   | Document curl requirement for REST API calls                          | Add to README.md (standard with most Linux) |
| TASK-005   | Create bash script template with common functions                     | Create `infra/lib/common.sh`                |
| TASK-006   | Document testing approach and validation criteria                     | Create test checklist in this file          |

### Phase 2 - Migrate configure-content-understanding.ps1

**Objective:** Create `configure-content-understanding.sh` with full functionality parity

**Dependencies:** Phase 1 complete

| Task       | Description                                                           | Action                                          |
|------------|-----------------------------------------------------------------------|-------------------------------------------------|
| TASK-007   | Create script header with usage documentation                         | Add shebang, description, and parameters        |
| TASK-008   | Implement parameter parsing using getopts                             | Parse --ai-foundry-endpoint and model flags     |
| TASK-009   | Implement Azure authentication check                                  | Use `az account show` with error handling       |
| TASK-010   | Implement access token acquisition function                           | Use `az account get-access-token`               |
| TASK-011   | Implement JSON payload construction                                   | Use `jq` to build configuration object          |
| TASK-012   | Implement PATCH request to configure defaults                         | Use `curl` with proper headers and error checks |
| TASK-013   | Implement GET request to verify configuration                         | Use `curl` to retrieve current configuration    |
| TASK-014   | Implement configuration comparison logic                              | Use `jq` to compare expected vs actual          |
| TASK-015   | Add colored output functions (success, error, warning)                | Use ANSI color codes with tput fallback         |
| TASK-016   | Add comprehensive error handling and exit codes                       | Set -e, trap, and explicit exit codes           |
| TASK-017   | Test script with valid deployment                                     | Run against existing infrastructure             |
| TASK-018   | Test script with invalid parameters                                   | Verify error handling and messages              |

### Phase 3 - Migrate validate-deployment.ps1

**Objective:** Create `validate-deployment.sh` with comprehensive validation

**Dependencies:** Phase 1 complete

| Task       | Description                                                           | Action                                             |
|------------|-----------------------------------------------------------------------|----------------------------------------------------|
| TASK-019   | Create script header with usage documentation                         | Add shebang, description, and parameters           |
| TASK-020   | Implement parameter parsing (resource group, account name)            | Use getopts with required parameter validation     |
| TASK-021   | Create test result tracking data structure                            | Use associative arrays or parallel indexed arrays  |
| TASK-022   | Implement test result recording functions                             | Functions to add passed/failed/warning results     |
| TASK-023   | Implement Test 1: Azure authentication check                          | Use `az account show`                              |
| TASK-024   | Implement Test 2: Resource group validation                           | Use `az group show`                                |
| TASK-025   | Implement Test 3: AI Foundry account validation                       | Use `az cognitiveservices account show`            |
| TASK-026   | Implement Test 4: Model deployments validation                        | Use `az cognitiveservices account deployment list` |
| TASK-027   | Implement Test 5: Managed identity validation                         | Use `az identity list --resource-group`            |
| TASK-028   | Implement Test 6: Storage account validation                          | Use `az storage account list --resource-group`     |
| TASK-029   | Implement Test 7: Key Vault validation                                | Use `az keyvault list --resource-group`            |
| TASK-030   | Implement Test 8: Content Understanding config verification           | Use `curl` to call defaults API                    |
| TASK-031   | Implement Test 9: Network connectivity testing                        | Use `curl` to test endpoint accessibility          |
| TASK-032   | Implement validation summary report generation                        | Format and display results with colors             |
| TASK-033   | Implement proper exit code based on results                           | Exit 0 (pass), 1 (fail)                            |
| TASK-034   | Test script with healthy deployment                                   | Verify all tests pass                              |
| TASK-035   | Test script with missing resources                                    | Verify appropriate failures are detected           |

### Phase 4 - Migrate deploy.ps1

**Objective:** Create `deploy.sh` orchestrating the complete deployment flow

**Dependencies:** Phase 2 and Phase 3 complete

| Task       | Description                                                           | Action                                          |
|------------|-----------------------------------------------------------------------|-------------------------------------------------|
| TASK-036   | Create script header with usage documentation                         | Add shebang, description, and parameters        |
| TASK-037   | Implement parameter parsing with defaults                             | Parse --location, --template-file, etc.         |
| TASK-038   | Implement deployment banner and user confirmation                     | Use echo with colors, read for confirmation     |
| TASK-039   | Implement Azure authentication check                                  | Use `az account show`                           |
| TASK-040   | Implement template file existence checks                              | Use `[ -f ]` tests                              |
| TASK-041   | Implement Bicep template build validation                             | Use `bicep build` with error capture            |
| TASK-042   | Implement subscription-level deployment                               | Use `az deployment sub create`                  |
| TASK-043   | Implement deployment output extraction                                | Use `jq` to parse outputs from deployment JSON  |
| TASK-044   | Implement model deployment hash conversion                            | Convert JSON to bash parameters for config      |
| TASK-045   | Implement configure-content-understanding.sh invocation               | Call bash script with appropriate parameters    |
| TASK-046   | Implement validate-deployment.sh invocation                           | Call validation script with extracted outputs   |
| TASK-047   | Implement deployment summary display                                  | Format and display key outputs                  |
| TASK-048   | Implement comprehensive error handling                                | Trap errors, provide cleanup if needed          |
| TASK-049   | Test complete deployment flow                                         | Run full deployment in test subscription        |
| TASK-050   | Test error scenarios (failed deployment, missing files)               | Verify proper error handling                    |

### Phase 5 - Documentation and Cleanup

**Objective:** Update documentation and provide migration guidance

| Task       | Description                                                           | Action                                    |
|------------|-----------------------------------------------------------------------|-------------------------------------------|
| TASK-051   | Update infra/README.md with bash script usage                         | Replace PowerShell examples with bash     |
| TASK-052   | Add prerequisites section for Linux environments                      | List Azure CLI, jq, curl, bicep           |
| TASK-053   | Add troubleshooting section for common issues                         | Document authentication, permission issues|
| TASK-054   | Create migration guide for users transitioning                        | Document parameter differences            |
| TASK-055   | Archive or remove PowerShell scripts                                  | Move to `infra/archive/` or delete        |
| TASK-056   | Update root README.md deployment instructions                         | Reference new bash scripts                |
| TASK-057   | Verify all .sh files have execute permissions                         | Run `chmod +x infra/*.sh`                 |
| TASK-058   | Create CI/CD workflow example using bash scripts                      | Add GitHub Actions or GitLab CI example   |

## Technical Design Specifications

### Common Functions Library (`infra/lib/common.sh`)

```bash
#!/usr/bin/env bash

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
```

### Script 1: configure-content-understanding.sh

**Key Design Decisions:**
- Use long-form parameters (--ai-foundry-endpoint, --gpt4-deployment, etc.)
- Validate required parameters early with explicit error messages
- Use `jq` for all JSON manipulation to ensure correctness
- Implement retry logic for REST API calls (similar to PowerShell)
- Maintain same API version as PowerShell script

**Parameter Structure:**
```bash
--ai-foundry-endpoint <url>     # Required
--gpt4-deployment <name>        # Required
--gpt4-mini-deployment <name>   # Required
--embedding-deployment <name>   # Required
--api-version <version>         # Optional, default: 2025-11-01
```

### Script 2: deploy.sh

**Key Design Decisions:**
- Use `az deployment sub create` for subscription-level deployments
- Parse deployment outputs using `jq` with proper error handling
- Call other bash scripts using `source` or direct execution
- Implement same interactive confirmation as PowerShell version
- Provide skip flags for configuration and validation phases

**Parameter Structure:**
```bash
--location <region>                  # Optional, default: westus
--template-file <path>               # Optional, default: ./main.bicep
--parameter-file <path>              # Optional, default: ./main.bicepparam
--skip-validation                    # Optional flag
--skip-configuration                 # Optional flag
--yes                                # Skip confirmation prompt
```

### Script 3: validate-deployment.sh

**Key Design Decisions:**
- Use indexed arrays for test tracking (names, statuses, messages)
- Implement each test as a separate function for modularity
- Provide verbose mode for detailed output
- Generate structured JSON output option for CI/CD integration
- Exit with code 0 for pass/warnings, 1 for failures

**Parameter Structure:**
```bash
--resource-group <name>           # Required
--ai-foundry-account <name>       # Required
--verbose                         # Optional, show detailed output
--json-output <file>              # Optional, write JSON report
```

## Testing Strategy

### Unit Testing
- Test each script independently with mock Azure resources
- Verify parameter validation and error handling
- Test edge cases (empty parameters, invalid JSON, network failures)

### Integration Testing
- Deploy to test subscription using bash scripts
- Verify resource creation and configuration
- Run validation script to confirm deployment health

### Regression Testing
- Compare outputs of PowerShell vs bash scripts
- Ensure identical deployment results
- Verify exit codes match for success/failure scenarios

### Test Checklist

#### configure-content-understanding.sh
- [ ] Script executes with valid parameters
- [ ] Script fails gracefully with missing parameters
- [ ] Script validates Azure authentication
- [ ] Script obtains access token successfully
- [ ] Script sends correct JSON payload to API
- [ ] Script verifies configuration correctly
- [ ] Script detects mismatched configuration
- [ ] Exit codes match PowerShell behavior

#### deploy.sh
- [ ] Script shows deployment banner and prompts
- [ ] Script validates template files exist
- [ ] Script validates Bicep syntax
- [ ] Script executes subscription deployment
- [ ] Script extracts outputs correctly
- [ ] Script calls configuration script
- [ ] Script calls validation script
- [ ] Script displays deployment summary
- [ ] Exit codes match PowerShell behavior

#### validate-deployment.sh
- [ ] Script validates all required parameters
- [ ] Script tracks test results correctly
- [ ] All 9 tests execute successfully
- [ ] Failed tests are reported correctly
- [ ] Warnings are displayed appropriately
- [ ] Summary report is accurate
- [ ] Exit codes match PowerShell behavior
- [ ] JSON output option works correctly

## Risk Assessment

### Low Risk
- Bash syntax conversion (well-documented patterns)
- Azure CLI command substitution (straightforward mappings)
- File operations and path handling

### Medium Risk
- JSON parsing complexity with `jq` (requires testing)
- Error handling differences between PowerShell and bash
- String manipulation for URL normalization

### High Risk
- REST API authentication token handling (security-sensitive)
- Concurrent script execution and state management
- Cross-platform compatibility (different bash versions)

## Mitigation Strategies

1. **JSON Handling**: Use `jq` with explicit error checking on all operations
2. **Error Handling**: Use `set -euo pipefail` and trap for robust error handling
3. **Token Security**: Never log tokens, use secure temporary files if needed
4. **Testing**: Comprehensive testing in isolated environment before production use
5. **Documentation**: Provide clear examples and troubleshooting guides

## Success Criteria

- [ ] All three bash scripts execute successfully on Linux
- [ ] Deployment completes without errors using bash scripts
- [ ] Validation reports match PowerShell validation results
- [ ] Content Understanding configuration is applied correctly
- [ ] Documentation is updated and clear
- [ ] Team members can use bash scripts without PowerShell knowledge
- [ ] CI/CD pipelines can integrate bash scripts

## Timeline Estimate

| Phase   | Estimated Duration | Dependencies    |
|---------|-------------------|-----------------|
| Phase 1 | 2-4 hours         | None            |
| Phase 2 | 4-6 hours         | Phase 1         |
| Phase 3 | 6-8 hours         | Phase 1         |
| Phase 4 | 4-6 hours         | Phase 2, 3      |
| Phase 5 | 2-3 hours         | Phase 4         |
| **Total** | **18-27 hours** | Sequential      |

## Post-Migration Tasks

1. Update CI/CD pipelines to use bash scripts
2. Train team members on new script usage
3. Monitor first few deployments for issues
4. Collect feedback and iterate on improvements
5. Consider adding shell completion scripts for better UX

## References

### Azure CLI Documentation
- [az deployment sub create](https://learn.microsoft.com/cli/azure/deployment/sub)
- [az cognitiveservices account](https://learn.microsoft.com/cli/azure/cognitiveservices/account)
- [az account get-access-token](https://learn.microsoft.com/cli/azure/account#az-account-get-access-token)

### Tools Documentation
- [jq Manual](https://stedolan.github.io/jq/manual/)
- [Bash Reference Manual](https://www.gnu.org/software/bash/manual/)
- [Azure REST API Reference](https://learn.microsoft.com/rest/api/azure/)

### Related Files
- `/infra/main.bicep` - Main infrastructure template
- `/infra/main.bicepparam` - Deployment parameters
- `/infra/README.md` - Infrastructure documentation

## Appendix A: Command Mapping Reference

| PowerShell Cmdlet | Bash/Azure CLI Equivalent |
|-------------------|---------------------------|
| `Get-AzContext` | `az account show` |
| `Get-AzAccessToken -ResourceUrl <url>` | `az account get-access-token --resource <url>` |
| `New-AzDeployment` | `az deployment sub create` |
| `Get-AzResourceGroup` | `az group show` |
| `Get-AzCognitiveServicesAccount` | `az cognitiveservices account show` |
| `Get-AzCognitiveServicesAccountDeployment` | `az cognitiveservices account deployment list` |
| `Get-AzUserAssignedIdentity` | `az identity list` |
| `Get-AzStorageAccount` | `az storage account list` |
| `Get-AzKeyVault` | `az keyvault list` |
| `Invoke-RestMethod` | `curl` with appropriate flags |
| `ConvertTo-Json` | `jq` |
| `ConvertFrom-Json` | `jq -r` |

## Appendix B: Error Handling Patterns

### PowerShell Pattern
```powershell
try {
    $result = Some-Command
    if ($result.Status -eq "Success") {
        Write-Success "Operation completed"
    }
} catch {
    Write-Error "Operation failed: $_"
    exit 1
}
```

### Bash Equivalent
```bash
set -euo pipefail

if result=$(az some-command 2>&1); then
    if echo "$result" | jq -e '.status == "Success"' >/dev/null; then
        write_success "Operation completed"
    fi
else
    write_error "Operation failed: $result"
    exit 1
fi
```

## Appendix C: JSON Processing Examples

### Extract deployment outputs
```bash
# Get all outputs as JSON
outputs=$(az deployment sub show \
    --name "$deployment_name" \
    --query properties.outputs \
    -o json)

# Extract specific values
endpoint=$(echo "$outputs" | jq -r '.aiFoundryAccountEndpoint.value')
resource_group=$(echo "$outputs" | jq -r '.resourceGroupName.value')

# Extract model deployments object
model_deployments=$(echo "$outputs" | jq -r '.modelDeployments.value')
gpt4_deployment=$(echo "$model_deployments" | jq -r '.["gpt-4.1"]')
```

### Build configuration JSON
```bash
config=$(jq -n \
    --arg doc_processing "$gpt4_deployment" \
    --arg ocr "$gpt4_mini_deployment" \
    --arg embedding "$embedding_deployment" \
    '{
        modelDeployments: {
            documentProcessing: $doc_processing,
            ocr: $ocr,
            embedding: $embedding
        }
    }')
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-23  
**Maintainer:** Infrastructure Team
