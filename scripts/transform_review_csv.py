#!/usr/bin/env python3
"""
Transform Review Output CSV to Human-Readable Format

Reads the existing review_output.csv files from batch-review-output and generates
flattened, human-readable CSV files suitable for manual review and annotation.

Usage:
    uv run scripts/transform_review_csv.py
    uv run scripts/transform_review_csv.py --input-folder batch-review-output
    uv run scripts/transform_review_csv.py --dry-run
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def log(message: str, level: str = "INFO") -> None:
    """Print a timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def safe_parse_json_or_python(value: str) -> Any:
    """Try to parse a value as JSON or Python literal, return original if fails."""
    if not value or not isinstance(value, str):
        return value
    
    value = value.strip()
    if not value:
        return value
    
    # Try JSON first
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Try Python literal (for dict/list representations)
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        pass
    
    return value


def extract_simple_value(obj: Any, max_length: int = 500) -> str:
    """Extract a simple string value from a potentially complex object."""
    if obj is None:
        return ""
    
    if isinstance(obj, str):
        return obj[:max_length] if len(obj) > max_length else obj
    
    if isinstance(obj, (int, float, bool)):
        return str(obj)
    
    if isinstance(obj, dict):
        # Look for common value keys
        for key in ['valueString', 'value', 'valueNumber', 'valueBoolean', 'valueDate']:
            if key in obj:
                return extract_simple_value(obj[key], max_length)
        
        # If it's a simple dict with just a few keys, format nicely
        if len(obj) <= 3:
            parts = []
            for k, v in obj.items():
                if k not in ['type', 'spans', 'source', 'confidence', 'offset', 'length']:
                    parts.append(f"{k}: {extract_simple_value(v, 100)}")
            if parts:
                result = "; ".join(parts)
                return result[:max_length] if len(result) > max_length else result
    
    if isinstance(obj, list):
        if len(obj) == 0:
            return ""
        # Extract values from list items
        values = []
        for item in obj[:10]:  # Limit to first 10 items
            val = extract_simple_value(item, 100)
            if val:
                values.append(val)
        result = " | ".join(values)
        return result[:max_length] if len(result) > max_length else result
    
    # Fallback: convert to string
    result = str(obj)
    return result[:max_length] if len(result) > max_length else result


def flatten_extracted_field(field_name: str, raw_value: str, confidence: str, source_page: str, source_file: str) -> List[Dict[str, str]]:
    """Flatten an extracted field into one or more human-readable rows."""
    rows = []
    
    parsed = safe_parse_json_or_python(raw_value)
    
    # Simple value case
    if isinstance(parsed, (str, int, float, bool)) or parsed is None:
        rows.append({
            "category": "Extracted Field",
            "field": field_name,
            "subfield": "",
            "value": str(parsed) if parsed else "",
            "confidence": confidence,
            "source_page": source_page,
            "source_file": source_file,
            "accuracy_rating": "",
            "issues_found": "",
            "corrections": "",
            "reviewer_notes": "",
        })
        return rows
    
    # Dict case - flatten each key
    if isinstance(parsed, dict):
        # Check if it's a nested field structure (like LipidPanelResults)
        has_nested = any(isinstance(v, dict) for v in parsed.values())
        
        if has_nested:
            for subfield, subvalue in parsed.items():
                if isinstance(subvalue, dict):
                    extracted_val = extract_simple_value(subvalue)
                    sub_conf = subvalue.get('confidence', '') if isinstance(subvalue, dict) else ''
                    rows.append({
                        "category": "Extracted Field",
                        "field": field_name,
                        "subfield": subfield,
                        "value": extracted_val,
                        "confidence": str(sub_conf) if sub_conf else confidence,
                        "source_page": source_page,
                        "source_file": source_file,
                        "accuracy_rating": "",
                        "issues_found": "",
                        "corrections": "",
                        "reviewer_notes": "",
                    })
                else:
                    rows.append({
                        "category": "Extracted Field",
                        "field": field_name,
                        "subfield": subfield,
                        "value": extract_simple_value(subvalue),
                        "confidence": confidence,
                        "source_page": source_page,
                        "source_file": source_file,
                        "accuracy_rating": "",
                        "issues_found": "",
                        "corrections": "",
                        "reviewer_notes": "",
                    })
        else:
            # Simple dict - show as single value
            rows.append({
                "category": "Extracted Field",
                "field": field_name,
                "subfield": "",
                "value": extract_simple_value(parsed),
                "confidence": confidence,
                "source_page": source_page,
                "source_file": source_file,
                "accuracy_rating": "",
                "issues_found": "",
                "corrections": "",
                "reviewer_notes": "",
            })
        return rows
    
    # List case - flatten each item
    if isinstance(parsed, list):
        for i, item in enumerate(parsed[:20]):  # Limit to 20 items
            if isinstance(item, dict):
                # Look for valueObject pattern
                if 'valueObject' in item:
                    item = item['valueObject']
                
                # Extract key fields from the item
                item_parts = []
                for k, v in item.items():
                    if k not in ['type', 'spans', 'source', 'offset', 'length']:
                        val = extract_simple_value(v, 100)
                        if val:
                            item_parts.append(f"{k}: {val}")
                
                if item_parts:
                    rows.append({
                        "category": "Extracted Field",
                        "field": field_name,
                        "subfield": f"[{i+1}]",
                        "value": "; ".join(item_parts),
                        "confidence": confidence,
                        "source_page": source_page,
                        "source_file": source_file,
                        "accuracy_rating": "",
                        "issues_found": "",
                        "corrections": "",
                        "reviewer_notes": "",
                    })
            else:
                rows.append({
                    "category": "Extracted Field",
                    "field": field_name,
                    "subfield": f"[{i+1}]",
                    "value": extract_simple_value(item),
                    "confidence": confidence,
                    "source_page": source_page,
                    "source_file": source_file,
                    "accuracy_rating": "",
                    "issues_found": "",
                    "corrections": "",
                    "reviewer_notes": "",
                })
        return rows
    
    # Fallback
    rows.append({
        "category": "Extracted Field",
        "field": field_name,
        "subfield": "",
        "value": extract_simple_value(parsed),
        "confidence": confidence,
        "source_page": source_page,
        "source_file": source_file,
        "accuracy_rating": "",
        "issues_found": "",
        "corrections": "",
        "reviewer_notes": "",
    })
    return rows


def flatten_llm_output(section: str, subsection: str, value: str, risk_level: str, underwriting_action: str) -> List[Dict[str, str]]:
    """Flatten an LLM output into human-readable rows."""
    rows = []
    
    # Clean up section/subsection names for display
    display_section = section.replace("_", " ").title() if section else ""
    display_subsection = subsection.replace("_", " ").title() if subsection else ""
    
    # Truncate long values but keep them readable
    display_value = value[:2000] if value else ""
    
    rows.append({
        "category": "LLM Analysis",
        "field": display_section,
        "subfield": display_subsection,
        "value": display_value,
        "confidence": risk_level,  # Use risk_level as confidence for LLM outputs
        "source_page": "",
        "source_file": "",
        "accuracy_rating": "",
        "issues_found": "",
        "corrections": "",
        "reviewer_notes": "",
    })
    
    # Add underwriting action as separate row if present
    if underwriting_action:
        rows.append({
            "category": "LLM Analysis",
            "field": display_section,
            "subfield": f"{display_subsection} - Action",
            "value": underwriting_action[:1000],
            "confidence": "",
            "source_page": "",
            "source_file": "",
            "accuracy_rating": "",
            "issues_found": "",
            "corrections": "",
            "reviewer_notes": "",
        })
    
    return rows


def flatten_risk_analysis(section: str, value: str, risk_level: str, underwriting_action: str, policy_citations: str) -> List[Dict[str, str]]:
    """Flatten risk analysis into human-readable rows."""
    rows = []
    
    # Parse the value if it's JSON (like the raw risk analysis)
    parsed = safe_parse_json_or_python(value)
    
    if isinstance(parsed, dict):
        # Handle the full risk analysis JSON structure
        if 'findings' in parsed:
            # Overall assessment
            overall_risk = parsed.get('overall_risk_level', '')
            overall_rationale = parsed.get('overall_rationale', '')
            
            rows.append({
                "category": "Risk Analysis",
                "field": "Overall Assessment",
                "subfield": "Risk Level",
                "value": overall_risk,
                "confidence": "",
                "source_page": "",
                "source_file": "",
                "accuracy_rating": "",
                "issues_found": "",
                "corrections": "",
                "reviewer_notes": "",
            })
            
            rows.append({
                "category": "Risk Analysis",
                "field": "Overall Assessment",
                "subfield": "Rationale",
                "value": overall_rationale[:2000],
                "confidence": "",
                "source_page": "",
                "source_file": "",
                "accuracy_rating": "",
                "issues_found": "",
                "corrections": "",
                "reviewer_notes": "",
            })
            
            # Individual findings
            for i, finding in enumerate(parsed.get('findings', []), 1):
                category = finding.get('category', '').replace('_', ' ').title()
                finding_text = finding.get('finding', '')
                policy_id = finding.get('policy_id', '')
                policy_name = finding.get('policy_name', '')
                finding_risk = finding.get('risk_level', '')
                action = finding.get('action', '')
                rationale = finding.get('rationale', '')
                
                # Main finding
                rows.append({
                    "category": "Risk Analysis",
                    "field": f"Finding {i}: {category}",
                    "subfield": "Description",
                    "value": finding_text,
                    "confidence": finding_risk,
                    "source_page": "",
                    "source_file": policy_id,
                    "accuracy_rating": "",
                    "issues_found": "",
                    "corrections": "",
                    "reviewer_notes": "",
                })
                
                if action:
                    rows.append({
                        "category": "Risk Analysis",
                        "field": f"Finding {i}: {category}",
                        "subfield": "Recommended Action",
                        "value": action,
                        "confidence": "",
                        "source_page": "",
                        "source_file": policy_name,
                        "accuracy_rating": "",
                        "issues_found": "",
                        "corrections": "",
                        "reviewer_notes": "",
                    })
                
                if rationale:
                    rows.append({
                        "category": "Risk Analysis",
                        "field": f"Finding {i}: {category}",
                        "subfield": "Rationale",
                        "value": rationale[:1000],
                        "confidence": "",
                        "source_page": "",
                        "source_file": "",
                        "accuracy_rating": "",
                        "issues_found": "",
                        "corrections": "",
                        "reviewer_notes": "",
                    })
        else:
            # Simple dict structure
            for key, val in parsed.items():
                rows.append({
                    "category": "Risk Analysis",
                    "field": section.replace('_', ' ').title() if section else key.replace('_', ' ').title(),
                    "subfield": key.replace('_', ' ').title(),
                    "value": extract_simple_value(val),
                    "confidence": risk_level,
                    "source_page": "",
                    "source_file": policy_citations,
                    "accuracy_rating": "",
                    "issues_found": "",
                    "corrections": "",
                    "reviewer_notes": "",
                })
    else:
        # Simple value
        display_section = section.replace("_", " ").title() if section else "Risk Analysis"
        
        rows.append({
            "category": "Risk Analysis",
            "field": display_section,
            "subfield": "",
            "value": str(parsed)[:2000] if parsed else "",
            "confidence": risk_level,
            "source_page": "",
            "source_file": policy_citations,
            "accuracy_rating": "",
            "issues_found": "",
            "corrections": "",
            "reviewer_notes": "",
        })
        
        if underwriting_action:
            rows.append({
                "category": "Risk Analysis",
                "field": display_section,
                "subfield": "Action",
                "value": underwriting_action,
                "confidence": "",
                "source_page": "",
                "source_file": "",
                "accuracy_rating": "",
                "issues_found": "",
                "corrections": "",
                "reviewer_notes": "",
            })
    
    return rows


def transform_csv(input_path: Path, output_path: Path) -> int:
    """Transform a single review_output.csv to human-readable format.
    
    Returns the number of rows written.
    """
    rows = []
    
    # Read input CSV
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            category = row.get('category', '')
            section = row.get('section', '')
            subsection = row.get('subsection', '')
            value = row.get('value', '')
            confidence = row.get('confidence', '')
            source_page = row.get('source_page', '')
            source_file = row.get('source_file', '')
            risk_level = row.get('risk_level', '')
            underwriting_action = row.get('underwriting_action', '')
            policy_citations = row.get('policy_citations', '')
            
            if category == 'extracted_field':
                rows.extend(flatten_extracted_field(
                    subsection, value, confidence, source_page, source_file
                ))
            elif category == 'llm_output':
                # Skip metadata rows
                if section == 'metadata':
                    continue
                rows.extend(flatten_llm_output(
                    section, subsection, value, risk_level, underwriting_action
                ))
            elif category == 'risk_analysis':
                # Handle the raw JSON case specially
                if section == 'raw':
                    rows.extend(flatten_risk_analysis(
                        section, value, risk_level, underwriting_action, policy_citations
                    ))
                elif section != 'timestamp':  # Skip timestamp
                    rows.extend(flatten_risk_analysis(
                        section, value, risk_level, underwriting_action, policy_citations
                    ))
    
    # Write output CSV
    fieldnames = [
        "category",
        "field",
        "subfield",
        "value",
        "confidence",
        "source_page",
        "source_file",
        "accuracy_rating",
        "issues_found",
        "corrections",
        "reviewer_notes",
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    return len(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Transform review CSVs to human-readable format",
    )
    parser.add_argument(
        "--input-folder",
        default="batch-review-output",
        help="Input folder containing application subfolders (default: batch-review-output)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files without transforming",
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    input_folder = project_root / args.input_folder
    
    if not input_folder.exists():
        log(f"Input folder not found: {input_folder}", "ERROR")
        return 1
    
    # Find all review_output.csv files
    csv_files = list(input_folder.glob("*/review_output.csv"))
    
    if not csv_files:
        log("No review_output.csv files found", "ERROR")
        return 1
    
    log(f"Found {len(csv_files)} CSV files to transform")
    
    if args.dry_run:
        log("DRY RUN - Files that would be transformed:")
        for csv_file in csv_files:
            print(f"  {csv_file.parent.name}/review_output.csv -> human_review.csv")
        return 0
    
    # Transform each file
    success_count = 0
    for csv_file in csv_files:
        app_name = csv_file.parent.name
        output_file = csv_file.parent / "human_review.csv"
        
        try:
            row_count = transform_csv(csv_file, output_file)
            log(f"Transformed {app_name}: {row_count} rows -> {output_file.name}")
            success_count += 1
        except Exception as e:
            log(f"Failed to transform {app_name}: {e}", "ERROR")
    
    log(f"Successfully transformed {success_count}/{len(csv_files)} files")
    return 0 if success_count == len(csv_files) else 1


if __name__ == "__main__":
    sys.exit(main())
