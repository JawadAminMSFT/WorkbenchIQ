#!/usr/bin/env python
"""
Index Automotive Claims Policies into PostgreSQL for RAG.

This script loads claims policies from JSON, chunks them, generates embeddings,
and stores them in the claim_policy_chunks table for semantic search.

Usage:
    python scripts/index_claims_policies.py
    python scripts/index_claims_policies.py --policies-path data/automotive-claims-policies.json
    python scripts/index_claims_policies.py --force-reindex
    python scripts/index_claims_policies.py --policy-ids DMG-SEV-001 LIA-001
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.claims.indexer import ClaimsPolicyIndexer
from app.claims.policies import ClaimsPolicyLoader
from app.utils import setup_logging

logger = setup_logging()


async def main():
    parser = argparse.ArgumentParser(
        description="Index automotive claims policies for RAG search"
    )
    parser.add_argument(
        "--policies-path",
        type=str,
        default="prompts/automotive-claims-policies.json",
        help="Path to claims policies JSON file",
    )
    parser.add_argument(
        "--policy-ids",
        nargs="+",
        type=str,
        default=None,
        help="Specific policy IDs to index (default: all)",
    )
    parser.add_argument(
        "--force-reindex",
        action="store_true",
        help="Delete existing chunks and reindex all",
    )
    parser.add_argument(
        "--schema",
        type=str,
        default="workbenchiq",
        help="PostgreSQL schema name",
    )

    args = parser.parse_args()

    # Validate policies path
    policies_path = Path(args.policies_path)
    if not policies_path.exists():
        logger.error(f"Policies file not found: {policies_path}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Automotive Claims Policy Indexer")
    logger.info("=" * 60)
    logger.info(f"Policies file: {policies_path}")
    logger.info(f"Schema: {args.schema}")
    logger.info(f"Force reindex: {args.force_reindex}")
    if args.policy_ids:
        logger.info(f"Policy IDs: {args.policy_ids}")
    logger.info("-" * 60)

    # Load settings
    settings = get_settings()

    # Initialize indexer
    indexer = ClaimsPolicyIndexer(
        settings=settings,
        policies_path=str(policies_path),
        schema=args.schema,
    )

    try:
        # Initialize database table
        logger.info("Initializing database table...")
        await indexer.initialize()

        # Handle force reindex
        if args.force_reindex:
            logger.info("Force reindex: deleting all existing chunks...")
            deleted = await indexer.repository.delete_all_chunks()
            logger.info(f"Deleted {deleted} existing chunks")

        # Load policies
        logger.info("Loading claims policies...")
        loader = ClaimsPolicyLoader(str(policies_path))
        all_policies = loader.load_policies()

        # Filter by policy IDs if specified
        if args.policy_ids:
            policies = [p for p in all_policies if p.id in args.policy_ids]
            if len(policies) != len(args.policy_ids):
                found = {p.id for p in policies}
                missing = set(args.policy_ids) - found
                logger.warning(f"Policy IDs not found: {missing}")
        else:
            policies = all_policies

        logger.info(f"Found {len(policies)} policies to index")

        # Index policies
        total_chunks = await indexer.index_policies(policies)

        logger.info("-" * 60)
        logger.info(f"Indexing complete: {total_chunks} chunks created")

        # Verify chunk count
        chunk_count = await indexer.repository.get_chunk_count()
        logger.info(f"Total chunks in database: {chunk_count}")

        logger.info("=" * 60)
        logger.info("SUCCESS")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
