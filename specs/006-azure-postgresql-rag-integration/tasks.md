# Tasks: Azure PostgreSQL RAG Integration

**Input**: Design documents from `/specs/006-azure-postgresql-rag-integration/`  
**Prerequisites**: spec.md ✅, research.md ✅, data-model.md ✅

---

## Format: `[ID] [Priority] [Phase] Description`

- **[P]**: Can run in parallel with other [P] tasks (different files, no dependencies)
- **[Phase]**: Which phase this task belongs to
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `app/` at repository root
- **Database**: `app/database/` (new package)
- **RAG Service**: `app/rag/` (new package)
- **Migrations**: `migrations/` at repository root
- **Tests**: `tests/` at repository root

---

## Phase 1: Infrastructure Setup

**Purpose**: Add dependencies, create package structure, configure database connection

### Dependencies & Configuration

- [ ] T001 Add database dependencies to requirements.txt: `asyncpg>=0.29.0`, `pgvector>=0.2.4`
- [ ] T002 [P] Add database environment variables to app/config.py: `DATABASE_BACKEND`, `POSTGRESQL_*`, `RAG_*`
- [ ] T003 [P] Create database package directory at app/database/
- [ ] T004 [P] Create app/database/__init__.py with public exports

### Database Connection Layer

- [ ] T005 Create app/database/settings.py with DatabaseSettings dataclass (from_env pattern)
- [ ] T006 Create app/database/pool.py with async connection pool using asyncpg
- [ ] T007 Add vector type codec registration in pool.py for pgvector compatibility
- [ ] T008 Create app/database/client.py with high-level database client class
- [ ] T009 Add database initialization to api_server.py startup event
- [ ] T010 Add database health check endpoint at GET /api/health/database

**Checkpoint**: Database connectivity verified, pool initialized at startup

---

## Phase 2: Policy Chunking & Embedding (P0 - Core RAG)

**Purpose**: Implement the chunking pipeline and embedding generation for policies

### Schema & Migrations

- [ ] T011 Create migrations/ directory structure
- [ ] T012 Create migrations/001_create_extensions.sql (pgvector, uuid-ossp, pg_trgm)
- [ ] T013 Create migrations/002_create_policy_chunks.sql per data-model.md (use unique INDEX not CONSTRAINT for COALESCE expressions)
- [ ] T014 Create app/database/migrate.py with migration runner
- [ ] T015 Add migration CLI command or startup auto-migration option

### Chunking Service

- [ ] T016 Create app/rag/ package directory
- [ ] T017 [P] Create app/rag/__init__.py with public exports
- [ ] T018 Create app/rag/chunker.py with PolicyChunker class
- [ ] T019 Implement chunk_policy_header() in chunker.py
- [ ] T020 Implement chunk_criteria() in chunker.py - one chunk per criteria
- [ ] T021 Implement chunk_modifying_factors() in chunker.py
- [ ] T022 Implement chunk_references() in chunker.py
- [ ] T023 Implement chunk_all_policies() orchestrator function
- [ ] T024 Add content hashing (SHA-256) for change detection

### Embedding Service

- [ ] T025 Create app/rag/embeddings.py with EmbeddingService class
- [ ] T026 Implement get_embedding() for single text using Azure OpenAI
- [ ] T027 Implement get_embeddings_batch() for batch processing (max 100)
- [ ] T028 Add retry logic with exponential backoff for embedding API calls
- [ ] T029 Add embedding dimension configuration support (1536 default)

### Chunk Storage

- [ ] T030 Create app/rag/repository.py with PolicyChunkRepository class
- [ ] T031 Implement insert_chunks() for batch upsert (pass embedding list directly to asyncpg codec)
- [ ] T032 Implement get_chunk_by_id() for single chunk retrieval
- [ ] T033 Implement delete_chunks_by_policy() for policy updates
- [ ] T034 Implement get_all_chunk_hashes() for change detection

### Indexing Pipeline

- [ ] T035 Create app/rag/indexer.py with PolicyIndexer orchestrator
- [ ] T036 Implement index_policies() - full pipeline: load → chunk → embed → store
- [ ] T037 Implement reindex_policy() - single policy re-indexing
- [ ] T038 Add CLI script scripts/index_policies.py for manual indexing
- [ ] T039 Add progress logging and metrics to indexing pipeline

### Reindexing API & Automation

- [ ] T039a Add `POST /api/admin/policies/reindex` endpoint for full reindex
- [ ] T039b Add `POST /api/admin/policies/{id}/reindex` endpoint for single policy
- [ ] T039c Hook policy save/update in api_server.py to trigger background reindex
- [ ] T039d Add "Reindex All Policies" button to frontend admin UI

**Checkpoint**: Policies chunked, embedded, and stored in PostgreSQL. Run indexer to verify.

---

## Phase 3: Semantic Search & RAG Query (P0 - Core RAG)

**Purpose**: Implement vector similarity search and RAG context retrieval

### Search Implementation

- [x] T040 Create app/rag/search.py with PolicySearchService class
- [x] T041 Implement semantic_search() - basic vector similarity query
- [x] T042 Implement filtered_search() - search with category/subcategory filters
- [x] T043 Add similarity threshold configuration (default 0.5 - NOTE: 0.7 was too high for text-embedding-3-small)
- [x] T044 Add top-k configuration (default 5)
- [x] T045 Implement search result ranking and deduplication

### Category Inference

- [x] T046 Create app/rag/inference.py with category inference logic
- [x] T047 Implement keyword-based category inference (CATEGORY_KEYWORDS map)
- [x] T048 [P] Implement optional LLM-based category inference
- [x] T049 Add category inference to search pipeline

### Context Assembly

- [x] T050 Create app/rag/context.py with RAGContextBuilder class
- [x] T051 Implement assemble_context() - format chunks for LLM prompt
- [x] T052 Add token budget management (max_tokens parameter)
- [x] T053 Preserve policy citations in context output

**Checkpoint**: ✅ PASSED - Query "blood pressure 145/92" returns relevant CVD-BP-001 chunks

---

## Phase 4: Chat Integration (P0 - Primary Deliverable)

**Purpose**: Integrate RAG into Ask IQ chat endpoint

### RAG Service Integration

- [x] T054 Create app/rag/service.py with unified RAGService class
- [x] T055 Implement query() - full RAG pipeline: infer → embed → search → assemble
- [x] T056 Add fallback to full policy injection if RAG fails
- [x] T057 Add RAG metrics logging (latency, chunks retrieved, tokens saved)

### Chat Endpoint Updates

- [x] T058 Modify api_server.py chat endpoint to use RAGService
- [x] T059 Replace format_all_policies_for_prompt() with RAG context
- [x] T060 Add RAG chunk citations to chat response metadata
- [x] T061 Add feature flag check (RAG_ENABLED env var)
- [x] T062 Update system prompt to reference retrieved context only

### Testing & Validation

- [x] T063 Create tests/test_rag_chunker.py - unit tests for chunking (scripts/test_phase4_chat.py)
- [x] T064 Create tests/test_rag_search.py - unit tests for search (scripts/test_phase3_search.py)
- [x] T065 Create tests/test_rag_integration.py - end-to-end RAG tests (scripts/test_retrieval_improvements.py)
- [ ] T066 Add test fixtures with sample policy chunks

**Checkpoint**: ✅ PASSED - Ask IQ chat uses RAG. Token usage reduced, latency improved.

---

## Phase 5: Metadata Filtering (P1)

**Purpose**: Enhance retrieval quality with metadata-based filtering

### Filter Implementation

- [x] T067 Add category index optimization to migrations (idx_policy_chunks_category exists)
- [x] T068 Enhance semantic_search() with pre-filter on category
- [x] T069 Enhance semantic_search() with pre-filter on risk_level
- [x] T070 Implement combined filter queries (category + risk_level)

### Query Analysis

- [x] T071 Improve category inference with expanded keyword lists
- [x] T072 Add risk level inference from question context
- [x] T073 Add metadata filter logging for debugging

**Checkpoint**: ✅ PASSED - Questions about "cholesterol" auto-filter to metabolic category

---

## Phase 6: Application Data Migration (P2)

**Purpose**: Migrate application metadata to PostgreSQL (optional)

### Schema

- [ ] T074 Create migrations/003_create_applications.sql per data-model.md
- [ ] T075 Create migrations/004_create_application_files.sql
- [ ] T076 Create migrations/005_create_conversations.sql

### Repository Layer

- [ ] T077 Create app/database/repositories/application_repo.py
- [ ] T078 Implement CRUD operations for applications table
- [ ] T079 Create app/database/repositories/file_repo.py
- [ ] T080 Implement CRUD for application_files table

### Migration Scripts

- [ ] T081 Create scripts/migrate_applications.py - JSON to PostgreSQL
- [ ] T082 Add dual-write mode to storage.py (JSON + PostgreSQL)
- [ ] T083 Add PostgreSQL read fallback in storage.py

**Checkpoint**: Applications can be read from PostgreSQL

---

## Phase 7: Hybrid Search (P3)

**Purpose**: Combine keyword and semantic search for edge cases

### Implementation

- [x] T084 Add full-text search index to policy_chunks (idx_policy_chunks_content_trgm exists)
- [x] T085 Create app/rag/hybrid_search.py with HybridSearchService (in search.py)
- [x] T086 Implement keyword_search() using pg_trgm
- [x] T087 Implement hybrid_search() combining keyword + semantic scores
- [x] T088 Add score weighting configuration (default 0.3 keyword, 0.7 semantic)

**Checkpoint**: ✅ PASSED - Searching "CVD-BP-001" returns that policy

---

## Phase 8: Observability & Optimization

**Purpose**: Add monitoring, caching, and performance tuning

### Monitoring

- [ ] T089 Add structured logging for RAG pipeline stages
- [ ] T090 Add latency metrics for embedding, search, assembly
- [ ] T091 Add token usage tracking per chat request
- [ ] T092 Create Prometheus metrics endpoint (optional)

### Optimization

- [ ] T093 Create embedding_cache table per data-model.md
- [ ] T094 Implement query embedding caching
- [ ] T095 Add cache hit/miss metrics
- [ ] T096 Tune HNSW index parameters based on load testing

**Checkpoint**: Full observability, <500ms RAG latency p95

---

## Validation Checklist

After Phase 4 completion (MVP):

- [ ] V001 Policies are chunked correctly (~190 chunks)
- [ ] V002 Embeddings stored with correct dimensions (1536)
- [ ] V003 Vector search returns relevant results
- [ ] V004 Chat endpoint uses RAG when enabled
- [ ] V005 Fallback to full policies works when RAG disabled
- [ ] V006 Token usage reduced by 50%+
- [ ] V007 Chat latency maintained or improved

---

## Learnings & Notes

### T012 pg_trgm Extension
The `pg_trgm` extension is needed for hybrid search's keyword matching (GIN indexes on text).

### T013 Unique Index vs Constraint
PostgreSQL does not allow COALESCE in UNIQUE CONSTRAINT definitions. Use a unique INDEX instead:
```sql
CREATE UNIQUE INDEX idx_policy_chunks_unique 
ON workbenchiq.policy_chunks (policy_id, chunk_type, COALESCE(criteria_id, ''));
```

### T031 Passing Embeddings to asyncpg
Pass raw Python list to asyncpg - the vector codec handles conversion. Do NOT use `json.dumps()` which causes nested encoding errors.

### T043 Similarity Threshold
The default 0.7 was too high for `text-embedding-3-small` model. Typical cosine similarities for relevant content are 0.5-0.6. Changed default to 0.5.
