"""Integration test using Ridgeview submission data."""

from app.broker.storage import BrokerStorage
from app.broker.acord_forms import get_acord_form_template, map_extracted_to_acord125
from app.broker.package_generator import SubmissionPackageGenerator


def test_ridgeview_integration():
    storage = BrokerStorage()
    sub_id = "78a85f5b-8cd6-4546-a8fc-ff068896b3a5"
    client_id = "eb6348e3-457e-46c3-a6ff-0d92a53d19a6"

    sub = storage.get_submission(sub_id)
    client = storage.get_client(client_id)
    assert sub is not None, "Ridgeview submission not found"
    assert client is not None, "Ridgeview client not found"

    name = client["name"]
    print(f"Client: {name}")
    print(f"Submission TIV: {sub['total_insured_value']}, carriers: {sub['submitted_carriers']}")

    # Test ACORD form templates
    t125 = get_acord_form_template("125")
    t140 = get_acord_form_template("140")
    tsov = get_acord_form_template("sov")
    assert len(t125["fields"]) == 13
    assert len(t140["fields"]) == 12
    assert len(tsov["fields"]) == 7
    print(f"Templates OK: 125={len(t125['fields'])}f, 140={len(t140['fields'])}f, SOV={len(tsov['fields'])}f")

    # Test compile_package with real data
    gen = SubmissionPackageGenerator.__new__(SubmissionPackageGenerator)
    email = gen._fallback_cover_email(
        name, sub["line_of_business"],
        sub["effective_date"], sub["total_insured_value"],
        "  - (No documents attached)",
    )
    package = gen.compile_package(client, sub, email)

    assert package["submission_id"] == sub_id
    assert package["client"]["name"] == name
    assert package["carriers"] == ["AIG", "Zurich", "Travelers"]
    assert len(package["cover_email"]) > 50
    print(f"Package: cover_email={len(package['cover_email'])}c, carriers={package['carriers']}")

    # Test carrier emails
    import asyncio
    emails = asyncio.run(gen.generate_carrier_emails(package, package["carriers"]))
    assert len(emails) == 3
    for e in emails:
        assert e["carrier"] in ["AIG", "Zurich", "Travelers"]
        assert name in e["email_subject"]
        print(f"  Carrier email: {e['carrier']} — subject: {e['email_subject'][:60]}...")


if __name__ == "__main__":
    test_ridgeview_integration()
    print("\n=== Ridgeview integration test PASSED ===")
