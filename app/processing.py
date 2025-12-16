
from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from typing import Any, Dict, List, Tuple

from .config import Settings
from .content_understanding_client import (
    analyze_document,
    analyze_document_with_confidence,
    extract_markdown_from_result,
    extract_fields_with_confidence,
    get_confidence_summary,
)
from .openai_client import chat_completion
from .prompts import load_prompts
from .storage import (
    ApplicationMetadata,
    save_application_metadata,
    save_cu_raw_result,
    load_file_content,
)
from .personas import get_persona_config
from .utils import setup_logging
from .underwriting_policies import format_all_policies_for_prompt

logger = setup_logging()


def load_policies(storage_root: str) -> Dict[str, Any]:
    """Load policy definitions from JSON file."""
    try:
        policy_path = os.path.join(storage_root, "policies.json")
        if os.path.exists(policy_path):
            with open(policy_path, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load policies: {e}")
    return {}


def load_underwriting_policies(storage_root: str) -> str:
    """Load and format underwriting policies for prompt injection.
    
    Returns a formatted string of all underwriting policies suitable
    for injection into LLM prompts.
    """
    try:
        return format_all_policies_for_prompt(storage_root)
    except Exception as e:
        logger.warning(f"Failed to load underwriting policies: {e}")
        return ""


def run_content_understanding_for_files(
    settings: Settings,
    app_md: ApplicationMetadata,
    use_confidence_scoring: bool = True,
) -> ApplicationMetadata:
    """Run Content Understanding for each uploaded PDF and aggregate markdown.
    
    Args:
        settings: Application settings
        app_md: Application metadata with uploaded files
        use_confidence_scoring: Whether to use custom analyzer with confidence scores
    
    Returns:
        Updated ApplicationMetadata with extracted content and confidence data
    """
    all_pages: List[Dict[str, Any]] = []
    all_markdown_parts: List[str] = []
    cu_payloads: List[Tuple[str, Dict[str, Any]]] = []
    all_fields: Dict[str, Any] = {}
    analyzer_used = None

    # Get persona-specific analyzer ID
    persona_analyzer_id = settings.content_understanding.custom_analyzer_id  # Default
    if app_md.persona:
        try:
            persona_config = get_persona_config(app_md.persona)
            persona_analyzer_id = persona_config.custom_analyzer_id
            logger.info("Using persona-specific analyzer: %s for persona: %s", persona_analyzer_id, app_md.persona)
        except ValueError as e:
            logger.warning("Failed to get persona config for %s: %s. Using default analyzer.", app_md.persona, e)

    for stored in app_md.files:
        logger.info("Analyzing file with Content Understanding: %s", stored.path)
        
        # Load file content from storage (supports both local and cloud storage)
        file_content = load_file_content(stored)
        if file_content is None:
            logger.error("Failed to load file content for: %s", stored.path)
            continue
        
        # Use confidence-enabled analyzer if enabled
        if use_confidence_scoring and settings.content_understanding.enable_confidence_scores:
            # Temporarily override the custom_analyzer_id in settings for this call
            original_analyzer = settings.content_understanding.custom_analyzer_id
            settings.content_understanding.custom_analyzer_id = persona_analyzer_id
            try:
                payload = analyze_document_with_confidence(
                    settings.content_understanding, 
                    stored.path,
                    file_bytes=file_content
                )
                analyzer_used = persona_analyzer_id
            finally:
                settings.content_understanding.custom_analyzer_id = original_analyzer
            
            # Extract fields with confidence
            fields = extract_fields_with_confidence(payload)
            # Convert FieldConfidence objects to serializable dicts
            for field_name, field_conf in fields.items():
                all_fields[f"{stored.filename}:{field_name}"] = {
                    "field_name": field_conf.field_name,
                    "value": field_conf.value,
                    "confidence": field_conf.confidence,
                    "page_number": field_conf.page_number,
                    "bounding_box": field_conf.bounding_box,
                    "source_text": field_conf.source_text,
                    "source_file": stored.filename,
                }
        else:
            payload = analyze_document(settings.content_understanding, stored.path, file_bytes=file_content)
            analyzer_used = settings.content_understanding.analyzer_id
        
        cu_payloads.append((stored.path, payload))

        extracted = extract_markdown_from_result(payload)
        pages = extracted["pages"]
        # Prefix each page with filename so underwriters see the source.
        for p in pages:
            prefix = f"# File: {stored.filename} – Page {p['page_number']}\n\n"
            all_pages.append(
                {
                    "file": stored.filename,
                    "page_number": p["page_number"],
                    "markdown": prefix + p["markdown"],
                }
            )
            all_markdown_parts.append(prefix + p["markdown"])

    combined_md = "\n\n---\n\n".join(all_markdown_parts)

    # Save raw CU payload (for first file only) for debugging
    if cu_payloads:
        cu_path = save_cu_raw_result(settings.app.storage_root, app_md.id, cu_payloads[0][1])
    else:
        cu_path = None

    # Generate confidence summary if we have extracted fields
    confidence_summary = None
    if all_fields:
        # Create FieldConfidence-like objects for summary calculation
        from .content_understanding_client import FieldConfidence
        field_objects = {}
        for key, field_data in all_fields.items():
            field_objects[key] = FieldConfidence(
                field_name=field_data["field_name"],
                value=field_data["value"],
                confidence=field_data["confidence"],
                page_number=field_data.get("page_number"),
                bounding_box=field_data.get("bounding_box"),
                source_text=field_data.get("source_text"),
            )
        confidence_summary = get_confidence_summary(field_objects)
        logger.info(
            "Extracted %d fields with average confidence %.2f",
            confidence_summary["total_fields"],
            confidence_summary["average_confidence"],
        )

    app_md.document_markdown = combined_md
    app_md.markdown_pages = all_pages
    app_md.cu_raw_result_path = cu_path
    app_md.extracted_fields = all_fields
    app_md.confidence_summary = confidence_summary
    app_md.analyzer_id_used = analyzer_used
    app_md.status = "extracted"
    save_application_metadata(settings.app.storage_root, app_md)
    logger.info("Content Understanding completed for application %s", app_md.id)
    return app_md


def _run_single_prompt(
    settings: Settings,
    section: str,
    subsection: str,
    prompt_template: str,
    document_markdown: str,
    additional_context: str = "",
    underwriting_policies: str = "",
) -> Dict[str, Any]:
    system_prompt = "You are an expert life insurance underwriter. Always return STRICT JSON."
    
    # Inject underwriting policies into the prompt template
    if "{underwriting_policies}" in prompt_template:
        prompt_with_policies = prompt_template.replace(
            "{underwriting_policies}",
            underwriting_policies if underwriting_policies else ""
        )
    else:
        prompt_with_policies = prompt_template
    
    user_prompt = prompt_with_policies.strip() + "\n\n---\n\nApplication Markdown:\n\n" + document_markdown
    
    if additional_context:
        user_prompt += additional_context

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    logger.info("Running prompt: %s.%s", section, subsection)
    result = chat_completion(settings.openai, messages)
    raw_content = result["content"]

    try:
        parsed = json.loads(raw_content)
    except Exception:
        parsed = {"_raw": raw_content, "_error": "Failed to parse JSON response."}

    return {
        "section": section,
        "subsection": subsection,
        "raw": raw_content,
        "parsed": parsed,
        "usage": result.get("usage", {}),
    }


def _run_section_prompts(
    settings: Settings,
    section: str,
    subsections: Dict[str, str],
    document_markdown: str,
    subsections_to_run: List[Tuple[str, str]] | None = None,
    max_workers: int = 4,
    additional_context: str = "",
    underwriting_policies: str = "",
) -> Dict[str, Any]:
    """Run all prompts for a single section in parallel.
    
    Args:
        settings: Application settings
        section: The section name (e.g., 'medical_summary')
        subsections: Dict of subsection name to prompt template
        document_markdown: The document content to analyze
        subsections_to_run: Optional filter for specific subsections
        max_workers: Maximum parallel workers for this section
        additional_context: Optional context to append to prompts
        underwriting_policies: Formatted underwriting policies for prompt injection
    
    Returns:
        Dict mapping subsection names to their results
    """
    work_items: List[Tuple[str, str]] = []
    
    for subsection, template in subsections.items():
        if subsections_to_run and (section, subsection) not in subsections_to_run:
            continue
        # Template should now be a string after normalization
        # But handle dict format for backward compatibility
        if isinstance(template, dict):
            if "prompt" in template:
                prompt_text = template["prompt"]
            else:
                continue
        else:
            prompt_text = str(template)
        work_items.append((subsection, prompt_text))
    
    if not work_items:
        return {}
    
    logger.info("Running %d prompts for section '%s'", len(work_items), section)
    section_results: Dict[str, Any] = {}
    
    with ThreadPoolExecutor(max_workers=min(max_workers, len(work_items))) as executor:
        futures = {
            executor.submit(
                _run_single_prompt,
                settings,
                section,
                subsection,
                template,
                document_markdown,
                additional_context,
                underwriting_policies,
            ): subsection
            for subsection, template in work_items
        }
        
        for fut in as_completed(futures):
            subsection = futures[fut]
            try:
                output = fut.result()
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Prompt %s.%s failed: %s", section, subsection, str(exc), exc_info=True
                )
                output = {
                    "section": section,
                    "subsection": subsection,
                    "raw": "",
                    "parsed": {"_error": str(exc)},
                    "usage": {},
                }
            section_results[subsection] = output
    
    return section_results


def run_underwriting_prompts(
    settings: Settings,
    app_md: ApplicationMetadata,
    prompts_override: Dict[str, Dict[str, str]] | None = None,
    sections_to_run: List[str] | None = None,
    subsections_to_run: List[Tuple[str, str]] | None = None,
    max_workers_per_section: int = 4,
    on_section_complete: Any | None = None,
) -> ApplicationMetadata:
    """Execute prompts section by section to avoid overwhelming the service.
    
    Each section (e.g., application_summary, medical_summary, requirements) is run
    sequentially, but prompts within a section are run in parallel with limited
    concurrency.
    
    Args:
        settings: Application settings
        app_md: Application metadata with document markdown
        prompts_override: Optional custom prompts dict
        sections_to_run: Optional list of section names to run
        subsections_to_run: Optional list of (section, subsection) tuples to run
        max_workers_per_section: Max parallel prompts per section (default: 4)
        on_section_complete: Optional callback(section_name, results) called after each section
    
    Returns:
        Updated ApplicationMetadata with LLM outputs
    """
    if not app_md.document_markdown:
        raise ValueError("ApplicationMarkdown is empty; run Content Understanding first.")

    # Load persona-specific prompts
    persona = app_md.persona or "underwriting"
    prompts = prompts_override or load_prompts(settings.app.storage_root, persona)

    # Normalize prompts structure - convert single prompts to subsection format
    # Structure can be either:
    # 1. {"section": {"prompt": "...", "json_schema": {...}}} - single prompt section
    # 2. {"section": {"subsection": {"prompt": "...", "json_schema": {...}}}} - nested subsections
    normalized_prompts: Dict[str, Dict[str, str]] = {}
    for section, content in prompts.items():
        if isinstance(content, dict):
            if "prompt" in content:
                # Single prompt section - use section name as subsection too
                normalized_prompts[section] = {section: content["prompt"]}
            else:
                # Nested subsections
                subsections = {}
                for subsection, sub_content in content.items():
                    if isinstance(sub_content, dict) and "prompt" in sub_content:
                        subsections[subsection] = sub_content["prompt"]
                    elif isinstance(sub_content, str):
                        subsections[subsection] = sub_content
                if subsections:
                    normalized_prompts[section] = subsections

    # Determine which sections to run
    sections_to_process = []
    for section, subs in normalized_prompts.items():
        if sections_to_run and section not in sections_to_run:
            continue
        # Check if any subsections in this section should be run
        has_subsections = False
        for subsection in subs.keys():
            if subsections_to_run is None or (section, subsection) in subsections_to_run:
                has_subsections = True
                break
        if has_subsections:
            sections_to_process.append((section, subs))

    if not sections_to_process:
        logger.warning("No prompts selected to run.")
        return app_md

    total_prompts = sum(
        len([s for s in subs.keys() if subsections_to_run is None or (section, s) in subsections_to_run])
        for section, subs in sections_to_process
    )
    logger.info(
        "Running %d prompts across %d sections for application %s",
        total_prompts,
        len(sections_to_process),
        app_md.id,
    )

    # Load policies and determine context
    policies = load_policies(settings.app.storage_root)
    policy_context = ""
    
    if policies:
        # Try to find plan name in extracted fields
        plan_name = None
        if app_md.extracted_fields:
            for key, data in app_md.extracted_fields.items():
                if "PlanName" in key or "plan_name" in key:
                    val = data.get("value")
                    if val and isinstance(val, str):
                        plan_name = val
                        break
        
        if plan_name:
            # Try to match specific policy
            matched_policy = None
            for policy_name, details in policies.items():
                if policy_name.lower() in plan_name.lower() or plan_name.lower() in policy_name.lower():
                    matched_policy = details
                    break
            
            if matched_policy:
                policy_context = f"\n\n---\n\nPOLICY REFERENCE DATA (Use this for benefits/coverage):\n{json.dumps(matched_policy, indent=2)}\n"
            else:
                # If plan name found but no match, provide all as reference
                policy_context = f"\n\n---\n\nAVAILABLE PLANS REFERENCE (Use if plan name matches):\n{json.dumps(policies, indent=2)}\n"
        else:
            # If no plan name found, provide all as reference
            policy_context = f"\n\n---\n\nAVAILABLE PLANS REFERENCE (Use if plan name matches):\n{json.dumps(policies, indent=2)}\n"

    # NOTE: Underwriting policies are NOT injected during standard extraction/analysis.
    # Risk analysis with policy citations is a separate operation triggered by the user.
    # This keeps extraction prompts focused and avoids context bloat.
    underwriting_policies = ""
    logger.info("Standard analysis - skipping underwriting policy injection")

    results: Dict[str, Dict[str, Any]] = {}

    # Run each section sequentially to avoid overwhelming the service
    for section, subs in sections_to_process:
        logger.info("Starting section: %s", section)
        
        section_results = _run_section_prompts(
            settings=settings,
            section=section,
            subsections=subs,
            document_markdown=app_md.document_markdown,
            subsections_to_run=subsections_to_run,
            max_workers=max_workers_per_section,
            additional_context=policy_context,
            underwriting_policies=underwriting_policies,
        )
        
        results[section] = section_results
        logger.info("Completed section: %s (%d prompts)", section, len(section_results))
        
        # Call optional callback after each section completes
        if on_section_complete:
            try:
                on_section_complete(section, section_results)
            except Exception as exc:  # noqa: BLE001
                logger.warning("on_section_complete callback failed: %s", exc)

    app_md.llm_outputs = results
    app_md.status = "completed"
    save_application_metadata(settings.app.storage_root, app_md)
    logger.info("Underwriting prompts completed for application %s", app_md.id)
    return app_md


def run_risk_analysis(
    settings: Settings,
    app_md: ApplicationMetadata,
) -> Dict[str, Any]:
    """Run policy-based risk analysis on an already-analyzed application.
    
    This is a SEPARATE operation from extraction/summarization.
    It applies underwriting policies to the extracted data and generates
    a comprehensive risk assessment with policy citations.
    
    Args:
        settings: Application settings
        app_md: Application metadata with completed LLM outputs
        
    Returns:
        Risk analysis results with policy citations
    """
    if not app_md.llm_outputs:
        raise ValueError("Application has no LLM outputs. Run analysis first.")
    
    # Load risk analysis prompts
    risk_prompts_path = os.path.join(settings.app.storage_root, "risk-analysis-prompts.json")
    if not os.path.exists(risk_prompts_path):
        raise ValueError("Risk analysis prompts file not found")
    
    with open(risk_prompts_path, "r") as f:
        risk_prompts_config = json.load(f)
    
    risk_prompts = risk_prompts_config.get("prompts", {})
    
    # Load underwriting policies
    underwriting_policies = load_underwriting_policies(settings.app.storage_root)
    if not underwriting_policies:
        raise ValueError("No underwriting policies found")
    
    logger.info("Running risk analysis for application %s with %d chars of policies", 
                app_md.id, len(underwriting_policies))
    
    # Build application data summary from LLM outputs
    application_data_parts = []
    
    for section, subsections in app_md.llm_outputs.items():
        if not subsections:
            continue
        for subsection, output in subsections.items():
            if output and output.get("parsed"):
                parsed = output["parsed"]
                if isinstance(parsed, dict):
                    # Format the extracted data
                    application_data_parts.append(f"### {section} - {subsection}\n```json\n{json.dumps(parsed, indent=2)}\n```")
    
    application_data = "\n\n".join(application_data_parts)
    
    # Also include document markdown excerpt for context
    doc_context = ""
    if app_md.document_markdown:
        doc_preview = app_md.document_markdown[:6000]
        if len(app_md.document_markdown) > 6000:
            doc_preview += "\n\n[Document truncated...]"
        doc_context = f"\n\n### Original Document Excerpt\n{doc_preview}"
    
    full_application_data = application_data + doc_context
    
    # Run the overall risk assessment prompt
    overall_prompt_config = risk_prompts.get("overall_risk_assessment", {})
    if not overall_prompt_config:
        raise ValueError("No overall_risk_assessment prompt found")
    
    prompt_template = overall_prompt_config.get("prompt", "")
    
    # Inject policies and application data
    filled_prompt = prompt_template.replace("{underwriting_policies}", underwriting_policies)
    filled_prompt = filled_prompt.replace("{application_data}", full_application_data)
    
    system_message = "You are an expert life insurance underwriter. Always return STRICT JSON."
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": filled_prompt},
    ]
    
    logger.info("Sending risk analysis prompt to LLM")
    result = chat_completion(settings.openai, messages, max_tokens=3000)
    raw_content = result["content"]
    
    # Strip markdown code fences if present (e.g., ```json ... ```)
    content_to_parse = raw_content.strip()
    if content_to_parse.startswith("```"):
        # Find the end of the first line (e.g., "```json\n")
        first_newline = content_to_parse.find("\n")
        if first_newline != -1:
            content_to_parse = content_to_parse[first_newline + 1:]
        # Remove trailing ``` if present
        if content_to_parse.endswith("```"):
            content_to_parse = content_to_parse[:-3].strip()
    
    try:
        parsed = json.loads(content_to_parse)
    except Exception:
        parsed = {"_raw": raw_content, "_error": "Failed to parse JSON response."}
    
    risk_analysis_result = {
        "timestamp": app_md.created_at,
        "raw": raw_content,
        "parsed": parsed,
        "usage": result.get("usage", {}),
    }
    
    # Store risk analysis separately in the application metadata
    if not hasattr(app_md, 'risk_analysis') or app_md.risk_analysis is None:
        app_md.risk_analysis = {}
    app_md.risk_analysis = risk_analysis_result
    
    save_application_metadata(settings.app.storage_root, app_md)
    logger.info("Risk analysis completed for application %s", app_md.id)
    
    return risk_analysis_result
