# Feature Specification: Azure PostgreSQL RAG Integration

**Feature Branch**: `006-azure-postgresql-rag-integration`  
**Created**: 2025-12-26  
**Status**: Draft  
**Input**: User description: "Implement RAG capability for Ask IQ chatbot using Azure PostgreSQL with pgvector to chunk underwriting policies, create embeddings, and retrieve relevant context. Unify structured data (applications), semi-structured data (summaries), and unstructured data (policy chunks) in a single database."

---

## Overview

This specification defines a comprehensive data layer refactoring to introduce Azure PostgreSQL Flexible Server as the primary database, supporting:

1. **Structured Data** - Application records, metadata, and relationships
2. **Semi-Structured Data** - Application summaries, LLM outputs, and extracted fields (JSON/JSONB)
3. **Unstructured Data** - Policy document chunks with vector embeddings for semantic search (pgvector)

The primary use case is enabling RAG (Retrieval-Augmented Generation) for the "Ask IQ" chatbot to retrieve only relevant policy chunks instead of passing the entire 700+ line policy document to the LLM.

### Goals

1. **Reduce Latency** - Retrieve only relevant policy chunks (target: <500ms retrieval)
2. **Save Inference Cost** - Reduce token usage by 60-80% by not passing full policy document
3. **Improve QnA Quality** - Semantic search retrieves higher-quality, more relevant context
4. **Unified Data Layer** - Single database for all data types simplifies architecture and enables joins

---

## User Stories

### US-1: Policy Document Chunking & Embedding (Priority: P0)
> As a system administrator, I want underwriting policies to be automatically chunked and embedded when loaded, so that the chatbot can perform semantic search over policy content.

**Why this priority**: This is the foundational capability - without chunked policies and embeddings, no RAG functionality is possible.

**Acceptance Scenarios**:
1. **Given** the life-health-underwriting-policies.json file exists, **When** the chunking job runs, **Then** each policy is chunked into semantic units (criteria, modifying factors, etc.) with metadata preserved.
2. **Given** policy chunks exist, **When** embeddings are generated, **Then** each chunk has a 1536-dimension vector (text-embedding-3-small) or 3072-dimension (text-embedding-3-large).
3. **Given** embeddings are stored, **When** querying the database, **Then** chunks can be retrieved via cosine similarity search using pgvector's `<=>` operator.

---

### US-2: Semantic Policy Retrieval for Ask IQ (Priority: P0)
> As an underwriter using Ask IQ, I want my questions to retrieve only the most relevant policy sections, so that responses are faster and more focused.

**Why this priority**: This is the primary user-facing benefit - directly improves chatbot experience.

**Acceptance Scenarios**:
1. **Given** a user asks "What is the risk rating for a patient with blood pressure 145/92?", **When** the query is processed, **Then** the system retrieves the CVD-BP-001 policy chunks about Stage 2 hypertension.
2. **Given** a semantic search is performed, **When** the top-k results are returned (default k=5), **Then** the total token count is under 2000 tokens.
3. **Given** retrieved chunks, **When** injected into the LLM prompt, **Then** policy IDs and citations are preserved for reference.

---

### US-3: Metadata Filtering for Targeted Retrieval (Priority: P1)
> As an underwriter, I want the chatbot to filter policies by category (cardiovascular, metabolic, etc.) when my question implies a specific domain, so that irrelevant policies are excluded.

**Why this priority**: Enhances retrieval quality but basic semantic search works without it.

**Acceptance Scenarios**:
1. **Given** a question about "cholesterol levels", **When** the query is analyzed, **Then** the retrieval filters to `category='metabolic'` before performing vector search.
2. **Given** metadata filters are applied, **When** results are returned, **Then** only chunks matching the filter are included.
3. **Given** no category can be inferred, **When** the query is processed, **Then** the system performs unfiltered semantic search.

---

### US-4: Application Data Migration to PostgreSQL (Priority: P2)
> As a developer, I want application metadata and files stored in PostgreSQL, so that we have transactional consistency and can join applications with policies.

**Why this priority**: Enables future features like "which policies affected this application" but not required for RAG MVP.

**Acceptance Scenarios**:
1. **Given** an application is created, **When** files are uploaded, **Then** metadata is stored in PostgreSQL with file content in blob storage (hybrid approach).
2. **Given** application data in PostgreSQL, **When** listing applications, **Then** queries return within 100ms for up to 10,000 applications.
3. **Given** the current local/blob storage data, **When** migration runs, **Then** all existing applications are migrated to PostgreSQL.

---

### US-5: Conversation History in PostgreSQL (Priority: P2)
> As an underwriter, I want chat history stored in PostgreSQL, so that conversations can be queried and analyzed for insights.

**Why this priority**: Nice-to-have for analytics but current JSON storage works.

**Acceptance Scenarios**:
1. **Given** a chat message is sent, **When** stored in PostgreSQL, **Then** the message, embedding, and metadata are persisted.
2. **Given** conversation history, **When** searching past conversations, **Then** semantic search finds relevant past Q&A pairs.

---

### US-6: Hybrid Search (Keyword + Semantic) (Priority: P3)
> As an underwriter, I want the system to combine keyword matching with semantic search, so that exact policy IDs or terms are always found even if embeddings don't prioritize them.

**Why this priority**: Enhancement for edge cases where exact matches matter.

**Acceptance Scenarios**:
1. **Given** a query mentions "CVD-BP-001", **When** searching, **Then** the exact policy chunk is always included regardless of semantic similarity.
2. **Given** hybrid search is enabled, **When** results are ranked, **Then** keyword matches are boosted in the final ranking.

---

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Ask IQ Chat Interface                                                │    │
│  │ - User question → API                                                │    │
│  │ - Receives focused, relevant policy context in response              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ REST API
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI)                               │
│                                                                              │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐    │
│  │ Chat Endpoint      │  │ RAG Service        │  │ Embedding Service  │    │
│  │ /api/.../chat      │─▶│ - Query analysis   │─▶│ - Azure OpenAI     │    │
│  │                    │  │ - Chunk retrieval  │  │ - text-embedding-3 │    │
│  └────────────────────┘  │ - Context assembly │  └────────────────────┘    │
│                          └────────────────────┘                             │
│                                    │                                         │
│  ┌─────────────────────────────────┴───────────────────────────────────┐    │
│  │                     Database Layer (New)                             │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐ │    │
│  │  │ PostgreSQL     │  │ Repository     │  │ Migration Service      │ │    │
│  │  │ Client Pool    │  │ Pattern        │  │ (JSON → PostgreSQL)    │ │    │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Azure PostgreSQL Flexible Server                         │
│                          (with pgvector extension)                           │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Schema: workbenchiq                                                   │   │
│  │                                                                       │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │   │
│  │  │ applications    │  │ policy_chunks   │  │ conversations       │   │   │
│  │  │ - id (PK)       │  │ - id (PK)       │  │ - id (PK)           │   │   │
│  │  │ - metadata JSON │  │ - content TEXT  │  │ - messages JSONB    │   │   │
│  │  │ - status        │  │ - embedding     │  │ - app_id (FK)       │   │   │
│  │  │ - created_at    │  │   VECTOR(1536)  │  │ - created_at        │   │   │
│  │  │ - persona       │  │ - policy_id     │  └─────────────────────┘   │   │
│  │  └─────────────────┘  │ - category      │                            │   │
│  │           │           │ - metadata JSONB│  ┌─────────────────────┐   │   │
│  │           │           └─────────────────┘  │ app_files           │   │   │
│  │           │                    │           │ - id (PK)           │   │   │
│  │           └────────────────────┼───────────│ - app_id (FK)       │   │   │
│  │                                │           │ - blob_path         │   │   │
│  │                                │           │ - filename          │   │   │
│  │  ┌─────────────────────────────┴─────┐     └─────────────────────┘   │   │
│  │  │ HNSW Index on embedding column    │                               │   │
│  │  │ for fast approximate NN search    │                               │   │
│  │  └───────────────────────────────────┘                               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ (Files stored in blob, metadata in PG)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Azure Blob Storage (existing)                            │
│  - Application files (PDFs, images)                                          │
│  - Content Understanding raw results                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### RAG Query Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   User       │     │   Chat       │     │   RAG        │     │  Embedding   │
│   Question   │────▶│   Endpoint   │────▶│   Service    │────▶│  Service     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                │                      │
                                                │                      ▼
                                                │              ┌──────────────┐
                                                │              │ Azure OpenAI │
                                                │              │ Embedding    │
                                                │              └──────────────┘
                                                │                      │
                                                ▼                      ▼
                                         ┌──────────────┐     ┌──────────────┐
                                         │ PostgreSQL   │◀────│ Query Vector │
                                         │ Vector Search│     │ (1536-dim)   │
                                         └──────────────┘     └──────────────┘
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │ Top-K Chunks │
                                         │ + Metadata   │
                                         └──────────────┘
                                                │
                                                ▼
                                         ┌──────────────┐     ┌──────────────┐
                                         │ LLM Prompt   │────▶│ Azure OpenAI │
                                         │ Assembly     │     │ GPT-4        │
                                         └──────────────┘     └──────────────┘
                                                                     │
                                                                     ▼
                                                              ┌──────────────┐
                                                              │   Response   │
                                                              └──────────────┘
```

---

## Data Model

### Policy Chunking Strategy

The life-health-underwriting-policies.json will be chunked as follows:

| Chunk Type | Granularity | Metadata | Estimated Count |
|------------|-------------|----------|-----------------|
| **Policy Header** | One per policy | policy_id, category, subcategory, name | ~15 |
| **Criteria** | One per criteria item | policy_id, criteria_id, risk_level | ~100 |
| **Modifying Factor** | One per factor | policy_id, factor_name | ~60 |
| **References** | Grouped per policy | policy_id | ~15 |

**Total Estimated Chunks**: ~190

#### Example Chunk (Criteria)

```json
{
  "id": "chunk-cvd-bp-001-c",
  "policy_id": "CVD-BP-001",
  "chunk_type": "criteria",
  "category": "cardiovascular",
  "subcategory": "hypertension",
  "policy_name": "Blood Pressure Risk Assessment",
  "criteria_id": "CVD-BP-001-C",
  "content": "Condition: Systolic 130-139 OR Diastolic 80-89. Risk Level: Low-Moderate. Action: Standard rates if controlled on single medication; otherwise +25% loading. Rationale: Stage 1 hypertension. Acceptable if well-controlled with good compliance.",
  "risk_level": "Low-Moderate",
  "embedding": [0.123, -0.456, ...],  // 1536 dimensions
  "token_count": 52,
  "created_at": "2025-12-26T10:00:00Z"
}
```

### Database Tables

#### `policy_chunks` (Primary RAG Table)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique chunk identifier |
| `policy_id` | VARCHAR(50) | NOT NULL, INDEX | Source policy ID (e.g., CVD-BP-001) |
| `chunk_type` | VARCHAR(20) | NOT NULL | header, criteria, modifying_factor, reference |
| `category` | VARCHAR(50) | INDEX | Policy category for filtering |
| `subcategory` | VARCHAR(50) | INDEX | Policy subcategory |
| `policy_name` | VARCHAR(200) | | Human-readable policy name |
| `criteria_id` | VARCHAR(50) | | If chunk_type=criteria, the criteria ID |
| `risk_level` | VARCHAR(20) | INDEX | If applicable: Low, Moderate, High, etc. |
| `content` | TEXT | NOT NULL | The chunk text content |
| `embedding` | VECTOR(1536) | NOT NULL | OpenAI embedding vector |
| `metadata` | JSONB | | Additional flexible metadata |
| `token_count` | INTEGER | | Estimated tokens for budget |
| `source_version` | VARCHAR(20) | | Policy document version |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | | |

**Indexes**:
- `HNSW` index on `embedding` for approximate nearest neighbor search
- `B-tree` index on `category`, `subcategory`, `risk_level` for filtering
- `GIN` index on `metadata` for JSONB queries

#### `applications` (Migrated from JSON)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | Application UUID |
| `external_reference` | VARCHAR(100) | INDEX | External ID reference |
| `persona` | VARCHAR(50) | INDEX | Persona type |
| `status` | VARCHAR(20) | NOT NULL, INDEX | uploaded, processing, complete, error |
| `document_markdown` | TEXT | | Extracted document text |
| `llm_outputs` | JSONB | | Analysis outputs |
| `extracted_fields` | JSONB | | Field extraction results |
| `confidence_summary` | JSONB | | Confidence scores |
| `risk_analysis` | JSONB | | Policy-based risk assessment |
| `analyzer_id_used` | VARCHAR(100) | | Content Understanding analyzer |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | | |

#### `application_files` (File Registry)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | |
| `application_id` | VARCHAR(36) | FK → applications | |
| `filename` | VARCHAR(255) | NOT NULL | Original filename |
| `blob_path` | VARCHAR(500) | NOT NULL | Azure Blob path |
| `content_type` | VARCHAR(100) | | MIME type |
| `size_bytes` | BIGINT | | File size |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

#### `conversations` (Chat History)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Conversation UUID |
| `application_id` | VARCHAR(36) | FK → applications, INDEX | |
| `title` | VARCHAR(200) | | Auto-generated title |
| `messages` | JSONB | NOT NULL | Array of message objects |
| `message_count` | INTEGER | DEFAULT 0 | |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | | |

---

## Requirements

### Functional Requirements

#### Core RAG (P0)
- **FR-001**: System MUST chunk underwriting policies into semantic units preserving policy ID and metadata.
- **FR-002**: System MUST generate embeddings for each chunk using Azure OpenAI text-embedding-3-small (1536 dimensions).
- **FR-003**: System MUST store embeddings in PostgreSQL using pgvector extension.
- **FR-004**: System MUST perform vector similarity search using cosine distance (`<=>` operator).
- **FR-005**: System MUST return top-k relevant chunks (configurable, default k=5).
- **FR-006**: System MUST assemble retrieved chunks into LLM prompt with policy citations preserved.
- **FR-007**: System MUST support re-chunking when policies are updated (version tracking).

#### Metadata Filtering (P1)
- **FR-008**: System MUST support filtering by category before vector search.
- **FR-009**: System MUST support filtering by risk_level when applicable.
- **FR-010**: System SHOULD infer filters from user query context.

#### Data Migration (P2)
- **FR-011**: System MUST provide migration script from JSON files to PostgreSQL.
- **FR-012**: System MUST maintain backward compatibility during migration (dual-read).
- **FR-013**: System MUST preserve all existing application data and relationships.

#### Configuration (P1)
- **FR-014**: System MUST support environment variable configuration for PostgreSQL connection.
- **FR-015**: System MUST default to local/blob storage when PostgreSQL is not configured.
- **FR-016**: System MUST validate database connection at startup with clear error messages.
- **FR-017**: System MUST support connection pooling for PostgreSQL connections.

### Non-Functional Requirements

- **NFR-001**: Vector search latency MUST be under 100ms for 1000 chunks.
- **NFR-002**: Full RAG pipeline (embed query + search + retrieve) MUST complete in under 500ms.
- **NFR-003**: Embedding generation MUST be batched (max 100 per request) with rate limiting.
- **NFR-004**: Database connections MUST use pooling with max 20 connections.
- **NFR-005**: System MUST handle PostgreSQL connection failures gracefully with fallback.

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_BACKEND` | No | `none` | `none`, `postgresql` |
| `POSTGRESQL_HOST` | If postgresql | - | Azure PostgreSQL host |
| `POSTGRESQL_PORT` | No | `5432` | PostgreSQL port |
| `POSTGRESQL_DATABASE` | If postgresql | - | Database name |
| `POSTGRESQL_USER` | If postgresql | - | Database user |
| `POSTGRESQL_PASSWORD` | If postgresql | - | Database password |
| `POSTGRESQL_SSL_MODE` | No | `require` | SSL mode |
| `RAG_ENABLED` | No | `false` | Enable RAG for Ask IQ |
| `RAG_TOP_K` | No | `5` | Number of chunks to retrieve |
| `RAG_SIMILARITY_THRESHOLD` | No | `0.7` | Minimum similarity score |
| `EMBEDDING_MODEL` | No | `text-embedding-3-small` | Azure OpenAI embedding model |
| `EMBEDDING_DIMENSIONS` | No | `1536` | Embedding vector dimensions |

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Chat latency reduced by 40% compared to full policy injection (baseline measurement required).
- **SC-002**: Token usage per chat request reduced by 60% minimum.
- **SC-003**: Retrieved policy chunks are rated "relevant" by human evaluators 90%+ of the time.
- **SC-004**: Vector search returns results in under 100ms for 95th percentile.
- **SC-005**: System handles 50 concurrent chat requests without degradation.

---

## Assumptions

1. Azure PostgreSQL Flexible Server is provisioned with pgvector extension enabled.
2. Azure OpenAI service is already configured (existing dependency).
3. Embedding costs are acceptable (~$0.02 per 1M tokens for text-embedding-3-small).
4. Policy document size remains under 10,000 chunks (current: ~190).
5. Connection pooling library (asyncpg or psycopg3) is acceptable addition.

---

## Open Questions

1. **Q**: Should we support multiple embedding models (e.g., upgrade path to text-embedding-3-large)?
   - **Proposed**: Yes, make embedding model and dimensions configurable.

2. **Q**: Should application document markdown also be chunked for RAG?
   - **Proposed**: Phase 2 enhancement - focus on policies first.

3. **Q**: What happens when PostgreSQL is unavailable? Fallback to full policy injection?
   - **Proposed**: Yes, graceful degradation to current behavior.

4. **Q**: Should we cache embeddings for frequent queries?
   - **Proposed**: Defer to Phase 2 - measure first.

---

## Future Enhancements (Out of Scope)

1. **Hybrid Search**: Combine BM25 keyword search with vector search.
2. **Query Rewriting**: Use LLM to expand/rewrite queries for better retrieval.
3. **Chunk Summarization**: Generate summaries for retrieved chunks.
4. **Cross-Application RAG**: Search similar past applications for decision support.
5. **Policy Change Detection**: Automated re-embedding when policies change.
6. **Feedback Loop**: Learn from underwriter corrections to improve retrieval.
