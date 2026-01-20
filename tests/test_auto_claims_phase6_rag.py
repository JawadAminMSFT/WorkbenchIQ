"""
Phase 6 Tests: RAG for Claims Policies
Feature: 007-automotive-claims-multimodal

Tests for the claims policy RAG system including:
- ClaimsPolicyChunker
- ClaimsPolicyChunkRepository
- ClaimsPolicyIndexer
- ClaimsPolicySearchService
"""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import asdict

from app.claims.chunker import ClaimsPolicyChunk, ClaimsPolicyChunker
from app.claims.indexer import ClaimsPolicyChunkRepository, ClaimsPolicyIndexer
from app.claims.search import ClaimsPolicySearchService, ClaimsSearchResult, get_claims_policy_context
from app.claims.policies import ClaimsPolicyLoader


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_policies_path():
    """Path to test claims policies."""
    return Path(__file__).parent.parent / "data" / "automotive-claims-policies.json"


@pytest.fixture
def policy_loader(sample_policies_path):
    """Initialize policy loader."""
    loader = ClaimsPolicyLoader()
    loader.load_policies(str(sample_policies_path))
    return loader


@pytest.fixture
def sample_policy(policy_loader):
    """Get a sample damage severity policy."""
    return policy_loader.get_policy_by_id("DMG-SEV-001")


@pytest.fixture
def all_policies(policy_loader):
    """Get all policies."""
    return list(policy_loader._policies_by_id.values())


@pytest.fixture
def chunker():
    """Initialize chunker."""
    return ClaimsPolicyChunker()


@pytest.fixture
def mock_settings():
    """Mock settings for indexer/search tests."""
    settings = MagicMock()
    settings.openai = MagicMock()
    settings.rag = MagicMock()
    settings.rag.top_k = 5
    settings.rag.similarity_threshold = 0.5
    return settings


# ============================================================================
# ClaimsPolicyChunker Tests
# ============================================================================

class TestClaimsPolicyChunker:
    """Tests for ClaimsPolicyChunker."""

    def test_chunk_policy_creates_header_chunk(self, chunker, sample_policy):
        """T073: Chunker creates policy header chunk."""
        chunks = chunker.chunk_policy(sample_policy)

        header_chunks = [c for c in chunks if c.chunk_type == "policy_header"]
        assert len(header_chunks) == 1

        header = header_chunks[0]
        assert header.policy_id == sample_policy.id
        assert header.policy_name == sample_policy.name
        assert header.chunk_sequence == 0
        assert sample_policy.name in header.content

    def test_chunk_policy_creates_criteria_chunks(self, chunker, sample_policy):
        """T074: Chunker creates chunks for each criterion."""
        chunks = chunker.chunk_policy(sample_policy)

        criteria_chunks = [c for c in chunks if c.chunk_type == "criteria"]
        assert len(criteria_chunks) == len(sample_policy.criteria)

        for chunk in criteria_chunks:
            assert chunk.criteria_id is not None
            assert chunk.severity is not None or chunk.risk_level is not None or chunk.liability_determination is not None
            assert chunk.category == sample_policy.category

    def test_chunk_policy_creates_modifying_factor_chunks(self, chunker, sample_policy):
        """T075: Chunker creates chunks for modifying factors if present."""
        chunks = chunker.chunk_policy(sample_policy)

        if sample_policy.modifying_factors:
            factor_chunks = [c for c in chunks if c.chunk_type == "modifying_factor"]
            # Modifying factors are combined into one chunk with metadata about all factors
            assert len(factor_chunks) == 1
            # The chunk should contain metadata about all factors
            assert factor_chunks[0].metadata.get("factor_count") == len(sample_policy.modifying_factors)

    def test_chunk_policy_includes_metadata(self, chunker, sample_policy):
        """Chunk metadata includes source policy info."""
        chunks = chunker.chunk_policy(sample_policy)

        for chunk in chunks:
            assert chunk.policy_version == chunker.policy_version
            assert chunk.category == sample_policy.category

    def test_chunk_policy_generates_content_hash(self, chunker, sample_policy):
        """Each chunk has a content hash."""
        chunks = chunker.chunk_policy(sample_policy)

        hashes = set()
        for chunk in chunks:
            assert chunk.content_hash is not None
            assert len(chunk.content_hash) == 64  # SHA-256 hex
            hashes.add(chunk.content_hash)

        # All hashes should be unique
        assert len(hashes) == len(chunks)

    def test_chunk_policies_processes_multiple(self, chunker, all_policies):
        """chunk_policies() processes all policies."""
        chunks = chunker.chunk_policies(all_policies)

        assert len(chunks) > len(all_policies)  # Multiple chunks per policy

        policy_ids = {c.policy_id for c in chunks}
        assert policy_ids == {p.id for p in all_policies}

    def test_chunk_has_correct_sequence_numbers(self, chunker, sample_policy):
        """Chunks have sequential sequence numbers."""
        chunks = chunker.chunk_policy(sample_policy)

        sequences = [c.chunk_sequence for c in chunks]
        expected = list(range(len(chunks)))
        assert sequences == expected


# ============================================================================
# ClaimsPolicyChunkRepository Tests
# ============================================================================

class TestClaimsPolicyChunkRepository:
    """Tests for ClaimsPolicyChunkRepository."""

    @pytest.fixture
    def repository(self):
        """Create repository instance."""
        return ClaimsPolicyChunkRepository(schema="workbenchiq")

    def test_repository_table_sql_valid(self, repository):
        """T076: Repository has valid CREATE TABLE SQL."""
        sql = repository.CREATE_TABLE_SQL
        assert "claim_policy_chunks" in sql
        assert "vector(1536)" in sql
        assert "policy_id" in sql
        assert "embedding" in sql

    @pytest.mark.asyncio
    async def test_repository_initialize_table(self, repository):
        """T077: Repository can initialize table."""
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn)))

        with patch("app.claims.indexer.get_pool", return_value=mock_pool):
            await repository.initialize_table()
            mock_conn.execute.assert_called()

    @pytest.mark.asyncio
    async def test_repository_insert_chunks(self, repository, chunker, sample_policy):
        """Repository can insert chunks."""
        chunks = chunker.chunk_policy(sample_policy)

        # Add mock embeddings
        for chunk in chunks:
            chunk.embedding = [0.1] * 1536

        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn)))

        with patch("app.claims.indexer.get_pool", return_value=mock_pool):
            result = await repository.insert_chunks(chunks)
            assert result == len(chunks)

    @pytest.mark.asyncio
    async def test_repository_delete_by_policy(self, repository):
        """Repository can delete chunks by policy ID."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=5)
        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn)))

        with patch("app.claims.indexer.get_pool", return_value=mock_pool):
            deleted = await repository.delete_chunks_by_policy("DMG-SEV-001")
            assert deleted == 5

    @pytest.mark.asyncio
    async def test_repository_get_chunk_count(self, repository):
        """Repository can get chunk count."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=42)
        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn)))

        with patch("app.claims.indexer.get_pool", return_value=mock_pool):
            count = await repository.get_chunk_count()
            assert count == 42


# ============================================================================
# ClaimsPolicyIndexer Tests
# ============================================================================

class TestClaimsPolicyIndexer:
    """Tests for ClaimsPolicyIndexer."""

    @pytest.fixture
    def indexer(self, mock_settings, sample_policies_path):
        """Create indexer instance."""
        return ClaimsPolicyIndexer(
            settings=mock_settings,
            policies_path=str(sample_policies_path),
        )

    def test_indexer_initialization(self, indexer):
        """T078: Indexer initializes with settings."""
        assert indexer.chunker is not None
        assert indexer.embedding_service is not None
        assert indexer.repository is not None

    @pytest.mark.asyncio
    async def test_indexer_generates_embeddings(self, indexer, chunker, sample_policy):
        """T079: Indexer generates embeddings for chunks."""
        chunks = chunker.chunk_policy(sample_policy)

        mock_embeddings = [[0.1] * 1536 for _ in chunks]
        with patch.object(indexer.embedding_service, "get_embeddings_batch", return_value=mock_embeddings):
            result = indexer._add_embeddings(chunks)

            for chunk in result:
                assert chunk.embedding is not None
                assert len(chunk.embedding) == 1536

    @pytest.mark.asyncio
    async def test_indexer_index_policies_pipeline(self, indexer, all_policies):
        """Indexer runs full pipeline: chunk -> embed -> store."""
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn)))

        with patch("app.claims.indexer.get_pool", return_value=mock_pool):
            with patch.object(indexer.embedding_service, "get_embeddings_batch") as mock_embed:
                mock_embed.return_value = [[0.1] * 1536] * 100  # Return enough embeddings

                total = await indexer.index_policies(all_policies)
                assert total > 0
                mock_embed.assert_called()


# ============================================================================
# ClaimsPolicySearchService Tests
# ============================================================================

class TestClaimsPolicySearchService:
    """Tests for ClaimsPolicySearchService."""

    @pytest.fixture
    def search_service(self, mock_settings):
        """Create search service instance."""
        return ClaimsPolicySearchService(settings=mock_settings)

    def test_search_service_initialization(self, search_service):
        """T080: Search service initializes correctly."""
        assert search_service.embedding_service is not None
        assert search_service.table == "workbenchiq.claim_policy_chunks"

    @pytest.mark.asyncio
    async def test_semantic_search(self, search_service):
        """T081: Semantic search returns results."""
        mock_rows = [
            {
                "id": "chunk-1",
                "policy_id": "DMG-SEV-001",
                "policy_name": "Vehicle Damage Severity Classification",
                "chunk_type": "criteria",
                "category": "damage_assessment",
                "subcategory": "severity",
                "criteria_id": "CRIT-001",
                "severity": "Minor",
                "risk_level": None,
                "liability_determination": None,
                "action_recommendation": "Proceed with repair",
                "content": "Minor damage includes scratches and dents",
                "metadata": "{}",
                "similarity": 0.85,
            }
        ]

        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=mock_rows)
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn)))

        with patch("app.claims.search.get_pool", return_value=mock_pool):
            with patch.object(search_service.embedding_service, "get_embedding", return_value=[0.1] * 1536):
                results = await search_service.semantic_search("vehicle damage")

                assert len(results) == 1
                assert isinstance(results[0], ClaimsSearchResult)
                assert results[0].policy_id == "DMG-SEV-001"
                assert results[0].similarity == 0.85

    @pytest.mark.asyncio
    async def test_filtered_search_by_category(self, search_service):
        """T082: Filtered search filters by category."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn)))

        with patch("app.claims.search.get_pool", return_value=mock_pool):
            with patch.object(search_service.embedding_service, "get_embedding", return_value=[0.1] * 1536):
                await search_service.filtered_search(
                    query="damage assessment",
                    category="damage_assessment",
                )

                # Check that category was included in query params
                call_args = mock_conn.fetch.call_args
                assert "damage_assessment" in call_args[0]

    @pytest.mark.asyncio
    async def test_filtered_search_by_severity(self, search_service):
        """T083: Filtered search filters by severity."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn)))

        with patch("app.claims.search.get_pool", return_value=mock_pool):
            with patch.object(search_service.embedding_service, "get_embedding", return_value=[0.1] * 1536):
                await search_service.filtered_search(
                    query="heavy damage",
                    severity="Heavy",
                )

                call_args = mock_conn.fetch.call_args
                assert "Heavy" in call_args[0]

    @pytest.mark.asyncio
    async def test_hybrid_search(self, search_service):
        """Hybrid search combines vector and keyword search."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn)))

        with patch("app.claims.search.get_pool", return_value=mock_pool):
            with patch.object(search_service.embedding_service, "get_embedding", return_value=[0.1] * 1536):
                await search_service.hybrid_search(
                    query="frame damage assessment",
                    category="damage_assessment",
                    keyword_boost=0.3,
                )

                # Verify SQL includes text search
                call_sql = mock_conn.fetch.call_args[0][0]
                assert "ts_rank" in call_sql or "plainto_tsquery" in call_sql

    @pytest.mark.asyncio
    async def test_search_by_policy_category(self, search_service):
        """Convenience method searches by category."""
        with patch.object(search_service, "filtered_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            await search_service.search_by_policy_category(
                query="rear-end collision",
                category="liability",
                top_k=5,
            )

            mock_search.assert_called_once_with(
                query="rear-end collision",
                category="liability",
                top_k=5,
            )

    @pytest.mark.asyncio
    async def test_get_relevant_policies_for_claim(self, search_service):
        """Gets relevant policies across categories for a claim."""
        with patch.object(search_service, "search_by_policy_category", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            results = await search_service.get_relevant_policies_for_claim(
                damage_description="Significant front-end damage",
                incident_description="Rear-end collision at intersection",
                estimate_amount=5000.0,
            )

            assert "damage_assessment" in results
            assert "liability" in results
            assert "fraud_detection" in results
            assert "payout_calculation" in results


# ============================================================================
# get_claims_policy_context Tests
# ============================================================================

class TestGetClaimsPolicyContext:
    """Tests for get_claims_policy_context helper."""

    @pytest.mark.asyncio
    async def test_returns_formatted_context(self, mock_settings):
        """T084: Context helper returns formatted string."""
        mock_result = ClaimsSearchResult(
            chunk_id="chunk-1",
            policy_id="DMG-SEV-001",
            policy_name="Vehicle Damage Severity",
            chunk_type="criteria",
            category="damage_assessment",
            subcategory="severity",
            criteria_id="CRIT-001",
            severity="Minor",
            risk_level=None,
            liability_determination=None,
            action_recommendation="Proceed",
            content="Minor damage policy content",
            similarity=0.85,
            metadata={},
        )

        with patch("app.claims.search.ClaimsPolicySearchService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.semantic_search = AsyncMock(return_value=[mock_result])

            context = await get_claims_policy_context(
                settings=mock_settings,
                query="damage assessment",
            )

            assert "Relevant Automotive Claims Policies" in context
            assert "DMG-SEV-001" in context
            assert "Vehicle Damage Severity" in context

    @pytest.mark.asyncio
    async def test_returns_no_results_message(self, mock_settings):
        """T085: Context helper returns message when no results."""
        with patch("app.claims.search.ClaimsPolicySearchService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.semantic_search = AsyncMock(return_value=[])

            context = await get_claims_policy_context(
                settings=mock_settings,
                query="irrelevant query",
            )

            assert "No relevant claims policies found" in context


# ============================================================================
# Integration Tests (Skipped without DB)
# ============================================================================

@pytest.mark.skip(reason="Requires PostgreSQL with pgvector")
class TestClaimsRAGIntegration:
    """Integration tests requiring real PostgreSQL database."""

    @pytest.mark.asyncio
    async def test_full_indexing_pipeline(self):
        """Full pipeline: load -> chunk -> embed -> store -> search."""
        pass

    @pytest.mark.asyncio
    async def test_search_returns_relevant_chunks(self):
        """Search returns chunks relevant to query."""
        pass
