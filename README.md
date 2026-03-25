<div align="center">

# WorkbenchIQ

### AI-Powered Workbench for Underwriters & Claims Processors

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)
[![Azure AI](https://img.shields.io/badge/Azure-AI%20Services-0078D4.svg)](https://azure.microsoft.com/en-us/products/ai-services/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**WorkbenchIQ** is a Microsoft accelerator that provides a modern workbench for **underwriters** and **claims processors**, combining **Azure AI Content Understanding** and **Azure AI Foundry** to streamline document-heavy insurance workflows. It includes a **Customer 360** unified data layer that aggregates customer interactions across all product lines into a single cross-persona view.

[Features](#features) | [Quick Start](#quick-start) | [Architecture](#architecture) | [Use Cases](#business-use-cases) | [Configuration](#configuration)

</div>

---

## Screenshots

<table>
<tr>
<td width="50%">

**Underwriting Dashboard**

![Underwriting Dashboard](docs/images/dashboard.png)

*Main dashboard showing application list and document summary*

</td>
<td width="50%">

**Document Extraction**

![Document Extraction](docs/images/extraction-results.png)

*AI-powered field extraction with confidence scores*

</td>
</tr>
<tr>
<td width="50%">

**Claims Processing View**

![Claims View](docs/images/claims-view.png)

*Claims processing interface for medical claim review*

</td>
<td width="50%">

**Policy Risk Analysis**

![Policy Risk Analysis](docs/images/policy-risk-analysis.png)

*Policy report modal with risk evaluations and PDF export*

</td>
</tr>
<tr>
<td width="50%">

**Admin Panel**

![Admin Panel](docs/images/admin-panel.png)

*Prompt management and analyzer configuration*

</td>
</tr>
<tr>
<td width="50%">

**Ask IQ Chat Interface**

![Ask IQ Chat](docs/images/ask-iq-chat.png)

*Context-aware chat with policy and application knowledge*

</td>
<td width="50%">

**Rich Chat Cards**

![Rich Chat Cards](docs/images/chat-cards.png)

*Structured responses with risk factors and recommendations*

</td>
</tr>
</table>

---

## Business Use Cases

WorkbenchIQ accelerates the daily work of underwriters and claims processors:

### Life Insurance Underwriting

- **Challenge**: Underwriters manually review 50+ page applications with medical records, lab results, and family history
- **Solution**: Automatically extract key fields (applicant info, medical conditions, medications, risk factors) and generate structured underwriting summaries
- **Outcome**: Reduce review time from hours to minutes with AI-assisted risk assessment

### Insurance Claims Processing

- **Challenge**: Claims adjusters process medical claims requiring cross-referencing diagnosis codes, procedures, and policy coverage
- **Solution**: Extract ICD-10 codes, treatment details, and provider information; verify coverage eligibility automatically
- **Outcome**: Accelerate claims adjudication with intelligent document triage

### Mortgage Underwriting

- **Challenge**: Loan officers review income verification, property appraisals, and credit documentation across dozens of documents
- **Solution**: Extract borrower information, income sources, debt-to-income ratios, and property valuations; auto-calculate GDS/TDS/LTV ratios against OSFI B-20 guidelines
- **Outcome**: Streamline loan approval with consistent document analysis and regulatory compliance checks

### Customer 360 — Unified Data Layer

- **Challenge**: Underwriters and claims assessors make decisions in silos, missing cross-product risk patterns (e.g., a health claim correlating with a life insurance referral)
- **Solution**: Aggregate customer interactions across all personas into a unified timeline with risk correlation insights and cross-persona summary cards
- **Outcome**: Holistic customer view enables better-informed decisions and reveals risk patterns invisible in single-product views

---

## Features

### Core Capabilities

- **Multi-Persona Workbench** - Switch between underwriting, claims, and mortgage workflows with persona-specific views
- **Customer 360 View** - Cross-persona customer journey with timeline, risk correlations, and persona summary cards
- **Intelligent Document Extraction** - Azure AI Content Understanding with custom and prebuilt analyzers
- **AI-Powered Analysis** - LLM prompts for comprehensive document summarization and risk assessment
- **Confidence Scoring** - Field-level confidence indicators for extracted data
- **Custom Prompt Engineering** - Editable prompt catalog tailored to each persona's workflow
- **Progress Tracking** - Real-time status updates for long-running operations
- **Deep-Link Navigation** - URL-based routing (`/?app={id}&persona={id}`) for cross-view navigation

### Underwriting Policy Integration

- **Policy-Driven Risk Ratings** - Automated risk assessment based on documented underwriting policies with auditable citations
- **Risk Rating Popovers** - Hover over any risk rating to see the rationale and policy reference
- **Policy Report Modal** - Full policy evaluation summary with all risk factors and PDF export
- **Policy Summary Panel** - At-a-glance recommended action with policy alignment

### AI Chat Experience

- **Ask IQ Chat Interface** - Context-aware chat drawer for asking questions about applications
- **Policy & Application Context** - AI responses grounded in both application data and underwriting policies
- **Rich Response Cards** - Structured responses with visual cards for risk factors, policy lists, recommendations, and comparisons
- **Chat History** - Persistent chat sessions per application with slide-out history panel
- **Smart Recommendations** - Decision cards showing approve/defer/decline with confidence levels and conditions

### RAG-Powered Policy Search *(Optional)*

- **Semantic Policy Retrieval** - Vector-based search finds relevant policy sections using Azure OpenAI embeddings
- **Hybrid Search** - Combines semantic similarity with keyword matching (pg_trgm) for comprehensive results
- **Policy Citations** - Chat responses include expandable citations linking to specific policy sections
- **RAG Metadata** - View chunks retrieved, token usage, and latency for transparency
- **Auto-Indexing** - Policies are automatically chunked and indexed when created or updated
- **Admin Controls** - Manual reindex button and index statistics in the Admin panel

### Customer 360 — Unified Data Layer

- **Cross-Persona Customer View** - Aggregates applications across underwriting, claims, and mortgage into a unified profile
- **Customer Journey Timeline** - Chronological view of all interactions, color-coded by persona (indigo/cyan/red/emerald)
- **Risk Correlation Engine** - Highlights cross-product risk patterns (e.g., cardiac health claim correlating with life insurance referral)
- **Persona Summary Cards** - Collapsible per-persona cards with key metrics (GDS/TDS for mortgage, risk class for underwriting, claim amounts for claims)
- **Journey Metrics Dashboard** - KPIs showing total products, active claims, risk score, and correlation severity
- **Workbench Deep-Links** - Click any timeline event to open the application in its persona-specific workbench
- **Azure Blob Storage** - Customer profiles stored alongside application data with provider abstraction
- **Seed Data Script** - `python scripts/seed_customer360.py` generates 3 customer profiles with 9 rich applications across all personas

### Mortgage Underwriting Workbench

- **3-Column Layout** - Evidence panel, Data/Calculations/Policy tabs, and Risk assessment
- **OSFI B-20 Compliance** - Automated GDS/TDS/LTV ratio calculation with stress testing at MQR
- **Borrower Analysis** - Income aggregation from T4s, pay stubs, employment letters; B1/B2 dual-income support
- **Property Deep Dive** - AI-powered property analysis with comparable sales data via Bing Grounding
- **Policy Checks Panel** - Pass/warning/fail findings with evidence citations and calculated values
- **Decision Footer** - Approve/Conditional/Decline with condition management

### Automotive Claims Workbench

- **Multimodal Evidence** - Process documents, images, and videos with specialized analyzers
- **Damage Assessment** - Visual damage analysis with severity ratings and repair cost estimates
- **Liability Determination** - Fault analysis with police report and video evidence correlation
- **Fraud Detection** - Red flag analysis with SIU investigation triggers
- **Payout Recommendation** - Settlement analysis with deductible calculations

### Technical Features

- **Modern Stack** - Next.js 14 + Tailwind CSS frontend, FastAPI backend
- **REST API** - Full API with interactive Swagger documentation
- **Azure AD Authentication** - Secure service-to-service authentication
- **Storage Abstraction** - Pluggable storage providers (local filesystem + Azure Blob Storage)
- **Extensible Personas** - Easy to add new industry verticals with persona-specific analyzers
- **Retry Logic** - Resilient API calls with exponential backoff
- **PostgreSQL + pgvector** - Optional vector database for RAG-powered policy search
- **Hybrid Search** - Semantic (HNSW index) + keyword (GIN/pg_trgm) search capabilities
- **Large Document Processing** - Auto-detection and batch processing for documents exceeding standard limits

---

## Architecture

```
+-----------------------------------------------------------------------------+
|                              USER INTERFACE                                  |
|                                                                             |
|    +-------------+    +-------------+    +-------------+                    |
|    | Underwriting|    |   Claims    |    |  Mortgage   |                    |
|    |  Workbench  |    |  Workbench  |    |  Workbench  |                    |
|    +------+------+    +------+------+    +------+------+                    |
|           |                  |                  |                           |
|           +------------------+------------------+                           |
|                              |                                              |
|                    +---------v---------+                                    |
|                    |   Next.js 14 UI   |                                    |
|                    |  (React + Tailwind)|                                   |
|                    +---------+---------+                                    |
+------------------------------+----------------------------------------------+
                               | REST API
+------------------------------+----------------------------------------------+
|                    +---------v---------+                                    |
|                    |   FastAPI Server  |                                    |
|                    |   (Python 3.10+)  |                                    |
|                    +---------+---------+                                    |
|                              |                                              |
|              +---------------+---------------+                              |
|              |               |               |                              |
|    +---------v-----+ +-------v-------+ +-----v-----+                        |
|    |   Personas    | |    Prompts    | |  Storage  |                        |
|    |    Engine     | |    Catalog    | |  Manager  |                        |
|    +---------------+ +---------------+ +-----------+                        |
|                              |                                              |
|                              | BACKEND                                      |
+------------------------------+----------------------------------------------+
                               |
+------------------------------+----------------------------------------------+
|                              | AZURE AI SERVICES                            |
|              +---------------+---------------+                              |
|              |                               |                              |
|    +---------v----------+      +-------------v-------------+                |
|    |  Azure AI Content  |      |      Azure OpenAI         |                |
|    |   Understanding    |      |       (LLM + Embeddings)  |                |
|    |                    |      |                           |                |
|    | - Document Search  |      | - Underwriting Summaries  |                |
|    | - Field Extraction |      | - Risk Assessment         |                |
|    | - OCR + Layout     |      | - Medical Analysis        |                |
|    | - Confidence Scores|      | - Requirements Checklist  |                |
|    +--------------------+      | - text-embedding-3-small  |                |
|                                +---------------------------+                |
|                                              |                              |
+----------------------------------------------+------------------------------+
                                               |
+----------------------------------------------+------------------------------+
|                              | AZURE DATA SERVICES (Optional)               |
|                              |                                              |
|                    +---------v---------+                                    |
|                    | Azure PostgreSQL  |                                    |
|                    | Flexible Server   |                                    |
|                    |                   |                                    |
|                    | - pgvector (HNSW) |                                    |
|                    | - pg_trgm (GIN)   |                                    |
|                    | - Policy Chunks   |                                    |
|                    | - RAG Search      |                                    |
|                    +-------------------+                                    |
|                                                                             |
+-----------------------------------------------------------------------------+
```

### Data Flow

```
+----------+     +--------------+     +-----------------+     +--------------+
|  Upload  |---->|   Extract    |---->|     Analyze     |---->|    Review    |
|   PDFs   |     |   (Azure CU) |     |   (Azure AI Foundry)   |     |   Results    |
+----------+     +--------------+     +-----------------+     +--------------+
     |                  |                      |                      |
     |           - Parse documents      - Run prompts           - View summaries
     |           - Extract fields       - Generate insights     - Check confidence
     |           - Get confidence       - Risk assessment       - Export data
     |
  PDF files stored locally in data/applications/{id}/files/
```

---

## Available Workbenches

| Persona | Status | Description |
|---------|--------|-------------|
| **Life & Health Underwriting** | ✅ Active | Life insurance underwriting — process applications, medical records, lab results, and risk assessment |
| **Life & Health Claims** | ✅ Active | Health insurance claims — eligibility verification, medical necessity review, benefits adjudication |
| **Automotive Claims** | ✅ Active | Multimodal vehicle claims — damage assessment, liability, fraud detection with image/video/document support |
| **Mortgage Underwriting** | ✅ Active | Canadian residential mortgage — OSFI B-20 compliance, GDS/TDS/LTV calculations, stress testing |
| **Customer 360** | ✅ Active | Cross-persona unified view — customer journey timeline, risk correlations, persona summary cards |

---

## Prerequisites

- **Python 3.10+** - Backend runtime
- **Node.js 18+** - Frontend runtime
- **[uv](https://github.com/astral-sh/uv)** or **pip** - Python dependency management
- **Azure Subscription** with the following services:
  - **Azure AI Content Understanding** with `prebuilt-documentSearch` analyzer
  - **Azure OpenAI Service** with `gpt-4.1` or `gpt-4o` deployment

---

## Quick Start

### 1. Clone & Install Dependencies

```bash
# Clone the repository
git clone https://github.com/microsoft/workbenchiq.git
cd workbenchiq

# Install Python dependencies (using uv - recommended)
uv sync

# OR using pip
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configure Azure Services

Create a `.env` file in the project root:

```env
# Azure AI Content Understanding
AZURE_CONTENT_UNDERSTANDING_ENDPOINT=https://your-resource.cognitiveservices.azure.com
AZURE_CONTENT_UNDERSTANDING_USE_AZURE_AD=true
# If not using Azure AD, set API key:
# AZURE_CONTENT_UNDERSTANDING_API_KEY=your-key-here

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-1

# Optional Configuration
# UW_APP_STORAGE_ROOT=data
# AZURE_OPENAI_API_VERSION=2024-10-21
```

**Authentication Options:**

| Method | When to Use | Configuration |
|--------|-------------|---------------|
| **Azure AD** (Recommended) | Production, CI/CD | Set `AZURE_CONTENT_UNDERSTANDING_USE_AZURE_AD=true` and run `az login` |
| **API Key** | Local development | Set `USE_AZURE_AD=false` and provide `AZURE_CONTENT_UNDERSTANDING_API_KEY` |

### 3. Run the Application

**Option 1: Run both servers together**

```bash
# Windows
scripts/run_frontend.bat

# Linux/Mac
./scripts/run_frontend.sh
```

**Option 2: Run servers separately**

```bash
# Terminal 1: Start API server
uv run python -m uvicorn api_server:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev
```

### 4. Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## API Authentication

The backend API supports optional API key authentication via the `X-API-Key` header.

### Setup

Set the `API_KEY` environment variable on **both** the backend and frontend:

```bash
# In your .env file (must be at least 32 characters)
API_KEY=your-secret-api-key-at-least-32-characters-long
```

### Behaviour

| `API_KEY` env var | Result |
|-------------------|--------|
| **Not set** | All endpoints are open (development mode). A warning is logged at startup. |
| **Set** | Every request must include an `X-API-Key` header with the matching key. Invalid/missing keys receive `401 Unauthorized`. |

### How it works

- The frontend Next.js proxy automatically injects the `X-API-Key` header server-side — the key is **never exposed to the browser**.
- Direct API consumers (scripts, Postman, etc.) must include the header manually:

```bash
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/applications
```

### Production deployment

When deploying to Azure App Service, set `API_KEY` as an app setting. The `scripts/set_webapp_settings.sh` script will pick it up from your `.env` file automatically.

---

## Usage Guide

### Underwriter Workflow

1. **Create New Application**
   - Select "Underwriting" persona from the dropdown
   - Click "New Application"
   - Enter optional external reference/policy number
   - Upload PDF documents (applications, medical records, lab reports)
   - Click "Create Application"

2. **Document Extraction**
   - The system automatically runs Azure AI Content Understanding
   - Extracts 30+ fields including: Applicant info, medical history, medications, lab results
   - Each field shows confidence scores (High/Medium/Low)

3. **AI Analysis**
   - LLM generates structured summaries:
     - **Customer Profile** - Demographics and policy details
     - **Medical Summary** - Conditions, medications, family history
     - **Risk Assessment** - Hypertension, cholesterol, lifestyle factors
     - **Requirements** - Pending items and next steps

4. **Policy-Driven Risk Assessment**
   - Hover over any risk rating to see the rationale and policy citation
   - Click "Run Policy Check" to generate a full policy evaluation report
   - View all risk factors at once with the Policy Report modal
   - Export policy reports as PDF for auditing or case files

5. **Ask IQ Chat**
   - Click the floating "Ask IQ" button to open the chat drawer
   - Ask questions about the application with full context awareness
   - AI responses include policy citations and structured risk analysis
   - View chat history in the slide-out panel; switch between conversations
   - Rich response cards display risk factors, recommendations, and comparisons

6. **Review & Export**
   - Review extracted fields with source citations
   - View confidence indicators
   - Export results as needed

### Admin Workflow

1. **Edit Prompts** - Customize AI prompts for your specific use case
2. **Manage Analyzers** - Create/delete custom analyzers for field extraction
3. **Re-run Analysis** - Selectively re-process sections with updated prompts

---

## Project Structure

```
workbenchiq/
├── api_server.py                 # FastAPI backend server
├── app/
│   ├── config.py                 # Configuration management
│   ├── customer360.py            # Customer 360 unified data layer (blob-aware)
│   ├── personas.py               # Multi-persona definitions & field schemas
│   ├── storage.py                # File and metadata handling (provider abstraction)
│   ├── storage_providers/        # Pluggable storage backends
│   │   ├── base.py               # StorageProvider protocol & settings
│   │   ├── local.py              # Local filesystem provider
│   │   └── azure_blob.py         # Azure Blob Storage provider
│   ├── prompts.py                # Prompt templates & catalog
│   ├── openai_client.py          # Azure OpenAI integration
│   ├── content_understanding_client.py  # Azure CU integration
│   ├── processing.py             # Orchestration logic
│   ├── underwriting_policies.py  # Policy loader and injector
│   ├── utils.py                  # Helper utilities
│   ├── claims/                   # Claims processing module
│   │   ├── api.py                # Claims API router
│   │   ├── engine.py             # Claims policy engine
│   │   ├── policies.py           # Claims policy loader
│   │   └── search.py             # Claims policy search (RAG)
│   ├── mortgage/                 # Mortgage underwriting module
│   │   ├── processor.py          # Document processing & extraction
│   │   ├── calculator.py         # GDS/TDS/LTV ratio calculations
│   │   ├── policy_engine.py      # OSFI B-20 compliance engine
│   │   ├── risk_analysis.py      # Mortgage risk factor scoring
│   │   ├── stress_test.py        # Stress test at MQR rates
│   │   ├── aggregator.py         # Multi-document data aggregation
│   │   ├── property_deep_dive.py # AI property analysis (Bing Grounding)
│   │   └── extractors/           # Field extractors (borrower, income, property, loan, credit)
│   ├── database/                 # PostgreSQL connection management
│   └── rag/                      # RAG module (optional PostgreSQL)
│       ├── chunker.py            # Policy text chunking
│       ├── embedder.py           # Azure OpenAI embedding client
│       ├── repository.py         # PostgreSQL CRUD operations
│       ├── search.py             # Semantic & hybrid search
│       ├── service.py            # Unified RAG service interface
│       └── indexer.py            # Policy indexing pipeline
├── scripts/                      # Utility scripts
│   ├── seed_customer360.py       # Seed Customer 360 data (local + Azure Blob)
│   ├── seed_data/                # Rich seed data modules
│   │   ├── underwriting.py       # 3 underwriting apps with full LLM outputs
│   │   ├── claims.py             # 2 auto claims + 1 health claim
│   │   └── mortgage.py           # 3 mortgage apps with extracted fields
│   ├── setup_postgresql_rag.py   # Azure PostgreSQL provisioning
│   └── index_policies.py         # CLI for policy indexing
├── prompts/                      # Git-tracked prompts & policies
│   ├── prompts.json              # LLM prompts for document analysis
│   ├── risk-analysis-prompts.json
│   ├── life-health-underwriting-policies.json
│   ├── life-health-claims-policies.json
│   ├── automotive-claims-policies.json
│   └── mortgage-underwriting-policies.json
├── frontend/                     # Next.js 14 frontend
│   ├── src/
│   │   ├── app/                  # Next.js pages (App Router)
│   │   │   ├── page.tsx          # Home — landing + workbench (deep-link support)
│   │   │   ├── customers/        # Customer 360 pages
│   │   │   │   ├── page.tsx      # Customer list
│   │   │   │   └── [id]/page.tsx # Customer detail (360 view)
│   │   │   ├── admin/            # Admin panel
│   │   │   └── login/            # Authentication
│   │   ├── components/           # React components
│   │   │   ├── customer360/      # Customer 360 components
│   │   │   │   ├── CustomerListView.tsx
│   │   │   │   ├── CustomerProfileHeader.tsx
│   │   │   │   ├── CustomerTimeline.tsx
│   │   │   │   ├── PersonaSummaryCard.tsx
│   │   │   │   ├── RiskCorrelationBanner.tsx
│   │   │   │   └── CustomerJourneyMetrics.tsx
│   │   │   ├── mortgage/         # Mortgage workbench components
│   │   │   │   ├── MortgageWorkbench.tsx
│   │   │   │   ├── DataWorksheet.tsx
│   │   │   │   ├── CalculationsPanel.tsx
│   │   │   │   ├── PolicyChecksPanel.tsx
│   │   │   │   ├── RiskPanel.tsx
│   │   │   │   └── DecisionFooter.tsx
│   │   │   ├── claims/           # Claims-specific components
│   │   │   ├── chat/             # Chat components
│   │   │   └── ...               # Shared components
│   │   └── lib/                  # Utilities, API client, types, PersonaContext
│   │       ├── customer360-types.ts  # Customer 360 type definitions
│   │       ├── customer360-api.ts    # Customer 360 API client
│   │       ├── personas.ts           # Persona definitions & UI config
│   │       └── ...
│   └── package.json
├── tests/                        # Test suite and fixtures
├── data/                         # Application data storage (gitignored)
├── docs/
│   └── images/                   # Screenshots for documentation
└── .env.example                  # Environment template
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| **Applications** | | |
| `GET` | `/api/personas` | List all available personas |
| `GET` | `/api/personas/{id}` | Get specific persona configuration |
| `GET` | `/api/applications` | List all applications (filterable by `?persona=`) |
| `GET` | `/api/applications/{id}` | Get application details |
| `POST` | `/api/applications` | Create new application with file upload |
| `POST` | `/api/applications/{id}/extract` | Run Content Understanding extraction |
| `POST` | `/api/applications/{id}/analyze` | Run GPT analysis |
| `POST` | `/api/applications/{id}/risk-analysis` | Run full policy evaluation |
| **Customer 360** | | |
| `GET` | `/api/customers` | List all customer profiles |
| `GET` | `/api/customers/{id}` | Get Customer 360 view (profile, journey, risk correlations) |
| **Mortgage** | | |
| `GET` | `/api/mortgage/applications` | List mortgage applications |
| `GET` | `/api/mortgage/applications/{id}` | Get mortgage app with computed ratios & findings |
| `GET` | `/api/mortgage/applications/{id}/property-deep-dive` | Get property deep dive analysis |
| `POST` | `/api/mortgage/applications/{id}/property-deep-dive` | Run property deep dive |
| **Claims** | | |
| `POST` | `/api/claims/submit` | Submit a claim with files |
| `GET` | `/api/claims/{id}/assessment` | Get claim assessment |
| `POST` | `/api/claims/policies/search` | Search claims policies |
| **Chat & RAG** | | |
| `POST` | `/api/applications/{id}/chat` | Send chat message with context |
| `GET` | `/api/applications/{id}/conversations` | List chat sessions |
| `GET` | `/api/conversations` | List all conversations across applications |
| `POST` | `/api/rag/index` | Index all policies for RAG |
| `GET` | `/api/rag/stats` | Get RAG index statistics |
| `POST` | `/api/rag/query` | Query policies using semantic search |
| **Admin** | | |
| `GET` | `/api/prompts` | Get prompt catalog |
| `PUT` | `/api/prompts/{section}/{subsection}` | Update a prompt |
| `GET` | `/api/policies` | Get all underwriting policies |
| `POST` | `/api/policies` | Create a new underwriting policy |
| `GET` | `/api/analyzer/status` | Get custom analyzer status |
| `POST` | `/api/analyzer/create` | Create custom analyzer |

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEY` | No | - | API key for backend authentication (`X-API-Key` header). Must be 32+ chars. Set on both backend and frontend. |
| `AZURE_CONTENT_UNDERSTANDING_ENDPOINT` | Yes | - | Azure AI Content Understanding endpoint |
| `AZURE_CONTENT_UNDERSTANDING_API_KEY` | Conditional | - | API key (if not using Azure AD) |
| `AZURE_CONTENT_UNDERSTANDING_USE_AZURE_AD` | No | `true` | Use Azure AD authentication |
| `AZURE_OPENAI_ENDPOINT` | Yes | - | Azure OpenAI endpoint |
| `AZURE_OPENAI_API_KEY` | Yes | - | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Yes | - | GPT-4.1 deployment name |
| `AZURE_OPENAI_API_VERSION` | No | `2024-10-21` | Azure OpenAI API version |
| `UW_APP_STORAGE_ROOT` | No | `data` | Local storage path for application data |
| `UW_APP_PROMPTS_ROOT` | No | `prompts` | Path to prompts and policies directory |
| `STORAGE_BACKEND` | No | `azure_blob` | Storage backend (`azure_blob` or `local`) |
| `AZURE_STORAGE_AUTH_MODE` | No | `default` | Auth method: `default` (DAC only) or `key` (account key only) — no fallback |
| `AZURE_STORAGE_ACCOUNT_NAME` | Conditional | - | Azure storage account name (required for DAC and key auth) |
| `AZURE_STORAGE_ACCOUNT_KEY` | Conditional | - | Azure storage account key (if not using DAC) |
| `AZURE_STORAGE_CONTAINER_NAME` | No | `workbenchiq-data` | Azure blob container name |
| `AZURE_STORAGE_ALLOW_CREATE_CONTAINER` | No | `false` | Auto-create container on startup (set `true` for dev only) |
| `DATABASE_BACKEND` | No | `json` | Database backend (`json` or `postgresql`) |
| `POSTGRESQL_HOST` | Conditional | - | PostgreSQL host (if using postgresql backend) |
| `POSTGRESQL_PORT` | No | `5432` | PostgreSQL port |
| `POSTGRESQL_DATABASE` | Conditional | - | PostgreSQL database name |
| `POSTGRESQL_USER` | Conditional | - | PostgreSQL username |
| `POSTGRESQL_PASSWORD` | Conditional | - | PostgreSQL password |
| `POSTGRESQL_SSL_MODE` | No | - | SSL mode (`require`, `verify-full`, etc.) |
| `POSTGRESQL_SCHEMA` | No | `public` | PostgreSQL schema for RAG tables |
| `RAG_ENABLED` | No | `false` | Enable RAG-powered policy search |
| `RAG_TOP_K` | No | `5` | Number of policy chunks to retrieve |
| `RAG_SIMILARITY_THRESHOLD` | No | `0.5` | Minimum similarity score for results |
| `EMBEDDING_MODEL` | No | `text-embedding-3-small` | Azure OpenAI embedding model name |
| `EMBEDDING_DEPLOYMENT` | No | Same as model | Azure OpenAI embedding deployment name |
| `EMBEDDING_DIMENSIONS` | No | `1536` | Embedding vector dimensions |

### Storage Configuration

WorkbenchIQ supports two storage backends:

**Azure Blob Storage (Default)**

For production deployments, use Azure Blob Storage. Set `AZURE_STORAGE_AUTH_MODE`
to choose your auth method explicitly — there is **no automatic fallback**.

```env
STORAGE_BACKEND=azure_blob

# Auth mode — "default" uses DefaultAzureCredential only.
# Set to "key" to use account name + key instead.
AZURE_STORAGE_AUTH_MODE=default

# Account name (required for DAC and key auth)
AZURE_STORAGE_ACCOUNT_NAME=mystorageaccount

# Option A: Managed identity / DefaultAzureCredential (recommended)
#   No secret needed — ensure the identity has the
#   "Storage Blob Data Contributor" role on the container.

# Option B: Account key
# AZURE_STORAGE_ACCOUNT_KEY=your-storage-account-key

# Container name (optional, defaults to workbenchiq-data)
AZURE_STORAGE_CONTAINER_NAME=workbenchiq-data

# Container auto-creation (default: false — least-privilege)
# Set to true only in dev/migration scenarios.
AZURE_STORAGE_ALLOW_CREATE_CONTAINER=false
```

**Local Storage**

For local development, you can use filesystem storage.

```env
STORAGE_BACKEND=local
UW_APP_STORAGE_ROOT=data
```

**RBAC Prerequisites for managed identity (DAC):**

| Role | Scope | Purpose |
|------|-------|---------|
| Storage Blob Data Contributor | Container | Read/write blobs |
| Storage Blob Data Reader | Container | Read-only access |

Assign via Azure CLI:

```bash
az role assignment create \
  --assignee <principal-id> \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<account>/blobServices/default/containers/<container>
```

See [quickstart.md](specs/003-azure-blob-storage-integration/quickstart.md) for detailed setup instructions.

### PostgreSQL RAG Configuration *(Optional)*

For enhanced policy search with semantic retrieval, you can enable the RAG (Retrieval-Augmented Generation) feature using Azure PostgreSQL Flexible Server with pgvector:

**Prerequisites:**
- Azure PostgreSQL Flexible Server (v15+)
- Extensions enabled: `vector` (pgvector), `pg_trgm`
- Azure OpenAI embedding model deployed (e.g., `text-embedding-3-small`)

**Quick Setup:**

```bash
# Start your Azure PostgreSQL server (if stopped)
az postgres flexible-server start --resource-group workbenchiq-rg --name workbenchiq-db

# Run the setup script to provision Azure PostgreSQL and create schema
uv run python scripts/setup_postgresql_rag.py

# Index existing policies
uv run python scripts/index_policies.py
```

**Server Management:**

```bash
# Check server status
az postgres flexible-server show --resource-group workbenchiq-rg --name workbenchiq-db --query "state"

# Stop server (to save costs when not in use)
az postgres flexible-server stop --resource-group workbenchiq-rg --name workbenchiq-db
```

**Manual Configuration:**

```env
# Enable PostgreSQL backend
DATABASE_BACKEND=postgresql

# PostgreSQL connection
POSTGRESQL_HOST=your-server.postgres.database.azure.com
POSTGRESQL_PORT=5432
POSTGRESQL_DATABASE=workbenchiq
POSTGRESQL_USER=your_admin_user
POSTGRESQL_PASSWORD=your_password
POSTGRESQL_SSL_MODE=require

# Enable RAG
RAG_ENABLED=true
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.5

# Embedding model (must match your Azure OpenAI deployment)
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DEPLOYMENT=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

**How RAG Works:**

1. **Indexing** - Policies are chunked (500 tokens, 50 overlap) and embedded using Azure OpenAI
2. **Storage** - Chunks stored in PostgreSQL with pgvector HNSW index for fast similarity search
3. **Query** - User questions are embedded and matched against policy chunks
4. **Hybrid Search** - Combines vector similarity with keyword matching (pg_trgm) for best results
5. **Augmentation** - Retrieved policy context is injected into chat prompts for grounded responses

**Admin Panel Features:**
- View index statistics (total chunks, last indexed time)
- Manual reindex button for underwriting policies
- Automatic reindexing when policies are created/updated/deleted

See [spec.md](specs/006-azure-postgresql-rag-integration/spec.md) for detailed architecture documentation.

### Adding a New Persona

1. Define field schema in `app/personas.py`:

```python
MY_PERSONA_FIELD_SCHEMA = {
    "name": "MyPersonaFields",
    "fields": {
        "FieldName": {
            "type": "string",
            "description": "Description for extraction",
            "method": "extract",
            "estimateSourceAndConfidence": True
        }
    }
}
```

2. Add prompts for analysis sections
3. Register in `PERSONA_CONFIGS` dictionary
4. Create frontend components as needed

### Seeding Customer 360 Data

The seed script creates 3 customer profiles with 9 rich applications across all personas. It supports both local filesystem and Azure Blob Storage.

```bash
# Local development (default)
python scripts/seed_customer360.py

# Azure Blob Storage (set env vars or use .env)
STORAGE_BACKEND=azure_blob \
AZURE_STORAGE_ACCOUNT_NAME=workbanchdata \
AZURE_STORAGE_ACCOUNT_KEY=<key> \
AZURE_STORAGE_CONTAINER_NAME=workbenchiq-data \
python scripts/seed_customer360.py
```

**Seed Customer Profiles:**

| Customer | Risk Tier | Products | Narrative |
|----------|-----------|----------|-----------|
| **Sarah Chen** | 🟢 Low | Life insurance (approved), mortgage (approved), auto claim (settled) | Loyal multi-product customer since 2019, consistent low-risk |
| **Marcus Williams** | 🟡 Medium | Life insurance (referred), health claim (approved), mortgage (conditional) | Cardiac health concerns correlate across products |
| **Priya Patel** | 🔴 High | Auto claim (investigating), life insurance (pending), mortgage (declined) | New customer, fraud flags + financial overextension |

Each application includes full workbench-quality data: `llm_outputs` with complete section/subsection structure, `extracted_fields` with confidence scores, and `risk_analysis` results. The seed data is modular — see `scripts/seed_data/` for per-persona data modules.

---

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
# Python
black app/ api_server.py
ruff check app/ api_server.py --fix

# Frontend
cd frontend
npm run lint
```

### Building for Production

```bash
# Frontend build
cd frontend
npm run build

# Run production server
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Settings incomplete" | Missing environment variables | Check `.env` file, restart API server |
| 401/403 errors | Invalid API keys | Verify Azure credentials |
| 404 errors | Wrong endpoint URLs | Remove trailing slashes from endpoints |
| 429 errors | Rate limiting | Wait and retry, or increase quota |
| CORS errors | Frontend can't reach API | Ensure API runs on port 8000 |

### Logs

- API logs: Check terminal running `uvicorn`
- Frontend logs: Browser developer console
- Azure logs: Azure Portal > Monitor > Logs

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Built with [Azure AI Content Understanding](https://azure.microsoft.com/en-us/products/ai-services/ai-document-intelligence)
- Powered by [Azure OpenAI Service](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- UI built with [Next.js](https://nextjs.org/) and [Tailwind CSS](https://tailwindcss.com/)
- API powered by [FastAPI](https://fastapi.tiangolo.com/)
