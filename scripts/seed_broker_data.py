#!/usr/bin/env python3
"""Seed sample data for Commercial Brokerage demo."""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.broker.storage import BrokerStorage
from app.broker.models import (
    Client, PropertyLocation, LossHistoryEntry, Submission, Quote,
    QuoteFields, PlacementScoring, CarrierProfile
)
from app.broker.constants import (
    SubmissionStatus, QuoteStatus, LineOfBusiness, CoverageAdequacy, PremiumBenchmark
)

# Fixed UUIDs for idempotency
RIDGEVIEW_CLIENT_ID = "c1111111-1111-1111-1111-111111111111"
MERIDIAN_CLIENT_ID = "c2222222-2222-2222-2222-222222222222"
RIDGEVIEW_SUBMISSION_ID = "s1111111-1111-1111-1111-111111111111"
AIG_QUOTE_ID = "q1111111-1111-1111-1111-111111111111"
ZURICH_QUOTE_ID = "q2222222-2222-2222-2222-222222222222"
TRAVELERS_QUOTE_ID = "q3333333-3333-3333-3333-333333333333"
AIG_CARRIER_ID = "carr1111-1111-1111-1111-111111111111"
ZURICH_CARRIER_ID = "carr2222-2222-2222-2222-222222222222"
TRAVELERS_CARRIER_ID = "carr3333-3333-3333-3333-333333333333"


def create_ridgeview_client():
    """Create Ridgeview Properties LLC client."""
    locations = [
        PropertyLocation(
            address="280 Riverside Drive, Hartford, CT 06103",
            occupancy="Multi-family residential (50 units)",
            construction="Masonry non-combustible",
            year_built=1985,
            square_footage=45000,
            building_value="$6,500,000",
            contents_value="$2,000,000",
            bi_value="$1,000,000",
            protection_class="3"
        ),
        PropertyLocation(
            address="1750 Main Street, New Haven, CT 06511",
            occupancy="Multi-family residential (32 units)",
            construction="Frame construction",
            year_built=1978,
            square_footage=28000,
            building_value="$3,800,000",
            contents_value="$1,500,000",
            bi_value="$750,000",
            protection_class="4"
        ),
        PropertyLocation(
            address="95 Elm Street, Stamford, CT 06902",
            occupancy="Mixed use - retail/residential (24 units)",
            construction="Masonry non-combustible",
            year_built=1992,
            square_footage=32000,
            building_value="$5,200,000",
            contents_value="$1,000,000",
            bi_value="$500,000",
            protection_class="2"
        )
    ]
    
    renewal_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    
    return Client(
        id=RIDGEVIEW_CLIENT_ID,
        name="Ridgeview Properties LLC",
        industry_code="NAICS 531110",
        business_type="Lessors of Residential Buildings",
        years_in_business=15,
        annual_revenue="$12,000,000",
        employee_count=45,
        headquarters_address="450 Commerce Drive, Hartford, CT 06103",
        property_locations=locations,
        renewal_date=renewal_date,
        broker_notes="Long-standing client, good loss history, looking to expand coverage. Recently completed roof replacements on two properties. Strong tenant retention rate.",
        research_brief={
            "market_position": "Established player in Hartford metro area",
            "growth_trajectory": "Steady organic growth, considering acquisition of 2 additional properties",
            "risk_profile": "Well-maintained properties, proactive maintenance program"
        },
        contacts=[
            {
                "name": "Sarah Mitchell",
                "title": "Chief Financial Officer",
                "email": "smitchell@ridgeviewproperties.com",
                "phone": "(860) 555-0145"
            },
            {
                "name": "David Chen",
                "title": "Director of Operations",
                "email": "dchen@ridgeviewproperties.com",
                "phone": "(860) 555-0146"
            }
        ],
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )


def create_meridian_client():
    """Create Meridian Manufacturing Inc client."""
    locations = [
        PropertyLocation(
            address="1200 Industrial Parkway, Cleveland, OH 44114",
            occupancy="Machine shop and manufacturing facility",
            construction="Masonry non-combustible with steel frame",
            year_built=2008,
            square_footage=55000,
            building_value="$8,500,000",
            contents_value="$4,200,000",
            bi_value="$1,800,000",
            protection_class="3"
        )
    ]
    
    renewal_date = (datetime.now() + timedelta(days=120)).strftime("%Y-%m-%d")
    
    return Client(
        id=MERIDIAN_CLIENT_ID,
        name="Meridian Manufacturing Inc",
        industry_code="NAICS 332710",
        business_type="Machine Shops",
        years_in_business=8,
        annual_revenue="$5,200,000",
        employee_count=32,
        headquarters_address="1200 Industrial Parkway, Cleveland, OH 44114",
        property_locations=locations,
        renewal_date=renewal_date,
        broker_notes="Growing manufacturing operation specializing in precision machined components for aerospace and medical device industries. ISO 9001 certified. Clean safety record.",
        research_brief={
            "market_position": "Niche player in high-precision machining",
            "growth_trajectory": "20% YoY revenue growth, recently added CNC equipment",
            "risk_profile": "Modern facility with fire suppression systems, regular equipment maintenance"
        },
        contacts=[
            {
                "name": "Robert Thompson",
                "title": "President & CEO",
                "email": "rthompson@meridianmfg.com",
                "phone": "(216) 555-0287"
            }
        ],
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )


def create_ridgeview_submission():
    """Create submission for Ridgeview Properties with embedded quotes."""
    effective_date = "2026-07-01"
    expiration_date = "2027-07-01"
    submission_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    
    acord_125_fields = {
        "applicant_name": "Ridgeview Properties LLC",
        "mailing_address": "450 Commerce Drive, Hartford, CT 06103",
        "effective_date": effective_date,
        "expiration_date": expiration_date,
        "policy_number": "",
        "description_of_operations": "Owner and lessor of multi-family residential properties and mixed-use retail/residential buildings",
        "number_of_locations": "3",
        "total_insured_value": "$18,500,000",
        "prior_carrier": "Liberty Mutual",
        "years_with_prior_carrier": "5",
        "any_losses_last_5_years": "Yes - minor water damage claim in 2023, $8,500 paid"
    }
    
    acord_140_fields = {
        "location_1": {
            "address": "280 Riverside Drive, Hartford, CT 06103",
            "building_limit": "$6,500,000",
            "contents_limit": "$2,000,000",
            "business_interruption": "$1,000,000",
            "year_built": "1985",
            "construction": "Masonry non-combustible",
            "occupancy": "Multi-family residential (50 units)",
            "protection_class": "3",
            "square_footage": "45000"
        },
        "location_2": {
            "address": "1750 Main Street, New Haven, CT 06511",
            "building_limit": "$3,800,000",
            "contents_limit": "$1,500,000",
            "business_interruption": "$750,000",
            "year_built": "1978",
            "construction": "Frame construction",
            "occupancy": "Multi-family residential (32 units)",
            "protection_class": "4",
            "square_footage": "28000"
        },
        "location_3": {
            "address": "95 Elm Street, Stamford, CT 06902",
            "building_limit": "$5,200,000",
            "contents_limit": "$1,000,000",
            "business_interruption": "$500,000",
            "year_built": "1992",
            "construction": "Masonry non-combustible",
            "occupancy": "Mixed use - retail/residential (24 units)",
            "protection_class": "2",
            "square_footage": "32000"
        }
    }
    
    acord_field_confidence = {
        "applicant_name": 0.98,
        "mailing_address": 0.95,
        "effective_date": 0.99,
        "total_insured_value": 0.92,
        "description_of_operations": 0.88,
        "number_of_locations": 0.97,
        "location_1_address": 0.96,
        "location_1_building_limit": 0.94,
        "location_2_address": 0.95,
        "location_2_building_limit": 0.93,
        "location_3_address": 0.97,
        "location_3_building_limit": 0.91
    }
    
    # Create quotes first (they'll be embedded in submission)
    aig_quote = create_aig_quote()
    zurich_quote = create_zurich_quote()
    travelers_quote = create_travelers_quote()
    
    return Submission(
        id=RIDGEVIEW_SUBMISSION_ID,
        client_id=RIDGEVIEW_CLIENT_ID,
        line_of_business=LineOfBusiness.PROPERTY,
        acord_form_types=["125", "140"],
        status=SubmissionStatus.QUOTED,
        effective_date=effective_date,
        expiration_date=expiration_date,
        total_insured_value="$18,500,000",
        coverage_requested={
            "property_damage": "$15,500,000",
            "business_interruption": "$2,250,000",
            "flood": "Sublimit requested",
            "earthquake": "Sublimit requested"
        },
        submitted_carriers=["AIG", "Zurich", "Travelers"],
        documents=[],
        quotes=[aig_quote, zurich_quote, travelers_quote],
        submission_date=submission_date,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        acord_125_fields=acord_125_fields,
        acord_140_fields=acord_140_fields,
        acord_field_confidence=acord_field_confidence
    )


def create_aig_quote():
    """Create AIG quote (strongest overall)."""
    return Quote(
        id=AIG_QUOTE_ID,
        submission_id=RIDGEVIEW_SUBMISSION_ID,
        carrier_name="AIG",
        source_format="pdf",
        source_file_name="aig_ridgeview_quote_2026.pdf",
        received_date=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        status=QuoteStatus.EXTRACTED,
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
            special_conditions=[
                "Annual inspection required",
                "Sprinkler system maintenance certificate required annually"
            ],
            policy_period="12 months",
            carrier_am_best_rating="A+ (Superior)",
            quote_reference_number="AIG-COM-2026-874521",
            expiry_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            underwriter="Jennifer Martinez"
        ),
        scoring=PlacementScoring(
            placement_score=88.5,
            placement_rank=2,
            recommendation_rationale="Strong coverage with comprehensive flood protection. Competitive premium with no material exclusions. AIG's A+ rating provides solid financial security. Slightly higher premium than Zurich but significantly better coverage terms.",
            coverage_adequacy=CoverageAdequacy.ADEQUATE,
            coverage_gaps=[],
            premium_percentile=PremiumBenchmark.MARKET
        ),
        confidence_scores={
            "annual_premium": 0.96,
            "total_insured_value": 0.94,
            "building_limit": 0.95,
            "contents_limit": 0.93,
            "business_interruption_limit": 0.91,
            "deductible": 0.97,
            "flood_sublimit": 0.89,
            "earthquake_sublimit": 0.87,
            "policy_period": 0.99,
            "carrier_am_best_rating": 0.98
        },
        created_at=datetime.now().isoformat()
    )


def create_zurich_quote():
    """Create Zurich quote (competitive price, some gaps)."""
    return Quote(
        id=ZURICH_QUOTE_ID,
        submission_id=RIDGEVIEW_SUBMISSION_ID,
        carrier_name="Zurich",
        source_format="pdf",
        source_file_name="zurich_ridgeview_quote_2026.pdf",
        received_date=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
        status=QuoteStatus.EXTRACTED,
        fields=QuoteFields(
            annual_premium="$38,750",
            total_insured_value="$18,500,000",
            building_limit="$11,500,000",
            contents_limit="$4,000,000",
            business_interruption_limit="$1,500,000",
            deductible="$15,000",
            flood_sublimit="$2,000,000",
            earthquake_sublimit="$1,000,000",
            named_perils_exclusions=["Mold", "Cyber"],
            special_conditions=[
                "Higher deductible applies to wind and hail",
                "Cyber exclusion - separate policy required",
                "Mold exclusion - limited coverage available by endorsement"
            ],
            policy_period="12 months",
            carrier_am_best_rating="A+ (Superior)",
            quote_reference_number="ZUR-PROP-2026-K8472",
            expiry_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            underwriter="Michael Chen"
        ),
        scoring=PlacementScoring(
            placement_score=72.3,
            placement_rank=3,
            recommendation_rationale="Most competitive premium but with notable coverage limitations. Lower flood sublimit may be inadequate given Hartford area flood exposure. Mold and cyber exclusions create gaps. BI limit is $500K below requested coverage. Consider only if budget is primary concern.",
            coverage_adequacy=CoverageAdequacy.PARTIAL,
            coverage_gaps=[
                "Flood sublimit 60% below AIG/Travelers",
                "Business Interruption $500K below requested",
                "Mold exclusion requires separate endorsement",
                "Cyber exclusion may require separate policy"
            ],
            premium_percentile=PremiumBenchmark.BELOW_MARKET
        ),
        confidence_scores={
            "annual_premium": 0.94,
            "total_insured_value": 0.93,
            "building_limit": 0.92,
            "contents_limit": 0.91,
            "business_interruption_limit": 0.58,
            "deductible": 0.95,
            "flood_sublimit": 0.55,
            "earthquake_sublimit": 0.86,
            "policy_period": 0.98,
            "carrier_am_best_rating": 0.97
        },
        created_at=datetime.now().isoformat()
    )


def create_travelers_quote():
    """Create Travelers quote (premium but broad coverage)."""
    return Quote(
        id=TRAVELERS_QUOTE_ID,
        submission_id=RIDGEVIEW_SUBMISSION_ID,
        carrier_name="Travelers",
        source_format="pdf",
        source_file_name="travelers_ridgeview_quote_2026.pdf",
        received_date=(datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        status=QuoteStatus.EXTRACTED,
        fields=QuoteFields(
            annual_premium="$47,200",
            total_insured_value="$18,500,000",
            building_limit="$12,500,000",
            contents_limit="$4,500,000",
            business_interruption_limit="$2,500,000",
            deductible="$5,000",
            flood_sublimit="$7,500,000",
            earthquake_sublimit="$3,000,000",
            named_perils_exclusions=[],
            special_conditions=[
                "Premium package includes equipment breakdown coverage",
                "Automatic 25% inflation guard included",
                "Loss prevention engineering survey included at no charge",
                "24/7 claims support with dedicated account manager"
            ],
            policy_period="12 months",
            carrier_am_best_rating="A++ (Superior)",
            quote_reference_number="TRV-CPP-2026-195847",
            expiry_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            underwriter="Patricia O'Brien"
        ),
        scoring=PlacementScoring(
            placement_score=93.2,
            placement_rank=1,
            recommendation_rationale="Highest quality coverage with superior terms across all categories. A++ rating provides exceptional financial security. Comprehensive flood/earthquake protection exceeds client requirements. Premium position justified by low deductible, inflation guard, and enhanced services. Best overall value despite higher premium.",
            coverage_adequacy=CoverageAdequacy.ADEQUATE,
            coverage_gaps=[],
            premium_percentile=PremiumBenchmark.ABOVE_MARKET
        ),
        confidence_scores={
            "annual_premium": 0.98,
            "total_insured_value": 0.97,
            "building_limit": 0.96,
            "contents_limit": 0.95,
            "business_interruption_limit": 0.94,
            "deductible": 0.99,
            "flood_sublimit": 0.92,
            "earthquake_sublimit": 0.91,
            "policy_period": 0.99,
            "carrier_am_best_rating": 0.99
        },
        created_at=datetime.now().isoformat()
    )


def create_aig_carrier_profile():
    """Create AIG carrier profile."""
    return CarrierProfile(
        id=AIG_CARRIER_ID,
        carrier_name="AIG",
        amb_number="058849",
        naic_code="19380",
        financial_strength_rating="A+",
        issuer_credit_rating="aa-",
        rating_outlook="Stable",
        balance_sheet_strength="Very Strong",
        operating_performance="Strong",
        business_profile="Very Strong",
        erm_assessment="Appropriate",
        net_premiums_written="$28,450,000,000",
        policyholders_surplus="$68,200,000,000",
        combined_ratio="96.2",
        five_year_avg_combined_ratio="97.8",
        report_date="2024-12-31",
        direct_written_premium="$32,100,000,000",
        dwp_growth_rate="4.2%",
        net_premiums_earned="$27,800,000,000",
        total_admitted_assets="$285,400,000,000",
        total_invested_assets="$245,600,000,000",
        loss_and_lae_reserves="$72,300,000,000",
        unearned_premiums="$15,200,000,000",
        rbc_total_adjusted_capital="$74,500,000,000",
        rbc_control_level="$4,200,000,000",
        nwp_to_surplus_ratio="0.42",
        reinsurance_per_risk_retention="$15,000,000",
        cat_retention="$750,000,000",
        reinsurance_cession_rate="11.2%",
        lines_of_business_written=[
            {"line": "Commercial Property", "percentage": "18%"},
            {"line": "General Liability", "percentage": "22%"},
            {"line": "Professional Liability", "percentage": "15%"},
            {"line": "Workers Compensation", "percentage": "12%"},
            {"line": "Other Commercial Lines", "percentage": "33%"}
        ],
        geographic_concentration=[
            {"region": "United States", "percentage": "62%"},
            {"region": "Europe", "percentage": "21%"},
            {"region": "Asia Pacific", "percentage": "12%"},
            {"region": "Other", "percentage": "5%"}
        ],
        mda_year="2024",
        net_income="$3,850,000,000",
        underwriting_gain_loss="$1,150,000,000",
        net_investment_income="$8,200,000,000"
    )


def create_zurich_carrier_profile():
    """Create Zurich carrier profile."""
    return CarrierProfile(
        id=ZURICH_CARRIER_ID,
        carrier_name="Zurich",
        amb_number="004170",
        naic_code="16535",
        financial_strength_rating="A+",
        issuer_credit_rating="aa-",
        rating_outlook="Stable",
        balance_sheet_strength="Very Strong",
        operating_performance="Strong",
        business_profile="Very Strong",
        erm_assessment="Appropriate",
        net_premiums_written="$32,800,000,000",
        policyholders_surplus="$48,900,000,000",
        combined_ratio="98.1",
        five_year_avg_combined_ratio="99.2",
        report_date="2024-12-31",
        direct_written_premium="$36,500,000,000",
        dwp_growth_rate="3.8%",
        net_premiums_earned="$31,900,000,000",
        total_admitted_assets="$268,700,000,000",
        total_invested_assets="$228,400,000,000",
        loss_and_lae_reserves="$65,800,000,000",
        unearned_premiums="$16,800,000,000",
        rbc_total_adjusted_capital="$52,100,000,000",
        rbc_control_level="$3,800,000,000",
        nwp_to_surplus_ratio="0.67",
        reinsurance_per_risk_retention="$12,500,000",
        cat_retention="$650,000,000",
        reinsurance_cession_rate="10.8%",
        lines_of_business_written=[
            {"line": "Commercial Property", "percentage": "16%"},
            {"line": "General Liability", "percentage": "24%"},
            {"line": "Professional Liability", "percentage": "14%"},
            {"line": "Workers Compensation", "percentage": "15%"},
            {"line": "Other Commercial Lines", "percentage": "31%"}
        ],
        geographic_concentration=[
            {"region": "Europe", "percentage": "38%"},
            {"region": "United States", "percentage": "35%"},
            {"region": "Asia Pacific", "percentage": "18%"},
            {"region": "Other", "percentage": "9%"}
        ],
        mda_year="2024",
        net_income="$3,200,000,000",
        underwriting_gain_loss="$620,000,000",
        net_investment_income="$7,450,000,000"
    )


def create_travelers_carrier_profile():
    """Create Travelers carrier profile."""
    return CarrierProfile(
        id=TRAVELERS_CARRIER_ID,
        carrier_name="Travelers",
        amb_number="001155",
        naic_code="25674",
        financial_strength_rating="A++",
        issuer_credit_rating="aaa",
        rating_outlook="Stable",
        balance_sheet_strength="Superior",
        operating_performance="Very Strong",
        business_profile="Very Strong",
        erm_assessment="Very Strong",
        net_premiums_written="$31,200,000,000",
        policyholders_surplus="$28,500,000,000",
        combined_ratio="94.5",
        five_year_avg_combined_ratio="95.8",
        report_date="2024-12-31",
        direct_written_premium="$33,800,000,000",
        dwp_growth_rate="5.1%",
        net_premiums_earned="$30,600,000,000",
        total_admitted_assets="$116,200,000,000",
        total_invested_assets="$92,400,000,000",
        loss_and_lae_reserves="$52,800,000,000",
        unearned_premiums="$14,600,000,000",
        rbc_total_adjusted_capital="$31,200,000,000",
        rbc_control_level="$2,100,000,000",
        nwp_to_surplus_ratio="1.09",
        reinsurance_per_risk_retention="$10,000,000",
        cat_retention="$500,000,000",
        reinsurance_cession_rate="7.5%",
        lines_of_business_written=[
            {"line": "Commercial Property", "percentage": "22%"},
            {"line": "General Liability", "percentage": "20%"},
            {"line": "Commercial Auto", "percentage": "18%"},
            {"line": "Workers Compensation", "percentage": "14%"},
            {"line": "Other Commercial Lines", "percentage": "26%"}
        ],
        geographic_concentration=[
            {"region": "United States", "percentage": "88%"},
            {"region": "Canada", "percentage": "8%"},
            {"region": "Other International", "percentage": "4%"}
        ],
        mda_year="2024",
        net_income="$4,950,000,000",
        underwriting_gain_loss="$1,680,000,000",
        net_investment_income="$3,420,000,000"
    )


def main():
    """Seed all demo data."""
    storage = BrokerStorage()
    
    print("🌱 Seeding Commercial Brokerage demo data...\n")
    
    # Create and save clients
    print("Creating clients...")
    ridgeview = create_ridgeview_client()
    storage.save_client(ridgeview)
    print(f"  ✓ {ridgeview.name} (ID: {ridgeview.id})")
    
    meridian = create_meridian_client()
    storage.save_client(meridian)
    print(f"  ✓ {meridian.name} (ID: {meridian.id})")
    
    # Create and save submission with embedded quotes
    print("\nCreating submission with quotes...")
    submission = create_ridgeview_submission()
    storage.save_submission(submission)
    print(f"  ✓ Submission for {ridgeview.name} (ID: {submission.id})")
    print(f"    - {len(submission.quotes)} quotes embedded: AIG, Zurich, Travelers")
    
    # Create and save carrier profiles
    print("\nCreating carrier profiles...")
    aig = create_aig_carrier_profile()
    storage.save_carrier_profile(aig)
    print(f"  ✓ {aig.carrier_name} - {aig.financial_strength_rating} ({aig.issuer_credit_rating})")
    
    zurich = create_zurich_carrier_profile()
    storage.save_carrier_profile(zurich)
    print(f"  ✓ {zurich.carrier_name} - {zurich.financial_strength_rating} ({zurich.issuer_credit_rating})")
    
    travelers = create_travelers_carrier_profile()
    storage.save_carrier_profile(travelers)
    print(f"  ✓ {travelers.carrier_name} - {travelers.financial_strength_rating} ({travelers.issuer_credit_rating})")
    
    print("\n" + "="*60)
    print("✅ Demo data seeded successfully!")
    print("="*60)
    print(f"\nData saved to: {storage.base_path}")
    print("\nQuick stats:")
    print(f"  • Clients: 2")
    print(f"  • Submissions: 1 (Ridgeview Properties - QUOTED)")
    print(f"  • Quotes: 3 (embedded in submission)")
    print(f"    - Travelers: Rank #1 (Score: 93.2) - Premium but comprehensive")
    print(f"    - AIG: Rank #2 (Score: 88.5) - Strong coverage, market premium")
    print(f"    - Zurich: Rank #3 (Score: 72.3) - Competitive price, coverage gaps")
    print(f"  • Carrier Profiles: 3")
    print("\nTo view the data:")
    print(f"  dir {storage.base_path}\\clients")
    print(f"  dir {storage.base_path}\\submissions")
    print(f"  dir {storage.base_path}\\carriers")


if __name__ == "__main__":
    main()
