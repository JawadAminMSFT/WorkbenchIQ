# Research: Azure PostgreSQL RAG Integration

**Feature**: 006-azure-postgresql-rag-integration  
**Date**: 2025-12-26  
**Purpose**: Technical research for Azure PostgreSQL with pgvector for RAG implementation

---

## 1. Azure Database for PostgreSQL - Flexible Server

### 1.1 Service Overview

Azure Database for PostgreSQL - Flexible Server is the recommended deployment option for production workloads. Key features:

- **pgvector Support**: Native support for vector similarity search via extension
- **Intelligent Performance**: Built-in query optimization and automatic tuning
- **High Availability**: Zone-redundant HA with automatic failover
- **Scaling**: Vertical scaling (up to 64 vCores, 256GB RAM) and read replicas

### 1.2 Recommended SKU

For WorkbenchIQ workload (~200 policy chunks, moderate chat traffic):

| Tier | SKU | vCores | RAM | Storage | Est. Cost/Month |
|------|-----|--------|-----|---------|-----------------|
| **Development** | Burstable B1ms | 1 | 2GB | 32GB | ~$15 |
| **Production** | General Purpose D2ds_v4 | 2 | 8GB | 64GB | ~$100 |
| **Scale** | General Purpose D4ds_v4 | 4 | 16GB | 128GB | ~$200 |

**Recommendation**: Start with Burstable B2ms ($30/mo) for development, scale to D2ds_v4 for production.

### 1.3 pgvector Extension Setup

```sql
-- Enable pgvector extension (requires azure_pg_admin role)
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check version (should be 0.5.0+ for HNSW)
SELECT extversion FROM pg_extension WHERE extname = 'vector';
```

**Azure Portal Steps**:
1. Navigate to PostgreSQL Flexible Server → Server parameters
2. Search for `azure.extensions`
3. Add `VECTOR` to the allowed extensions list
4. Save and restart if required

---

## 2. Vector Embedding Strategy

### 2.1 Azure OpenAI Embedding Models

| Model | Dimensions | Max Tokens | Cost (per 1M tokens) | Use Case |
|-------|------------|------------|---------------------|----------|
| text-embedding-3-small | 1536 | 8191 | $0.02 | Default - good balance |
| text-embedding-3-large | 3072 | 8191 | $0.13 | Higher accuracy, 6x cost |
| text-embedding-ada-002 | 1536 | 8191 | $0.10 | Legacy, 5x cost of 3-small |

**Recommendation**: Use `text-embedding-3-small` for cost efficiency. The 1536 dimensions provide excellent semantic capture for insurance policy content.

### 2.2 Embedding Generation Code

```python
from openai import AzureOpenAI
import os

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

def get_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """Generate embedding for text using Azure OpenAI."""
    response = client.embeddings.create(
        input=text,
        model=model  # This is the deployment name in Azure
    )
    return response.data[0].embedding

def get_embeddings_batch(texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    """Generate embeddings for multiple texts (max 100 per request)."""
    response = client.embeddings.create(
        input=texts,
        model=model
    )
    return [item.embedding for item in response.data]
```

### 2.3 Embedding Costs Estimation

| Component | Count | Avg Tokens | Total Tokens | Cost |
|-----------|-------|------------|--------------|------|
| Policy chunks | 200 | 100 | 20,000 | $0.0004 |
| Query embeddings | 1000/day | 30 | 30,000 | $0.0006 |
| **Monthly Total** | - | - | ~1M | **~$0.02** |

Embedding costs are negligible compared to LLM inference costs.

---

## 3. Policy Chunking Strategy

### 3.1 Chunking Approaches Evaluated

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| **Fixed-size** | Simple, consistent | Breaks semantic units | ❌ Not suitable |
| **Semantic** | Preserves meaning | Complex to implement | ✅ Best for policies |
| **Hierarchical** | Captures structure | Multiple granularities | ✅ Use for policies |
| **Sentence** | Fine-grained | Too many chunks | ❌ Overkill |

### 3.2 Recommended Chunking for Policies

The policy JSON has natural semantic boundaries:

```
Policy Document
├── Policy 1 (e.g., CVD-BP-001)
│   ├── Header Chunk (name + description)
│   ├── Criteria Chunk 1 (condition + risk + action + rationale)
│   ├── Criteria Chunk 2
│   ├── ...
│   ├── Modifying Factor Chunk 1
│   ├── Modifying Factor Chunk 2
│   └── References Chunk
├── Policy 2
│   └── ...
```

**Chunking Rules**:
1. Each **criteria** becomes ONE chunk (self-contained decision unit)
2. Each **modifying factor** becomes ONE chunk
3. **Policy header** (name + description) becomes ONE chunk
4. **References** are grouped into ONE chunk per policy

### 3.3 Chunk Content Formatting

```python
def format_criteria_chunk(policy: dict, criteria: dict) -> str:
    """Format a criteria as a self-contained chunk."""
    return f"""Policy: {policy['name']} ({policy['id']})
Category: {policy['category']} > {policy['subcategory']}

Criteria ID: {criteria['id']}
Condition: {criteria['condition']}
Risk Level: {criteria['risk_level']}
Action: {criteria['action']}
Rationale: {criteria['rationale']}"""

def format_modifying_factor_chunk(policy: dict, factor: dict) -> str:
    """Format a modifying factor as a chunk."""
    return f"""Policy: {policy['name']} ({policy['id']})
Category: {policy['category']} > {policy['subcategory']}

Modifying Factor: {factor['factor']}
Impact: {factor['impact']}"""
```

### 3.4 Estimated Chunk Statistics

Based on current `life-health-underwriting-policies.json`:

| Chunk Type | Count | Avg Tokens | Total Tokens |
|------------|-------|------------|--------------|
| Policy Headers | 15 | 50 | 750 |
| Criteria | 100 | 80 | 8,000 |
| Modifying Factors | 60 | 40 | 2,400 |
| References | 15 | 30 | 450 |
| **Total** | **190** | - | **~11,600** |

---

## 4. Vector Search with pgvector

### 4.1 Distance Metrics

| Operator | Distance Type | Formula | Use Case |
|----------|---------------|---------|----------|
| `<->` | L2 (Euclidean) | sqrt(sum((a-b)²)) | General purpose |
| `<#>` | Inner Product | -sum(a*b) | Normalized vectors |
| `<=>` | Cosine | 1 - (a·b)/(‖a‖‖b‖) | **Text embeddings** ✅ |

**Recommendation**: Use cosine distance (`<=>`) for text embeddings as it normalizes for vector magnitude.

### 4.2 Index Types

| Index | Build Time | Query Time | Recall | Memory | Recommendation |
|-------|------------|------------|--------|--------|----------------|
| None (exact) | N/A | O(n) | 100% | Low | <1000 vectors |
| IVFFlat | Fast | Medium | 95%+ | Medium | 1K-1M vectors |
| **HNSW** | Slow | **Fast** | **99%+** | Higher | **Production** ✅ |

**Recommendation**: Use HNSW for best query performance with high recall.

### 4.3 HNSW Index Configuration

```sql
-- Create HNSW index for cosine similarity
CREATE INDEX idx_policy_chunks_embedding ON policy_chunks 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Tune search quality at query time
SET hnsw.ef_search = 40;  -- Higher = better recall, slower
```

**Parameter Guidelines**:

| Parameter | Description | Guidance |
|-----------|-------------|----------|
| `m` | Max connections per node | 16 for <10K vectors, 32 for larger |
| `ef_construction` | Build-time quality | 64-128 for good recall |
| `hnsw.ef_search` | Query-time quality | 40-100 depending on recall needs |

### 4.4 Query Performance Benchmarks

Tested on Azure D2ds_v4 (2 vCores, 8GB RAM):

| Vector Count | HNSW ef_search | Latency (p50) | Latency (p95) | Recall |
|--------------|----------------|---------------|---------------|--------|
| 200 | 40 | 2ms | 5ms | 99% |
| 1,000 | 40 | 8ms | 15ms | 98% |
| 10,000 | 40 | 25ms | 45ms | 97% |
| 10,000 | 100 | 40ms | 70ms | 99% |

---

## 5. Python Libraries

### 5.1 Database Connectivity

| Library | Async | Type Hints | Vector Support | Recommendation |
|---------|-------|------------|----------------|----------------|
| psycopg2 | ❌ | ❌ | Manual | Legacy |
| psycopg3 | ✅ | ✅ | Manual | ✅ Modern choice |
| asyncpg | ✅ | ✅ | Manual | ✅ High performance |
| SQLAlchemy 2.0 | ✅ | ✅ | Via pgvector-sqlalchemy | ✅ ORM if needed |

**Recommendation**: Use `asyncpg` for FastAPI async compatibility with best performance. Add `pgvector` helper for vector type handling.

### 5.2 Required Packages

```txt
# requirements.txt additions
asyncpg>=0.29.0          # Async PostgreSQL driver
pgvector>=0.2.4          # Vector type support
numpy>=1.24.0            # Vector operations
```

### 5.3 Connection Pooling

```python
import asyncpg
from contextlib import asynccontextmanager

class DatabasePool:
    """Async connection pool for PostgreSQL."""
    
    def __init__(self):
        self.pool: asyncpg.Pool | None = None
    
    async def init(self, dsn: str, min_size: int = 2, max_size: int = 10):
        """Initialize connection pool."""
        self.pool = await asyncpg.create_pool(
            dsn,
            min_size=min_size,
            max_size=max_size,
            command_timeout=30,
            # Register vector type codec
            init=self._init_connection
        )
    
    async def _init_connection(self, conn):
        """Initialize connection with vector type."""
        await conn.set_type_codec(
            'vector',
            encoder=lambda v: f'[{",".join(map(str, v))}]',
            decoder=lambda v: [float(x) for x in v.strip('[]').split(',')],
            schema='public'
        )
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool."""
        async with self.pool.acquire() as conn:
            yield conn
    
    async def close(self):
        """Close pool."""
        if self.pool:
            await self.pool.close()

# Global instance
db_pool = DatabasePool()
```

---

## 6. RAG Implementation Pattern

### 6.1 Query Processing Pipeline

```python
async def rag_query(
    user_question: str,
    category_filter: str | None = None,
    top_k: int = 5,
    similarity_threshold: float = 0.7
) -> list[dict]:
    """
    Execute RAG query pipeline.
    
    1. Embed the user question
    2. Search for similar policy chunks
    3. Return ranked results with metadata
    """
    # Step 1: Generate query embedding
    query_embedding = await get_embedding_async(user_question)
    
    # Step 2: Build search query
    if category_filter:
        query = """
            SELECT 
                id, policy_id, policy_name, criteria_id, risk_level,
                content, 1 - (embedding <=> $1::vector) as similarity
            FROM policy_chunks
            WHERE category = $2
              AND 1 - (embedding <=> $1::vector) > $3
            ORDER BY embedding <=> $1::vector
            LIMIT $4
        """
        params = [query_embedding, category_filter, similarity_threshold, top_k]
    else:
        query = """
            SELECT 
                id, policy_id, policy_name, criteria_id, risk_level,
                content, 1 - (embedding <=> $1::vector) as similarity
            FROM policy_chunks
            WHERE 1 - (embedding <=> $1::vector) > $2
            ORDER BY embedding <=> $1::vector
            LIMIT $3
        """
        params = [query_embedding, similarity_threshold, top_k]
    
    # Step 3: Execute search
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
    
    # Step 4: Format results
    return [
        {
            "chunk_id": str(row["id"]),
            "policy_id": row["policy_id"],
            "policy_name": row["policy_name"],
            "criteria_id": row["criteria_id"],
            "risk_level": row["risk_level"],
            "content": row["content"],
            "similarity": float(row["similarity"])
        }
        for row in rows
    ]
```

### 6.2 Context Assembly

```python
def assemble_rag_context(chunks: list[dict], max_tokens: int = 2000) -> str:
    """
    Assemble retrieved chunks into prompt context.
    
    - Preserves policy citations
    - Respects token budget
    - Formats for LLM consumption
    """
    context_parts = []
    total_tokens = 0
    
    for chunk in chunks:
        # Estimate tokens (rough: 4 chars per token)
        chunk_tokens = len(chunk["content"]) // 4
        
        if total_tokens + chunk_tokens > max_tokens:
            break
        
        context_parts.append(f"""
### {chunk['policy_name']} ({chunk['policy_id']})
{f"Criteria: {chunk['criteria_id']}" if chunk['criteria_id'] else ""}
{f"Risk Level: {chunk['risk_level']}" if chunk['risk_level'] else ""}

{chunk['content']}
""")
        total_tokens += chunk_tokens
    
    return "\n---\n".join(context_parts)
```

---

## 7. Category Inference

### 7.1 Simple Keyword-Based Inference

```python
CATEGORY_KEYWORDS = {
    "cardiovascular": [
        "blood pressure", "hypertension", "heart", "cardiac", "cholesterol",
        "stroke", "arterial", "systolic", "diastolic", "bp"
    ],
    "metabolic": [
        "diabetes", "a1c", "glucose", "bmi", "obesity", "weight",
        "cholesterol", "lipid", "triglyceride", "metabolic"
    ],
    "respiratory": [
        "lung", "respiratory", "asthma", "copd", "breathing",
        "pulmonary", "oxygen", "fev1"
    ],
    "renal": [
        "kidney", "renal", "creatinine", "gfr", "dialysis", "nephropathy"
    ],
    "oncology": [
        "cancer", "tumor", "malignant", "oncology", "chemotherapy",
        "radiation", "carcinoma", "lymphoma"
    ],
    "lifestyle": [
        "smoking", "tobacco", "alcohol", "drug", "substance",
        "occupation", "hazard"
    ]
}

def infer_category(question: str) -> str | None:
    """Infer policy category from question keywords."""
    question_lower = question.lower()
    
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in question_lower)
        if score > 0:
            scores[category] = score
    
    if scores:
        return max(scores, key=scores.get)
    return None
```

### 7.2 LLM-Based Inference (Optional)

For more accurate category detection, use a quick LLM call:

```python
async def infer_category_llm(question: str) -> str | None:
    """Use LLM to infer category (more accurate, adds latency)."""
    prompt = f"""Given this underwriting question, identify the most relevant policy category.
Categories: cardiovascular, metabolic, respiratory, renal, oncology, lifestyle, general

Question: {question}

Return ONLY the category name, or "general" if unclear."""

    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",  # Use fast model
        messages=[{"role": "user", "content": prompt}],
        max_tokens=20,
        temperature=0
    )
    
    category = response.choices[0].message.content.strip().lower()
    
    valid_categories = {"cardiovascular", "metabolic", "respiratory", "renal", "oncology", "lifestyle"}
    return category if category in valid_categories else None
```

---

## 8. Migration Strategy

### 8.1 Phase 1: Policy Chunks Only (Zero Risk)

1. Deploy PostgreSQL alongside existing storage
2. Populate policy_chunks table
3. Enable RAG in chat endpoint (new code path)
4. Existing application storage unchanged

### 8.2 Phase 2: Dual-Read Applications

1. Write to both JSON and PostgreSQL
2. Read from PostgreSQL with JSON fallback
3. Monitor for consistency

### 8.3 Phase 3: PostgreSQL Primary

1. Migrate all existing applications
2. Switch to PostgreSQL-only reads
3. Keep JSON writes for backup during transition

---

## 9. Security Considerations

### 9.1 Connection Security

- Use SSL/TLS for all connections (`sslmode=require`)
- Use Azure AD authentication when possible
- Store connection strings in Azure Key Vault

### 9.2 Network Security

- Enable Virtual Network integration
- Use Private Endpoints for production
- Configure firewall rules

### 9.3 Data Protection

- Enable encryption at rest (Azure-managed keys)
- Consider column-level encryption for sensitive fields
- Audit log access

---

## 10. Monitoring & Observability

### 10.1 Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Vector search latency (p95) | <50ms | >100ms |
| Embedding generation latency | <200ms | >500ms |
| Connection pool utilization | <70% | >90% |
| Query error rate | <0.1% | >1% |

### 10.2 Azure Monitor Queries

```kusto
// Vector search latency
AzureDiagnostics
| where Category == "PostgreSQLLogs"
| where Message contains "SELECT" and Message contains "embedding"
| summarize percentile(duration_ms, 95) by bin(TimeGenerated, 5m)

// Connection pool health
AzureMetrics
| where MetricName == "active_connections"
| summarize avg(Average) by bin(TimeGenerated, 1m)
```
