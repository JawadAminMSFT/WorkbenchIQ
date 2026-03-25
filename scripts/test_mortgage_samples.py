#!/usr/bin/env python3
"""
Upload all 7 Mortgage Underwriting Profile sets to the Azure-deployed
WorkbenchIQ backend, run extraction + analysis, poll for completion,
and verify the mortgage detail endpoint returns valid data.

Usage:
    python scripts/test_mortgage_samples.py [--base-url URL]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

BASE_URL = "https://workbenchiq-api.azurewebsites.net"
PROFILES_DIR = Path(__file__).resolve().parent.parent / "mortgage-research" / "Mortgage Underwriting Profiles"
PERSONA = "mortgage"  # will be normalised to mortgage_underwriting by backend


def upload_application(base_url: str, pdf_paths: list[Path], ref: str) -> dict:
    """Create an application by uploading PDFs."""
    url = f"{base_url}/api/applications"
    files = [("files", (p.name, open(p, "rb"), "application/pdf")) for p in pdf_paths]
    data = {"persona": PERSONA}
    if ref:
        data["external_reference"] = ref

    print(f"  Uploading {len(pdf_paths)} files ...")
    resp = requests.post(url, files=files, data=data, timeout=120)
    # Close file handles
    for _, fobj in files:
        fobj[1].close()

    resp.raise_for_status()
    app = resp.json()
    print(f"  Created app {app['id']} (status={app.get('status')})")
    return app


def run_extract_and_analyze(base_url: str, app_id: str) -> dict:
    """Kick off background extraction + analysis via /process endpoint."""
    url = f"{base_url}/api/applications/{app_id}/process"
    resp = requests.post(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def poll_until_done(base_url: str, app_id: str, timeout_s: int = 600, interval_s: int = 10) -> dict:
    """Poll the application until processing_status is None (done) or error."""
    url = f"{base_url}/api/applications/{app_id}"
    start = time.time()
    while True:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        app = resp.json()
        status = app.get("processing_status")
        elapsed = int(time.time() - start)
        if status is None:
            print(f"  ✓ Processing complete ({elapsed}s)")
            return app
        if status == "error":
            err = app.get("processing_error", "unknown")
            print(f"  ✗ Processing error after {elapsed}s: {err}")
            return app
        if time.time() - start > timeout_s:
            print(f"  ✗ Timed out after {timeout_s}s (status={status})")
            return app
        print(f"    ... {status} ({elapsed}s)", end="\r")
        time.sleep(interval_s)


def verify_mortgage_detail(base_url: str, app_id: str) -> dict:
    """Call the mortgage-specific detail endpoint and check fields."""
    url = f"{base_url}/api/mortgage/applications/{app_id}"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.json()


def run_set(base_url: str, set_dir: Path) -> dict:
    """Process one profile set end-to-end."""
    set_name = set_dir.name
    print(f"\n{'='*60}")
    print(f"SET: {set_name}")
    print(f"{'='*60}")

    pdfs = sorted(set_dir.glob("*.pdf"))
    if not pdfs:
        print("  ⚠ No PDFs found, skipping")
        return {"set": set_name, "status": "skipped", "reason": "no PDFs"}

    # 1) Upload
    try:
        app = upload_application(base_url, pdfs, ref=set_name)
    except Exception as e:
        print(f"  ✗ Upload failed: {e}")
        return {"set": set_name, "status": "upload_failed", "error": str(e)}

    app_id = app["id"]

    # 2) Extract + Analyze
    try:
        run_extract_and_analyze(base_url, app_id)
        print(f"  Extraction + analysis started in background")
    except Exception as e:
        print(f"  ✗ Extract/analyze trigger failed: {e}")
        return {"set": set_name, "status": "trigger_failed", "app_id": app_id, "error": str(e)}

    # 3) Poll
    final_app = poll_until_done(base_url, app_id, timeout_s=600)
    app_status = final_app.get("status")
    proc_status = final_app.get("processing_status")

    if proc_status == "error":
        return {
            "set": set_name, "status": "processing_error",
            "app_id": app_id, "error": final_app.get("processing_error"),
        }

    # 4) Verify mortgage detail
    try:
        detail = verify_mortgage_detail(base_url, app_id)
    except Exception as e:
        print(f"  ✗ Mortgage detail endpoint failed: {e}")
        return {"set": set_name, "status": "detail_failed", "app_id": app_id, "error": str(e)}

    borrower = detail.get("borrower", {}).get("name", "Unknown")
    decision = detail.get("decision", "N/A")
    gds = detail.get("ratios", {}).get("gds", 0)
    tds = detail.get("ratios", {}).get("tds", 0)
    ltv = detail.get("ratios", {}).get("ltv", 0)
    findings_count = len(detail.get("findings", []))
    docs_count = len(detail.get("documents", []))

    print(f"  Borrower: {borrower}")
    print(f"  Decision: {decision}")
    print(f"  GDS: {gds}%  TDS: {tds}%  LTV: {ltv}%")
    print(f"  Findings: {findings_count}  Documents: {docs_count}")

    # Validation checks
    issues = []
    if docs_count == 0:
        issues.append("no documents in response")
    if findings_count == 0:
        issues.append("no findings generated")
    if decision not in ("APPROVE", "DECLINE", "REFER"):
        issues.append(f"unexpected decision: {decision}")

    if issues:
        print(f"  ⚠ Issues: {', '.join(issues)}")
    else:
        print(f"  ✓ All checks passed")

    return {
        "set": set_name, "status": "success" if not issues else "issues",
        "app_id": app_id, "borrower": borrower, "decision": decision,
        "gds": gds, "tds": tds, "ltv": ltv,
        "findings": findings_count, "documents": docs_count,
        "issues": issues,
    }


def main():
    parser = argparse.ArgumentParser(description="Test mortgage sample profiles")
    parser.add_argument("--base-url", default=BASE_URL, help="Backend API base URL")
    parser.add_argument("--sets", nargs="*", help="Specific set numbers to run (e.g. 1 3 7)")
    args = parser.parse_args()

    if not PROFILES_DIR.exists():
        print(f"Profiles directory not found: {PROFILES_DIR}")
        sys.exit(1)

    set_dirs = sorted(PROFILES_DIR.iterdir())
    if args.sets:
        set_dirs = [d for d in set_dirs if any(f"Set {n}" in d.name or f"set {n}" in d.name.lower() for n in args.sets)]

    print(f"WorkbenchIQ Mortgage Sample Test")
    print(f"Backend: {args.base_url}")
    print(f"Sets to process: {len(set_dirs)}")

    # Health check
    try:
        r = requests.get(f"{args.base_url}/", timeout=10)
        print(f"Backend health: {r.status_code} - {r.json().get('status', 'unknown')}")
    except Exception as e:
        print(f"Backend unreachable: {e}")
        sys.exit(1)

    results = []
    for set_dir in set_dirs:
        if not set_dir.is_dir():
            continue
        result = run_set(args.base_url, set_dir)
        results.append(result)

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    passed = sum(1 for r in results if r["status"] == "success")
    issues = sum(1 for r in results if r["status"] == "issues")
    failed = sum(1 for r in results if r["status"] not in ("success", "issues", "skipped"))
    skipped = sum(1 for r in results if r["status"] == "skipped")

    for r in results:
        icon = "✓" if r["status"] == "success" else "⚠" if r["status"] == "issues" else "✗"
        line = f"  {icon} {r['set']}: {r['status']}"
        if r.get("decision"):
            line += f" → {r['decision']}"
        if r.get("issues"):
            line += f" ({', '.join(r['issues'])})"
        if r.get("error"):
            line += f" [{r['error'][:60]}]"
        print(line)

    print(f"\nTotal: {passed} passed, {issues} with issues, {failed} failed, {skipped} skipped")

    # Save results to JSON
    results_path = Path(__file__).parent / "mortgage_test_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {results_path}")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
