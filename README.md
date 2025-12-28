<div align="center">

# WorkbenchIQ

### AI-Powered Workbench for Underwriters & Claims Processors

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)
[![Azure AI](https://img.shields.io/badge/Azure-AI%20Services-0078D4.svg)](https://azure.microsoft.com/en-us/products/ai-services/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**WorkbenchIQ** is a Microsoft accelerator that provides a modern workbench for **underwriters** and **claims processors**, combining **Azure AI Content Understanding** and **Azure AI Foundry** to streamline document-heavy insurance workflows.

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

### Mortgage Underwriting *(Coming Soon)*

- **Challenge**: Loan officers review income verification, property appraisals, and credit documentation
- **Solution**: Extract borrower information, income sources, debt-to-income ratios, and property valuations
- **Outcome**: Streamline loan approval with consistent document analysis

---

## Features

### Core Capabilities

- **Multi-Persona Workbench** - Switch between underwriting and claims processing workflows
- **Intelligent Document Extraction** - Azure AI Content Understanding with `prebuilt-documentSearch`
- **AI-Powered Analysis** - LLM prompts for comprehensive document summarization and risk assessment
- **Confidence Scoring** - Field-level confidence indicators for extracted data
- **Custom Prompt Engineering** - Editable prompt catalog tailored to underwriting and claims workflows
- **Progress Tracking** - Real-time status updates for long-running operations

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

### Technical Features

- **Modern Stack** - Next.js 14 + Tailwind CSS frontend, FastAPI backend
- **REST API** - Full API with interactive Swagger documentation
- **Azure AD Authentication** - Secure service-to-service authentication
- **Extensible Personas** - Easy to add new industry verticals
- **Retry Logic** - Resilient API calls with exponential backoff
- **PostgreSQL + pgvector** - Optional vector database for RAG-powered policy search
- **Hybrid Search** - Semantic (HNSW index) + keyword (GIN/pg_trgm) search capabilities

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
| **Underwriting** | Active | Life insurance underwriting - process applications and medical documents |
| **Claims** | Demo | Insurance claims processing - review medical claims and documentation |
| **Mortgage** | Coming Soon | Mortgage underwriting - loan applications and property documents |

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
run_frontend.bat

# Linux/Mac
./run_frontend.sh
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
│   ├── personas.py               # Multi-persona definitions & field schemas
│   ├── storage.py                # File and metadata handling
│   ├── prompts.py                # Prompt templates & catalog
│   ├── openai_client.py          # Azure OpenAI integration
│   ├── content_understanding_client.py  # Azure CU integration
│   ├── processing.py             # Orchestration logic
│   ├── underwriting_policies.py  # Policy loader and injector
│   ├── utils.py                  # Helper utilities
│   └── rag/                      # RAG module (optional PostgreSQL)
│       ├── __init__.py           # RAG service exports
│       ├── chunker.py            # Policy text chunking
│       ├── embedder.py           # Azure OpenAI embedding client
│       ├── repository.py         # PostgreSQL CRUD operations
│       ├── search.py             # Semantic & hybrid search
│       ├── service.py            # Unified RAG service interface
│       └── indexer.py            # Policy indexing pipeline
├── scripts/                      # Utility scripts
│   ├── setup_postgresql_rag.py   # Azure PostgreSQL provisioning
│   └── index_policies.py         # CLI for policy indexing
├── prompts/                      # Git-tracked prompts & policies
│   ├── prompts.json              # LLM prompts for document analysis
│   ├── risk-analysis-prompts.json # Risk analysis prompt templates
│   ├── life-health-underwriting-policies.json # Underwriting policy manual
│   └── policies.json             # Claims/health plan policies
├── frontend/                     # Next.js 14 frontend
│   ├── src/
│   │   ├── app/                  # Next.js pages (App Router)
│   │   ├── components/           # React components
│   │   │   ├── claims/           # Claims-specific components
│   │   │   ├── chat/             # Chat components
│   │   │   │   ├── ChatCards.tsx     # Rich response cards (risk factors, recommendations)
│   │   │   │   └── ChatHistoryPanel.tsx
│   │   │   ├── ChatDrawer.tsx    # Slide-out chat interface
│   │   │   ├── PatientHeader.tsx
│   │   │   ├── LabResultsPanel.tsx
│   │   │   └── ...
│   │   └── lib/                  # Utilities, API client, PersonaContext
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
| `GET` | `/api/personas` | List all available personas |
| `GET` | `/api/personas/{id}` | Get specific persona configuration |
| `GET` | `/api/applications` | List all applications |
| `GET` | `/api/applications/{id}` | Get application details |
| `POST` | `/api/applications` | Create new application with file upload |
| `POST` | `/api/applications/{id}/extract` | Run Content Understanding extraction |
| `POST` | `/api/applications/{id}/analyze` | Run GPT analysis |
| `GET` | `/api/prompts` | Get prompt catalog |
| `PUT` | `/api/prompts/{section}/{subsection}` | Update a prompt |
| `POST` | `/api/prompts/{section}/{subsection}` | Create a new prompt |
| `DELETE` | `/api/prompts/{section}/{subsection}` | Delete/reset a prompt |
| `GET` | `/api/policies` | Get all underwriting policies |
| `GET` | `/api/policies/{id}` | Get specific policy by ID |
| `POST` | `/api/policies` | Create a new underwriting policy |
| `PUT` | `/api/policies/{id}` | Update an underwriting policy |
| `DELETE` | `/api/policies/{id}` | Delete an underwriting policy |
| `GET` | `/api/analyzer/status` | Get custom analyzer status |
| `POST` | `/api/analyzer/create` | Create custom analyzer |
| `GET` | `/api/analyzer/schema?persona={id}` | Get field extraction schema |
| `POST` | `/api/applications/{id}/risk-analysis` | Run full policy evaluation |
| `POST` | `/api/applications/{id}/chat` | Send chat message with context |
| `GET` | `/api/applications/{id}/conversations` | List chat sessions for an application |
| `GET` | `/api/applications/{id}/conversations/{chat_id}` | Get specific chat session |
| `DELETE` | `/api/applications/{id}/conversations/{chat_id}` | Delete a chat session |
| `GET` | `/api/conversations` | List all conversations across applications |
| `POST` | `/api/rag/index` | Index all underwriting policies for RAG |
| `GET` | `/api/rag/stats` | Get RAG index statistics |
| `POST` | `/api/rag/query` | Query policies using semantic search |

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_CONTENT_UNDERSTANDING_ENDPOINT` | Yes | - | Azure AI Content Understanding endpoint |
| `AZURE_CONTENT_UNDERSTANDING_API_KEY` | Conditional | - | API key (if not using Azure AD) |
| `AZURE_CONTENT_UNDERSTANDING_USE_AZURE_AD` | No | `true` | Use Azure AD authentication |
| `AZURE_OPENAI_ENDPOINT` | Yes | - | Azure OpenAI endpoint |
| `AZURE_OPENAI_API_KEY` | Yes | - | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Yes | - | GPT-4.1 deployment name |
| `AZURE_OPENAI_API_VERSION` | No | `2024-10-21` | Azure OpenAI API version |
| `UW_APP_STORAGE_ROOT` | No | `data` | Local storage path for application data |
| `UW_APP_PROMPTS_ROOT` | No | `prompts` | Path to prompts and policies directory |
| `STORAGE_BACKEND` | No | `local` | Storage backend (`local` or `azure_blob`) |
| `AZURE_STORAGE_ACCOUNT_NAME` | Conditional | - | Azure storage account name (if using azure_blob) |
| `AZURE_STORAGE_ACCOUNT_KEY` | Conditional | - | Azure storage account key (if using azure_blob) |
| `AZURE_STORAGE_CONNECTION_STRING` | Conditional | - | Azure storage connection string (alternative to account name/key) |
| `AZURE_STORAGE_CONTAINER_NAME` | No | `workbenchiq-data` | Azure blob container name |
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

**Local Storage (Default)**

No additional configuration needed. Files are stored in the local `data/` directory.

```env
STORAGE_BACKEND=local
UW_APP_STORAGE_ROOT=data
```

**Azure Blob Storage**

For production deployments, you can use Azure Blob Storage:

```env
STORAGE_BACKEND=azure_blob

# Option 1: Account name and key
AZURE_STORAGE_ACCOUNT_NAME=mystorageaccount
AZURE_STORAGE_ACCOUNT_KEY=your-storage-account-key

# Option 2: Connection string (alternative)
# AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...

# Container name (optional, defaults to workbenchiq-data)
AZURE_STORAGE_CONTAINER_NAME=workbenchiq-data
```

The container will be automatically created if it doesn't exist. See [quickstart.md](specs/003-azure-blob-storage-integration/quickstart.md) for detailed setup instructions.

### PostgreSQL RAG Configuration *(Optional)*

For enhanced policy search with semantic retrieval, you can enable the RAG (Retrieval-Augmented Generation) feature using Azure PostgreSQL Flexible Server with pgvector:

**Prerequisites:**
- Azure PostgreSQL Flexible Server (v15+)
- Extensions enabled: `vector` (pgvector), `pg_trgm`
- Azure OpenAI embedding model deployed (e.g., `text-embedding-3-small`)

**Quick Setup:**

```bash
# Run the setup script to provision Azure PostgreSQL and create schema
uv run python scripts/setup_postgresql_rag.py

# Index existing policies
uv run python scripts/index_policies.py
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
