<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 → 1.0.0
Bump rationale: Initial constitution adoption (MAJOR)

Modified principles: N/A (initial version)

Added sections:
- Core Principles (5 principles)
- Technology Stack & Constraints
- Quality & Development Workflow
- Governance

Removed sections: N/A (initial version)

Templates requiring updates:
- .specify/templates/plan-template.md ✅ (Constitution Check section compatible)
- .specify/templates/spec-template.md ✅ (Requirements alignment verified)
- .specify/templates/tasks-template.md ✅ (Phase structure compatible)

Deferred items: None
-->

# WorkbenchIQ Constitution

## Core Principles

### I. Persona-Driven Design
All features MUST be designed around the multi-persona workbench architecture. Each workflow (underwriting, claims processing) MUST:
- Operate independently with persona-specific prompts and configurations
- Share common infrastructure (API, storage, UI components) without tight coupling
- Support seamless persona switching without data loss or state corruption
- Enable future verticals (e.g., mortgage underwriting) through extensible persona patterns

**Rationale**: Insurance workflows differ significantly between underwriting and claims; persona isolation ensures domain-specific accuracy while code reuse minimizes maintenance burden.

### II. Confidence-Aware Extraction
All AI-extracted data MUST include field-level confidence scoring. The system MUST:
- Surface confidence indicators (high/medium/low) for every extracted field
- Never present AI-generated data without provenance tracking
- Enable users to verify extracted values against source documents
- Log extraction confidence for audit and model improvement

**Rationale**: Insurance decisions carry financial and regulatory consequences; underwriters and claims processors MUST know when to trust automated extraction vs. manual verification.

### III. Azure-First Integration
All cloud services MUST leverage Azure AI and Azure infrastructure. Specifically:
- Azure AI Content Understanding for document extraction (prebuilt-documentSearch)
- Azure AI Foundry for LLM-powered analysis and summarization
- Azure AD for secure service-to-service authentication
- Azure Blob Storage for document persistence (when configured)

**Rationale**: Microsoft accelerator status requires Azure-native implementation; consistent cloud provider reduces operational complexity and enables unified security posture.

### IV. Resilient API Design
All external API calls MUST implement resilience patterns. The system MUST:
- Apply exponential backoff with configurable retry limits
- Handle transient Azure service failures gracefully
- Provide real-time progress tracking for long-running operations
- Return structured error responses with actionable remediation guidance

**Rationale**: Document processing involves multi-second Azure AI calls; users MUST see progress and the system MUST recover from intermittent failures without manual intervention.

### V. Separation of Frontend and Backend
The application MUST maintain strict separation between:
- **Frontend**: Next.js 14 + Tailwind CSS for UI rendering and user interaction
- **Backend**: FastAPI for business logic, AI orchestration, and data persistence
- **API Contract**: REST endpoints with interactive Swagger documentation

Changes to backend logic MUST NOT require frontend modifications beyond API consumption. Frontend components MUST remain stateless where possible, delegating state management to API calls.

**Rationale**: Decoupled architecture enables independent scaling, testing, and deployment; Swagger documentation ensures API discoverability for integrators.

## Technology Stack & Constraints

### Mandated Technologies
| Layer | Technology | Version/Notes |
|-------|------------|---------------|
| Frontend | Next.js | 14.x with App Router |
| Styling | Tailwind CSS | Utility-first approach |
| Backend | FastAPI | Python 3.10+ |
| AI Extraction | Azure AI Content Understanding | prebuilt-documentSearch analyzer |
| LLM Analysis | Azure AI Foundry | GPT-4 class models |
| Authentication | Azure AD | Service-to-service auth |
| Storage | Local filesystem / Azure Blob | Configurable per deployment |

### Performance Expectations
- Document extraction: Complete within 60 seconds for standard applications (≤50 pages)
- API response time: ≤200ms for cached/simple operations; progress polling for long-running
- Frontend initial load: ≤3 seconds on broadband connections
- Concurrent users: Support 10+ simultaneous workbench sessions

### Security Constraints
- All Azure credentials MUST use environment variables or Azure Key Vault
- No PII (patient data, SSN, policy numbers) in application logs
- API endpoints MUST validate authentication before processing

## Quality & Development Workflow

### Code Quality Gates
- All PRs MUST pass linting (Python: ruff/black; TypeScript: ESLint)
- New API endpoints MUST include Swagger documentation
- Prompt changes MUST document expected behavior delta
- Configuration changes MUST update README or relevant docs

### Documentation Standards
- README.md MUST reflect current feature set and setup instructions
- API changes MUST update Swagger annotations
- Prompt catalog changes MUST include rationale in commit message

## Governance

This constitution supersedes all other development practices for WorkbenchIQ. Amendments require:

1. **Proposal**: Document the change with rationale and impact assessment
2. **Review**: At least one maintainer approval
3. **Migration**: Update affected code, tests, and documentation before merge
4. **Version Bump**: Follow semantic versioning (MAJOR for principle changes, MINOR for additions, PATCH for clarifications)

All pull requests MUST verify compliance with Core Principles. Deviations MUST be justified in PR description with reference to specific business requirements.

**Version**: 1.0.0 | **Ratified**: 2025-12-08 | **Last Amended**: 2025-12-08
