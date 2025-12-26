# Quickstart: Azure PostgreSQL RAG Integration

**Feature**: 006-azure-postgresql-rag-integration  
**Date**: 2025-12-26

---

## Prerequisites

1. **Azure Subscription** with permissions to create PostgreSQL Flexible Server
2. **Azure OpenAI** deployment with `text-embedding-3-small` model
3. **Python 3.10+** with pip
4. **psql** CLI (optional, for direct database access)

---

## 1. Provision Azure PostgreSQL Flexible Server

### Azure Portal

1. Go to **Azure Portal** → **Create a Resource** → **Azure Database for PostgreSQL Flexible Server**
2. Configure:
   - **Resource Group**: Your existing RG or create new
   - **Server Name**: `workbenchiq-db` (must be globally unique)
   - **Region**: Same as your other resources
   - **Workload Type**: Development (for dev/test) or Production
   - **Compute + Storage**: B2ms (2 vCores, 4GB RAM) for dev
   - **Authentication**: PostgreSQL authentication
   - **Admin Username**: `workbenchiq_admin`
   - **Password**: Generate strong password, save securely
3. **Networking**:
   - Enable **Public access** for development
   - Add your IP to firewall rules
   - (Production: Use Private Endpoint)
4. Review and Create

### Azure CLI

```bash
# Create resource group (if needed)
az group create --name workbenchiq-rg --location eastus

# Create PostgreSQL Flexible Server
az postgres flexible-server create \
  --resource-group workbenchiq-rg \
  --name workbenchiq-db \
  --location eastus \
  --admin-user workbenchiq_admin \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B2ms \
  --storage-size 32 \
  --version 15 \
  --public-access 0.0.0.0-255.255.255.255

# Enable pgvector extension
az postgres flexible-server parameter set \
  --resource-group workbenchiq-rg \
  --server-name workbenchiq-db \
  --name azure.extensions \
  --value vector
```

---

## 2. Configure pgvector Extension

Connect to your database and enable the extension:

```bash
# Connect via psql
psql "host=workbenchiq-db.postgres.database.azure.com port=5432 dbname=postgres user=workbenchiq_admin sslmode=require"
```

```sql
-- Create application database
CREATE DATABASE workbenchiq;

-- Connect to it
\c workbenchiq

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verify
SELECT * FROM pg_extension WHERE extname = 'vector';
```

---

## 3. Create Schema

Run the initial schema migration:

```sql
-- Create schema
CREATE SCHEMA IF NOT EXISTS workbenchiq;
SET search_path TO workbenchiq, public;

-- Policy chunks table with vector embeddings
CREATE TABLE policy_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id VARCHAR(50) NOT NULL,
    policy_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    policy_name VARCHAR(200) NOT NULL,
    chunk_type VARCHAR(30) NOT NULL,
    chunk_sequence INTEGER NOT NULL DEFAULT 0,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    criteria_id VARCHAR(50),
    risk_level VARCHAR(30),
    action_recommendation TEXT,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    embedding VECTOR(1536) NOT NULL,
    embedding_model VARCHAR(50) NOT NULL DEFAULT 'text-embedding-3-small',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create HNSW index for fast vector search
CREATE INDEX idx_policy_chunks_embedding ON policy_chunks 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Additional indexes for filtering
CREATE INDEX idx_policy_chunks_category ON policy_chunks (category);
CREATE INDEX idx_policy_chunks_policy_id ON policy_chunks (policy_id);
CREATE INDEX idx_policy_chunks_risk_level ON policy_chunks (risk_level);
```

---

## 4. Configure Environment Variables

Add to your `.env` file:

```bash
# Database Configuration
DATABASE_BACKEND=postgresql
POSTGRESQL_HOST=workbenchiq-db.postgres.database.azure.com
POSTGRESQL_PORT=5432
POSTGRESQL_DATABASE=workbenchiq
POSTGRESQL_USER=workbenchiq_admin
POSTGRESQL_PASSWORD=YourSecurePassword123!
POSTGRESQL_SSL_MODE=require

# RAG Configuration
RAG_ENABLED=true
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.7

# Embedding Configuration (uses existing Azure OpenAI)
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

---

## 5. Install Python Dependencies

```bash
pip install asyncpg pgvector numpy
```

Or add to requirements.txt:
```txt
asyncpg>=0.29.0
pgvector>=0.2.4
numpy>=1.24.0
```

---

## 6. Test Connection

Create a quick test script:

```python
# test_db_connection.py
import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()

async def test_connection():
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRESQL_HOST"),
        port=int(os.getenv("POSTGRESQL_PORT", 5432)),
        database=os.getenv("POSTGRESQL_DATABASE"),
        user=os.getenv("POSTGRESQL_USER"),
        password=os.getenv("POSTGRESQL_PASSWORD"),
        ssl="require"
    )
    
    # Test basic query
    version = await conn.fetchval("SELECT version();")
    print(f"Connected! PostgreSQL version: {version}")
    
    # Test pgvector
    result = await conn.fetchval("SELECT '[1,2,3]'::vector;")
    print(f"pgvector working: {result}")
    
    await conn.close()

asyncio.run(test_connection())
```

Run:
```bash
python test_db_connection.py
```

---

## 7. Index Sample Policies

Quick test of the chunking and embedding pipeline:

```python
# test_index_policies.py
import asyncio
import json
import hashlib
import os
from dotenv import load_dotenv
import asyncpg
from openai import AzureOpenAI

load_dotenv()

# Initialize OpenAI client
openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

def get_embedding(text: str) -> list[float]:
    """Generate embedding for text."""
    response = openai_client.embeddings.create(
        input=text,
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    )
    return response.data[0].embedding

def chunk_policy(policy: dict) -> list[dict]:
    """Chunk a single policy into semantic units."""
    chunks = []
    
    # Header chunk
    header_content = f"{policy['name']}: {policy['description']}"
    chunks.append({
        "policy_id": policy["id"],
        "policy_name": policy["name"],
        "chunk_type": "policy_header",
        "category": policy["category"],
        "subcategory": policy.get("subcategory", ""),
        "content": header_content,
    })
    
    # Criteria chunks
    for criteria in policy.get("criteria", []):
        content = f"""Condition: {criteria['condition']}
Risk Level: {criteria['risk_level']}
Action: {criteria['action']}
Rationale: {criteria['rationale']}"""
        
        chunks.append({
            "policy_id": policy["id"],
            "policy_name": policy["name"],
            "chunk_type": "criteria",
            "category": policy["category"],
            "subcategory": policy.get("subcategory", ""),
            "criteria_id": criteria["id"],
            "risk_level": criteria["risk_level"],
            "content": content,
        })
    
    return chunks

async def index_policies():
    """Load, chunk, embed, and store policies."""
    # Load policies
    with open("data/life-health-underwriting-policies.json") as f:
        data = json.load(f)
    
    # Connect to database
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRESQL_HOST"),
        port=int(os.getenv("POSTGRESQL_PORT", 5432)),
        database=os.getenv("POSTGRESQL_DATABASE"),
        user=os.getenv("POSTGRESQL_USER"),
        password=os.getenv("POSTGRESQL_PASSWORD"),
        ssl="require"
    )
    
    # Process each policy
    total_chunks = 0
    for policy in data["policies"][:2]:  # Limit to 2 for testing
        chunks = chunk_policy(policy)
        
        for chunk in chunks:
            # Generate embedding
            embedding = get_embedding(chunk["content"])
            content_hash = hashlib.sha256(chunk["content"].encode()).hexdigest()
            
            # Insert into database
            await conn.execute("""
                INSERT INTO workbenchiq.policy_chunks 
                (policy_id, policy_name, chunk_type, category, subcategory, 
                 criteria_id, risk_level, content, content_hash, embedding,
                 token_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (policy_id, chunk_type, criteria_id, content_hash) 
                DO UPDATE SET updated_at = NOW()
            """,
                chunk["policy_id"],
                chunk["policy_name"],
                chunk["chunk_type"],
                chunk["category"],
                chunk.get("subcategory", ""),
                chunk.get("criteria_id"),
                chunk.get("risk_level"),
                chunk["content"],
                content_hash,
                str(embedding),  # pgvector accepts string format
                len(chunk["content"]) // 4  # Rough token estimate
            )
            total_chunks += 1
            print(f"Indexed: {chunk['policy_id']} - {chunk['chunk_type']}")
    
    await conn.close()
    print(f"\nTotal chunks indexed: {total_chunks}")

asyncio.run(index_policies())
```

---

## 8. Test Vector Search

```python
# test_vector_search.py
import asyncio
import os
from dotenv import load_dotenv
import asyncpg
from openai import AzureOpenAI

load_dotenv()

openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

def get_embedding(text: str) -> list[float]:
    response = openai_client.embeddings.create(
        input=text,
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    )
    return response.data[0].embedding

async def search_policies(question: str, top_k: int = 3):
    """Search for relevant policy chunks."""
    # Generate query embedding
    query_embedding = get_embedding(question)
    
    # Connect and search
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRESQL_HOST"),
        port=int(os.getenv("POSTGRESQL_PORT", 5432)),
        database=os.getenv("POSTGRESQL_DATABASE"),
        user=os.getenv("POSTGRESQL_USER"),
        password=os.getenv("POSTGRESQL_PASSWORD"),
        ssl="require"
    )
    
    # Vector similarity search
    rows = await conn.fetch(f"""
        SELECT 
            policy_id,
            policy_name,
            criteria_id,
            risk_level,
            content,
            1 - (embedding <=> '{query_embedding}'::vector) as similarity
        FROM workbenchiq.policy_chunks
        ORDER BY embedding <=> '{query_embedding}'::vector
        LIMIT $1
    """, top_k)
    
    await conn.close()
    
    print(f"\nQuestion: {question}\n")
    print("=" * 60)
    for row in rows:
        print(f"\n[{row['policy_id']}] {row['policy_name']}")
        print(f"Criteria: {row['criteria_id'] or 'N/A'} | Risk: {row['risk_level'] or 'N/A'}")
        print(f"Similarity: {row['similarity']:.3f}")
        print(f"Content: {row['content'][:200]}...")

# Test queries
asyncio.run(search_policies("What is the risk for blood pressure 145/92?"))
asyncio.run(search_policies("How should I rate a diabetic patient with A1C of 8.5?"))
```

---

## Expected Output

```
Question: What is the risk for blood pressure 145/92?

============================================================

[CVD-BP-001] Blood Pressure Risk Assessment
Criteria: CVD-BP-001-D | Risk: Moderate
Similarity: 0.892
Content: Condition: Systolic 140-159 OR Diastolic 90-99
Risk Level: Moderate
Action: +25-50% loading depending on control and duration
Rationale: Stage 2 hypertension...

[CVD-BP-001] Blood Pressure Risk Assessment
Criteria: CVD-BP-001-C | Risk: Low-Moderate
Similarity: 0.845
Content: Condition: Systolic 130-139 OR Diastolic 80-89
Risk Level: Low-Moderate
Action: Standard rates if controlled on single medication...
```

---

## Next Steps

1. ✅ Database provisioned and connected
2. ✅ pgvector extension enabled
3. ✅ Schema created
4. ✅ Sample policies indexed
5. ✅ Vector search working
6. → Implement full chunking pipeline (Phase 2 tasks)
7. → Integrate with chat endpoint (Phase 4 tasks)
8. → Deploy to production

---

## Troubleshooting

### "extension 'vector' is not available"

Enable the extension in Azure Portal:
1. Go to PostgreSQL server → Server parameters
2. Find `azure.extensions`
3. Add `VECTOR` to the list
4. Save (may require restart)

### Connection timeout

- Check firewall rules include your IP
- Verify SSL mode is `require`
- Check server is running (not paused)

### Embedding dimension mismatch

Ensure `EMBEDDING_DIMENSIONS` matches your model:
- text-embedding-3-small: 1536
- text-embedding-3-large: 3072
- text-embedding-ada-002: 1536
