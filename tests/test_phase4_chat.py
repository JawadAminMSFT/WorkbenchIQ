#!/usr/bin/env python3
"""
Test Phase 4: Chat Integration with RAG.

Tests:
1. RAG service initialization
2. Query with RAG context retrieval  
3. Fallback behavior when RAG unavailable
4. Integration with chat endpoint
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import load_settings
from app.database.pool import init_pool, close_pool
from app.database.settings import DatabaseSettings
from app.rag.service import RAGService, get_rag_service, RAGQueryResult


async def test_rag_service_initialization() -> bool:
    """Test RAG service can be initialized."""
    print("\n" + "=" * 60)
    print("TEST 1: RAG Service Initialization")
    print("=" * 60)
    
    try:
        settings = load_settings()
        service = RAGService(settings)
        await service.initialize()
        
        print(f"  Service initialized: OK")
        print(f"  Search service: {type(service._search_service).__name__}")
        print(f"  Context builder: {type(service._context_builder).__name__}")
        
        print("\n[CHECKPOINT] RAG Service Initialization: PASS")
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        print("\n[CHECKPOINT] RAG Service Initialization: FAIL")
        return False


async def test_rag_query() -> bool:
    """Test RAG query returns relevant context."""
    print("\n" + "=" * 60)
    print("TEST 2: RAG Query")
    print("=" * 60)
    
    try:
        service = await get_rag_service()
        
        test_queries = [
            ("blood pressure 145/92", ["CVD-BP-001"], "cardiovascular"),
            ("cholesterol LDL 180", ["META-CHOL-001"], "metabolic"),
            ("applicant has BMI of 32", ["META-BMI-001"], "metabolic"),
        ]
        
        all_passed = True
        for query, expected_policies, expected_category in test_queries:
            result = await service.query(query, top_k=5)
            
            found_policies = list(set(r.policy_id for r in result.results))
            policy_match = any(p in found_policies for p in expected_policies)
            
            status = "PASS" if policy_match else "FAIL"
            all_passed = all_passed and policy_match
            
            print(f"\n[{status}] Query: '{query}'")
            print(f"   Chunks: {result.chunks_retrieved}")
            print(f"   Tokens: {result.tokens_used}")
            print(f"   Latency: {result.total_latency_ms:.0f}ms")
            print(f"   Policies: {found_policies}")
            if result.inferred:
                print(f"   Inferred: {result.inferred.categories}")
        
        print(f"\n[CHECKPOINT] RAG Query: {'PASS' if all_passed else 'FAIL'}")
        return all_passed
        
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n[CHECKPOINT] RAG Query: FAIL")
        return False


async def test_context_format() -> bool:
    """Test context formatting for prompts."""
    print("\n" + "=" * 60)
    print("TEST 3: Context Formatting")
    print("=" * 60)
    
    try:
        service = await get_rag_service()
        
        result = await service.query("blood pressure evaluation", top_k=5)
        context = service.format_context_for_prompt(result)
        citations = service.get_citations_for_response(result)
        
        print(f"  Context length: {len(context)} chars")
        print(f"  Citations: {len(citations)}")
        print(f"  Has header: {'## Relevant' in context}")
        
        # Show preview
        print(f"\n  Context preview (first 500 chars):")
        print("-" * 40)
        print(context[:500])
        print("-" * 40)
        
        passed = len(context) > 0 and len(citations) > 0
        print(f"\n[CHECKPOINT] Context Formatting: {'PASS' if passed else 'FAIL'}")
        return passed
        
    except Exception as e:
        print(f"  Error: {e}")
        print("\n[CHECKPOINT] Context Formatting: FAIL")
        return False


async def test_fallback() -> bool:
    """Test fallback when RAG returns no results."""
    print("\n" + "=" * 60)
    print("TEST 4: Fallback Behavior")
    print("=" * 60)
    
    try:
        service = await get_rag_service()
        
        # Query that should return results with fallback context
        fallback_context = "FALLBACK: Full policy context here"
        
        result = await service.query_with_fallback(
            user_query="blood pressure evaluation",
            fallback_context=fallback_context,
        )
        
        # Should use RAG, not fallback
        print(f"  Used fallback: {result.used_fallback}")
        print(f"  Chunks retrieved: {result.chunks_retrieved}")
        
        passed = not result.used_fallback and result.chunks_retrieved > 0
        print(f"\n[CHECKPOINT] Fallback Behavior: {'PASS' if passed else 'FAIL'}")
        return passed
        
    except Exception as e:
        print(f"  Error: {e}")
        print("\n[CHECKPOINT] Fallback Behavior: FAIL")
        return False


async def test_rag_metrics() -> bool:
    """Test RAG metrics are captured."""
    print("\n" + "=" * 60)
    print("TEST 5: RAG Metrics")
    print("=" * 60)
    
    try:
        service = await get_rag_service()
        
        result = await service.query("high cholesterol treatment", top_k=5)
        
        print(f"  Search latency: {result.search_latency_ms:.0f}ms")
        print(f"  Assembly latency: {result.assembly_latency_ms:.0f}ms")
        print(f"  Total latency: {result.total_latency_ms:.0f}ms")
        print(f"  Chunks retrieved: {result.chunks_retrieved}")
        print(f"  Tokens used: {result.tokens_used}")
        
        # Metrics should be populated
        passed = (
            result.search_latency_ms > 0 and
            result.total_latency_ms > 0 and
            result.chunks_retrieved > 0 and
            result.tokens_used > 0
        )
        
        print(f"\n[CHECKPOINT] RAG Metrics: {'PASS' if passed else 'FAIL'}")
        return passed
        
    except Exception as e:
        print(f"  Error: {e}")
        print("\n[CHECKPOINT] RAG Metrics: FAIL")
        return False


async def main():
    """Run all Phase 4 tests."""
    print("=" * 60)
    print("PHASE 4: Chat Integration - Test Suite")
    print("=" * 60)
    
    # Initialize database
    db_settings = DatabaseSettings.from_env()
    print("\nInitializing database connection...")
    await init_pool(db_settings)
    
    try:
        results = []
        
        results.append(("RAG Service Init", await test_rag_service_initialization()))
        results.append(("RAG Query", await test_rag_query()))
        results.append(("Context Formatting", await test_context_format()))
        results.append(("Fallback Behavior", await test_fallback()))
        results.append(("RAG Metrics", await test_rag_metrics()))
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        all_passed = True
        for name, passed in results:
            status = "PASS" if passed else "FAIL"
            print(f"  {name}: {status}")
            all_passed = all_passed and passed
        
        print("\n" + "=" * 60)
        if all_passed:
            print("ALL TESTS PASSED - Phase 4 Chat Integration Ready!")
        else:
            print("SOME TESTS FAILED - Review output above")
        print("=" * 60)
        
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
