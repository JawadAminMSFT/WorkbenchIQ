"""
Seed broker demo data using real engines.

Creates clients, submissions, quotes, runs PlacementEngine to score them,
and creates carrier profiles. This is an iterative script designed to be
run multiple times until all data is clean.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.broker.storage import BrokerStorage
from app.broker.models import (
    Client,
    Submission,
    Quote,
    QuoteFields,
    CarrierProfile,
)
from app.broker.constants import (
    LineOfBusiness,
    SubmissionStatus,
    QuoteStatus,
)
from app.broker.placement_engine import PlacementEngine


def main():
    """Seed broker demo data."""
    print("=" * 80)
    print("BROKER DEMO DATA SEEDING")
    print("=" * 80)
    print()
    
    # Initialize storage
    storage = BrokerStorage()
    print("✓ Initialized BrokerStorage")
    print()
    
    # ====================================================================
    # 1. Create Clients
    # ====================================================================
    print("1. Creating Clients")
    print("-" * 80)
    
    ridgeview = Client(
        name="Ridgeview Properties LLC",
        industry_code="531110",
        business_type="LLC",
        years_in_business=15,
        annual_revenue="$12,000,000",
        employee_count=45,
        headquarters_address="450 Commerce Drive, Suite 100, Hartford, CT 06103",
        broker_notes="Long-standing client, good loss history, looking to expand coverage",
    )
    storage.save_client(ridgeview)
    print(f"  ✓ Created: {ridgeview.name} (ID: {ridgeview.id})")
    
    meridian = Client(
        name="Meridian Manufacturing Inc",
        industry_code="332710",
        business_type="Corporation",
        years_in_business=8,
        annual_revenue="$5,200,000",
        employee_count=32,
        headquarters_address="1200 Industrial Parkway, Cleveland, OH 44114",
    )
    storage.save_client(meridian)
    print(f"  ✓ Created: {meridian.name} (ID: {meridian.id})")
    print()
    
    # ====================================================================
    # 2. Create Submission for Ridgeview
    # ====================================================================
    print("2. Creating Submission for Ridgeview")
    print("-" * 80)
    
    submission = Submission(
        client_id=ridgeview.id,
        line_of_business=LineOfBusiness.PROPERTY.value,
        status=SubmissionStatus.QUOTED.value,
        effective_date="2026-07-01",
        expiration_date="2027-07-01",
        total_insured_value="$18,500,000",
        submitted_carriers=["AIG", "Zurich", "Travelers"],
    )
    storage.save_submission(submission)
    print(f"  ✓ Created submission (ID: {submission.id})")
    print(f"    - Client: {ridgeview.name}")
    print(f"    - Line: {submission.line_of_business}")
    print(f"    - Status: {submission.status}")
    print(f"    - TIV: {submission.total_insured_value}")
    print()
    
    # ====================================================================
    # 3. Create Quotes with Realistic Data
    # ====================================================================
    print("3. Creating Quotes from Sample Data")
    print("-" * 80)
    
    # AIG Quote (balanced, mid-premium, good coverage)
    aig_quote = Quote(
        submission_id=submission.id,
        carrier_name="AIG",
        source_format="pdf",
        source_file_name="quote-aig.txt",
        status=QuoteStatus.EXTRACTED.value,
        fields=QuoteFields(
            annual_premium="$42,500",
            total_insured_value="$18,500,000",
            building_limit="$12,000,000",
            contents_limit="$4,500,000",
            business_interruption_limit="$2,000,000",
            deductible="$10,000",
            flood_sublimit="$5,000,000",
            earthquake_sublimit="$2,500,000",
            named_perils_exclusions=[],
            policy_period="07/01/2026 - 07/01/2027",
            carrier_am_best_rating="A+",
            quote_reference_number="AIG-CPP-2026-04821",
            underwriter="Jennifer M. Blackwood",
        ),
        confidence_scores={
            "annual_premium": 0.95,
            "building_limit": 0.92,
            "contents_limit": 0.90,
            "deductible": 0.95,
            "flood_sublimit": 0.88,
            "earthquake_sublimit": 0.85,
            "business_interruption_limit": 0.87,
            "carrier_am_best_rating": 0.98,
        },
    )
    print(f"  ✓ Created AIG quote")
    print(f"    - Premium: {aig_quote.fields.annual_premium}")
    print(f"    - TIV: {aig_quote.fields.total_insured_value}")
    print(f"    - Exclusions: {len(aig_quote.fields.named_perils_exclusions)}")
    
    # Zurich Quote (lowest premium, coverage gaps, exclusions)
    zurich_quote = Quote(
        submission_id=submission.id,
        carrier_name="Zurich",
        source_format="pdf",
        source_file_name="quote-zurich.txt",
        status=QuoteStatus.EXTRACTED.value,
        fields=QuoteFields(
            annual_premium="$38,750",
            total_insured_value="$18,000,000",
            building_limit="$11,500,000",
            contents_limit="$4,000,000",
            business_interruption_limit="$1,500,000",
            deductible="$15,000",
            flood_sublimit="$2,000,000",
            earthquake_sublimit="$1,000,000",
            named_perils_exclusions=["Mold", "Cyber"],
            policy_period="07/01/2026 - 07/01/2027",
            carrier_am_best_rating="A+",
            quote_reference_number="ZNA-CPP-2026-17493",
            underwriter="David R. Castillo",
        ),
        confidence_scores={
            "annual_premium": 0.93,
            "building_limit": 0.88,
            "contents_limit": 0.85,
            "deductible": 0.92,
            "flood_sublimit": 0.55,
            "earthquake_sublimit": 0.58,
            "business_interruption_limit": 0.58,
            "carrier_am_best_rating": 0.95,
        },
    )
    print(f"  ✓ Created Zurich quote")
    print(f"    - Premium: {zurich_quote.fields.annual_premium}")
    print(f"    - TIV: {zurich_quote.fields.total_insured_value}")
    print(f"    - Exclusions: {len(zurich_quote.fields.named_perils_exclusions)} ({', '.join(zurich_quote.fields.named_perils_exclusions)})")
    
    # Travelers Quote (highest premium, best coverage, top rating)
    travelers_quote = Quote(
        submission_id=submission.id,
        carrier_name="Travelers",
        source_format="pdf",
        source_file_name="quote-travelers.txt",
        status=QuoteStatus.EXTRACTED.value,
        fields=QuoteFields(
            annual_premium="$47,200",
            total_insured_value="$19,500,000",
            building_limit="$12,500,000",
            contents_limit="$4,500,000",
            business_interruption_limit="$2,500,000",
            deductible="$5,000",
            flood_sublimit="$7,500,000",
            earthquake_sublimit="$3,000,000",
            named_perils_exclusions=[],
            policy_period="07/01/2026 - 07/01/2027",
            carrier_am_best_rating="A++",
            quote_reference_number="TRVLR-CPP-2026-88214",
            underwriter="Sarah K. Whitfield",
        ),
        confidence_scores={
            "annual_premium": 0.97,
            "building_limit": 0.95,
            "contents_limit": 0.93,
            "deductible": 0.96,
            "flood_sublimit": 0.92,
            "earthquake_sublimit": 0.90,
            "business_interruption_limit": 0.94,
            "carrier_am_best_rating": 0.99,
        },
    )
    print(f"  ✓ Created Travelers quote")
    print(f"    - Premium: {travelers_quote.fields.annual_premium}")
    print(f"    - TIV: {travelers_quote.fields.total_insured_value}")
    print(f"    - Exclusions: {len(travelers_quote.fields.named_perils_exclusions)}")
    print()
    
    # ====================================================================
    # 4. Create Carrier Profiles
    # ====================================================================
    print("4. Creating Carrier Profiles")
    print("-" * 80)
    
    aig_profile = CarrierProfile(
        carrier_name="AIG",
        naic_code="19402",
        financial_strength_rating="A+",
        issuer_credit_rating="aa-",
        rating_outlook="Stable",
        combined_ratio="96.2%",
        balance_sheet_strength="Very Strong",
        operating_performance="Strong",
    )
    storage.save_carrier_profile(aig_profile)
    print(f"  ✓ Created AIG profile (FSR: {aig_profile.financial_strength_rating}, CR: {aig_profile.combined_ratio})")
    
    zurich_profile = CarrierProfile(
        carrier_name="Zurich",
        naic_code="16535",
        financial_strength_rating="A+",
        issuer_credit_rating="aa-",
        rating_outlook="Stable",
        combined_ratio="98.1%",
        balance_sheet_strength="Very Strong",
        operating_performance="Strong",
    )
    storage.save_carrier_profile(zurich_profile)
    print(f"  ✓ Created Zurich profile (FSR: {zurich_profile.financial_strength_rating}, CR: {zurich_profile.combined_ratio})")
    
    travelers_profile = CarrierProfile(
        carrier_name="Travelers",
        naic_code="25658",
        financial_strength_rating="A++",
        issuer_credit_rating="aaa",
        rating_outlook="Stable",
        combined_ratio="94.5%",
        balance_sheet_strength="Strongest",
        operating_performance="Strongest",
    )
    storage.save_carrier_profile(travelers_profile)
    print(f"  ✓ Created Travelers profile (FSR: {travelers_profile.financial_strength_rating}, CR: {travelers_profile.combined_ratio})")
    print()
    
    # ====================================================================
    # 5. Run PlacementEngine to Score Quotes
    # ====================================================================
    print("5. Running PlacementEngine")
    print("-" * 80)
    
    engine = PlacementEngine()
    quotes = [aig_quote, zurich_quote, travelers_quote]
    
    # Build carrier profiles dict for engine
    carrier_profiles_dict = {
        "AIG": aig_profile,
        "Zurich": zurich_profile,
        "Travelers": travelers_profile,
    }
    
    print("  → Scoring quotes...")
    scored_quotes = engine.score_quotes(quotes, submission, carrier_profiles_dict)
    
    print(f"  ✓ Scored {len(scored_quotes)} quotes")
    print()
    
    for quote in scored_quotes:
        print(f"  {quote.carrier_name}:")
        print(f"    - Rank: #{quote.scoring.placement_rank}")
        print(f"    - Score: {quote.scoring.placement_score:.2f}/100")
        print(f"    - Coverage Adequacy: {quote.scoring.coverage_adequacy}")
        print(f"    - Premium Benchmark: {quote.scoring.premium_percentile}")
        print(f"    - Coverage Gaps: {len(quote.scoring.coverage_gaps)}")
        if quote.scoring.coverage_gaps:
            for gap in quote.scoring.coverage_gaps:
                print(f"      • {gap}")
    print()
    
    # Generate recommendation
    print("  → Generating recommendation...")
    recommendation = engine.generate_recommendation(scored_quotes)
    print(f"  ✓ Recommendation: {recommendation}")
    print()
    
    # ====================================================================
    # 6. Save Quotes to Submission
    # ====================================================================
    print("6. Saving Quotes to Submission")
    print("-" * 80)
    
    submission.quotes = scored_quotes
    storage.save_submission(submission)
    print(f"  ✓ Saved {len(scored_quotes)} quotes to submission {submission.id}")
    print()
    
    # ====================================================================
    # 7. Verify Everything Saved
    # ====================================================================
    print("7. Verification")
    print("-" * 80)
    
    # Verify clients
    clients = storage.list_clients()
    print(f"Clients: {len(clients)}")
    for c in clients:
        print(f"  - {c['name']} ({c['id']})")
    print()
    
    # Verify submissions
    subs = storage.list_submissions(ridgeview.id)
    print(f"Submissions for Ridgeview: {len(subs)}")
    for s in subs:
        print(f"  - {s['id']}: {s['status']}, {len(s.get('quotes', []))} quotes")
        for q in s.get("quotes", []):
            scoring = q.get("scoring", {})
            print(f"    - {q['carrier_name']}: score={scoring.get('placement_score')}, rank={scoring.get('placement_rank')}")
    print()
    
    # Verify metrics
    metrics = storage.get_dashboard_metrics()
    print(f"Dashboard Metrics:")
    print(f"  - Total accounts: {metrics['total_accounts']}")
    print(f"  - Open submissions: {metrics['open_submissions']}")
    print(f"  - Total bound premium: {metrics['total_bound_premium']}")
    print(f"  - Renewals due (90 days): {metrics['renewals_due_90_days']}")
    print(f"  - Stale submissions: {metrics['stale_submissions']}")
    print()
    
    # Verify carriers
    carriers = storage.list_carrier_profiles()
    print(f"Carrier Profiles: {len(carriers)}")
    for carrier in carriers:
        print(f"  - {carrier['carrier_name']} (FSR: {carrier['financial_strength_rating']})")
    print()
    
    # ====================================================================
    # Done
    # ====================================================================
    print("=" * 80)
    print("✓ SEEDING COMPLETE")
    print("=" * 80)
    print()
    print("Data Files Created:")
    print(f"  - data/broker/clients/ ({len(clients)} files)")
    print(f"  - data/broker/submissions/ ({len(subs)} files)")
    print(f"  - data/broker/carriers/ ({len(carriers)} files)")
    print()
    print("Next Steps:")
    print("  - Start API server: python api_server.py")
    print("  - Test endpoints: GET /api/broker/dashboard")
    print("  - View clients: GET /api/broker/clients")
    print()


if __name__ == "__main__":
    main()
