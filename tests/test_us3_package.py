"""Tests for US-3 Submission Package Generation backend."""

import asyncio
from app.broker.acord_forms import (
    ACORD_125_FIELDS,
    ACORD_140_FIELDS,
    SOV_FIELDS,
    get_acord_form_template,
    map_extracted_to_acord125,
)
from app.broker.package_generator import SubmissionPackageGenerator


def test_acord_forms():
    """Test ACORD form templates and field schemas."""
    # Verify field counts
    assert len(ACORD_125_FIELDS) == 13, f"Expected 13 ACORD 125 fields, got {len(ACORD_125_FIELDS)}"
    assert len(ACORD_140_FIELDS) == 12, f"Expected 12 ACORD 140 fields, got {len(ACORD_140_FIELDS)}"
    assert len(SOV_FIELDS) == 7, f"Expected 7 SOV fields, got {len(SOV_FIELDS)}"
    print(f"Field counts: 125={len(ACORD_125_FIELDS)}, 140={len(ACORD_140_FIELDS)}, SOV={len(SOV_FIELDS)} OK")

    # Verify required fields
    required_125 = [k for k, v in ACORD_125_FIELDS.items() if v.get("required")]
    assert "InsuredName" in required_125
    assert "FEIN" in required_125
    assert "BusinessAddress" in required_125
    print(f"Required ACORD 125 fields: {required_125} OK")

    required_140 = [k for k, v in ACORD_140_FIELDS.items() if v.get("required")]
    assert "PropertyAddress" in required_140
    assert "BuildingValue" in required_140
    print(f"Required ACORD 140 fields: {required_140} OK")

    # Test templates
    t125 = get_acord_form_template("125")
    assert t125["form_type"] == "ACORD 125"
    assert t125["title"] == "Commercial Insurance Application"
    assert "InsuredName" in t125["fields"]
    print("get_acord_form_template('125') OK")

    t140 = get_acord_form_template("140")
    assert t140["form_type"] == "ACORD 140"
    print("get_acord_form_template('140') OK")

    tsov = get_acord_form_template("sov")
    assert tsov["form_type"] == "Statement of Values"
    print("get_acord_form_template('sov') OK")

    try:
        get_acord_form_template("999")
        assert False, "Should have raised ValueError"
    except ValueError:
        print("get_acord_form_template('999') raises ValueError OK")

    # Test field mapping
    extracted = {"applicant_name": "Test Corp", "fein": "12-345", "unknown": "x"}
    mapped = map_extracted_to_acord125(extracted)
    assert mapped["InsuredName"] == "Test Corp"
    assert mapped["FEIN"] == "12-345"
    assert "unknown" not in mapped
    print("map_extracted_to_acord125 OK")


def test_package_generator():
    """Test SubmissionPackageGenerator (non-LLM methods)."""
    # Test _sum_dollar_values
    result = SubmissionPackageGenerator._sum_dollar_values(
        "$2,500,000", "$500,000", "$750,000"
    )
    assert result == "$3,750,000", f"Got {result}"
    print(f"_sum_dollar_values: {result} OK")

    # Test _build_sov
    gen = SubmissionPackageGenerator.__new__(SubmissionPackageGenerator)
    acord_140 = {
        "property_locations": [
            {
                "address": "123 Main St",
                "occupancy": "Office",
                "building_value": "$2,500,000",
                "contents_value": "$500,000",
                "bi_value": "$750,000",
            },
            {
                "address": "456 Oak Ave",
                "occupancy": "Warehouse",
                "building_value": "$3,000,000",
                "contents_value": "$1,000,000",
                "bi_value": "$500,000",
            },
        ]
    }
    sov = gen._build_sov(acord_140)
    assert len(sov) == 2
    assert sov[0]["SiteNumber"] == "1"
    assert sov[0]["Address"] == "123 Main St"
    assert sov[0]["TotalInsuredValue"] == "$3,750,000"
    assert sov[1]["SiteNumber"] == "2"
    assert sov[1]["TotalInsuredValue"] == "$4,500,000"
    print(f"_build_sov: {len(sov)} locations OK")

    # Test compile_package
    client = {"id": "c1", "name": "Test Corp", "headquarters_address": "789 HQ St"}
    submission = {
        "id": "s1",
        "client_id": "c1",
        "line_of_business": "property",
        "effective_date": "2026-01-01",
        "expiration_date": "2027-01-01",
        "total_insured_value": "$8,250,000",
        "submitted_carriers": ["AIG", "Zurich"],
        "acord_125_fields": {"applicant_name": "Test Corp"},
        "acord_140_fields": acord_140,
        "acord_field_confidence": {"applicant_name": 0.95},
        "documents": [
            {
                "id": "d1",
                "document_type": "sov",
                "file_name": "sov.pdf",
                "uploaded_at": "2025-01-01",
            }
        ],
    }
    package = gen.compile_package(client, submission, "Dear Underwriter, ...")
    assert package["submission_id"] == "s1"
    assert package["cover_email"] == "Dear Underwriter, ..."
    assert package["acord_125"] == {"applicant_name": "Test Corp"}
    assert len(package["sov"]) == 2
    assert len(package["documents"]) == 1
    assert package["carriers"] == ["AIG", "Zurich"]
    assert package["client"]["name"] == "Test Corp"
    print("compile_package OK")

    # Test fallback email
    email = SubmissionPackageGenerator._fallback_cover_email(
        "Test Corp", "property", "2026-01-01", "$8,250,000", "  - sov.pdf"
    )
    assert "Test Corp" in email
    assert "2026-01-01" in email
    assert "sov.pdf" in email
    print("_fallback_cover_email OK")

    # Test generate_carrier_emails
    package["cover_email"] = "Dear Underwriter,\n\nPlease find attached..."
    emails = asyncio.run(gen.generate_carrier_emails(package, ["AIG", "Zurich"]))
    assert len(emails) == 2
    assert emails[0]["carrier"] == "AIG"
    assert "AIG" in emails[0]["email_subject"] or "Test Corp" in emails[0]["email_subject"]
    assert emails[1]["carrier"] == "Zurich"
    assert len(emails[0]["attachments"]) == 1
    print(f"generate_carrier_emails: {len(emails)} emails OK")


def test_api_endpoints_exist():
    """Verify all new endpoints are registered on the router."""
    from app.broker.api import router

    routes = {r.path: r.methods for r in router.routes if hasattr(r, "path")}
    print(f"\nRegistered broker routes: {len(routes)}")

    # Check new endpoints
    assert "/api/broker/submissions/{submission_id}/extract-acord" in routes
    print("POST /extract-acord registered OK")

    assert "/api/broker/submissions/{submission_id}/acord-forms" in routes
    print("GET /acord-forms registered OK")

    assert "/api/broker/submissions/{submission_id}/acord-fields" in routes
    print("PUT /acord-fields registered OK")

    assert "/api/broker/submissions/{submission_id}/generate-package" in routes
    print("POST /generate-package registered OK")

    assert "/api/broker/submissions/{submission_id}/package-email" in routes
    print("PUT /package-email registered OK")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing ACORD Forms...")
    print("=" * 60)
    test_acord_forms()

    print("\n" + "=" * 60)
    print("Testing Package Generator...")
    print("=" * 60)
    test_package_generator()

    print("\n" + "=" * 60)
    print("Testing API Endpoint Registration...")
    print("=" * 60)
    test_api_endpoints_exist()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
