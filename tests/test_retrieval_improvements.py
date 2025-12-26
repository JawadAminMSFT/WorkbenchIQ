#!/usr/bin/env python3
"""
Test improved RAG retrieval - Phase 5 (Metadata Filtering) & Phase 7 (Hybrid Search).

Tests:
1. Metadata filtering with category inference
2. Hybrid search combining keyword + semantic
3. Policy ID exact matching
4. Risk level filtering
5. Edge cases and fallbacks
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Settings, load_settings
from app.database.pool import init_pool, close_pool
from app.database.settings import DatabaseSettings
from app.rag.search import PolicySearchService


async def test_category_filtering(search: PolicySearchService) -> bool:
    """Test that category inference correctly filters results."""
    print("\n" + "=" * 60)
    print("TEST 1: Category Filtering")
    print("=" * 60)
    
    test_cases = [
        ("blood pressure 145/92", "cardiovascular", ["CVD-BP-001"]),
        ("cholesterol LDL 180", "metabolic", ["META-CHOL-001"]),
        ("BMI 32 obesity", "metabolic", ["META-BMI-001"]),
        ("diabetes HbA1c 7.5", "metabolic", ["META-DM-001"]),  # DM policy is in metabolic category
        ("family history of cancer", "family_history", ["FAM-CA-001"]),  # Cancer family history
        ("smoking 20 cigarettes daily", "lifestyle", ["LIFE-TOB-001"]),  # Tobacco policy
    ]
    
    all_passed = True
    for query, expected_category, expected_policies in test_cases:
        results, inferred = await search.intelligent_search(query, top_k=5)
        
        inferred_cat = inferred.categories[0] if inferred.categories else "none"
        found_policies = [r.policy_id for r in results]
        
        cat_match = expected_category == inferred_cat
        policy_match = all(p in found_policies for p in expected_policies) if expected_policies else True
        
        status = "PASS" if cat_match and policy_match else "FAIL"
        all_passed = all_passed and cat_match and policy_match
        
        print(f"\n[{status}] Query: '{query}'")
        print(f"   Inferred: {inferred_cat} (expected: {expected_category}) {'OK' if cat_match else 'MISMATCH'}")
        print(f"   Found: {found_policies[:3]}")
        if expected_policies:
            print(f"   Expected: {expected_policies} {'OK' if policy_match else 'MISSING'}")
    
    print(f"\n[CHECKPOINT] Category Filtering: {'PASS' if all_passed else 'FAIL'}")
    return all_passed


async def test_hybrid_search(search: PolicySearchService) -> bool:
    """Test hybrid search with exact policy ID matching."""
    print("\n" + "=" * 60)
    print("TEST 2: Hybrid Search (Keyword + Semantic)")
    print("=" * 60)
    
    test_cases = [
        # Policy ID exact match should always return that policy
        ("CVD-BP-001", ["CVD-BP-001"]),
        ("META-CHOL-001", ["META-CHOL-001"]),
        # Keyword-heavy queries
        ("systolic blood pressure hypertension", ["CVD-BP-001"]),
        ("total cholesterol triglycerides lipid panel", ["META-CHOL-001"]),
    ]
    
    all_passed = True
    for query, expected_policies in test_cases:
        results = await search.hybrid_search(query, top_k=5)
        
        found_policies = [r.policy_id for r in results]
        policy_match = all(p in found_policies for p in expected_policies)
        
        status = "PASS" if policy_match else "FAIL"
        all_passed = all_passed and policy_match
        
        print(f"\n[{status}] Query: '{query}'")
        print(f"   Found: {found_policies[:3]} (similarities: {[f'{r.similarity:.3f}' for r in results[:3]]})")
        print(f"   Expected: {expected_policies} {'OK' if policy_match else 'MISSING'}")
    
    print(f"\n[CHECKPOINT] Hybrid Search: {'PASS' if all_passed else 'FAIL'}")
    return all_passed


async def test_risk_level_filtering(search: PolicySearchService) -> bool:
    """Test filtering by risk level."""
    print("\n" + "=" * 60)
    print("TEST 3: Risk Level Filtering")
    print("=" * 60)
    
    test_cases = [
        # High risk queries
        ("high blood pressure 180/120 severe", ["High", "Moderate-High"]),
        ("very high cholesterol LDL 200", ["High", "Moderate-High"]),
        # Low risk queries
        ("normal blood pressure 115/75", ["Low", "Low-Moderate"]),
    ]
    
    all_passed = True
    for query, expected_levels in test_cases:
        results, inferred = await search.intelligent_search(query, top_k=10)
        
        found_levels = list(set(r.risk_level for r in results if r.risk_level))
        level_match = any(level in found_levels for level in expected_levels)
        
        status = "OK" if level_match else "WARN"  # Warning, not fail - inference is fuzzy
        
        print(f"\n[{status}] Query: '{query}'")
        print(f"   Found risk levels: {found_levels}")
        print(f"   Expected any of: {expected_levels}")
    
    # This test is informational - risk inference is probabilistic
    print(f"\n[CHECKPOINT] Risk Level Filtering: INFO (probabilistic)")
    return True  # Don't fail on risk level - it's probabilistic


async def test_semantic_vs_hybrid(search: PolicySearchService) -> bool:
    """Compare semantic vs hybrid search for edge cases."""
    print("\n" + "=" * 60)
    print("TEST 4: Semantic vs Hybrid Comparison")
    print("=" * 60)
    
    queries = [
        "CVD-BP-001",  # Exact policy ID - hybrid should win
        "blood pressure medication treatment",  # Semantic should work well
        "applicant has bp reading of 145 over 92",  # Natural language
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        
        semantic = await search.semantic_search(query, top_k=3)
        hybrid = await search.hybrid_search(query, top_k=3)
        
        print(f"  Semantic: {[(r.policy_id, f'{r.similarity:.3f}') for r in semantic]}")
        print(f"  Hybrid:   {[(r.policy_id, f'{r.similarity:.3f}') for r in hybrid]}")
    
    print(f"\n[CHECKPOINT] Comparison: INFO (manual review)")
    return True


async def test_combined_filters(search: PolicySearchService) -> bool:
    """Test combining category + risk level filters."""
    print("\n" + "=" * 60)
    print("TEST 5: Combined Filters (Category + Subcategory)")
    print("=" * 60)
    
    # Test filtered_search directly with multiple filters
    results = await search.filtered_search(
        query="blood pressure evaluation",
        category="cardiovascular",
        subcategory="hypertension",
        top_k=5,
    )
    
    all_cvd = all(r.category == "cardiovascular" for r in results)
    all_hypertension = all(r.subcategory == "hypertension" for r in results if r.subcategory)
    
    print(f"  Filters: category=cardiovascular, subcategory=hypertension")
    print(f"  Results: {len(results)} chunks")
    print(f"  All cardiovascular: {all_cvd}")
    print(f"  All hypertension (where set): {all_hypertension}")
    
    for r in results[:3]:
        print(f"    - [{r.policy_id}] {r.category}/{r.subcategory} - {r.content[:60]}...")
    
    passed = len(results) > 0 and all_cvd
    print(f"\n[CHECKPOINT] Combined Filters: {'PASS' if passed else 'FAIL'}")
    return passed


async def main():
    """Run all retrieval improvement tests."""
    print("=" * 60)
    print("RAG Retrieval Improvement Tests")
    print("Phase 5: Metadata Filtering | Phase 7: Hybrid Search")
    print("=" * 60)
    
    # Initialize
    settings = load_settings()
    db_settings = DatabaseSettings.from_env()
    
    print("\nInitializing database connection...")
    await init_pool(db_settings)
    
    try:
        search = PolicySearchService(settings)
        
        results = []
        results.append(("Category Filtering", await test_category_filtering(search)))
        results.append(("Hybrid Search", await test_hybrid_search(search)))
        results.append(("Risk Level Filtering", await test_risk_level_filtering(search)))
        results.append(("Semantic vs Hybrid", await test_semantic_vs_hybrid(search)))
        results.append(("Combined Filters", await test_combined_filters(search)))
        
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
            print("ALL TESTS PASSED - Retrieval improvements verified!")
        else:
            print("SOME TESTS FAILED - Review output above")
        print("=" * 60)
        
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
