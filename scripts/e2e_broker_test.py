"""
End-to-end broker API test using real sample data from data/broker-sample-data-v2/.
Creates clients, uploads research docs, runs research, creates submissions,
uploads documents & quotes, extracts ACORD fields, runs comparison, generates packages.
Performs accuracy analysis on all responses.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/broker"
DATA_DIR = Path("data/broker-sample-data-v2")

# ── Helpers ─────────────────────────────────────────────────────────────────

def api(method, path, **kwargs):
    url = f"{BASE_URL}{path}"
    r = getattr(requests, method)(url, **kwargs)
    return r

def check(label, response, expected_status=200):
    ok = response.status_code == expected_status
    status = "✅" if ok else "❌"
    print(f"  {status} {label}: HTTP {response.status_code}")
    if not ok:
        try:
            print(f"     Response: {response.json()}")
        except Exception:
            print(f"     Response: {response.text[:500]}")
    return ok

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


# ── Client definitions ──────────────────────────────────────────────────────

CLIENTS = [
    {
        "name": "Oakwood Commercial Properties LLC",
        "industry_code": "531120",
        "business_type": "LLC",
        "years_in_business": 18,
        "annual_revenue": "$42,000,000",
        "employee_count": 95,
        "headquarters_address": "2500 Commerce Blvd, Suite 400, Milwaukee, WI 53202",
        "property_locations": [
            {"address": "1200 Industrial Park Dr, Milwaukee, WI 53215", "building_value": "$8,500,000", "contents_value": "$2,100,000", "construction_type": "Fire Resistive", "occupancy_type": "Office/Warehouse"},
            {"address": "4500 Lakeshore Ave, Racine, WI 53403", "building_value": "$12,000,000", "contents_value": "$3,500,000", "construction_type": "Modified Fire Resistive", "occupancy_type": "Mixed-Use Retail"},
            {"address": "780 Technology Way, Waukesha, WI 53186", "building_value": "$6,200,000", "contents_value": "$1,800,000", "construction_type": "Non-Combustible", "occupancy_type": "Light Manufacturing"},
        ],
        "renewal_date": (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d"),
        "broker_notes": "Long-standing client. Portfolio of commercial properties across SE Wisconsin. Looking to consolidate coverage under fewer carriers. Prior claim for roof damage at Racine location in 2023.",
        "contacts": [
            {"name": "Sarah Chen", "email": "schen@oakwoodcommercial.com", "phone": "414-555-0123", "role": "CFO"},
            {"name": "Marcus Rivera", "email": "mrivera@oakwoodcommercial.com", "phone": "414-555-0124", "role": "VP Risk Management"},
        ],
    },
    {
        "name": "Summit Industrial Group Inc",
        "industry_code": "332999",
        "business_type": "Corporation",
        "years_in_business": 12,
        "annual_revenue": "$28,000,000",
        "employee_count": 210,
        "headquarters_address": "1000 Summit Pkwy, Green Bay, WI 54304",
        "property_locations": [
            {"address": "1000 Summit Pkwy, Green Bay, WI 54304", "building_value": "$15,000,000", "contents_value": "$8,000,000", "construction_type": "Non-Combustible", "occupancy_type": "Heavy Manufacturing"},
            {"address": "2200 Foundry Rd, Appleton, WI 54914", "building_value": "$9,500,000", "contents_value": "$5,500,000", "construction_type": "Joisted Masonry", "occupancy_type": "Manufacturing/Distribution"},
        ],
        "renewal_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "broker_notes": "Manufacturing client with significant equipment values. Recent expansion to Appleton facility. Interested in competitive quoting for property and inland marine. History of minor WC claims.",
        "contacts": [
            {"name": "James Kowalski", "email": "jkowalski@summitindustrial.com", "phone": "920-555-0201", "role": "CEO"},
            {"name": "Linda Park", "email": "lpark@summitindustrial.com", "phone": "920-555-0202", "role": "Risk Manager"},
        ],
    },
]

# Map carrier names to their research doc files
CARRIER_DOCS = {
    "Acuity": ["Acuity - AMB Credit Report (Feb 2025).pdf", "Acuity - MD&A 2025.pdf"],
    "IN Farmers": ["IN Farmers - AMB Credit Report (Jun 2024).pdf", "IN Farmers - MD&A 2025.pdf"],
    "Midwest Family": ["Midwest Family - AMB Credit Report (Apr 2025).pdf", "Midwest Family - MD&A 2025.pdf"],
    "Preferred": ["Preferred - AMB Credit Report (Jul 2024).pdf", "Preferred - MD&A 2025.pdf"],
    "Society": ["Society - AMB Credit Report (Jun 2024).pdf", "Society - MD&A 2025.pdf"],
}

QUOTE_FILES = [
    ("AIG", "sample-quote-aig.pdf"),
    ("Hartford", "sample-quote-hartford.docx"),
    ("Travelers", "sample-quote-travelers.pdf"),
]

# Map client names to their SOV + loss-run submission documents
CLIENT_SUBMISSION_DOCS = {
    "Oakwood": {
        "sov": "oakwood-sov.txt",
        "loss_runs": "oakwood-loss-runs.txt",
    },
    "Summit": {
        "sov": "summit-sov.txt",
        "loss_runs": "summit-loss-runs.txt",
    },
}

# ── Test state tracking ─────────────────────────────────────────────────────

results = {
    "clients": [],
    "research": [],
    "submissions": [],
    "documents": [],
    "acord_extraction": [],
    "quotes": [],
    "comparisons": [],
    "packages": [],
    "bugs": [],
    "accuracy": [],
}


def log_bug(component, description, details=None):
    bug = {"component": component, "description": description, "details": details}
    results["bugs"].append(bug)
    print(f"  🐛 BUG [{component}]: {description}")
    if details:
        print(f"     Details: {json.dumps(details, indent=2)[:500]}")


def log_accuracy(component, metric, value, expected=None, status="info"):
    entry = {"component": component, "metric": metric, "value": value, "expected": expected, "status": status}
    results["accuracy"].append(entry)
    icon = {"pass": "✅", "warn": "⚠️", "fail": "❌", "info": "ℹ️"}.get(status, "ℹ️")
    print(f"  {icon} [{component}] {metric}: {value}" + (f" (expected: {expected})" if expected else ""))


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 1: CREATE CLIENTS
# ═══════════════════════════════════════════════════════════════════════════

def phase1_create_clients():
    section("PHASE 1: Create Test Clients")
    for client_data in CLIENTS:
        r = api("post", "/clients", json=client_data)
        if not check(f"Create client: {client_data['name']}", r, 201):
            log_bug("client_creation", f"Failed to create {client_data['name']}", r.text)
            continue
        client = r.json()
        results["clients"].append(client)
        print(f"     ID: {client['id']}")
        print(f"     Properties: {len(client.get('property_locations', []))}")
        print(f"     Contacts: {len(client.get('contacts', []))}")

        # Verify roundtrip
        r2 = api("get", f"/clients/{client['id']}")
        check(f"Get client roundtrip: {client_data['name']}", r2)
        if r2.status_code == 200:
            fetched = r2.json()
            if fetched["name"] != client_data["name"]:
                log_bug("client_creation", "Name mismatch on roundtrip", {"sent": client_data["name"], "got": fetched["name"]})
            if len(fetched.get("property_locations", [])) != len(client_data.get("property_locations", [])):
                log_bug("client_creation", "Property locations count mismatch")
            if len(fetched.get("contacts", [])) != len(client_data.get("contacts", [])):
                log_bug("client_creation", "Contacts count mismatch")


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 2: UPLOAD RESEARCH DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════

def phase2_upload_research_docs():
    section("PHASE 2: Upload Carrier Research Documents")
    for client in results["clients"]:
        cid = client["id"]
        cname = client["name"]
        print(f"\n  📁 Client: {cname}")

        for carrier, files in CARRIER_DOCS.items():
            for fname in files:
                fpath = DATA_DIR / fname
                if not fpath.exists():
                    log_bug("research_docs", f"File not found: {fname}")
                    continue
                doc_type = "am_best" if "Credit Report" in fname else "annual_report"
                with open(fpath, "rb") as f:
                    r = api("post", f"/clients/{cid}/research-documents",
                            files={"file": (fname, f, "application/pdf")},
                            data={"document_type": doc_type})
                if not check(f"Upload {carrier} - {doc_type}", r, 200):
                    # Try 201 too
                    if r.status_code == 201:
                        print(f"     (Got 201 instead of 200 - still OK)")
                    else:
                        log_bug("research_docs", f"Upload failed for {fname}", r.text[:200])
                        continue
                doc_meta = r.json()
                print(f"     Doc ID: {doc_meta.get('id', '?')}, Type: {doc_meta.get('document_type', '?')}")

        # Verify docs listing
        r = api("get", f"/clients/{cid}/research-documents")
        if check(f"List research docs for {cname}", r):
            docs = r.json()
            log_accuracy("research_docs", f"Docs uploaded for {cname}", len(docs), 10,
                        "pass" if len(docs) >= 10 else "fail")


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 3: RUN RESEARCH
# ═══════════════════════════════════════════════════════════════════════════

def phase3_run_research():
    section("PHASE 3: Run Client Research")
    for client in results["clients"]:
        cid = client["id"]
        cname = client["name"]
        print(f"\n  🔍 Researching: {cname}")

        # Get doc IDs
        r = api("get", f"/clients/{cid}/research-documents")
        doc_ids = [d["id"] for d in r.json()] if r.status_code == 200 else []

        r = api("post", f"/clients/{cid}/research",
                json={"company_name": cname, "document_ids": doc_ids},
                timeout=120)
        if not check(f"Research {cname}", r):
            log_bug("research", f"Research failed for {cname}", r.text[:300])
            results["research"].append({"client": cname, "error": True})
            continue

        brief = r.json()
        results["research"].append({"client": cname, "brief": brief})

        # Accuracy checks
        fields_to_check = [
            "business_description", "headquarters", "industry_sector",
            "annual_revenue", "employee_count", "confidence_level",
            "insurance_needs", "carrier_matches", "citations", "data_sources"
        ]
        populated = sum(1 for f in fields_to_check if brief.get(f))
        log_accuracy("research", f"Fields populated for {cname}",
                    f"{populated}/{len(fields_to_check)}", "10/10",
                    "pass" if populated >= 8 else "warn" if populated >= 5 else "fail")

        if brief.get("citations"):
            log_accuracy("research", f"Citations count for {cname}", len(brief["citations"]), ">=1",
                        "pass" if len(brief["citations"]) >= 1 else "warn")
        else:
            log_accuracy("research", f"Citations for {cname}", "EMPTY", ">=1", "warn")

        if brief.get("data_sources"):
            has_uploaded = any("Uploaded" in ds for ds in brief.get("data_sources", []))
            log_accuracy("research", f"Data sources include uploaded docs ({cname})",
                        brief["data_sources"], "Should include Uploaded Documents",
                        "pass" if has_uploaded else "fail")

        if brief.get("carrier_matches"):
            log_accuracy("research", f"Carrier matches for {cname}",
                        len(brief["carrier_matches"]), ">=3",
                        "pass" if len(brief["carrier_matches"]) >= 3 else "warn")

        if brief.get("insurance_needs"):
            log_accuracy("research", f"Insurance needs for {cname}",
                        len(brief["insurance_needs"]), ">=2",
                        "pass" if len(brief["insurance_needs"]) >= 2 else "warn")

        # Check research history
        r = api("get", f"/clients/{cid}/research-history")
        if check(f"Research history for {cname}", r):
            history = r.json()
            log_accuracy("research", f"Research history entries for {cname}",
                        len(history), ">=1",
                        "pass" if len(history) >= 1 else "fail")


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 4: CREATE SUBMISSIONS & UPLOAD DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════

def phase4_create_submissions():
    section("PHASE 4: Create Submissions & Upload Documents")
    for client in results["clients"]:
        cid = client["id"]
        cname = client["name"]
        print(f"\n  📋 Creating submission for: {cname}")

        tiv = "$26,800,000" if "Oakwood" in cname else "$38,000,000"
        sub_data = {
            "client_id": cid,
            "line_of_business": "property",
            "effective_date": (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d"),
            "expiration_date": (datetime.now() + timedelta(days=45+365)).strftime("%Y-%m-%d"),
            "total_insured_value": tiv,
            "coverage_requested": {
                "property": True,
                "business_interruption": True,
                "inland_marine": "Summit" in cname,
                "general_liability": False,
            },
            "submitted_carriers": ["AIG", "Hartford", "Travelers"],
        }
        r = api("post", "/submissions", json=sub_data)
        if not check(f"Create submission for {cname}", r, 201):
            log_bug("submission", f"Create failed for {cname}", r.text[:300])
            continue

        sub = r.json()
        results["submissions"].append(sub)
        print(f"     Submission ID: {sub['id']}")
        print(f"     Status: {sub['status']}")
        print(f"     TIV: {sub.get('total_insured_value')}")

        # Upload carrier credit reports & MD&As as submission documents
        sid = sub["id"]

        # Upload SOV and loss-run documents (critical for ACORD extraction)
        client_key = "Oakwood" if "Oakwood" in cname else "Summit"
        if client_key in CLIENT_SUBMISSION_DOCS:
            for doc_label, fname in CLIENT_SUBMISSION_DOCS[client_key].items():
                fpath = DATA_DIR / fname
                if not fpath.exists():
                    log_bug("document_upload", f"Submission doc not found: {fname}")
                    continue
                with open(fpath, "rb") as f:
                    r = api("post", f"/submissions/{sid}/documents",
                            files={"file": (fname, f, "text/plain")},
                            data={"document_type": "other"})
                if r.status_code in (200, 201):
                    doc = r.json()
                    results["documents"].append(doc)
                    print(f"     📎 Uploaded: {fname} → {doc.get('document_type', doc_label)}")
                else:
                    log_bug("document_upload", f"Upload failed: {fname}", r.text[:200])

        for carrier, files in CARRIER_DOCS.items():
            for fname in files:
                fpath = DATA_DIR / fname
                if not fpath.exists():
                    continue
                doc_type = "other"
                mime = "application/pdf"
                with open(fpath, "rb") as f:
                    r = api("post", f"/submissions/{sid}/documents",
                            files={"file": (fname, f, mime)},
                            data={"document_type": doc_type})
                if r.status_code in (200, 201):
                    doc = r.json()
                    results["documents"].append(doc)
                    print(f"     📎 Uploaded: {fname} → {doc.get('document_type', doc_type)}")
                else:
                    log_bug("document_upload", f"Upload failed: {fname}", r.text[:200])

        # Verify document listing
        r = api("get", f"/submissions/{sid}")
        if check(f"Get submission with docs for {cname}", r):
            sub_full = r.json()
            doc_count = len(sub_full.get("documents", []))
            log_accuracy("documents", f"Documents uploaded for {cname}",
                        doc_count, ">=12",
                        "pass" if doc_count >= 12 else "warn")


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 5: EXTRACT ACORD FIELDS
# ═══════════════════════════════════════════════════════════════════════════

def phase5_extract_acord():
    section("PHASE 5: Extract ACORD Fields")
    for sub in results["submissions"]:
        sid = sub["id"]
        cname = next((c["name"] for c in results["clients"] if c["id"] == sub["client_id"]), "?")
        print(f"\n  📝 Extracting ACORD fields for: {cname}")

        r = api("post", f"/submissions/{sid}/extract-acord", timeout=120)
        if not check(f"Extract ACORD for {cname}", r):
            log_bug("acord_extraction", f"Extract failed for {cname}", r.text[:300])
            results["acord_extraction"].append({"submission_id": sid, "error": True})
            continue

        acord = r.json()
        results["acord_extraction"].append(acord)

        # Check ACORD 125 fields
        a125 = acord.get("acord_125", {})
        a125_filled = sum(1 for v in a125.values() if v and v not in ("", "N/A", "Not provided", None))
        log_accuracy("acord_125", f"Fields populated for {cname}",
                    f"{a125_filled}/{len(a125)}", ">=5",
                    "pass" if a125_filled >= 5 else "warn" if a125_filled >= 3 else "fail")

        # Check ACORD 140 fields
        a140 = acord.get("acord_140", {})
        a140_filled = sum(1 for v in a140.values() if v and v not in ("", "N/A", "Not provided", None, []))
        log_accuracy("acord_140", f"Fields populated for {cname}",
                    f"{a140_filled}/{len(a140)}", ">=3",
                    "pass" if a140_filled >= 3 else "warn" if a140_filled >= 1 else "fail")

        # Check confidence
        confidence = acord.get("confidence", {})
        if confidence:
            avg_conf = sum(confidence.values()) / len(confidence) if confidence else 0
            log_accuracy("acord_confidence", f"Average confidence for {cname}",
                        f"{avg_conf:.2f}", ">=0.5",
                        "pass" if avg_conf >= 0.5 else "warn" if avg_conf >= 0.3 else "fail")

        # Check field_sources
        sources = acord.get("field_sources", {})
        log_accuracy("acord_sources", f"Field sources for {cname}",
                    len(sources), ">=1",
                    "pass" if len(sources) >= 1 else "warn")

        # Get ACORD forms view
        r2 = api("get", f"/submissions/{sid}/acord-forms")
        if check(f"Get ACORD forms view for {cname}", r2):
            forms = r2.json()
            print(f"     ACORD 125 form fields: {len(forms.get('acord_125', {}).get('fields', {}))}")
            print(f"     ACORD 140 form fields: {len(forms.get('acord_140', {}).get('fields', {}))}")


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 6: UPLOAD QUOTES & RUN COMPARISON
# ═══════════════════════════════════════════════════════════════════════════

def phase6_quotes_and_comparison():
    section("PHASE 6: Upload Quotes & Run Comparison")
    for sub in results["submissions"]:
        sid = sub["id"]
        cname = next((c["name"] for c in results["clients"] if c["id"] == sub["client_id"]), "?")
        print(f"\n  💰 Processing quotes for: {cname}")

        # Upload each quote
        for carrier, fname in QUOTE_FILES:
            fpath = DATA_DIR / fname
            if not fpath.exists():
                log_bug("quote_upload", f"Quote file not found: {fname}")
                continue
            mime = "application/pdf" if fname.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            with open(fpath, "rb") as f:
                r = api("post", f"/submissions/{sid}/quotes",
                        files={"file": (fname, f, mime)},
                        data={"carrier_name": carrier},
                        timeout=120)
            if r.status_code in (200, 201):
                quote_resp = r.json()
                results["quotes"].append({"carrier": carrier, "submission_id": sid, "response": quote_resp})
                print(f"     📊 {carrier}: {quote_resp.get('status', '?')} - {quote_resp.get('message', '')}")
            else:
                log_bug("quote_upload", f"Quote upload failed: {carrier} - {fname}", r.text[:300])

        # Verify quotes
        r = api("get", f"/submissions/{sid}/quotes")
        if check(f"List quotes for {cname}", r):
            quotes = r.json()
            log_accuracy("quotes", f"Quotes ingested for {cname}",
                        len(quotes), "3",
                        "pass" if len(quotes) == 3 else "warn")

            for q in quotes:
                fields = q.get("fields", {})
                carrier = q.get("carrier_name", "?")
                premium = fields.get("annual_premium", "")
                tiv = fields.get("total_insured_value", "")
                deductible = fields.get("deductible", "")
                print(f"     {carrier}: Premium={premium}, TIV={tiv}, Deductible={deductible}")

                # Check key fields populated
                key_fields = ["annual_premium", "deductible", "policy_period"]
                filled = sum(1 for kf in key_fields if fields.get(kf) and fields[kf] not in ("", "N/A", None))
                log_accuracy("quote_fields", f"{carrier} key fields for {cname}",
                            f"{filled}/{len(key_fields)}", "3/3",
                            "pass" if filled == len(key_fields) else "warn" if filled >= 1 else "fail")

                # Check confidence
                conf = q.get("confidence_scores", {})
                if conf:
                    avg_conf = sum(conf.values()) / len(conf)
                    log_accuracy("quote_confidence", f"{carrier} avg confidence",
                                f"{avg_conf:.2f}", ">=0.6",
                                "pass" if avg_conf >= 0.6 else "warn")

        # Run comparison
        print(f"\n  ⚖️  Running quote comparison for: {cname}")
        r = api("post", f"/submissions/{sid}/compare",
                json={"weights": {"premium_weight": 35, "coverage_weight": 30,
                                  "financial_weight": 20, "completeness_weight": 15}},
                timeout=120)
        if not check(f"Quote comparison for {cname}", r):
            log_bug("comparison", f"Comparison failed for {cname}", r.text[:300])
            continue

        comp = r.json()
        results["comparisons"].append({"client": cname, "comparison": comp})

        table = comp.get("comparison_table", [])
        rec = comp.get("recommendation", "")
        scores = comp.get("placement_scores", [])
        log_accuracy("comparison", f"Comparison table rows for {cname}",
                    len(table), ">=1",
                    "pass" if len(table) >= 1 else "fail")
        log_accuracy("comparison", f"Placement scores for {cname}",
                    len(scores), ">=1",
                    "pass" if len(scores) >= 1 else "fail")
        if rec:
            print(f"     📌 Recommendation: {rec[:200]}")
        for s in scores:
            print(f"     {s.get('carrier', '?')}: Score={s.get('placement_score', '?')}, Rank={s.get('placement_rank', '?')}")


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 7: GENERATE PACKAGES
# ═══════════════════════════════════════════════════════════════════════════

def phase7_generate_packages():
    section("PHASE 7: Generate Submission Packages")
    for sub in results["submissions"]:
        sid = sub["id"]
        cname = next((c["name"] for c in results["clients"] if c["id"] == sub["client_id"]), "?")
        print(f"\n  📦 Generating package for: {cname}")

        r = api("post", f"/submissions/{sid}/generate-package",
                json={"carriers": ["AIG", "Hartford", "Travelers"]},
                timeout=120)
        if not check(f"Generate package for {cname}", r):
            log_bug("package", f"Package generation failed for {cname}", r.text[:300])
            continue

        pkg = r.json()
        results["packages"].append({"client": cname, "package": pkg})

        # Check package components
        has_email = bool(pkg.get("cover_email"))
        has_125 = bool(pkg.get("acord_125"))
        has_140 = bool(pkg.get("acord_140"))
        has_carriers = bool(pkg.get("carriers"))
        log_accuracy("package", f"Cover email for {cname}", "Present" if has_email else "Missing", "Present",
                    "pass" if has_email else "fail")
        log_accuracy("package", f"ACORD 125 in package for {cname}", "Present" if has_125 else "Missing", "Present",
                    "pass" if has_125 else "warn")
        log_accuracy("package", f"ACORD 140 in package for {cname}", "Present" if has_140 else "Missing", "Present",
                    "pass" if has_140 else "warn")
        if has_email:
            print(f"     Email preview: {pkg['cover_email'][:200]}...")


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 8: DASHBOARD VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════

def phase8_dashboard():
    section("PHASE 8: Dashboard Verification")
    r = api("get", "/dashboard")
    if check("Dashboard loads", r):
        d = r.json()
        print(f"     Total accounts: {d.get('total_accounts')}")
        print(f"     Open submissions: {d.get('open_submissions')}")
        print(f"     Renewals (90d): {d.get('renewals_due_90_days')}")
        log_accuracy("dashboard", "Total accounts includes new clients",
                    d.get("total_accounts", 0), ">=4",
                    "pass" if d.get("total_accounts", 0) >= 4 else "fail")


# ═══════════════════════════════════════════════════════════════════════════
#  FINAL REPORT
# ═══════════════════════════════════════════════════════════════════════════

def final_report():
    section("FINAL ACCURACY REPORT")
    
    total_checks = len(results["accuracy"])
    passes = sum(1 for a in results["accuracy"] if a["status"] == "pass")
    warns = sum(1 for a in results["accuracy"] if a["status"] == "warn")
    fails = sum(1 for a in results["accuracy"] if a["status"] == "fail")
    bugs = len(results["bugs"])

    print(f"\n  📊 Accuracy Checks: {total_checks}")
    print(f"     ✅ Pass: {passes}")
    print(f"     ⚠️  Warn: {warns}")
    print(f"     ❌ Fail: {fails}")
    print(f"     🐛 Bugs: {bugs}")
    print(f"     Score: {passes}/{total_checks} ({100*passes/max(total_checks,1):.0f}%)")

    if bugs:
        print(f"\n  🐛 BUGS FOUND:")
        for i, bug in enumerate(results["bugs"], 1):
            print(f"     {i}. [{bug['component']}] {bug['description']}")

    if fails:
        print(f"\n  ❌ FAILURES:")
        for a in results["accuracy"]:
            if a["status"] == "fail":
                print(f"     [{a['component']}] {a['metric']}: got {a['value']}, expected {a['expected']}")

    if warns:
        print(f"\n  ⚠️  WARNINGS:")
        for a in results["accuracy"]:
            if a["status"] == "warn":
                print(f"     [{a['component']}] {a['metric']}: got {a['value']}, expected {a['expected']}")

    # Save full results
    report_path = Path("data/broker-sample-data-v2/test-results.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  💾 Full results saved to: {report_path}")

    return bugs == 0 and fails == 0


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "🚀" * 35)
    print("  COMMERCIAL BROKERAGE E2E TEST")
    print("  Using real sample data from data/broker-sample-data-v2/")
    print("🚀" * 35)

    try:
        phase1_create_clients()
        phase2_upload_research_docs()
        phase3_run_research()
        phase4_create_submissions()
        phase5_extract_acord()
        phase6_quotes_and_comparison()
        phase7_generate_packages()
        phase8_dashboard()
        success = final_report()
        
        if success:
            print("\n  🎉 ALL TESTS PASSED - Data preserved in UI for review!")
        else:
            print("\n  ⚠️  Tests completed with issues - see report above")
        
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n  💥 FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        final_report()
        sys.exit(2)
