# Data Model: Azure PostgreSQL RAG Integration

**Feature**: 006-azure-postgresql-rag-integration  
**Date**: 2025-12-26  
**Source**: Feature spec entities + RAG architecture requirements

---

## Overview

This document defines the complete data model for the unified Azure PostgreSQL database supporting structured, semi-structured, and unstructured (vector) data for WorkbenchIQ.

---

## Database Configuration

### PostgreSQL Extensions Required

```sql
-- pgvector for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- pg_trgm for text search optimization (optional, for hybrid search)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- uuid-ossp for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Schema

```sql
CREATE SCHEMA IF NOT EXISTS workbenchiq;
SET search_path TO workbenchiq, public;
```

---

## Entity Definitions

### 1. PolicyChunk (Primary RAG Entity)

Stores chunked underwriting policy content with vector embeddings for semantic search.

```sql
CREATE TABLE policy_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Policy identification
    policy_id VARCHAR(50) NOT NULL,
    policy_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    policy_name VARCHAR(200) NOT NULL,
    
    -- Chunk classification
    chunk_type VARCHAR(30) NOT NULL CHECK (chunk_type IN (
        'policy_header',
        'criteria',
        'modifying_factor',
        'reference',
        'description'
    )),
    chunk_sequence INTEGER NOT NULL DEFAULT 0,
    
    -- Hierarchical metadata for filtering
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    
    -- Criteria-specific fields (nullable for non-criteria chunks)
    criteria_id VARCHAR(50),
    risk_level VARCHAR(30),
    action_recommendation TEXT,
    
    -- Content
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL, -- SHA-256 for change detection
    token_count INTEGER NOT NULL DEFAULT 0,
    
    -- Vector embedding
    embedding VECTOR(1536) NOT NULL,
    embedding_model VARCHAR(50) NOT NULL DEFAULT 'text-embedding-3-small',
    
    -- Flexible metadata for future extension
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Unique index for upsert operations (uses COALESCE for nullable criteria_id)
-- Note: Must be index, not constraint, to support COALESCE expression
CREATE UNIQUE INDEX idx_policy_chunks_unique ON policy_chunks 
    (policy_id, chunk_type, COALESCE(criteria_id, ''), content_hash);

-- Indexes for RAG queries
CREATE INDEX idx_policy_chunks_embedding ON policy_chunks 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_policy_chunks_category ON policy_chunks (category);
CREATE INDEX idx_policy_chunks_subcategory ON policy_chunks (subcategory);
CREATE INDEX idx_policy_chunks_risk_level ON policy_chunks (risk_level);
CREATE INDEX idx_policy_chunks_policy_id ON policy_chunks (policy_id);
CREATE INDEX idx_policy_chunks_chunk_type ON policy_chunks (chunk_type);
CREATE INDEX idx_policy_chunks_metadata ON policy_chunks USING gin (metadata);

-- Full-text search index for hybrid search (optional)
CREATE INDEX idx_policy_chunks_content_trgm ON policy_chunks 
    USING gin (content gin_trgm_ops);
```

#### Chunk Type Definitions

| Chunk Type | Description | Content Template |
|------------|-------------|------------------|
| `policy_header` | Policy overview | Name, description, category context |
| `criteria` | Single evaluation criteria | Condition, risk level, action, rationale |
| `modifying_factor` | Risk modifier | Factor name, impact description |
| `reference` | External reference | Source document/guideline citation |
| `description` | General description | Policy description text |

#### Risk Level Enum Values

```
Low, Low-Moderate, Moderate, Moderate-High, High, Defer, Decline
```

---

### 2. Application (Migrated from JSON)

Stores application metadata, replacing the current JSON file storage.

```sql
CREATE TABLE applications (
    id VARCHAR(36) PRIMARY KEY,  -- Preserve existing UUIDs
    
    -- Core metadata
    external_reference VARCHAR(100),
    persona VARCHAR(50),
    status VARCHAR(30) NOT NULL DEFAULT 'uploaded' CHECK (status IN (
        'uploaded',
        'processing',
        'analyzed',
        'complete',
        'error'
    )),
    
    -- Document content
    document_markdown TEXT,
    markdown_pages JSONB,  -- Array of page objects
    
    -- Analysis results (semi-structured)
    llm_outputs JSONB,
    extracted_fields JSONB,
    confidence_summary JSONB,
    risk_analysis JSONB,
    
    -- Content Understanding metadata
    analyzer_id_used VARCHAR(100),
    cu_raw_result_path VARCHAR(500),  -- Blob storage path
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT valid_persona CHECK (persona IS NULL OR persona != '')
);

CREATE INDEX idx_applications_persona ON applications (persona);
CREATE INDEX idx_applications_status ON applications (status);
CREATE INDEX idx_applications_created_at ON applications (created_at DESC);
CREATE INDEX idx_applications_external_ref ON applications (external_reference);
CREATE INDEX idx_applications_llm_outputs ON applications USING gin (llm_outputs);
CREATE INDEX idx_applications_extracted_fields ON applications USING gin (extracted_fields);
```

---

### 3. ApplicationFile (File Registry)

Links applications to their files stored in blob storage.

```sql
CREATE TABLE application_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id VARCHAR(36) NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    
    -- File metadata
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    content_type VARCHAR(100),
    size_bytes BIGINT,
    
    -- Storage location
    storage_backend VARCHAR(20) NOT NULL DEFAULT 'local' CHECK (storage_backend IN ('local', 'azure_blob')),
    blob_path VARCHAR(500) NOT NULL,
    blob_url TEXT,  -- SAS URL if applicable
    
    -- Processing status
    is_processed BOOLEAN NOT NULL DEFAULT FALSE,
    processing_error TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_app_file UNIQUE (application_id, filename)
);

CREATE INDEX idx_app_files_application ON application_files (application_id);
CREATE INDEX idx_app_files_processed ON application_files (is_processed);
```

---

### 4. Conversation (Chat History)

Stores chat conversations with message history.

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id VARCHAR(36) REFERENCES applications(id) ON DELETE SET NULL,
    
    -- Conversation metadata
    title VARCHAR(200),
    summary TEXT,
    
    -- Messages stored as JSONB array
    messages JSONB NOT NULL DEFAULT '[]',
    message_count INTEGER NOT NULL DEFAULT 0,
    
    -- RAG context (for debugging/analysis)
    last_rag_context JSONB,  -- Chunks retrieved for last query
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversations_application ON conversations (application_id);
CREATE INDEX idx_conversations_created_at ON conversations (created_at DESC);
CREATE INDEX idx_conversations_updated_at ON conversations (updated_at DESC);

-- Optional: Full-text search on messages
CREATE INDEX idx_conversations_messages ON conversations USING gin (messages);
```

#### Message JSONB Structure

```json
{
  "messages": [
    {
      "id": "msg-uuid-1",
      "role": "user",
      "content": "What is the risk rating for blood pressure 145/92?",
      "timestamp": "2025-12-26T10:00:00Z"
    },
    {
      "id": "msg-uuid-2",
      "role": "assistant",
      "content": "Based on policy CVD-BP-001...",
      "timestamp": "2025-12-26T10:00:02Z",
      "rag_chunks_used": ["chunk-id-1", "chunk-id-2"],
      "tokens_used": 450
    }
  ]
}
```

---

### 5. EmbeddingCache (Optional Performance Optimization)

Caches embeddings for frequent queries to reduce Azure OpenAI API calls.

```sql
CREATE TABLE embedding_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Cache key
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256 of normalized query
    
    -- Cached embedding
    embedding VECTOR(1536) NOT NULL,
    embedding_model VARCHAR(50) NOT NULL,
    
    -- Cache metadata
    hit_count INTEGER NOT NULL DEFAULT 0,
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '7 days')
);

CREATE INDEX idx_embedding_cache_hash ON embedding_cache (query_hash);
CREATE INDEX idx_embedding_cache_expires ON embedding_cache (expires_at);
```

---

## Relationships

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Entity Relationships                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  applications ─────────────┬───────────────── conversations         │
│       │                    │ 1:N                    │                │
│       │                    │                        │                │
│       │ 1:N               │                        │                │
│       ▼                    │                        │                │
│  application_files         │                        │                │
│       │                    │                        │                │
│       │                    │                        │                │
│       ▼                    ▼                        ▼                │
│  Azure Blob Storage    policy_chunks         RAG Retrieval          │
│  (file content)        (independent)         (at query time)        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

Notes:
- policy_chunks is independent (no FK to applications)
- conversations optionally link to applications (can have orphan chats)
- application_files reference blob storage, not inline content
- RAG retrieval joins query embedding against policy_chunks at runtime
```

---

## Data Migration Strategy

### Phase 1: Policy Chunks (P0)

```python
# Pseudocode for policy chunking
def chunk_policies(policies_json):
    chunks = []
    for policy in policies_json["policies"]:
        # Policy header chunk
        chunks.append({
            "policy_id": policy["id"],
            "chunk_type": "policy_header",
            "category": policy["category"],
            "subcategory": policy["subcategory"],
            "content": f"{policy['name']}: {policy['description']}",
            # ... other fields
        })
        
        # Criteria chunks (one per criteria)
        for criteria in policy.get("criteria", []):
            chunks.append({
                "policy_id": policy["id"],
                "chunk_type": "criteria",
                "criteria_id": criteria["id"],
                "risk_level": criteria["risk_level"],
                "content": format_criteria_content(criteria),
                # ... other fields
            })
        
        # Modifying factor chunks
        for factor in policy.get("modifying_factors", []):
            chunks.append({
                "policy_id": policy["id"],
                "chunk_type": "modifying_factor",
                "content": f"{factor['factor']}: {factor['impact']}",
                # ... other fields
            })
    
    return chunks
```

### Phase 2: Applications (P2)

Migration script to move data from JSON files to PostgreSQL:

```python
def migrate_applications():
    for app_dir in data_dir.glob("applications/*"):
        metadata_file = app_dir / "metadata.json"
        if metadata_file.exists():
            metadata = json.load(metadata_file)
            
            # Insert into applications table
            insert_application(metadata)
            
            # Register files
            for file_info in metadata.get("files", []):
                insert_application_file(app_id, file_info)
```

---

## Vector Search Queries

### Basic Semantic Search

```sql
-- Find top 5 most similar policy chunks
SELECT 
    id,
    policy_id,
    policy_name,
    criteria_id,
    risk_level,
    content,
    1 - (embedding <=> $1::vector) as similarity
FROM policy_chunks
WHERE 1 - (embedding <=> $1::vector) > 0.7  -- Similarity threshold
ORDER BY embedding <=> $1::vector
LIMIT 5;
```

### Filtered Semantic Search

```sql
-- Find top 5 chunks in 'cardiovascular' category
SELECT 
    id,
    policy_id,
    policy_name,
    criteria_id,
    risk_level,
    content,
    1 - (embedding <=> $1::vector) as similarity
FROM policy_chunks
WHERE category = 'cardiovascular'
  AND 1 - (embedding <=> $1::vector) > 0.7
ORDER BY embedding <=> $1::vector
LIMIT 5;
```

### Hybrid Search (Keyword + Semantic)

```sql
-- Combine keyword match with semantic similarity
WITH keyword_matches AS (
    SELECT id, 
           ts_rank(to_tsvector('english', content), plainto_tsquery($2)) as keyword_score
    FROM policy_chunks
    WHERE to_tsvector('english', content) @@ plainto_tsquery($2)
),
semantic_matches AS (
    SELECT id, 
           1 - (embedding <=> $1::vector) as semantic_score
    FROM policy_chunks
    WHERE 1 - (embedding <=> $1::vector) > 0.5
)
SELECT 
    pc.*,
    COALESCE(km.keyword_score, 0) * 0.3 + COALESCE(sm.semantic_score, 0) * 0.7 as combined_score
FROM policy_chunks pc
LEFT JOIN keyword_matches km ON pc.id = km.id
LEFT JOIN semantic_matches sm ON pc.id = sm.id
WHERE km.id IS NOT NULL OR sm.id IS NOT NULL
ORDER BY combined_score DESC
LIMIT 5;
```

---

## Index Tuning

### HNSW Index Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `m` | 16 | Connections per node; 16 is good balance for <10K vectors |
| `ef_construction` | 64 | Build-time quality; higher = better recall, slower build |
| `ef_search` | 40 | Query-time quality; set via `SET hnsw.ef_search = 40;` |

### Expected Performance

| Vector Count | Dimensions | Search Latency (p95) | Memory |
|--------------|------------|---------------------|--------|
| 200 | 1536 | <10ms | ~1.2MB |
| 1,000 | 1536 | <20ms | ~6MB |
| 10,000 | 1536 | <50ms | ~60MB |

---

## Validation Rules

### PolicyChunk

- `content` must be non-empty
- `embedding` must have exactly 1536 dimensions (or configured dimension)
- `token_count` should be positive
- `content_hash` must match SHA-256 of `content`

### Application

- `id` must be valid UUID format (existing format preserved)
- `status` must be one of defined enum values
- JSONB fields must be valid JSON

### ApplicationFile

- `blob_path` must follow pattern `applications/{app_id}/files/{filename}`
- `filename` must not contain path separators

---

## Change Detection

To detect when policies need re-embedding:

```sql
-- Check if source policy content has changed
SELECT 
    policy_id,
    MAX(updated_at) as last_updated,
    COUNT(*) as chunk_count
FROM policy_chunks
WHERE policy_version = $1
GROUP BY policy_id;

-- Compare content_hash to detect changes
SELECT policy_id, criteria_id
FROM policy_chunks
WHERE content_hash != $expected_hash;
```
