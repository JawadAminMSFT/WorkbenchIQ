#!/usr/bin/env python3
"""
Batch APS Document Processing Script

Processes APS (Attending Physician Statement) documents through the WorkbenchIQ API
using large document processing mode. Designed for robustness, idempotency, and human review.

Features:
- Sequential processing to avoid overwhelming Azure OpenAI
- Idempotent: resumes from where it stopped on restart
- Generates consolidated CSV for human review
- Includes risk analysis for each application

Usage:
    python scripts/batch_process_aps.py --help
    python scripts/batch_process_aps.py --dry-run
    python scripts/batch_process_aps.py
    python scripts/batch_process_aps.py --cleanup  # Remove all created applications
    python scripts/batch_process_aps.py --reset    # Clear progress and start fresh
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

# =============================================================================
# Configuration
# =============================================================================

DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_SOURCE_FOLDER = "underwriting-aps-docs"
DEFAULT_OUTPUT_FOLDER = "batch-review-output"
DEFAULT_POLL_INTERVAL = 10  # seconds
DEFAULT_TIMEOUT = 1800  # 30 minutes
PROGRESS_TRACKER_FILENAME = "progress_tracker.csv"

# Status values for progress tracking
STATUS_PENDING = "pending"
STATUS_UPLOADED = "uploaded"
STATUS_PROCESSING = "processing"
STATUS_RUNNING_RISK = "running_risk"
STATUS_COMPLETED = "completed"
STATUS_ERROR = "error"


# =============================================================================
# Utility Functions
# =============================================================================

def log(message: str, level: str = "INFO") -> None:
    """Print a timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def log_error(message: str) -> None:
    log(message, "ERROR")


def log_warning(message: str) -> None:
    log(message, "WARN")


def log_success(message: str) -> None:
    log(message, "SUCCESS")


# =============================================================================
# Progress Tracker
# =============================================================================

class ProgressTracker:
    """Manages the progress tracking CSV for idempotent processing."""
    
    FIELDNAMES = [
        "document_filename",
        "application_id", 
        "status",
        "started_at",
        "completed_at",
        "error_message",
    ]
    
    def __init__(self, output_folder: Path):
        self.filepath = output_folder / PROGRESS_TRACKER_FILENAME
        self.records: Dict[str, Dict[str, str]] = {}
        self._load()
    
    def _load(self) -> None:
        """Load existing progress from CSV."""
        if not self.filepath.exists():
            return
        
        with open(self.filepath, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.records[row["document_filename"]] = dict(row)
        
        log(f"Loaded {len(self.records)} records from progress tracker")
    
    def _save(self) -> None:
        """Save progress to CSV."""
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            writer.writeheader()
            for record in self.records.values():
                writer.writerow(record)
    
    def get_status(self, filename: str) -> Optional[str]:
        """Get the status of a document."""
        record = self.records.get(filename)
        return record["status"] if record else None
    
    def get_application_id(self, filename: str) -> Optional[str]:
        """Get the application ID for a document."""
        record = self.records.get(filename)
        return record.get("application_id") if record else None
    
    def get_all_application_ids(self) -> List[str]:
        """Get all application IDs from the tracker."""
        return [
            r["application_id"] 
            for r in self.records.values() 
            if r.get("application_id")
        ]
    
    def update(
        self,
        filename: str,
        status: str,
        application_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update the status of a document."""
        now = datetime.now().isoformat()
        
        if filename not in self.records:
            self.records[filename] = {
                "document_filename": filename,
                "application_id": "",
                "status": STATUS_PENDING,
                "started_at": "",
                "completed_at": "",
                "error_message": "",
            }
        
        record = self.records[filename]
        record["status"] = status
        
        if application_id:
            record["application_id"] = application_id
        
        if status == STATUS_UPLOADED:
            record["started_at"] = now
        
        if status == STATUS_COMPLETED:
            record["completed_at"] = now
            record["error_message"] = ""
        
        if status == STATUS_ERROR:
            record["error_message"] = error_message or "Unknown error"
        
        self._save()
    
    def clear(self) -> None:
        """Clear all progress records."""
        self.records = {}
        if self.filepath.exists():
            self.filepath.unlink()
        log("Progress tracker cleared")
    
    def delete_if_all_complete(self) -> bool:
        """Delete the tracker file if all documents completed successfully."""
        if not self.records:
            return False
        
        all_complete = all(
            r["status"] == STATUS_COMPLETED 
            for r in self.records.values()
        )
        
        if all_complete and self.filepath.exists():
            self.filepath.unlink()
            log_success("All documents completed - progress tracker removed")
            return True
        
        return False
    
    def get_summary(self) -> Dict[str, int]:
        """Get a summary of document statuses."""
        summary = {
            STATUS_PENDING: 0,
            STATUS_UPLOADED: 0,
            STATUS_PROCESSING: 0,
            STATUS_RUNNING_RISK: 0,
            STATUS_COMPLETED: 0,
            STATUS_ERROR: 0,
        }
        for record in self.records.values():
            status = record["status"]
            if status in summary:
                summary[status] += 1
        return summary


# =============================================================================
# API Client
# =============================================================================

class WorkbenchAPIClient:
    """Client for interacting with the WorkbenchIQ API."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
    
    def health_check(self) -> bool:
        """Check if the API is reachable."""
        try:
            resp = self.session.get(f"{self.base_url}/", timeout=10)
            return resp.status_code == 200
        except requests.RequestException:
            return False
    
    def create_application(self, pdf_path: Path) -> Dict[str, Any]:
        """Upload a PDF and create a new application."""
        with open(pdf_path, "rb") as f:
            files = {"files": (pdf_path.name, f, "application/pdf")}
            data = {"persona": "underwriting"}
            resp = self.session.post(
                f"{self.base_url}/api/applications",
                files=files,
                data=data,
                timeout=60,
            )
        resp.raise_for_status()
        return resp.json()
    
    def start_processing(self, app_id: str) -> Dict[str, Any]:
        """Start processing an application with large document mode."""
        resp = self.session.post(
            f"{self.base_url}/api/applications/{app_id}/process",
            params={"processing_mode": "large_document"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    
    def get_application(self, app_id: str) -> Dict[str, Any]:
        """Get application details."""
        resp = self.session.get(
            f"{self.base_url}/api/applications/{app_id}",
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    
    def run_risk_analysis(self, app_id: str) -> Dict[str, Any]:
        """Run risk analysis on an application."""
        resp = self.session.post(
            f"{self.base_url}/api/applications/{app_id}/risk-analysis",
            timeout=300,  # Risk analysis can take a while
        )
        resp.raise_for_status()
        return resp.json()
    
    def delete_application(self, app_id: str) -> bool:
        """Delete an application. Returns True if successful or not found."""
        try:
            resp = self.session.delete(
                f"{self.base_url}/api/applications/{app_id}",
                timeout=30,
            )
            return resp.status_code in (200, 204, 404)
        except requests.RequestException:
            return False


# =============================================================================
# CSV Export
# =============================================================================

def export_review_csv(
    app_data: Dict[str, Any],
    output_folder: Path,
    document_name: str,
) -> Path:
    """Export a consolidated review CSV for human annotation."""
    
    # Create output directory named after the document (without extension)
    doc_folder = output_folder / Path(document_name).stem
    doc_folder.mkdir(parents=True, exist_ok=True)
    
    csv_path = doc_folder / "review_output.csv"
    
    fieldnames = [
        "category",
        "section", 
        "subsection",
        "value",
        "confidence",
        "source_page",
        "source_file",
        "risk_level",
        "underwriting_action",
        "policy_citations",
        "accuracy_rating",
        "issues_found",
        "corrections",
        "reviewer_notes",
    ]
    
    rows: List[Dict[str, Any]] = []
    
    # 1. Extracted Fields
    extracted_fields = app_data.get("extracted_fields") or {}
    for field_key, field_data in extracted_fields.items():
        if isinstance(field_data, dict):
            rows.append({
                "category": "extracted_field",
                "section": "",
                "subsection": field_data.get("field_name", field_key),
                "value": str(field_data.get("value", "")),
                "confidence": field_data.get("confidence", ""),
                "source_page": field_data.get("page_number", ""),
                "source_file": field_data.get("source_file", ""),
                "risk_level": "",
                "underwriting_action": "",
                "policy_citations": "",
                "accuracy_rating": "",
                "issues_found": "",
                "corrections": "",
                "reviewer_notes": "",
            })
    
    # 2. LLM Outputs
    llm_outputs = app_data.get("llm_outputs") or {}
    for section_name, section_data in llm_outputs.items():
        if isinstance(section_data, dict):
            for subsection_name, subsection_data in section_data.items():
                if isinstance(subsection_data, dict):
                    parsed = subsection_data.get("parsed", {})
                    if isinstance(parsed, dict):
                        summary = parsed.get("summary", "")
                        risk = parsed.get("risk_assessment", "")
                        action = parsed.get("underwriting_action", "")
                    else:
                        summary = str(parsed) if parsed else subsection_data.get("raw", "")
                        risk = ""
                        action = ""
                    
                    rows.append({
                        "category": "llm_output",
                        "section": section_name,
                        "subsection": subsection_name,
                        "value": summary[:2000] if summary else "",  # Truncate long summaries
                        "confidence": "",
                        "source_page": "",
                        "source_file": "",
                        "risk_level": risk,
                        "underwriting_action": action,
                        "policy_citations": "",
                        "accuracy_rating": "",
                        "issues_found": "",
                        "corrections": "",
                        "reviewer_notes": "",
                    })
    
    # 3. Risk Analysis
    risk_analysis = app_data.get("risk_analysis") or {}
    
    # Handle different risk analysis structures
    if isinstance(risk_analysis, dict):
        # Try to extract from nested structure
        for section_name, section_data in risk_analysis.items():
            if isinstance(section_data, dict):
                # Could be a nested section or a direct finding
                summary = section_data.get("summary", section_data.get("finding", ""))
                risk_level = section_data.get("risk_level", section_data.get("risk", ""))
                action = section_data.get("recommendation", section_data.get("action", ""))
                policies = section_data.get("policy_citations", section_data.get("policies", []))
                
                if isinstance(policies, list):
                    policies = ", ".join(str(p) for p in policies)
                
                rows.append({
                    "category": "risk_analysis",
                    "section": section_name,
                    "subsection": "",
                    "value": str(summary)[:2000] if summary else "",
                    "confidence": "",
                    "source_page": "",
                    "source_file": "",
                    "risk_level": risk_level,
                    "underwriting_action": action,
                    "policy_citations": policies,
                    "accuracy_rating": "",
                    "issues_found": "",
                    "corrections": "",
                    "reviewer_notes": "",
                })
            elif isinstance(section_data, str):
                rows.append({
                    "category": "risk_analysis",
                    "section": section_name,
                    "subsection": "",
                    "value": section_data[:2000],
                    "confidence": "",
                    "source_page": "",
                    "source_file": "",
                    "risk_level": "",
                    "underwriting_action": "",
                    "policy_citations": "",
                    "accuracy_rating": "",
                    "issues_found": "",
                    "corrections": "",
                    "reviewer_notes": "",
                })
    
    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    return csv_path


# =============================================================================
# Main Processing Logic
# =============================================================================

def discover_documents(source_folder: Path) -> List[Path]:
    """Find all PDF files in the source folder."""
    pdfs = sorted(source_folder.glob("*.pdf"))
    # Filter out any non-APS files (like PowerPoint files)
    return [p for p in pdfs if p.suffix.lower() == ".pdf"]


def wait_for_processing(
    client: WorkbenchAPIClient,
    app_id: str,
    poll_interval: int,
    timeout: int,
) -> Tuple[bool, Optional[str]]:
    """
    Poll until processing is complete.
    Returns (success, error_message).
    """
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            return False, f"Timeout after {timeout} seconds"
        
        try:
            app_data = client.get_application(app_id)
            status = app_data.get("processing_status")
            error = app_data.get("processing_error")
            
            if error:
                return False, f"Processing error: {error}"
            
            if status is None:
                # Processing complete
                return True, None
            
            log(f"  Status: {status} (elapsed: {int(elapsed)}s)")
            time.sleep(poll_interval)
            
        except requests.RequestException as e:
            return False, f"API error while polling: {e}"


def process_single_document(
    client: WorkbenchAPIClient,
    pdf_path: Path,
    tracker: ProgressTracker,
    output_folder: Path,
    poll_interval: int,
    timeout: int,
) -> bool:
    """
    Process a single document through the full pipeline.
    Returns True if successful.
    """
    filename = pdf_path.name
    current_status = tracker.get_status(filename)
    app_id = tracker.get_application_id(filename)
    
    log(f"Processing: {filename}")
    
    # Step 1: Upload if needed
    if current_status in (None, STATUS_PENDING):
        log("  Uploading...")
        try:
            result = client.create_application(pdf_path)
            app_id = result["id"]
            tracker.update(filename, STATUS_UPLOADED, application_id=app_id)
            log(f"  Created application: {app_id}")
        except requests.RequestException as e:
            log_error(f"  Upload failed: {e}")
            tracker.update(filename, STATUS_ERROR, error_message=str(e))
            return False
    
    # Step 2: Start processing if needed
    if tracker.get_status(filename) == STATUS_UPLOADED:
        log("  Starting extraction and analysis...")
        try:
            client.start_processing(app_id)
            tracker.update(filename, STATUS_PROCESSING, application_id=app_id)
        except requests.RequestException as e:
            log_error(f"  Failed to start processing: {e}")
            tracker.update(filename, STATUS_ERROR, application_id=app_id, error_message=str(e))
            return False
    
    # Step 3: Wait for processing to complete
    if tracker.get_status(filename) == STATUS_PROCESSING:
        log("  Waiting for extraction and analysis...")
        success, error = wait_for_processing(client, app_id, poll_interval, timeout)
        if not success:
            log_error(f"  Processing failed: {error}")
            tracker.update(filename, STATUS_ERROR, application_id=app_id, error_message=error)
            return False
        tracker.update(filename, STATUS_RUNNING_RISK, application_id=app_id)
    
    # Step 4: Run risk analysis
    if tracker.get_status(filename) == STATUS_RUNNING_RISK:
        log("  Running risk analysis...")
        try:
            client.run_risk_analysis(app_id)
            log("  Risk analysis complete")
        except requests.RequestException as e:
            # Log but don't fail - risk analysis is optional
            log_warning(f"  Risk analysis failed (continuing): {e}")
    
    # Step 5: Export CSV
    log("  Exporting review CSV...")
    try:
        app_data = client.get_application(app_id)
        csv_path = export_review_csv(app_data, output_folder, filename)
        log(f"  Exported: {csv_path}")
    except Exception as e:
        log_error(f"  CSV export failed: {e}")
        tracker.update(filename, STATUS_ERROR, application_id=app_id, error_message=str(e))
        return False
    
    # Mark complete
    tracker.update(filename, STATUS_COMPLETED, application_id=app_id)
    log_success(f"  Completed: {filename}")
    return True


def cleanup_applications(
    client: WorkbenchAPIClient,
    tracker: ProgressTracker,
    output_folder: Path,
) -> None:
    """Delete all applications created by this script and clean up output files."""
    app_ids = tracker.get_all_application_ids()
    
    if not app_ids:
        log("No applications to clean up")
    else:
        log(f"Cleaning up {len(app_ids)} applications...")
        
        for app_id in app_ids:
            if app_id:
                log(f"  Deleting application: {app_id}")
                if client.delete_application(app_id):
                    log(f"    Deleted: {app_id}")
                else:
                    log_warning(f"    Failed to delete: {app_id}")
    
    # Clear the progress tracker
    tracker.clear()
    
    # Remove output folders
    if output_folder.exists():
        import shutil
        for item in output_folder.iterdir():
            if item.is_dir():
                log(f"  Removing output folder: {item.name}")
                shutil.rmtree(item)
        
        # Remove progress tracker if it exists
        progress_file = output_folder / PROGRESS_TRACKER_FILENAME
        if progress_file.exists():
            progress_file.unlink()
    
    log_success("Cleanup complete")


def run_batch_processing(
    api_url: str,
    source_folder: Path,
    output_folder: Path,
    poll_interval: int,
    timeout: int,
    dry_run: bool = False,
) -> int:
    """
    Run the batch processing pipeline.
    Returns exit code (0 for success, 1 for errors).
    """
    # Initialize client
    client = WorkbenchAPIClient(api_url)
    
    # Check backend connectivity
    log(f"Checking backend connectivity: {api_url}")
    if not client.health_check():
        log_error("Backend is not reachable. Please ensure the API server is running.")
        return 1
    log_success("Backend is online")
    
    # Discover documents
    documents = discover_documents(source_folder)
    if not documents:
        log_error(f"No PDF files found in: {source_folder}")
        return 1
    log(f"Found {len(documents)} PDF documents")
    
    # Initialize progress tracker
    output_folder.mkdir(parents=True, exist_ok=True)
    tracker = ProgressTracker(output_folder)
    
    # Initialize records for any new documents
    for doc in documents:
        if tracker.get_status(doc.name) is None:
            tracker.update(doc.name, STATUS_PENDING)
    
    # Show summary
    summary = tracker.get_summary()
    log(f"Status: {summary[STATUS_COMPLETED]} completed, "
        f"{summary[STATUS_ERROR]} errors, "
        f"{summary[STATUS_PENDING] + summary[STATUS_UPLOADED] + summary[STATUS_PROCESSING] + summary[STATUS_RUNNING_RISK]} pending")
    
    if dry_run:
        log("DRY RUN - Documents that would be processed:")
        for doc in documents:
            status = tracker.get_status(doc.name)
            if status != STATUS_COMPLETED:
                print(f"  [{status or 'new'}] {doc.name}")
        return 0
    
    # Process documents sequentially
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for doc in documents:
        status = tracker.get_status(doc.name)
        
        if status == STATUS_COMPLETED:
            log(f"Skipping (already completed): {doc.name}")
            skipped_count += 1
            continue
        
        if process_single_document(
            client, doc, tracker, output_folder, poll_interval, timeout
        ):
            success_count += 1
        else:
            error_count += 1
    
    # Final summary
    log("=" * 60)
    log(f"BATCH PROCESSING COMPLETE")
    log(f"  Processed: {success_count}")
    log(f"  Errors:    {error_count}")
    log(f"  Skipped:   {skipped_count}")
    log("=" * 60)
    
    # Clean up progress tracker if all complete
    tracker.delete_if_all_complete()
    
    return 0 if error_count == 0 else 1


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Batch process APS documents through WorkbenchIQ API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/batch_process_aps.py --dry-run
  python scripts/batch_process_aps.py
  python scripts/batch_process_aps.py --cleanup
  python scripts/batch_process_aps.py --reset
        """,
    )
    
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"Backend API URL (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--source-folder",
        default=DEFAULT_SOURCE_FOLDER,
        help=f"Folder containing APS PDFs (default: {DEFAULT_SOURCE_FOLDER})",
    )
    parser.add_argument(
        "--output-folder",
        default=DEFAULT_OUTPUT_FOLDER,
        help=f"Output folder for review CSVs (default: {DEFAULT_OUTPUT_FOLDER})",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        help=f"Seconds between status polls (default: {DEFAULT_POLL_INTERVAL})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Max seconds to wait per document (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List documents without processing",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear progress tracker and start fresh (keeps created applications)",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete all applications created by this script and clear outputs",
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to the project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    source_folder = project_root / args.source_folder
    output_folder = project_root / args.output_folder
    
    # Handle cleanup mode
    if args.cleanup:
        log("CLEANUP MODE")
        client = WorkbenchAPIClient(args.api_url)
        
        if not client.health_check():
            log_warning("Backend not reachable - will only clean local files")
            # Create a dummy tracker to clear local files
            tracker = ProgressTracker(output_folder)
            tracker.clear()
            
            # Still try to remove output folders
            if output_folder.exists():
                import shutil
                for item in output_folder.iterdir():
                    if item.is_dir():
                        log(f"  Removing output folder: {item.name}")
                        shutil.rmtree(item)
            log_success("Local cleanup complete")
        else:
            tracker = ProgressTracker(output_folder)
            cleanup_applications(client, tracker, output_folder)
        
        return 0
    
    # Handle reset mode
    if args.reset:
        log("RESET MODE - Clearing progress tracker")
        tracker = ProgressTracker(output_folder)
        tracker.clear()
        log("Progress cleared. Run again without --reset to start fresh processing.")
        return 0
    
    # Validate source folder
    if not source_folder.exists():
        log_error(f"Source folder not found: {source_folder}")
        return 1
    
    # Run batch processing
    return run_batch_processing(
        api_url=args.api_url,
        source_folder=source_folder,
        output_folder=output_folder,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
