#!/usr/bin/env python
"""
Index Mortgage Policies Script

Indexes mortgage underwriting policies (OSFI B-20, etc.) into PostgreSQL
using the unified indexer pattern.

Usage:
    python scripts/index_mortgage_policies.py
    
Environment:
    Requires AZURE_OPENAI_* and POSTGRES_* environment variables
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import load_settings
from app.rag.unified_indexer import UnifiedPolicyIndexer, PERSONA_CONFIG
from app.utils import setup_logging

logger = setup_logging()


def main():
    """Index mortgage underwriting policies."""
    persona = "mortgage_underwriting"
    
    logger.info(f"Starting indexing for persona: {persona}")
    
    # Verify config exists
    if persona not in PERSONA_CONFIG:
        logger.error(f"Persona '{persona}' not found in PERSONA_CONFIG")
        sys.exit(1)
    
    config = PERSONA_CONFIG[persona]
    logger.info(f"Policy file: {config['policies_path']}")
    logger.info(f"Target table: {config['table_name']}")
    
    # Check policy file exists
    policy_path = project_root / config["policies_path"]
    if not policy_path.exists():
        logger.error(f"Policy file not found: {policy_path}")
        sys.exit(1)
    
    try:
        # Initialize settings
        settings = load_settings()
        
        # Create indexer
        indexer = UnifiedPolicyIndexer(settings=settings)
        
        # Index the persona
        result = indexer.index_persona(persona)
        
        logger.info(f"Indexing complete for {persona}")
        logger.info(f"Chunks indexed: {result.get('chunks_indexed', 0)}")
        logger.info(f"Time taken: {result.get('duration_seconds', 0):.2f}s")
        
        return result
        
    except Exception as e:
        logger.exception(f"Error indexing {persona}: {e}")
        sys.exit(1)


async def main_async():
    """Async version of indexing."""
    persona = "mortgage_underwriting"
    
    logger.info(f"Starting async indexing for persona: {persona}")
    
    try:
        settings = load_settings()
        indexer = UnifiedPolicyIndexer(settings=settings)
        
        result = await indexer.index_persona_async(persona)
        
        logger.info(f"Async indexing complete for {persona}")
        logger.info(f"Chunks indexed: {result.get('chunks_indexed', 0)}")
        
        return result
        
    except Exception as e:
        logger.exception(f"Error in async indexing: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Index mortgage underwriting policies"
    )
    parser.add_argument(
        "--async",
        dest="use_async",
        action="store_true",
        help="Use async indexing",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config without indexing",
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("Dry run - validating configuration")
        config = PERSONA_CONFIG.get("mortgage_underwriting", {})
        policy_path = project_root / config.get("policies_path", "")
        
        print(f"Persona: mortgage_underwriting")
        print(f"Policy file: {config.get('policies_path')}")
        print(f"Policy file exists: {policy_path.exists()}")
        print(f"Table name: {config.get('table_name')}")
        
    elif args.use_async:
        asyncio.run(main_async())
    else:
        main()
