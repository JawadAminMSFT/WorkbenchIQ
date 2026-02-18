"""
Mortgage Policy Chunk Storage - PostgreSQL storage for mortgage policy chunks.

Provides vector storage and similarity search for mortgage underwriting policies,
using pgvector for efficient nearest-neighbor search.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Iterator

from app.mortgage.rag.chunker import MortgagePolicyChunk


@dataclass
class SearchResult:
    """Result from a similarity search."""
    
    chunk_id: str
    content: str
    source: str
    score: float
    chunk_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class MortgagePolicyChunkStorage:
    """
    PostgreSQL storage for mortgage policy chunks with vector search.
    
    Uses the mortgage_policy_chunks table with:
    - chunk_text: The chunk content
    - embedding: 1536-dimensional vector (text-embedding-3-small)
    - source: Policy source identifier
    - chunk_index: Order within source
    - metadata: JSONB for additional fields
    """
    
    TABLE_NAME = "mortgage_policy_chunks"
    SCHEMA = "public"
    EMBEDDING_DIM = 1536
    
    # SQL for creating the table
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS {schema}.{table} (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        chunk_text TEXT NOT NULL,
        embedding VECTOR({dim}) NOT NULL,
        source VARCHAR(200) NOT NULL,
        chunk_index INTEGER NOT NULL DEFAULT 0,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_{table}_embedding 
    ON {schema}.{table} USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
    
    CREATE INDEX IF NOT EXISTS idx_{table}_source
    ON {schema}.{table}(source);
    """
    
    # SQL for inserting a chunk
    INSERT_SQL = """
    INSERT INTO {schema}.{table} 
    (id, chunk_text, embedding, source, chunk_index, metadata)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id;
    """
    
    # SQL for similarity search
    SEARCH_SQL = """
    SELECT 
        id,
        chunk_text,
        source,
        chunk_index,
        metadata,
        1 - (embedding <=> %s::vector) AS similarity_score
    FROM {schema}.{table}
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
    """
    
    # SQL for filtered search
    SEARCH_FILTERED_SQL = """
    SELECT 
        id,
        chunk_text,
        source,
        chunk_index,
        metadata,
        1 - (embedding <=> %s::vector) AS similarity_score
    FROM {schema}.{table}
    WHERE source = %s
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
    """
    
    def __init__(
        self,
        db_client: Any,
        schema: str = "public",
        table_name: Optional[str] = None,
    ):
        """
        Initialize storage.
        
        Args:
            db_client: Database connection/pool with execute() method
            schema: PostgreSQL schema name
            table_name: Override default table name
        """
        self.db = db_client
        self.schema = schema
        self.table_name = table_name or self.TABLE_NAME
    
    def create_table(self) -> None:
        """Create the chunks table if it doesn't exist."""
        sql = self.CREATE_TABLE_SQL.format(
            schema=self.schema,
            table=self.table_name,
            dim=self.EMBEDDING_DIM,
        )
        self.db.execute(sql)
    
    def insert(self, chunk: Dict[str, Any]) -> str:
        """
        Insert a policy chunk.
        
        Args:
            chunk: Dict with chunk_text, embedding, source, chunk_index, metadata
            
        Returns:
            The generated chunk ID
        """
        chunk_id = chunk.get("id") or str(uuid.uuid4())
        
        sql = self.INSERT_SQL.format(
            schema=self.schema,
            table=self.table_name,
        )
        
        params = (
            chunk_id,
            chunk["chunk_text"],
            chunk["embedding"],
            chunk["source"],
            chunk.get("chunk_index", 0),
            json.dumps(chunk.get("metadata", {})),
        )
        
        self.db.execute(sql, params)
        return chunk_id
    
    def insert_batch(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple chunks efficiently.
        
        Args:
            chunks: List of chunk dicts
            
        Returns:
            List of generated chunk IDs
        """
        ids = []
        for chunk in chunks:
            chunk_id = self.insert(chunk)
            ids.append(chunk_id)
        return ids
    
    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        source_filter: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Search for similar chunks by vector similarity.
        
        Args:
            query_embedding: 1536-dimensional query vector
            top_k: Number of results to return
            source_filter: Optional filter by source
            
        Returns:
            List of SearchResult objects ordered by similarity
        """
        if source_filter:
            sql = self.SEARCH_FILTERED_SQL.format(
                schema=self.schema,
                table=self.table_name,
            )
            params = (query_embedding, source_filter, query_embedding, top_k)
        else:
            sql = self.SEARCH_SQL.format(
                schema=self.schema,
                table=self.table_name,
            )
            params = (query_embedding, query_embedding, top_k)
        
        result = self.db.execute(sql, params)
        
        # Convert to SearchResult objects
        results = []
        if hasattr(result, 'fetchall'):
            rows = result.fetchall()
        elif hasattr(result, '__iter__'):
            rows = result
        else:
            rows = []
        
        for row in rows:
            if isinstance(row, dict):
                results.append(SearchResult(
                    chunk_id=str(row["id"]),
                    content=row["chunk_text"],
                    source=row["source"],
                    score=float(row["similarity_score"]),
                    chunk_index=row.get("chunk_index", 0),
                    metadata=row.get("metadata", {}),
                ))
            else:
                # Tuple format
                results.append(SearchResult(
                    chunk_id=str(row[0]),
                    content=row[1],
                    source=row[2],
                    score=float(row[5]),
                    chunk_index=row[3],
                    metadata=row[4] if len(row) > 4 else {},
                ))
        
        return results
    
    def delete_by_source(self, source: str) -> int:
        """
        Delete all chunks from a source.
        
        Args:
            source: Source identifier to delete
            
        Returns:
            Number of rows deleted
        """
        sql = f"DELETE FROM {self.schema}.{self.table_name} WHERE source = %s"
        result = self.db.execute(sql, (source,))
        return getattr(result, 'rowcount', 0)
    
    def count(self, source_filter: Optional[str] = None) -> int:
        """
        Count chunks in storage.
        
        Args:
            source_filter: Optional filter by source
            
        Returns:
            Number of chunks
        """
        if source_filter:
            sql = f"SELECT COUNT(*) FROM {self.schema}.{self.table_name} WHERE source = %s"
            result = self.db.execute(sql, (source_filter,))
        else:
            sql = f"SELECT COUNT(*) FROM {self.schema}.{self.table_name}"
            result = self.db.execute(sql)
        
        if hasattr(result, 'fetchone'):
            row = result.fetchone()
            return row[0] if row else 0
        return 0
    
    def get_by_id(self, chunk_id: str) -> Optional[SearchResult]:
        """
        Get a chunk by ID.
        
        Args:
            chunk_id: The chunk UUID
            
        Returns:
            SearchResult or None if not found
        """
        sql = f"""
        SELECT id, chunk_text, source, chunk_index, metadata
        FROM {self.schema}.{self.table_name}
        WHERE id = %s
        """
        result = self.db.execute(sql, (chunk_id,))
        
        if hasattr(result, 'fetchone'):
            row = result.fetchone()
            if row:
                return SearchResult(
                    chunk_id=str(row[0]),
                    content=row[1],
                    source=row[2],
                    score=1.0,  # Perfect match
                    chunk_index=row[3],
                    metadata=row[4] if len(row) > 4 else {},
                )
        return None
    
    def iter_all(
        self,
        source_filter: Optional[str] = None,
        batch_size: int = 100,
    ) -> Iterator[SearchResult]:
        """
        Iterate over all chunks.
        
        Args:
            source_filter: Optional filter by source
            batch_size: Number of rows to fetch at a time
            
        Yields:
            SearchResult objects
        """
        offset = 0
        while True:
            if source_filter:
                sql = f"""
                SELECT id, chunk_text, source, chunk_index, metadata
                FROM {self.schema}.{self.table_name}
                WHERE source = %s
                ORDER BY chunk_index
                LIMIT %s OFFSET %s
                """
                result = self.db.execute(sql, (source_filter, batch_size, offset))
            else:
                sql = f"""
                SELECT id, chunk_text, source, chunk_index, metadata
                FROM {self.schema}.{self.table_name}
                ORDER BY source, chunk_index
                LIMIT %s OFFSET %s
                """
                result = self.db.execute(sql, (batch_size, offset))
            
            rows = []
            if hasattr(result, 'fetchall'):
                rows = result.fetchall()
            
            if not rows:
                break
            
            for row in rows:
                yield SearchResult(
                    chunk_id=str(row[0]),
                    content=row[1],
                    source=row[2],
                    score=1.0,
                    chunk_index=row[3],
                    metadata=row[4] if len(row) > 4 else {},
                )
            
            offset += batch_size
