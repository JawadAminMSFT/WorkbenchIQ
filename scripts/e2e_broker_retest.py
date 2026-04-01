"""
Re-test script: Fix and re-run the failing phases from the initial E2E test.
Uses existing clients created in the first run.
Uploads proper submission documents (SOV, loss runs), re-extracts ACORD fields,
re-uploads quotes with proper parsing, and re-runs comparison.
"""

import json
import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/broker"
DATA_DIR = Path("data/broker-sample-data-v2")

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
            print(f"     Body: {json.dumps(response.json(), indent=2)[:500]}")
        except Exception:
            print(f"     Body: {response.text[:500]}")
    return ok

def section(title):
    print(f"\n{'='*70}\n  {title}\n{'='*70}")

# ── Find existing clients ────────────────────────────────────────────────

print("🔍 Finding existing test clients...")
r = api("get", "/clients")
clients = r.json()
oakwood = next((c for c in clients if "Oakwood" in c.get("name", "")), None)
summit = next((c for c in clients if "Summit" in c.get("name", "")), None)

if not oakwood or not summit:
    print("❌ Test clients not found! Run the full E2E test first.")
    sys.exit(1)

print(f"  ✅ Oakwood: {oakwood['id']}")
print(f"  ✅ Summit: {summit['id']}")

CLIENT_DOCS = {
    oakwood["id"]: {
        "name": "Oakwood Commercial Properties LLC",
        "sov": "oakwood-sov.txt",
        "loss_runs": "oakwood-loss-runs.txt",
    },
    summit["id"]: {
        "name": "Summit Industrial Group Inc",
        "sov": "summit-sov.txt",
        "loss_runs": "summit-loss-runs.txt",
    },
}

QUOTE_FILES = [
    ("AIG", "sample-quote-aig.pdf"),
    ("Hartford", "sample-quote-hartford.docx"),
    ("Travelers", "sample-quote-travelers.pdf"),
]

results = {
    "acord": [],
    "quotes": [],
    "comparisons": [],
    "packages": [],
    "bugs": [],
    "accuracy": [],
}

def log_accuracy(component, metric, value, expected=None, status="info"):
    entry = {"component": component, "metric": metric, "value": value, "expected": expected, "status": status}
    results["accuracy"].append(entry)
    icon = {"pass": "✅", "warn": "⚠️", "fail": "❌", "info": "ℹ️"}.get(status, "ℹ️")
    print(f"  {icon} [{component}] {metric}: {value}" + (f" (expected: {expected})" if expected else ""))

def log_bug(component, description, details=None):
    bug = {"component": component, "description": description, "details": details}
    results["bugs"].append(bug)
    print(f"  🐛 BUG [{component}]: {description}")

# ═══════════════════════════════════════════════════════════════════════════
#  STEP 1: Create new submissions with SOV + loss runs
# ═══════════════════════════════════════════════════════════════════════════

section("STEP 1: Create New Submissions with SOV + Loss Runs")

submissions = {}
for cid, info in CLIENT_DOCS.items():
    cname = info["name"]
    print(f"\n  📋 Creating submission for: {cname}")

    tiv = "$36,760,000" if "Oakwood" in cname else "$46,500,000"
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
        },
        "submitted_carriers": ["AIG", "Hartford", "Travelers"],
    }
    r = api("post", "/submissions", json=sub_data)
    if not check(f"Create submission for {cname}", r, 201):
        log_bug("submission", f"Create failed for {cname}", r.text[:300])
        continue

    sub = r.json()
    submissions[cid] = sub
    sid = sub["id"]
    print(f"     Submission ID: {sid}")

    # Upload SOV
    sov_path = DATA_DIR / info["sov"]
    with open(sov_path, "rb") as f:
        r = api("post", f"/submissions/{sid}/documents",
                files={"file": (info["sov"], f, "text/plain")},
                data={"document_type": "sov"})
    check(f"Upload SOV for {cname}", r, 201) or check(f"Upload SOV for {cname}", r, 200)
    if r.status_code in (200, 201):
        print(f"     📎 SOV uploaded: {r.json().get('document_type')}")

    # Upload Loss Runs
    lr_path = DATA_DIR / info["loss_runs"]
    with open(lr_path, "rb") as f:
        r = api("post", f"/submissions/{sid}/documents",
                files={"file": (info["loss_runs"], f, "text/plain")},
                data={"document_type": "loss_runs"})
    check(f"Upload Loss Runs for {cname}", r, 201) or check(f"Upload Loss Runs for {cname}", r, 200)
    if r.status_code in (200, 201):
        print(f"     📎 Loss Runs uploaded: {r.json().get('document_type')}")

    # Also upload carrier credit reports as research context
    carrier_docs = [
        ("Acuity - AMB Credit Report (Feb 2025).pdf", "am_best"),
        ("Acuity - MD&A 2025.pdf", "annual_report"),
        ("Society - AMB Credit Report (Jun 2024).pdf", "am_best"),
    ]
    for fname, doc_type in carrier_docs:
        fpath = DATA_DIR / fname
        if fpath.exists():
            with open(fpath, "rb") as f:
                r = api("post", f"/submissions/{sid}/documents",
                        files={"file": (fname, f, "application/pdf")},
                        data={"document_type": doc_type})
            if r.status_code in (200, 201):
                print(f"     📎 Uploaded: {fname}")

    # Verify docs
    r = api("get", f"/submissions/{sid}")
    if r.status_code == 200:
        doc_count = len(r.json().get("documents", []))
        log_accuracy("documents", f"Total docs for {cname}", doc_count, ">=5",
                    "pass" if doc_count >= 5 else "warn")

# ═══════════════════════════════════════════════════════════════════════════
#  STEP 2: Extract ACORD Fields
# ═══════════════════════════════════════════════════════════════════════════

section("STEP 2: Extract ACORD Fields from SOV + Loss Runs")

for cid, sub in submissions.items():
    sid = sub["id"]
    cname = CLIENT_DOCS[cid]["name"]
    print(f"\n  📝 Extracting ACORD fields for: {cname}")

    r = api("post", f"/submissions/{sid}/extract-acord", timeout=120)
    if not check(f"Extract ACORD for {cname}", r):
        log_bug("acord_extraction", f"Extract failed for {cname}", r.text[:300])
        continue

    acord = r.json()
    results["acord"].append({"client": cname, "data": acord})

    # ACORD 125 analysis
    a125 = acord.get("acord_125", {})
    a125_filled = {}
    for k, v in a125.items():
        if v and v not in ("", "N/A", "Not provided", None, "null"):
            a125_filled[k] = v
    
    print(f"     ACORD 125 fields filled: {len(a125_filled)}/{len(a125)}")
    for k, v in list(a125_filled.items())[:8]:
        print(f"       {k}: {str(v)[:80]}")

    log_accuracy("acord_125", f"Fields populated for {cname}",
                f"{len(a125_filled)}/{len(a125)}", ">=8",
                "pass" if len(a125_filled) >= 8 else "warn" if len(a125_filled) >= 4 else "fail")

    # ACORD 140 analysis
    a140 = acord.get("acord_140", {})
    a140_filled = {}
    for k, v in a140.items():
        if v and v not in ("", "N/A", "Not provided", None, "null", []):
            a140_filled[k] = v
    
    print(f"     ACORD 140 fields filled: {len(a140_filled)}/{len(a140)}")
    for k, v in list(a140_filled.items())[:8]:
        val = str(v)[:80] if not isinstance(v, list) else f"[{len(v)} items]"
        print(f"       {k}: {val}")

    log_accuracy("acord_140", f"Fields populated for {cname}",
                f"{len(a140_filled)}/{len(a140)}", ">=5",
                "pass" if len(a140_filled) >= 5 else "warn" if len(a140_filled) >= 2 else "fail")

    # Confidence
    confidence = acord.get("confidence", {})
    if confidence:
        avg_conf = sum(confidence.values()) / len(confidence)
        log_accuracy("acord_confidence", f"Avg confidence for {cname}",
                    f"{avg_conf:.2f}", ">=0.6",
                    "pass" if avg_conf >= 0.6 else "warn" if avg_conf >= 0.3 else "fail")

    # Field sources
    sources = acord.get("field_sources", {})
    log_accuracy("acord_sources", f"Field sources for {cname}",
                len(sources), ">=3",
                "pass" if len(sources) >= 3 else "warn" if len(sources) >= 1 else "fail")
    if sources:
        print(f"     Source files: {set(sources.values())}")

    # Specific accuracy checks
    if "Oakwood" in cname:
        checks = {
            "applicant_name": "Oakwood",
            "fein": "39-1234567",
            "business_type": "Liability",
            "years_in_business": "18",
        }
        for field, expected_substr in checks.items():
            val = str(a125.get(field, ""))
            if expected_substr.lower() in val.lower():
                log_accuracy("acord_data", f"{field} for {cname}", val, f"contains '{expected_substr}'", "pass")
            else:
                log_accuracy("acord_data", f"{field} for {cname}", val, f"contains '{expected_substr}'", "fail")

# ═══════════════════════════════════════════════════════════════════════════
#  STEP 3: Upload & Extract Quotes
# ═══════════════════════════════════════════════════════════════════════════

section("STEP 3: Upload & Extract Quotes")

for cid, sub in submissions.items():
    sid = sub["id"]
    cname = CLIENT_DOCS[cid]["name"]
    print(f"\n  💰 Uploading quotes for: {cname}")

    for carrier, fname in QUOTE_FILES:
        fpath = DATA_DIR / fname
        if not fpath.exists():
            log_bug("quote_upload", f"File not found: {fname}")
            continue
        ext = fname.rsplit(".", 1)[-1].lower()
        mime_map = {"pdf": "application/pdf", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        mime = mime_map.get(ext, "application/octet-stream")
        
        with open(fpath, "rb") as f:
            r = api("post", f"/submissions/{sid}/quotes",
                    files={"file": (fname, f, mime)},
                    data={"carrier_name": carrier},
                    timeout=120)
        if r.status_code in (200, 201):
            resp = r.json()
            print(f"     📊 {carrier}: {resp.get('status', '?')} - {resp.get('message', '')}")
            results["quotes"].append({"carrier": carrier, "submission_id": sid, "response": resp})
        else:
            log_bug("quote_upload", f"Upload failed: {carrier}", r.text[:300])

    # Verify quotes
    r = api("get", f"/submissions/{sid}/quotes")
    if check(f"List quotes for {cname}", r):
        quotes = r.json()
        log_accuracy("quotes", f"Quotes ingested for {cname}", len(quotes), "3",
                    "pass" if len(quotes) == 3 else "warn")

        for q in quotes:
            fields = q.get("fields", {})
            carrier = q.get("carrier_name", "?")
            premium = fields.get("annual_premium", "")
            tiv = fields.get("total_insured_value", "")
            deductible = fields.get("deductible", "")
            bi_limit = fields.get("business_interruption_limit", "")
            policy_period = fields.get("policy_period", "")
            rating = fields.get("carrier_am_best_rating", "")
            
            print(f"\n     --- {carrier} Quote Details ---")
            print(f"       Premium: {premium}")
            print(f"       TIV: {tiv}")
            print(f"       Deductible: {deductible}")
            print(f"       BI Limit: {bi_limit}")
            print(f"       Policy Period: {policy_period}")
            print(f"       AM Best: {rating}")
            print(f"       Exclusions: {fields.get('named_perils_exclusions', [])}")
            print(f"       Conditions: {fields.get('special_conditions', [])[:3]}")

            # Key field checks
            key_fields = ["annual_premium", "deductible", "policy_period", "total_insured_value"]
            filled = sum(1 for kf in key_fields if fields.get(kf) and str(fields[kf]) not in ("", "N/A", "None"))
            log_accuracy("quote_fields", f"{carrier} key fields for {cname}",
                        f"{filled}/{len(key_fields)}", f"{len(key_fields)}/{len(key_fields)}",
                        "pass" if filled == len(key_fields) else "warn" if filled >= 2 else "fail")

            conf = q.get("confidence_scores", {})
            if conf:
                avg = sum(conf.values()) / len(conf)
                log_accuracy("quote_confidence", f"{carrier} avg confidence",
                            f"{avg:.2f}", ">=0.6",
                            "pass" if avg >= 0.6 else "warn" if avg >= 0.3 else "fail")

            # Specific accuracy checks
            if carrier == "AIG":
                if premium and "$43" in premium.replace(",", ""):
                    log_accuracy("quote_accuracy", f"AIG premium for {cname}", premium, "~$43,100", "pass")
                elif premium:
                    log_accuracy("quote_accuracy", f"AIG premium for {cname}", premium, "~$43,100", "warn")
                else:
                    log_accuracy("quote_accuracy", f"AIG premium for {cname}", "EMPTY", "~$43,100", "fail")
            elif carrier == "Travelers":
                if premium and "$42" in premium.replace(",", ""):
                    log_accuracy("quote_accuracy", f"Travelers premium for {cname}", premium, "~$42,800", "pass")
                elif premium:
                    log_accuracy("quote_accuracy", f"Travelers premium for {cname}", premium, "~$42,800", "warn")
                else:
                    log_accuracy("quote_accuracy", f"Travelers premium for {cname}", "EMPTY", "~$42,800", "fail")

# ═══════════════════════════════════════════════════════════════════════════
#  STEP 4: Run Quote Comparison
# ═══════════════════════════════════════════════════════════════════════════

section("STEP 4: Run Quote Comparison")

for cid, sub in submissions.items():
    sid = sub["id"]
    cname = CLIENT_DOCS[cid]["name"]
    print(f"\n  ⚖️  Comparing quotes for: {cname}")

    r = api("post", f"/submissions/{sid}/compare",
            json={"weights": {"premium_weight": 35, "coverage_weight": 30,
                              "financial_weight": 20, "completeness_weight": 15}},
            timeout=120)
    if not check(f"Comparison for {cname}", r):
        log_bug("comparison", f"Comparison failed for {cname}", r.text[:300])
        continue

    comp = r.json()
    results["comparisons"].append({"client": cname, "comparison": comp})

    table = comp.get("comparison_table", [])
    rec = comp.get("recommendation", "")
    scores = comp.get("placement_scores", [])

    log_accuracy("comparison", f"Table rows for {cname}", len(table), "3",
                "pass" if len(table) == 3 else "warn")
    log_accuracy("comparison", f"Has recommendation for {cname}",
                "Yes" if rec and rec != "No recommendation available." else "No",
                "Yes",
                "pass" if rec and rec != "No recommendation available." else "fail")

    if rec:
        print(f"     📌 Recommendation: {rec[:300]}")

    for s in scores:
        carrier = s.get("carrier", "?")
        score = s.get("placement_score", 0)
        rank = s.get("placement_rank", 0)
        adequacy = s.get("coverage_adequacy", "?")
        gaps = s.get("coverage_gaps", [])
        print(f"     {carrier}: Score={score}, Rank={rank}, Adequacy={adequacy}")
        if gaps:
            print(f"       Gaps: {gaps[:3]}")

        log_accuracy("scores", f"{carrier} score for {cname}",
                    score, ">0",
                    "pass" if score > 0 else "fail")

# ═══════════════════════════════════════════════════════════════════════════
#  STEP 5: Generate Packages
# ═══════════════════════════════════════════════════════════════════════════

section("STEP 5: Generate Submission Packages")

for cid, sub in submissions.items():
    sid = sub["id"]
    cname = CLIENT_DOCS[cid]["name"]
    print(f"\n  📦 Generating package for: {cname}")

    r = api("post", f"/submissions/{sid}/generate-package",
            json={"carriers": ["AIG", "Hartford", "Travelers"]},
            timeout=120)
    if not check(f"Package for {cname}", r):
        log_bug("package", f"Package failed for {cname}", r.text[:300])
        continue

    pkg = r.json()
    results["packages"].append({"client": cname, "package": pkg})

    has_email = bool(pkg.get("cover_email"))
    has_125 = bool(pkg.get("acord_125"))
    has_140 = bool(pkg.get("acord_140"))
    log_accuracy("package", f"Cover email for {cname}", "Present" if has_email else "Missing", "Present",
                "pass" if has_email else "fail")
    log_accuracy("package", f"ACORD 125 for {cname}", "Present" if has_125 else "Missing", "Present",
                "pass" if has_125 else "warn")
    log_accuracy("package", f"ACORD 140 for {cname}", "Present" if has_140 else "Missing", "Present",
                "pass" if has_140 else "warn")

    if has_email:
        print(f"     Email preview: {pkg['cover_email'][:250]}...")

# ═══════════════════════════════════════════════════════════════════════════
#  STEP 6: Re-run Research with PDF Parsing
# ═══════════════════════════════════════════════════════════════════════════

section("STEP 6: Re-run Research (with PDF Parsing)")

for cid, info in CLIENT_DOCS.items():
    cname = info["name"]
    print(f"\n  🔍 Re-researching: {cname}")

    # Get doc IDs
    r = api("get", f"/clients/{cid}/research-documents")
    doc_ids = [d["id"] for d in r.json()] if r.status_code == 200 else []
    print(f"     Using {len(doc_ids)} research documents")

    r = api("post", f"/clients/{cid}/research",
            json={"company_name": cname, "document_ids": doc_ids},
            timeout=300)
    if not check(f"Research {cname}", r):
        log_bug("research", f"Research failed for {cname}", r.text[:300])
        continue

    brief = r.json()
    
    # Check for carrier-specific data from the credit reports
    carrier_matches = brief.get("carrier_matches", [])
    print(f"     Carrier matches: {len(carrier_matches)}")
    for cm in carrier_matches[:5]:
        carrier = cm.get("carrier", "?")
        rating = cm.get("rating", "?")
        appetite = cm.get("appetite", "?")
        print(f"       {carrier}: Rating={rating}, Appetite={appetite}")

    log_accuracy("research_v2", f"Carrier matches for {cname}",
                len(carrier_matches), ">=3",
                "pass" if len(carrier_matches) >= 3 else "warn")

    # Check if uploaded doc data is reflected
    data_sources = brief.get("data_sources", [])
    has_uploaded = any("Uploaded" in ds for ds in data_sources)
    log_accuracy("research_v2", f"Uses uploaded docs for {cname}",
                "Yes" if has_uploaded else "No", "Yes",
                "pass" if has_uploaded else "fail")

    citations = brief.get("citations", [])
    log_accuracy("research_v2", f"Citations for {cname}",
                len(citations), ">=1",
                "pass" if len(citations) >= 1 else "warn")

# ═══════════════════════════════════════════════════════════════════════════
#  STEP 7: Dashboard Check
# ═══════════════════════════════════════════════════════════════════════════

section("STEP 7: Dashboard Verification")

r = api("get", "/dashboard")
if check("Dashboard loads", r):
    d = r.json()
    print(f"     Accounts: {d.get('total_accounts')}")
    print(f"     Open submissions: {d.get('open_submissions')}")
    print(f"     Renewals: {d.get('renewals_due_90_days')}")
    log_accuracy("dashboard", "Total accounts", d.get("total_accounts", 0), ">=4",
                "pass" if d.get("total_accounts", 0) >= 4 else "fail")

# ═══════════════════════════════════════════════════════════════════════════
#  FINAL REPORT
# ═══════════════════════════════════════════════════════════════════════════

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
    print(f"\n  🐛 BUGS:")
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

# Save results
report_path = Path("data/broker-sample-data-v2/retest-results.json")
with open(report_path, "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\n  💾 Results saved to: {report_path}")

if fails == 0 and bugs == 0:
    print("\n  🎉 ALL CHECKS PASSED!")
    sys.exit(0)
else:
    print(f"\n  ⚠️  {fails} failures, {bugs} bugs — fixes needed")
    sys.exit(1)
