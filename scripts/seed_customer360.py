#!/usr/bin/env python3
"""
Seed Customer 360 data.

Creates 3 customer profiles with realistic cross-persona journey events
and rich application metadata that populates the persona workbench views.

Uses save_application_metadata() which delegates to the configured storage
provider (local filesystem or Azure Blob Storage).

Usage:
    python scripts/seed_customer360.py [--storage-root data]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.customer360 import (
    CustomerJourneyEvent,
    CustomerProfile,
    RiskCorrelation,
    delete_customer,
    save_customer_journey,
    save_customer_profile,
    save_customer_risk_correlations,
)
from app.storage import (
    ApplicationMetadata,
    StoredFile,
    save_application_metadata,
    get_application_dir,
)

# Rich seed data modules
from scripts.seed_data.underwriting import get_underwriting_apps
from scripts.seed_data.claims import get_claims_apps
from scripts.seed_data.mortgage import get_mortgage_apps


# =============================================================================
# Application seeding (provider-abstracted)
# =============================================================================

SEED_APP_IDS = [
    "app-sc-uw-001", "app-sc-mtg-001", "app-sc-auto-001",
    "app-mw-uw-001", "app-mw-hc-001", "app-mw-mtg-001",
    "app-pp-auto-001", "app-pp-uw-001", "app-pp-mtg-001",
]


def _clean_old_seed_apps(storage_root: str) -> None:
    """Remove previously seeded applications to allow clean re-seeding."""
    for app_id in SEED_APP_IDS:
        app_dir = Path(storage_root) / "applications" / app_id
        if app_dir.exists():
            shutil.rmtree(app_dir)


def _save_app_from_dict(storage_root: str, app_dict: dict) -> None:
    """Create an ApplicationMetadata from a dict and save via provider."""
    get_application_dir(storage_root, app_dict["id"])
    metadata = ApplicationMetadata(
        id=app_dict["id"],
        created_at=app_dict["created_at"],
        external_reference=app_dict.get("external_reference"),
        status=app_dict.get("status", "completed"),
        files=[StoredFile(**f) for f in app_dict.get("files", [])],
        persona=app_dict.get("persona"),
        llm_outputs=app_dict.get("llm_outputs"),
        extracted_fields=app_dict.get("extracted_fields"),
        confidence_summary=app_dict.get("confidence_summary"),
        risk_analysis=app_dict.get("risk_analysis"),
    )
    save_application_metadata(storage_root, metadata)


def seed_applications(storage_root: str) -> int:
    """Seed all rich application data. Returns count of apps created."""
    _clean_old_seed_apps(storage_root)
    all_apps = get_underwriting_apps() + get_claims_apps() + get_mortgage_apps()
    for app_dict in all_apps:
        _save_app_from_dict(storage_root, app_dict)
    return len(all_apps)


def _upload_customers_to_blob(storage_root: str, settings) -> None:
    """Upload customer profile/journey/risk JSON files to Azure Blob Storage."""
    from azure.storage.blob import BlobServiceClient

    blob_service = BlobServiceClient(
        account_url=f"https://{settings.azure_account_name}.blob.core.windows.net",
        credential=settings.azure_account_key,
    )
    container = blob_service.get_container_client(settings.azure_container_name)

    customers_dir = Path(storage_root) / "customers"
    if not customers_dir.exists():
        print("  No local customer data to upload")
        return

    count = 0
    for json_file in customers_dir.rglob("*.json"):
        blob_name = "customers/" + json_file.relative_to(customers_dir).as_posix()
        container.upload_blob(blob_name, json_file.read_bytes(), overwrite=True)
        count += 1
    print(f"  ✓ Uploaded {count} customer data files to blob")


# =============================================================================
# Customer profile & journey seeding
# =============================================================================

# (keeping _create_application for backward compat but it's no longer the
#  primary path — rich data comes from seed_data modules)

def _create_application(
    storage_root: str,
    app_id: str,
    persona: str,
    customer_id: str,
    customer_name: str,
    created_at: str,
    status: str,
    summary_title: str,
    summary_text: str,
    risk_assessment: str = "Standard",
) -> None:
    """Create a real ApplicationMetadata entry so it appears in persona workbenches."""
    # Ensure app directory exists
    get_application_dir(storage_root, app_id)

    metadata = ApplicationMetadata(
        id=app_id,
        created_at=created_at + "T12:00:00Z",
        external_reference=customer_id,
        status=status,
        files=[],
        persona=persona,
        llm_outputs={
            "application_summary": {
                "customer_profile": {
                    "section": "application_summary",
                    "subsection": "customer_profile",
                    "raw": summary_text,
                    "parsed": {
                        "summary": summary_title,
                        "risk_assessment": risk_assessment,
                    },
                }
            }
        },
    )
    save_application_metadata(storage_root, metadata)


def create_sarah_chen(storage_root: str) -> None:
    """Sarah Chen — Low risk, loyal multi-product customer."""
    customer_id = "CUST-SC-001"

    profile = CustomerProfile(
        id=customer_id,
        name="Sarah Chen",
        date_of_birth="1988-03-15",
        email="sarah.chen@email.com",
        phone="(416) 555-0142",
        address="42 Maple Grove Ave, Toronto, ON M4C 1L8",
        customer_since="2019-06-01",
        risk_tier="low",
        tags=["long-term", "multi-product", "preferred"],
        notes="Excellent customer history across all product lines. Consistent low-risk profile with strong financial standing.",
    )

    events = [
        CustomerJourneyEvent(
            date="2019-06-15",
            persona="underwriting",
            application_id="app-sc-uw-001",
            event_type="application_submitted",
            title="Life Insurance Application Submitted",
            summary="Term life insurance application — $500K coverage, 20-year term.",
            status="completed",
            risk_level="low",
            key_metrics={
                "coverage_amount": "$500,000",
                "term": "20 years",
                "product": "Term Life",
            },
        ),
        CustomerJourneyEvent(
            date="2019-07-02",
            persona="underwriting",
            application_id="app-sc-uw-001",
            event_type="underwriting_complete",
            title="Life Insurance — Approved at Standard Rates",
            summary="Healthy 31-year-old female, non-smoker, BMI 22.1. No significant medical history. All lab results within normal ranges. Clean family history. Approved at standard rates.",
            status="approved",
            risk_level="low",
            key_metrics={
                "risk_class": "Standard Plus",
                "decision": "Approved",
                "bmi": "22.1",
                "smoker": "No",
                "monthly_premium": "$42.50",
            },
        ),
        CustomerJourneyEvent(
            date="2021-09-10",
            persona="mortgage_underwriting",
            application_id="app-sc-mtg-001",
            event_type="application_submitted",
            title="Mortgage Application Submitted",
            summary="Conventional mortgage application for primary residence purchase in Toronto.",
            status="completed",
            risk_level="low",
            key_metrics={
                "property_value": "$650,000",
                "mortgage_amount": "$520,000",
                "ltv": "80%",
                "property_type": "Detached House",
            },
        ),
        CustomerJourneyEvent(
            date="2021-10-05",
            persona="mortgage_underwriting",
            application_id="app-sc-mtg-001",
            event_type="underwriting_complete",
            title="Mortgage — Approved (Conventional)",
            summary="Dual income household ($185K combined). Strong credit score (780). GDS 28%, TDS 35% — well within limits. 20% down payment. Approved with no conditions.",
            status="approved",
            risk_level="low",
            key_metrics={
                "gds_ratio": "28%",
                "tds_ratio": "35%",
                "credit_score": "780",
                "combined_income": "$185,000",
                "ltv": "80%",
                "decision": "Approved",
                "amortization": "25 years",
                "rate": "3.49% fixed",
            },
        ),
        CustomerJourneyEvent(
            date="2024-11-18",
            persona="automotive_claims",
            application_id="app-sc-auto-001",
            event_type="claim_filed",
            title="Auto Claim Filed — Rear-End Collision",
            summary="Minor rear-end collision at intersection. Other driver at fault (confirmed by police report). Damage to rear bumper and trunk lid.",
            status="completed",
            risk_level="low",
            key_metrics={
                "claim_type": "Collision",
                "damage_severity": "Minor",
                "repair_estimate": "$3,200",
                "liability": "Other party at fault",
            },
        ),
        CustomerJourneyEvent(
            date="2024-12-02",
            persona="automotive_claims",
            application_id="app-sc-auto-001",
            event_type="claim_resolved",
            title="Auto Claim — Settled",
            summary="Claim settled. $3,200 repair completed at authorized shop. Subrogation initiated against at-fault party's insurer. No injuries reported.",
            status="closed",
            risk_level="low",
            key_metrics={
                "payout": "$3,200",
                "fraud_risk": "None",
                "injuries": "None",
                "decision": "Approved",
                "settlement_type": "Direct Repair",
            },
        ),
    ]

    correlations = [
        RiskCorrelation(
            severity="info",
            title="Consistent Low-Risk Profile",
            description="Customer maintains a low-risk profile across all product lines — life insurance approved at standard-plus rates, mortgage well within OSFI B-20 limits, and auto claim was a straightforward not-at-fault incident.",
            personas_involved=["underwriting", "mortgage_underwriting", "automotive_claims"],
        ),
    ]

    save_customer_profile(storage_root, profile)
    save_customer_journey(storage_root, customer_id, events)
    save_customer_risk_correlations(storage_root, customer_id, correlations)
    print(f"  ✓ Created {profile.name} ({customer_id}) — 3 products, 6 events")


def create_marcus_williams(storage_root: str) -> None:
    """Marcus Williams — Medium risk, health concerns across products."""
    customer_id = "CUST-MW-002"

    profile = CustomerProfile(
        id=customer_id,
        name="Marcus Williams",
        date_of_birth="1981-08-22",
        email="m.williams@email.com",
        phone="(905) 555-0287",
        address="118 Oakridge Blvd, Mississauga, ON L5B 3J7",
        customer_since="2021-02-15",
        risk_tier="medium",
        tags=["multi-product", "health-watch", "conditional"],
        notes="Health concerns create cross-product risk correlation. Cardiac history relevant to both life insurance underwriting and health claims.",
    )

    events = [
        CustomerJourneyEvent(
            date="2021-02-20",
            persona="underwriting",
            application_id="app-mw-uw-001",
            event_type="application_submitted",
            title="Life Insurance Application Submitted",
            summary="Whole life insurance application — $750K coverage.",
            status="completed",
            risk_level="medium",
            key_metrics={
                "coverage_amount": "$750,000",
                "product": "Whole Life",
            },
        ),
        CustomerJourneyEvent(
            date="2021-03-15",
            persona="underwriting",
            application_id="app-mw-uw-001",
            event_type="underwriting_complete",
            title="Life Insurance — Referred for Medical Review",
            summary="45-year-old male, elevated BMI (29.1), controlled hypertension on lisinopril. Family history of cardiac disease (father — MI at 58). Borderline lipid panel: total cholesterol 5.8 mmol/L, LDL 3.9 mmol/L. Referred for senior underwriter review and additional cardiac workup.",
            status="referred",
            risk_level="medium",
            key_metrics={
                "risk_class": "Substandard — Pending Review",
                "decision": "Referred",
                "bmi": "29.1",
                "smoker": "No",
                "blood_pressure": "138/88",
                "cholesterol": "5.8 mmol/L",
                "medications": "Lisinopril 10mg",
                "family_history": "Father — MI at 58",
            },
        ),
        CustomerJourneyEvent(
            date="2023-06-05",
            persona="life_health_claims",
            application_id="app-mw-hc-001",
            event_type="claim_filed",
            title="Health Claim Filed — Cardiac Evaluation",
            summary="Claim submitted for cardiac stress test, echocardiogram, and specialist consultations following chest discomfort episodes.",
            status="completed",
            risk_level="medium",
            key_metrics={
                "claim_type": "Medical — Cardiac Evaluation",
                "provider": "Trillium Health Partners",
                "total_claimed": "$4,800",
            },
        ),
        CustomerJourneyEvent(
            date="2023-07-12",
            persona="life_health_claims",
            application_id="app-mw-hc-001",
            event_type="claim_resolved",
            title="Health Claim — Approved",
            summary="Claim approved after eligibility verification. Cardiac stress test showed no ischemia. Echo revealed mild LVH consistent with hypertension. Cardiologist recommended ongoing monitoring and medication adjustment. All services covered under plan benefits.",
            status="approved",
            risk_level="medium",
            key_metrics={
                "payout": "$4,800",
                "eligibility": "Verified",
                "decision": "Approved",
                "diagnosis": "Mild LVH, controlled hypertension",
                "follow_up": "6-month cardiology review",
            },
        ),
        CustomerJourneyEvent(
            date="2024-03-20",
            persona="mortgage_underwriting",
            application_id="app-mw-mtg-001",
            event_type="application_submitted",
            title="Mortgage Application Submitted",
            summary="Insured mortgage application for townhouse purchase in Mississauga.",
            status="completed",
            risk_level="medium",
            key_metrics={
                "property_value": "$480,000",
                "mortgage_amount": "$432,000",
                "ltv": "90%",
                "property_type": "Townhouse",
            },
        ),
        CustomerJourneyEvent(
            date="2024-04-18",
            persona="mortgage_underwriting",
            application_id="app-mw-mtg-001",
            event_type="underwriting_complete",
            title="Mortgage — Conditional Approval",
            summary="Single income ($95K). GDS 36%, TDS 42% — approaching limits. Credit score 710. 90% LTV requires CMHC insurance. Approved with conditions: confirmation of employment tenure, updated pay stubs, and mortgage insurance premium.",
            status="conditional",
            risk_level="medium",
            key_metrics={
                "gds_ratio": "36%",
                "tds_ratio": "42%",
                "credit_score": "710",
                "income": "$95,000",
                "ltv": "90%",
                "decision": "Conditional Approval",
                "conditions": "Employment verification, CMHC insurance",
                "amortization": "25 years",
                "rate": "5.24% fixed",
            },
        ),
    ]

    correlations = [
        RiskCorrelation(
            severity="warning",
            title="Cardiac Health — Cross-Product Impact",
            description="Life insurance underwriting referral (elevated BMI, hypertension, family cardiac history) correlates with subsequent health claim for cardiac evaluation. The cardiac stress test and echocardiogram results from the health claim may be material to resolving the pending underwriting decision.",
            personas_involved=["underwriting", "life_health_claims"],
        ),
        RiskCorrelation(
            severity="info",
            title="Financial Capacity — Near Limits",
            description="Mortgage ratios (GDS 36%, TDS 42%) are approaching OSFI B-20 limits on a single income. Combined with health-related insurance costs, overall financial capacity should be monitored.",
            personas_involved=["mortgage_underwriting", "underwriting"],
        ),
    ]

    save_customer_profile(storage_root, profile)
    save_customer_journey(storage_root, customer_id, events)
    save_customer_risk_correlations(storage_root, customer_id, correlations)
    print(f"  ✓ Created {profile.name} ({customer_id}) — 3 products, 6 events")


def create_priya_patel(storage_root: str) -> None:
    """Priya Patel — Higher risk, newer customer with multiple red flags."""
    customer_id = "CUST-PP-003"

    profile = CustomerProfile(
        id=customer_id,
        name="Priya Patel",
        date_of_birth="1994-01-28",
        email="priya.patel@email.com",
        phone="(647) 555-0193",
        address="3301-88 Harbour St, Toronto, ON M5J 0B5",
        customer_since="2025-09-10",
        risk_tier="high",
        tags=["new-customer", "multi-risk", "investigation"],
        notes="New customer with concurrent applications across multiple lines. Pattern of risk flags across products warrants holistic review.",
    )

    events = [
        CustomerJourneyEvent(
            date="2025-09-10",
            persona="automotive_claims",
            application_id="app-pp-auto-001",
            event_type="claim_filed",
            title="Auto Claim Filed — Significant Collision",
            summary="Major collision on Highway 401. Extensive front-end damage to 2023 BMW X5. Single-vehicle incident — claims to have swerved to avoid debris. Reported 72 hours after incident.",
            status="in_progress",
            risk_level="high",
            key_metrics={
                "claim_type": "Collision — Single Vehicle",
                "damage_severity": "Major",
                "repair_estimate": "$18,500",
                "vehicle": "2023 BMW X5",
                "delayed_reporting": "Yes (72hrs)",
            },
        ),
        CustomerJourneyEvent(
            date="2025-09-25",
            persona="automotive_claims",
            application_id="app-pp-auto-001",
            event_type="investigation_opened",
            title="Auto Claim — Under Investigation",
            summary="SIU investigation initiated. Two fraud indicators: (1) inconsistency between reported damage pattern and photos — front-end impact inconsistent with swerve maneuver; (2) 72-hour reporting delay with no police report filed. Damage photos submitted appear to show pre-existing wear on adjacent panels.",
            status="investigating",
            risk_level="high",
            key_metrics={
                "fraud_risk": "High",
                "red_flags": "2",
                "red_flag_details": "Inconsistent damage pattern, delayed reporting",
                "siu_assigned": "Yes",
                "decision": "Under Investigation",
            },
        ),
        CustomerJourneyEvent(
            date="2025-10-01",
            persona="underwriting",
            application_id="app-pp-uw-001",
            event_type="application_submitted",
            title="Life Insurance Application Submitted",
            summary="Term life insurance application — $1M coverage, 30-year term. Applicant is a recreational pilot (PPL holder) with approximately 120 flight hours.",
            status="in_progress",
            risk_level="medium",
            key_metrics={
                "coverage_amount": "$1,000,000",
                "term": "30 years",
                "product": "Term Life",
                "occupation_risk": "Recreational Pilot",
                "flight_hours": "120",
            },
        ),
        CustomerJourneyEvent(
            date="2025-10-15",
            persona="underwriting",
            application_id="app-pp-uw-001",
            event_type="additional_info_requested",
            title="Life Insurance — Pending Aviation Medical",
            summary="32-year-old female, otherwise healthy (BMI 23.4, non-smoker, no medical history). However, recreational aviation activity requires Transport Canada aviation medical certificate and flight log review. Flat extra premium for aviation rider under consideration. Pending documentation.",
            status="pending",
            risk_level="medium",
            key_metrics={
                "risk_class": "Standard — Pending Aviation Review",
                "decision": "Pending",
                "bmi": "23.4",
                "smoker": "No",
                "pending_docs": "Aviation medical certificate, flight log",
                "potential_rider": "Aviation exclusion or flat extra",
            },
        ),
        CustomerJourneyEvent(
            date="2025-10-20",
            persona="mortgage_underwriting",
            application_id="app-pp-mtg-001",
            event_type="application_submitted",
            title="Mortgage Application Submitted",
            summary="High-ratio insured mortgage for downtown Toronto condo. Self-employed applicant (freelance UX consultant).",
            status="completed",
            risk_level="high",
            key_metrics={
                "property_value": "$750,000",
                "mortgage_amount": "$712,500",
                "ltv": "95%",
                "property_type": "Condo — High-Rise",
            },
        ),
        CustomerJourneyEvent(
            date="2025-11-08",
            persona="mortgage_underwriting",
            application_id="app-pp-mtg-001",
            event_type="underwriting_complete",
            title="Mortgage — Declined",
            summary="Self-employed income ($110K gross, variable) with only 2 years' history. GDS 41% exceeds 39% limit. TDS 47% exceeds 44% limit. Credit score 680 — below preferred threshold. 95% LTV with high-rise condo concentration risk. Insufficient income stability for stress test qualification at MQR 7.24%. Application declined — advised to reapply with larger down payment and 2 additional years of income history.",
            status="declined",
            risk_level="high",
            key_metrics={
                "gds_ratio": "41%",
                "tds_ratio": "47%",
                "credit_score": "680",
                "income": "$110,000 (variable)",
                "ltv": "95%",
                "decision": "Declined",
                "decline_reasons": "GDS/TDS exceed limits, insufficient income history",
                "stress_test": "Failed at MQR 7.24%",
            },
        ),
    ]

    correlations = [
        RiskCorrelation(
            severity="critical",
            title="Multi-Product Risk Accumulation",
            description="New customer (6 months) with concurrent applications across 3 product lines, all showing elevated risk: auto claim under SIU investigation for fraud indicators, life insurance pending with aviation risk, and mortgage declined for financial overextension. The pattern of simultaneous applications combined with the auto claim investigation warrants a holistic risk review.",
            personas_involved=["automotive_claims", "underwriting", "mortgage_underwriting"],
        ),
        RiskCorrelation(
            severity="warning",
            title="Financial Stress Indicators",
            description="Mortgage declined due to GDS/TDS exceeding limits with variable self-employment income. Combined with a high-value auto claim ($18,500) under investigation, there may be financial pressure that is relevant to the fraud assessment.",
            personas_involved=["mortgage_underwriting", "automotive_claims"],
        ),
        RiskCorrelation(
            severity="info",
            title="Pending Life Insurance — Aviation Risk",
            description="Life insurance application pending aviation medical documentation. This is an isolated risk factor (recreational pilot) not directly correlated with other product risks, but the overall customer risk profile should inform the underwriting decision.",
            personas_involved=["underwriting"],
        ),
    ]

    save_customer_profile(storage_root, profile)
    save_customer_journey(storage_root, customer_id, events)
    save_customer_risk_correlations(storage_root, customer_id, correlations)
    print(f"  ✓ Created {profile.name} ({customer_id}) — 3 products, 6 events")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Customer 360 data")
    parser.add_argument(
        "--storage-root",
        default="data",
        help="Storage root directory (default: data)",
    )
    args = parser.parse_args()

    # Initialize storage provider (supports local and Azure Blob)
    from app.storage_providers import init_storage_provider, StorageSettings
    settings = StorageSettings.from_env()
    init_storage_provider(settings)
    print(f"Storage provider: {settings.backend.value}")

    print("Seeding Customer 360 data...")
    print(f"  Storage root: {args.storage_root}")
    print()

    # 1. Seed customer profiles and journey events (local filesystem)
    print("Creating customer profiles & journey events...")
    create_sarah_chen(args.storage_root)
    create_marcus_williams(args.storage_root)
    create_priya_patel(args.storage_root)

    # 2. Seed rich application data (uses storage provider abstraction)
    print()
    print("Creating rich application data...")
    app_count = seed_applications(args.storage_root)
    print(f"  ✓ Created {app_count} applications with full workbench data")

    # 3. Upload customer profiles to blob storage if using Azure
    if settings.backend.value == "azure_blob":
        print()
        print("Uploading customer profiles to Azure Blob...")
        _upload_customers_to_blob(args.storage_root, settings)

    print()
    print("Done! 3 customer profiles + 9 rich applications seeded.")


if __name__ == "__main__":
    main()
