#!/usr/bin/env python3
"""
CLI script for indexing underwriting policies into PostgreSQL for RAG.

Usage:
    # Index all policies
    python scripts/index_policies.py

    # Index specific policies
    python scripts/index_policies.py --policy-ids CVD-BP-001 META-CHOL-001

    # Force reindex (delete existing first)
    python scripts/index_policies.py --force

    # Show index statistics
    python scripts/index_policies.py --stats

    # Use different policies file
    python scripts/index_policies.py --policies prompts/life-health-underwriting-policies.json
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.indexer import PolicyIndexer


async def main():
    parser = argparse.ArgumentParser(
        description="Index underwriting policies for RAG search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Index all policies
  %(prog)s --force                   # Force reindex all
  %(prog)s --policy-ids CVD-BP-001   # Index specific policy
  %(prog)s --stats                   # Show index statistics
        """,
    )
    
    parser.add_argument(
        "--policies",
        default="data/life-health-underwriting-policies.json",
        help="Path to policies JSON file (default: data/life-health-underwriting-policies.json)",
    )
    
    parser.add_argument(
        "--policy-ids",
        nargs="*",
        help="Specific policy IDs to index (indexes all if not specified)",
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reindex - delete existing chunks before indexing",
    )
    
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show index statistics instead of indexing",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    
    args = parser.parse_args()
    
    # Validate policies file exists
    policies_path = Path(args.policies)
    if not policies_path.exists() and not args.stats:
        print(f"❌ Policies file not found: {policies_path}")
        print("   Check the --policies argument or create the file.")
        sys.exit(1)
    
    # Create indexer
    indexer = PolicyIndexer(policies_path=policies_path)
    
    try:
        if args.stats:
            # Show statistics
            print("\n📊 Index Statistics")
            print("=" * 40)
            
            stats = await indexer.get_index_stats()
            
            print(f"Total chunks:  {stats['total_chunks']}")
            print(f"Total policies: {stats['policy_count']}")
            
            print("\nChunks by type:")
            for chunk_type, count in stats.get('chunks_by_type', {}).items():
                print(f"  {chunk_type}: {count}")
            
            print("\nChunks by category:")
            for category, count in stats.get('chunks_by_category', {}).items():
                print(f"  {category}: {count}")
        
        else:
            # Run indexing
            metrics = await indexer.index_policies(
                policy_ids=args.policy_ids,
                force_reindex=args.force,
            )
            
            if metrics.get("status") == "success":
                print(f"\n✅ Indexing complete!")
                print(f"   Policies: {metrics['policies_indexed']}")
                print(f"   Chunks: {metrics['chunks_stored']}")
                print(f"   Time: {metrics['total_time_seconds']}s")
            else:
                print(f"\n⚠️  Indexing completed with status: {metrics.get('status')}")
                if metrics.get('reason'):
                    print(f"   Reason: {metrics['reason']}")
    
    except KeyboardInterrupt:
        print("\n\n[!] Indexing cancelled by user")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n[ERROR] Indexing failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
