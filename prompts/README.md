# Prompts and Policies Directory

This directory contains the git-tracked configuration files for prompts and underwriting policies used by WorkbenchIQ.

## Files

### prompts.json
Contains the LLM prompts used for document analysis and extraction. These are organized by section and subsection, and can be customized per persona.

### risk-analysis-prompts.json
Contains prompts specifically for risk analysis operations that apply underwriting policies to extracted application data.

### life-health-underwriting-policies.json
Contains the life and health underwriting policy manual with risk assessment guidelines. These policies are used to:
- Evaluate applicant risk levels based on medical conditions
- Provide policy citations in risk assessments
- Determine premium loading recommendations

### policies.json
Contains claims/health plan policy definitions used for benefits and coverage information.

## Environment Variable

The location of this directory can be configured via the `UW_APP_PROMPTS_ROOT` environment variable (defaults to `prompts`).

## Editing

All files in this directory can be edited via the Admin panel in the WorkbenchIQ frontend:
- **Prompt Catalog** tab: Edit prompts.json
- **Underwriting Policies** tab: Edit life-health-underwriting-policies.json

Changes made through the admin interface are automatically saved to these files.
