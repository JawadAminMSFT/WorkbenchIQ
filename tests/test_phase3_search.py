#!/usr/bin/env python3
"""
Test script for Phase 3: Semantic Search & RAG Query.

Tests:
1. Basic semantic search
2. Filtered search with category inference
3. Intelligent search with auto-inference
4. Context assembly

Checkpoint: Can query "blood pressure 145/92" and get relevant CVD-BP-001 chunks
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from app.config import Settings
from app.database.pool import init_pool, close_pool
from app.database.settings import DatabaseSettings
from app.rag.search import PolicySearchService
from app.rag.inference import CategoryInference
from app.rag.context import RAGContextBuilder


async def test_semantic_search(search_service: PolicySearchService):
    """Test basic semantic search."""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Semantic Search")
    print("=" * 60)
    
    query = "blood pressure 145/92"
    print(f"Query: '{query}'")
    
    results = await search_service.semantic_search(query, top_k=5)
    
    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. [{result.policy_id}] {result.policy_name}")
        print(f"   Type: {result.chunk_type} | Category: {result.category}")
        print(f"   Similarity: {result.similarity:.4f}")
        print(f"   Content: {result.content[:150]}...")
        if result.action_recommendation:
            print(f"   Action: {result.action_recommendation[:100]}...")
    
    # Checkpoint: Should find CVD-BP-001
    cvd_found = any(r.policy_id == "CVD-BP-001" for r in results)
    print(f"\n[CHECKPOINT] CVD-BP-001 found: {'PASS' if cvd_found else 'FAIL'}")
    return cvd_found


async def test_category_inference(settings: Settings):
    """Test category inference from queries."""
    print("\n" + "=" * 60)
    print("TEST 2: Category Inference")
    print("=" * 60)
    
    inference = CategoryInference(settings.openai)
    
    test_queries = [
        ("blood pressure 145/92", ["cardiovascular"]),
        ("cholesterol level 250", ["metabolic"]),
        ("BMI of 32", ["metabolic"]),
        ("diabetes type 2", ["endocrine"]),
        ("family history of cancer", ["family_history"]),
        ("smoking 20 cigarettes daily", ["lifestyle"]),
        ("heart rate irregular", ["cardiovascular"]),
    ]
    
    all_passed = True
    for query, expected_categories in test_queries:
        result = inference.infer_from_keywords(query)
        matched = any(c in expected_categories for c in result.categories)
        status = "PASS" if matched else "FAIL"
        if not matched:
            all_passed = False
        print(f"Query: '{query}'")
        print(f"  Inferred: {result.categories} (expected: {expected_categories}) [{status}]")
    
    print(f"\n[CHECKPOINT] Category inference: {'PASS' if all_passed else 'FAIL'}")
    return all_passed


async def test_intelligent_search(search_service: PolicySearchService):
    """Test intelligent search with auto-inference."""
    print("\n" + "=" * 60)
    print("TEST 3: Intelligent Search with Category Inference")
    print("=" * 60)
    
    query = "applicant has high cholesterol LDL 180"
    print(f"Query: '{query}'")
    
    results, inferred = await search_service.intelligent_search(query, top_k=5)
    
    print(f"\nInferred context:")
    print(f"  Categories: {inferred.categories}")
    print(f"  Subcategories: {inferred.subcategories}")
    print(f"  Risk levels: {inferred.risk_levels}")
    print(f"  Confidence: {inferred.confidence:.2f}")
    print(f"  Method: {inferred.method}")
    
    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. [{result.policy_id}] {result.chunk_type} - similarity: {result.similarity:.4f}")
    
    # Should find metabolic/cholesterol policies
    metabolic_found = any(r.category == "metabolic" for r in results)
    print(f"\n[CHECKPOINT] Metabolic policies found: {'PASS' if metabolic_found else 'FAIL'}")
    return metabolic_found


async def test_context_assembly(search_service: PolicySearchService):
    """Test context assembly for LLM prompts."""
    print("\n" + "=" * 60)
    print("TEST 4: Context Assembly")
    print("=" * 60)
    
    query = "blood pressure 145/92 with family history of heart disease"
    print(f"Query: '{query}'")
    
    # Get search results
    results = await search_service.semantic_search(query, top_k=5)
    
    # Assemble context
    builder = RAGContextBuilder(max_tokens=2000)
    context = builder.assemble_context(results, query=query)
    
    print(f"\nContext Stats:")
    print(f"  Chunks included: {context.chunks_included}")
    print(f"  Chunks truncated: {context.chunks_truncated}")
    print(f"  Total tokens: {context.total_tokens}")
    print(f"  Categories covered: {context.categories_covered}")
    
    print(f"\nCitations ({len(context.citations)}):")
    for citation in context.citations[:5]:
        print(f"  - {citation}")
    
    print(f"\nContext preview (first 500 chars):")
    print("-" * 40)
    print(context.context_text[:500])
    print("-" * 40)
    
    success = context.chunks_included > 0 and len(context.citations) > 0
    print(f"\n[CHECKPOINT] Context assembly: {'PASS' if success else 'FAIL'}")
    return success


async def main():
    """Run all Phase 3 tests."""
    print("=" * 60)
    print("PHASE 3: Semantic Search & RAG Query - Test Suite")
    print("=" * 60)
    
    # Load settings
    from app.config import load_settings
    settings = load_settings()
    db_settings = DatabaseSettings.from_env()
    
    # Initialize database pool
    print("\nInitializing database connection...")
    await init_pool(db_settings)
    
    try:
        # Create search service
        search_service = PolicySearchService(settings)
        
        # Run tests
        results = []
        
        results.append(("Semantic Search", await test_semantic_search(search_service)))
        results.append(("Category Inference", await test_category_inference(settings)))
        results.append(("Intelligent Search", await test_intelligent_search(search_service)))
        results.append(("Context Assembly", await test_context_assembly(search_service)))
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        all_passed = True
        for name, passed in results:
            status = "PASS" if passed else "FAIL"
            if not passed:
                all_passed = False
            print(f"  {name}: {status}")
        
        print("\n" + "=" * 60)
        if all_passed:
            print("ALL TESTS PASSED - Phase 3 Checkpoint Complete!")
        else:
            print("SOME TESTS FAILED - Review output above")
        print("=" * 60)
        
        return 0 if all_passed else 1
        
    finally:
        await close_pool()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
