#!/usr/bin/env python3
"""
Test script for PostgreSQL RAG integration.
Combines connection test, policy indexing, and vector search in one file.

Usage:
    python test_postgresql_rag.py
"""

import asyncio
import json
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration from environment
DB_CONFIG = {
    "host": os.getenv("POSTGRESQL_HOST"),
    "port": int(os.getenv("POSTGRESQL_PORT", 5432)),
    "database": os.getenv("POSTGRESQL_DATABASE"),
    "user": os.getenv("POSTGRESQL_USER"),
    "password": os.getenv("POSTGRESQL_PASSWORD"),
    "ssl": os.getenv("POSTGRESQL_SSL_MODE", "require"),
    "schema": os.getenv("POSTGRESQL_SCHEMA", "workbenchiq"),
}

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def get_openai_client():
    """Initialize Azure OpenAI client."""
    from openai import AzureOpenAI
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )


def get_embedding(client, text: str) -> list[float]:
    """Generate embedding for text using Azure OpenAI."""
    response = client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding


def chunk_policy(policy: dict) -> list[dict]:
    """Chunk a single policy into semantic units."""
    chunks = []
    
    # Header chunk - includes description for context
    header_content = f"""Policy: {policy['name']}
Category: {policy['category']}
Subcategory: {policy.get('subcategory', 'N/A')}
Description: {policy['description']}"""
    
    chunks.append({
        "policy_id": policy["id"],
        "policy_name": policy["name"],
        "chunk_type": "policy_header",
        "chunk_sequence": 0,
        "category": policy["category"],
        "subcategory": policy.get("subcategory", ""),
        "criteria_id": None,
        "risk_level": None,
        "content": header_content,
    })
    
    # Criteria chunks - each criterion as a separate chunk
    for idx, criteria in enumerate(policy.get("criteria", []), start=1):
        content = f"""Policy: {policy['name']}
Condition: {criteria['condition']}
Risk Level: {criteria['risk_level']}
Action: {criteria['action']}
Rationale: {criteria['rationale']}"""
        
        chunks.append({
            "policy_id": policy["id"],
            "policy_name": policy["name"],
            "chunk_type": "criteria",
            "chunk_sequence": idx,
            "category": policy["category"],
            "subcategory": policy.get("subcategory", ""),
            "criteria_id": criteria["id"],
            "risk_level": criteria["risk_level"],
            "content": content,
        })
    
    # Modifying factors chunk (if present)
    modifying_factors = policy.get("modifying_factors", [])
    if modifying_factors:
        factors_content = f"Policy: {policy['name']}\nModifying Factors:\n"
        for factor in modifying_factors:
            factors_content += f"- {factor['factor']}: {factor['impact']}\n"
        
        chunks.append({
            "policy_id": policy["id"],
            "policy_name": policy["name"],
            "chunk_type": "modifying_factors",
            "chunk_sequence": len(policy.get("criteria", [])) + 1,
            "category": policy["category"],
            "subcategory": policy.get("subcategory", ""),
            "criteria_id": None,
            "risk_level": None,
            "content": factors_content.strip(),
        })
    
    return chunks


async def test_connection():
    """Step 1: Test database connection."""
    print("\n" + "=" * 60)
    print("Step 1: Test Database Connection")
    print("=" * 60)
    
    try:
        import asyncpg
    except ImportError:
        print("❌ asyncpg not installed. Run: pip install asyncpg")
        return None
    
    print(f"⏳ Connecting to {DB_CONFIG['host']}...")
    
    try:
        conn = await asyncpg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            ssl=DB_CONFIG["ssl"]
        )
        
        # Test basic query
        version = await conn.fetchval("SELECT version();")
        print(f"✅ Connected to PostgreSQL")
        print(f"   Version: {version[:60]}...")
        
        # Test pgvector
        result = await conn.fetchval("SELECT '[1,2,3]'::vector;")
        print(f"✅ pgvector extension working: {result}")
        
        # Test pg_trgm extension
        trgm_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'
            )
        """)
        if trgm_exists:
            print(f"✅ pg_trgm extension enabled (hybrid search ready)")
        else:
            print(f"⚠️  pg_trgm extension not found (hybrid search unavailable)")
        
        # Check schema exists
        schema_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.schemata 
                WHERE schema_name = $1
            )
        """, DB_CONFIG["schema"])
        
        if schema_exists:
            print(f"✅ Schema '{DB_CONFIG['schema']}' exists")
        else:
            print(f"❌ Schema '{DB_CONFIG['schema']}' not found")
            await conn.close()
            return None
        
        # Check table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = $1 AND table_name = 'policy_chunks'
            )
        """, DB_CONFIG["schema"])
        
        if table_exists:
            print(f"✅ Table 'policy_chunks' exists")
        else:
            print(f"❌ Table 'policy_chunks' not found")
            await conn.close()
            return None
        
        return conn
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None


async def index_policies(conn, openai_client, limit: int = 2):
    """Step 2: Index sample policies."""
    print("\n" + "=" * 60)
    print(f"Step 2: Index Policies (first {limit})")
    print("=" * 60)
    
    # Load policies
    policies_path = "prompts/life-health-underwriting-policies.json"
    print(f"⏳ Loading policies from {policies_path}...")
    
    with open(policies_path) as f:
        data = json.load(f)
    
    policies = data["policies"][:limit]
    print(f"✅ Loaded {len(policies)} policies to index")
    
    total_chunks = 0
    schema = DB_CONFIG["schema"]
    
    for policy in policies:
        print(f"\n📋 Processing: {policy['id']} - {policy['name']}")
        chunks = chunk_policy(policy)
        print(f"   Generated {len(chunks)} chunks")
        
        for chunk in chunks:
            # Generate embedding
            embedding = get_embedding(openai_client, chunk["content"])
            content_hash = hashlib.sha256(chunk["content"].encode()).hexdigest()
            
            # Insert into database
            await conn.execute(f"""
                INSERT INTO {schema}.policy_chunks 
                (policy_id, policy_name, chunk_type, chunk_sequence, category, 
                 subcategory, criteria_id, risk_level, content, content_hash, 
                 embedding, token_count, embedding_model)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT DO NOTHING
            """,
                chunk["policy_id"],
                chunk["policy_name"],
                chunk["chunk_type"],
                chunk["chunk_sequence"],
                chunk["category"],
                chunk.get("subcategory", ""),
                chunk.get("criteria_id"),
                chunk.get("risk_level"),
                chunk["content"],
                content_hash,
                str(embedding),  # pgvector accepts string format
                len(chunk["content"]) // 4,  # Rough token estimate
                EMBEDDING_MODEL
            )
            total_chunks += 1
            
            chunk_desc = chunk.get("criteria_id") or chunk["chunk_type"]
            print(f"   ✓ Indexed: {chunk_desc}")
    
    # Verify count
    count = await conn.fetchval(f"SELECT COUNT(*) FROM {schema}.policy_chunks")
    print(f"\n✅ Total chunks in database: {count}")
    
    return total_chunks


async def test_vector_search(conn, openai_client):
    """Step 3: Test vector search."""
    print("\n" + "=" * 60)
    print("Step 3: Test Vector Search")
    print("=" * 60)
    
    schema = DB_CONFIG["schema"]
    test_queries = [
        "What is the risk for blood pressure 145/92?",
        "How should I rate a patient with high cholesterol LDL 180?",
    ]
    
    for question in test_queries:
        print(f"\n🔍 Query: {question}")
        print("-" * 50)
        
        # Generate query embedding
        query_embedding = get_embedding(openai_client, question)
        
        # Vector similarity search
        rows = await conn.fetch(f"""
            SELECT 
                policy_id,
                policy_name,
                criteria_id,
                risk_level,
                content,
                1 - (embedding <=> $1::vector) as similarity
            FROM {schema}.policy_chunks
            ORDER BY embedding <=> $1::vector
            LIMIT 3
        """, str(query_embedding))
        
        if not rows:
            print("   No results found")
            continue
        
        for i, row in enumerate(rows, 1):
            print(f"\n   [{i}] {row['policy_name']}")
            print(f"       Policy ID: {row['policy_id']}")
            print(f"       Criteria: {row['criteria_id'] or 'N/A'}")
            print(f"       Risk Level: {row['risk_level'] or 'N/A'}")
            print(f"       Similarity: {row['similarity']:.4f}")
            # Show first 150 chars of content
            content_preview = row['content'][:150].replace('\n', ' ')
            print(f"       Content: {content_preview}...")
    
    print("\n✅ Vector search working!")


async def test_filtered_search(conn, openai_client):
    """Step 4: Test filtered search by category."""
    print("\n" + "=" * 60)
    print("Step 4: Test Filtered Search (by category)")
    print("=" * 60)
    
    schema = DB_CONFIG["schema"]
    question = "What are the risk factors?"
    category_filter = "cardiovascular"
    
    print(f"\n🔍 Query: {question}")
    print(f"   Filter: category = '{category_filter}'")
    print("-" * 50)
    
    query_embedding = get_embedding(openai_client, question)
    
    # Filtered vector search
    rows = await conn.fetch(f"""
        SELECT 
            policy_id,
            policy_name,
            category,
            criteria_id,
            risk_level,
            content,
            1 - (embedding <=> $1::vector) as similarity
        FROM {schema}.policy_chunks
        WHERE category = $2
        ORDER BY embedding <=> $1::vector
        LIMIT 3
    """, str(query_embedding), category_filter)
    
    if not rows:
        print("   No results found (may need more test data)")
    else:
        for i, row in enumerate(rows, 1):
            print(f"\n   [{i}] {row['policy_name']} (category: {row['category']})")
            print(f"       Similarity: {row['similarity']:.4f}")
        print("\n✅ Filtered search working!")


async def test_similarity_threshold(conn, openai_client):
    """Step 5: Test similarity threshold filtering."""
    print("\n" + "=" * 60)
    print("Step 5: Test Similarity Threshold")
    print("=" * 60)
    
    schema = DB_CONFIG["schema"]
    threshold = float(os.getenv("RAG_SIMILARITY_THRESHOLD", 0.7))
    question = "What is the risk for blood pressure 145/92?"
    
    print(f"\n🔍 Query: {question}")
    print(f"   Threshold: {threshold}")
    print("-" * 50)
    
    query_embedding = get_embedding(openai_client, question)
    
    # Search with threshold
    rows = await conn.fetch(f"""
        SELECT 
            policy_id,
            policy_name,
            criteria_id,
            1 - (embedding <=> $1::vector) as similarity
        FROM {schema}.policy_chunks
        WHERE 1 - (embedding <=> $1::vector) >= $2
        ORDER BY embedding <=> $1::vector
        LIMIT 5
    """, str(query_embedding), threshold)
    
    print(f"   Results above threshold: {len(rows)}")
    for row in rows:
        print(f"   - {row['policy_name']}: {row['similarity']:.4f}")
    
    print("\n✅ Similarity threshold working!")


async def test_hybrid_search(conn, openai_client):
    """Step 6: Test hybrid search (keyword + semantic)."""
    print("\n" + "=" * 60)
    print("Step 6: Test Hybrid Search")
    print("=" * 60)
    
    schema = DB_CONFIG["schema"]
    
    # Check if pg_trgm is available
    trgm_exists = await conn.fetchval("""
        SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')
    """)
    
    if not trgm_exists:
        print("⚠️  Skipping hybrid search test (pg_trgm not installed)")
        return
    
    question = "blood pressure hypertension"
    keyword = "blood pressure"
    
    print(f"\n🔍 Query: {question}")
    print(f"   Keyword: '{keyword}'")
    print("-" * 50)
    
    query_embedding = get_embedding(openai_client, question)
    
    # Hybrid search: combine keyword similarity and vector similarity
    rows = await conn.fetch(f"""
        SELECT 
            policy_id,
            policy_name,
            criteria_id,
            content,
            similarity(content, $2) as keyword_score,
            1 - (embedding <=> $1::vector) as semantic_score,
            (0.3 * similarity(content, $2) + 0.7 * (1 - (embedding <=> $1::vector))) as hybrid_score
        FROM {schema}.policy_chunks
        WHERE content ILIKE '%' || $2 || '%'
           OR 1 - (embedding <=> $1::vector) >= 0.5
        ORDER BY hybrid_score DESC
        LIMIT 5
    """, str(query_embedding), keyword)
    
    if not rows:
        print("   No results found")
    else:
        for i, row in enumerate(rows, 1):
            print(f"\n   [{i}] {row['policy_name']}")
            print(f"       Keyword Score: {row['keyword_score']:.4f}")
            print(f"       Semantic Score: {row['semantic_score']:.4f}")
            print(f"       Hybrid Score: {row['hybrid_score']:.4f}")
    
    print("\n✅ Hybrid search working!")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PostgreSQL RAG Integration Test")
    print("=" * 60)
    
    # Step 1: Test connection
    conn = await test_connection()
    if not conn:
        print("\n❌ Tests failed: Could not connect to database")
        return
    
    test_policy_ids = []
    try:
        # Initialize OpenAI client
        print("\n⏳ Initializing Azure OpenAI client...")
        openai_client = get_openai_client()
        print("✅ OpenAI client ready")

        # Step 2: Index policies
        # Also collect test policy IDs for cleanup
        policies_path = "prompts/life-health-underwriting-policies.json"
        with open(policies_path) as f:
            data = json.load(f)
        test_policy_ids = [p["id"] for p in data["policies"][:2]]
        await index_policies(conn, openai_client, limit=2)

        # Step 3: Test vector search
        await test_vector_search(conn, openai_client)

        # Step 4: Test filtered search
        await test_filtered_search(conn, openai_client)

        # Step 5: Test similarity threshold
        await test_similarity_threshold(conn, openai_client)

        # Step 6: Test hybrid search
        await test_hybrid_search(conn, openai_client)

        print("\n" + "=" * 60)
        print("🎉 All Tests Passed!")
        print("=" * 60)

    finally:
        # Cleanup: delete test policy data
        if test_policy_ids:
            print("\n⏳ Cleaning up test data...")
            schema = DB_CONFIG["schema"]
            await conn.execute(f"DELETE FROM {schema}.policy_chunks WHERE policy_id = ANY($1)", test_policy_ids)
            print(f"✅ Deleted test data for policies: {', '.join(test_policy_ids)}")
        await conn.close()
        print("\n✅ Connection closed")


if __name__ == "__main__":
    asyncio.run(main())
