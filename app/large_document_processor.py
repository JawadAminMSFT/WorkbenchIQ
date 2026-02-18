"""
Large Document Processing Module

This module handles processing of large documents (>1.5MB markdown) that would
otherwise exceed token limits and rate limit quotas.

Instead of sending the full document to each prompt, this module uses
**Progressive Summarization**:

1. Phase 1: Batch summarization - Process ALL pages in batches of ~20
2. Phase 2: Consolidation - Combine batch summaries + CU fields
3. Result: Rich ~15K token context covering the entire document

Rate limit protection:
- Sequential batch processing (not parallel)
- Configurable delay between batches
- Total usage stays well under 1M TPM limit

This reduces token usage from ~1.5M to ~15K while preserving ALL document content.

Prompts are externalized to: prompts/large-document-prompts.json
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from .config import Settings, ProcessingSettings
from .openai_client import chat_completion
from .utils import setup_logging

logger = setup_logging()

# Cache for loaded prompts
_prompts_cache: Optional[Dict[str, Any]] = None


def _get_prompts_path() -> str:
    """Get the path to the large document prompts file."""
    # Navigate from app/ to prompts/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "prompts", "large-document-prompts.json")


def load_large_doc_prompts(force_reload: bool = False) -> Dict[str, Any]:
    """Load large document processing prompts from JSON file.
    
    Args:
        force_reload: If True, reload from disk even if cached
        
    Returns:
        Dictionary containing prompts and system messages
    """
    global _prompts_cache
    
    if _prompts_cache is not None and not force_reload:
        return _prompts_cache
    
    prompts_path = _get_prompts_path()
    
    try:
        with open(prompts_path, 'r', encoding='utf-8') as f:
            _prompts_cache = json.load(f)
            logger.info("Loaded large document prompts from %s", prompts_path)
            return _prompts_cache
    except FileNotFoundError:
        logger.warning("Large document prompts file not found: %s, using defaults", prompts_path)
        return _get_default_prompts()
    except json.JSONDecodeError as e:
        logger.error("Failed to parse large document prompts: %s", e)
        return _get_default_prompts()


def _get_default_prompts() -> Dict[str, Any]:
    """Return default prompts if JSON file is not available."""
    return {
        "system_messages": {
            "summarize_pages": "You are an expert insurance underwriting analyst specializing in APS review.",
            "summarize_batch": "You are an expert insurance underwriting analyst specializing in medical records review.",
            "consolidation": "You are an expert insurance underwriting analyst. Consolidate batch summaries accurately."
        },
        "prompts": {
            "summarize_pages": {
                "template": "Summarize the following document pages for insurance underwriting.\n\n{pages_text}",
                "max_tokens": 3000,
                "temperature": 0.0
            },
            "summarize_batch": {
                "template": "Summarize pages {page_nums} for underwriting.\n\n{batch_text}",
                "max_tokens": 2000,
                "temperature": 0.0
            },
            "consolidation": {
                "template": "Consolidate these summaries:\n\n{combined_summaries}",
                "max_tokens": 4000,
                "temperature": 0.0
            }
        }
    }


def detect_processing_mode(
    document_markdown: str,
    threshold_kb: int = 1500,
) -> str:
    """Determine if document needs large document processing.
    
    Args:
        document_markdown: The full document markdown content
        threshold_kb: Size threshold in KB (default 1500KB / 1.5MB)
        
    Returns:
        'large_document' if size >= threshold, 'standard' otherwise
    """
    size_bytes = len(document_markdown.encode('utf-8'))
    size_kb = size_bytes / 1024
    
    mode = "large_document" if size_kb >= threshold_kb else "standard"
    logger.info(
        "Document size: %.1f KB, threshold: %d KB, mode: %s",
        size_kb, threshold_kb, mode
    )
    
    return mode


def extract_pages_from_markdown(markdown: str) -> List[Dict[str, Any]]:
    """Extract individual pages from document markdown.
    
    Parses the markdown looking for page headers in the format:
    "# File: document.pdf – Page N" or similar patterns.
    
    Args:
        markdown: Full document markdown
        
    Returns:
        List of page dictionaries with 'number', 'content', 'file' keys
    """
    pages: List[Dict[str, Any]] = []
    current_page: Dict[str, Any] = {"number": 0, "content": "", "file": ""}
    
    # Pattern to match page headers like "# File: document.pdf – Page 5"
    # Also handles variations like "## Page 5" or "--- Page 5 ---"
    page_header_pattern = re.compile(
        r'^#+ (?:File:\s*(.+?)\s*[–-]\s*)?Page\s*(\d+)',
        re.IGNORECASE | re.MULTILINE
    )
    
    lines = markdown.split('\n')
    for line in lines:
        match = page_header_pattern.match(line)
        if match:
            # Save current page if it has content
            if current_page["content"].strip():
                pages.append(current_page)
            
            # Start new page
            file_name = match.group(1) or ""
            page_num = int(match.group(2)) if match.group(2) else len(pages) + 1
            current_page = {
                "number": page_num,
                "content": "",
                "file": file_name.strip()
            }
        else:
            current_page["content"] += line + "\n"
    
    # Don't forget the last page
    if current_page["content"].strip():
        pages.append(current_page)
    
    # If no page structure found, treat entire document as single page
    if not pages and markdown.strip():
        pages.append({
            "number": 1,
            "content": markdown,
            "file": ""
        })
    
    logger.info("Extracted %d pages from markdown", len(pages))
    return pages


def format_extracted_fields(cu_result: Dict[str, Any]) -> str:
    """Format CU extracted fields as readable text for prompts.
    
    Args:
        cu_result: Raw Content Understanding result with extracted fields
        
    Returns:
        Formatted string of extracted fields with confidence scores
    """
    fields_text = "## Extracted Document Fields\n\n"
    fields_count = 0
    
    result = cu_result.get("result", {})
    contents = result.get("contents", [])
    
    for content in contents:
        content_fields = content.get("fields", {})
        for field_name, field_data in content_fields.items():
            # Handle different value formats
            value = (
                field_data.get("valueString") or 
                field_data.get("valueNumber") or 
                field_data.get("valueDate") or 
                field_data.get("valueArray") or 
                field_data.get("value", "")
            )
            
            confidence = field_data.get("confidence", 0)
            
            if value:
                # Format arrays nicely
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                
                fields_text += f"**{field_name}**: {value}"
                if confidence:
                    fields_text += f" (confidence: {confidence:.0%})"
                fields_text += "\n"
                fields_count += 1
    
    logger.info("Formatted %d extracted fields", fields_count)
    return fields_text


def select_key_pages(
    pages: List[Dict[str, Any]],
    max_pages: int = 15,
    first_pages: int = 5,
) -> List[Dict[str, Any]]:
    """Select the most relevant pages for summarization.
    
    Strategy:
    1. Always include first N pages (application form, cover sheet)
    2. Find pages with medical-related keywords
    3. Fill remaining slots with evenly spaced pages
    
    Args:
        pages: All extracted pages
        max_pages: Maximum pages to return
        first_pages: Number of first pages to always include
        
    Returns:
        Selected pages, sorted by page number
    """
    if len(pages) <= max_pages:
        logger.info("Document has %d pages, using all (below max %d)", len(pages), max_pages)
        return pages
    
    selected: List[Dict[str, Any]] = []
    
    # Always include first N pages (application form, cover sheet)
    selected.extend(pages[:first_pages])
    
    # Keywords that indicate important medical/financial content
    medical_keywords = [
        'medical', 'diagnosis', 'treatment', 'medication', 'prescription',
        'lab', 'laboratory', 'blood', 'health', 'hospital', 'physician',
        'surgery', 'condition', 'symptom', 'disease', 'chronic', 'acute',
        'insurance', 'policy', 'coverage', 'benefit', 'premium',
        'income', 'salary', 'employment', 'occupation', 'employer',
        'beneficiary', 'applicant', 'insured', 'tobacco', 'smoking',
        'alcohol', 'drug', 'family history', 'hereditary'
    ]
    
    # Score remaining pages by keyword matches
    page_scores: List[Tuple[int, Dict[str, Any]]] = []
    for page in pages[first_pages:]:
        content_lower = page["content"].lower()
        score = sum(1 for kw in medical_keywords if kw in content_lower)
        page_scores.append((score, page))
    
    # Sort by score (descending) and take top pages
    page_scores.sort(key=lambda x: x[0], reverse=True)
    
    remaining_slots = max_pages - len(selected)
    for score, page in page_scores[:remaining_slots]:
        if page not in selected:
            selected.append(page)
    
    # Sort by page number for coherent reading
    selected.sort(key=lambda p: p["number"])
    
    logger.info(
        "Selected %d key pages from %d total (first %d + %d medical/financial)",
        len(selected), len(pages), first_pages, len(selected) - first_pages
    )
    
    return selected


def summarize_pages(
    settings: Settings,
    pages: List[Dict[str, Any]],
    max_content_per_page: int = 10000,
    max_total_chars: int = 50000,
) -> str:
    """Create a structured summary of selected pages using LLM.
    
    Args:
        settings: Application settings with OpenAI config
        pages: Selected pages to summarize
        max_content_per_page: Max characters per page (truncate if longer)
        max_total_chars: Max total characters for all pages combined
        
    Returns:
        Summarized text suitable for underwriting analysis
    """
    # Load prompts from JSON file
    prompts_config = load_large_doc_prompts()
    prompt_template = prompts_config["prompts"]["summarize_pages"]["template"]
    system_message = prompts_config["system_messages"]["summarize_pages"]
    max_tokens = prompts_config["prompts"]["summarize_pages"].get("max_tokens", 3000)
    temperature = prompts_config["prompts"]["summarize_pages"].get("temperature", 0.0)
    
    # Build pages text with truncation
    pages_text = ""
    for page in pages:
        page_content = page["content"][:max_content_per_page]
        pages_text += f"\n---\n## Page {page['number']}\n{page_content}\n"
        
        if len(pages_text) > max_total_chars:
            pages_text = pages_text[:max_total_chars] + "\n...[truncated due to length]..."
            break
    
    logger.info(
        "Summarizing %d pages, total input: %d chars",
        len(pages), len(pages_text)
    )

    # Format the prompt template with pages_text
    prompt = prompt_template.format(pages_text=pages_text)

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ]
    
    try:
        result = chat_completion(
            settings.openai,
            messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        summary = result["content"]
        logger.info(
            "Generated page summary: %d chars, tokens used: %s",
            len(summary), result.get("usage", {})
        )
        return summary
    except Exception as e:
        logger.error("Failed to summarize pages: %s", e)
        # Fallback: return raw truncated content
        return f"[Summary generation failed: {e}]\n\nRaw content excerpt:\n{pages_text[:5000]}"


def summarize_batch(
    settings: Settings,
    pages: List[Dict[str, Any]],
    batch_num: int,
    total_batches: int,
    max_chars_per_page: int = 8000,
) -> str:
    """Summarize a single batch of pages.
    
    Args:
        settings: Application settings
        pages: Pages in this batch
        batch_num: Current batch number (1-indexed)
        total_batches: Total number of batches
        max_chars_per_page: Max characters per page
        
    Returns:
        Summary of the batch
    """
    # Load prompts from JSON file
    prompts_config = load_large_doc_prompts()
    prompt_template = prompts_config["prompts"]["summarize_batch"]["template"]
    system_message = prompts_config["system_messages"]["summarize_batch"]
    max_tokens = prompts_config["prompts"]["summarize_batch"].get("max_tokens", 2000)
    temperature = prompts_config["prompts"]["summarize_batch"].get("temperature", 0.0)
    
    # Build batch content
    batch_text = ""
    page_nums = []
    for page in pages:
        page_nums.append(str(page["number"]))
        content = page["content"][:max_chars_per_page]
        batch_text += f"\n---\n### Page {page['number']}\n{content}\n"
    
    # Format the prompt template
    prompt = prompt_template.format(
        page_nums=', '.join(page_nums),
        batch_num=batch_num,
        total_batches=total_batches,
        batch_text=batch_text
    )

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ]
    
    try:
        result = chat_completion(
            settings.openai,
            messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        usage = result.get("usage", {})
        logger.info(
            "Batch %d/%d: pages %s, tokens: %d prompt + %d completion",
            batch_num, total_batches, '-'.join([page_nums[0], page_nums[-1]]),
            usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
        )
        return result["content"]
    except Exception as e:
        logger.error("Batch %d summarization failed: %s", batch_num, e)
        return f"[Batch {batch_num} failed: {e}]"


def progressive_summarize(
    settings: Settings,
    pages: List[Dict[str, Any]],
    pages_per_batch: int = 20,
    delay_between_batches: float = 0.5,
) -> Tuple[str, Dict[str, Any]]:
    """Progressively summarize ALL pages using batch processing.
    
    Phase 1: Summarize pages in batches
    Phase 2: Consolidate batch summaries into final context
    
    Args:
        settings: Application settings
        pages: All document pages
        pages_per_batch: Pages per batch (default 20)
        delay_between_batches: Seconds between batches for rate limiting
        
    Returns:
        Tuple of (final_summary, stats_dict)
    """
    total_pages = len(pages)
    
    # Small documents: use simple summarization
    if total_pages <= pages_per_batch:
        logger.info("Document has %d pages, using simple summarization", total_pages)
        summary = summarize_pages(settings, pages)
        stats = {
            "mode": "simple",
            "total_pages": total_pages,
            "batches": 1,
            "total_tokens_used": 0,
        }
        return summary, stats
    
    # Calculate batches
    batches: List[List[Dict[str, Any]]] = []
    for i in range(0, total_pages, pages_per_batch):
        batches.append(pages[i:i + pages_per_batch])
    
    total_batches = len(batches)
    logger.info(
        "Progressive summarization: %d pages → %d batches of ~%d pages",
        total_pages, total_batches, pages_per_batch
    )
    
    # Phase 1: Summarize each batch
    batch_summaries: List[str] = []
    batch_summaries_structured: List[Dict[str, Any]] = []  # For UI display
    total_tokens = 0
    
    for i, batch in enumerate(batches):
        batch_num = i + 1
        
        # Rate limit protection: delay between batches
        if i > 0 and delay_between_batches > 0:
            time.sleep(delay_between_batches)
        
        summary = summarize_batch(settings, batch, batch_num, total_batches)
        batch_summaries.append(f"### Batch {batch_num} (Pages {batch[0]['number']}-{batch[-1]['number']})\n{summary}")
        
        # Store structured batch info for UI
        batch_summaries_structured.append({
            "batch_num": batch_num,
            "page_start": batch[0]['number'],
            "page_end": batch[-1]['number'],
            "page_count": len(batch),
            "summary": summary,
        })
        
        # Rough token tracking
        total_tokens += len(summary) // 4  # Output tokens estimate
    
    logger.info(
        "Phase 1 complete: %d batches summarized, ~%d tokens used",
        total_batches, total_tokens
    )
    
    # Phase 2: Consolidate batch summaries
    combined_summaries = "\n\n".join(batch_summaries)
    
    # If combined summaries are small enough, use directly
    if len(combined_summaries) < 60000:  # ~15K tokens
        logger.info("Batch summaries fit in context (%d chars), using directly", len(combined_summaries))
        final_summary = combined_summaries
    else:
        # Need to consolidate further
        logger.info("Consolidating %d chars of batch summaries...", len(combined_summaries))
        
        # Load prompts from JSON file
        prompts_config = load_large_doc_prompts()
        prompt_template = prompts_config["prompts"]["consolidation"]["template"]
        system_message = prompts_config["system_messages"]["consolidation"]
        max_tokens = prompts_config["prompts"]["consolidation"].get("max_tokens", 4000)
        temperature = prompts_config["prompts"]["consolidation"].get("temperature", 0.0)
        
        # Format the prompt template (truncate combined_summaries if needed)
        consolidation_prompt = prompt_template.format(
            combined_summaries=combined_summaries[:80000]
        )

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": consolidation_prompt},
        ]
        
        try:
            result = chat_completion(
                settings.openai,
                messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            final_summary = result["content"]
            total_tokens += result.get("usage", {}).get("total_tokens", 0)
            logger.info("Phase 2 consolidation complete: %d chars", len(final_summary))
        except Exception as e:
            logger.error("Consolidation failed: %s, using combined summaries", e)
            final_summary = combined_summaries[:60000]
    
    stats = {
        "mode": "progressive",
        "total_pages": total_pages,
        "batches": total_batches,
        "pages_per_batch": pages_per_batch,
        "total_tokens_used": total_tokens,
        "batch_summaries": batch_summaries_structured,  # Structured batch data for UI
    }
    
    return final_summary, stats


def build_condensed_context(
    settings: Settings,
    document_markdown: str,
    cu_result: Optional[Dict[str, Any]] = None,
    use_progressive: bool = True,
) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
    """Build a condensed context suitable for prompt analysis.
    
    This is the main entry point for large document processing.
    Uses progressive summarization to capture ALL pages, not just samples.
    
    Args:
        settings: Application settings
        document_markdown: Full document markdown
        cu_result: Optional CU result with extracted fields
        use_progressive: Use progressive multi-batch summarization (default True)
        
    Returns:
        Tuple of (condensed_context, batch_summaries_list)
        - condensed_context: String suitable for LLM prompts
        - batch_summaries_list: List of batch summary dicts for UI (or None for simple mode)
    """
    logger.info("Building condensed context for large document (progressive=%s)...", use_progressive)
    
    # Track document size
    doc_size_kb = len(document_markdown.encode('utf-8')) / 1024
    
    # 1. Format extracted fields from CU (if available)
    fields_text = ""
    if cu_result:
        fields_text = format_extracted_fields(cu_result)
        logger.info("Extracted fields: %d characters", len(fields_text))
    else:
        fields_text = "## Extracted Fields\n*No structured fields available from Content Understanding*\n"
    
    # 2. Extract ALL pages
    pages = extract_pages_from_markdown(document_markdown)
    logger.info("Document has %d pages", len(pages))
    
    # 3. Summarize using progressive approach (all pages) or sample approach
    batch_summaries_list: Optional[List[Dict[str, Any]]] = None
    
    if use_progressive and len(pages) > 20:
        # Progressive: process ALL pages in batches
        pages_summary, summary_stats = progressive_summarize(
            settings,
            pages,
            pages_per_batch=20,
            delay_between_batches=0.5,  # 500ms between batches for rate limiting
        )
        batch_summaries_list = summary_stats.get("batch_summaries")
        logger.info(
            "Progressive summarization complete: %d batches, %d pages covered",
            summary_stats.get("batches", 0), summary_stats.get("total_pages", 0)
        )
    else:
        # Simple: sample key pages (legacy approach for smaller docs)
        max_sample_pages = settings.processing.max_sample_pages
        selected_pages = select_key_pages(pages, max_pages=max_sample_pages)
        logger.info("Selected %d key pages for summarization", len(selected_pages))
        pages_summary = summarize_pages(settings, selected_pages)
    
    logger.info("Generated page summary: %d characters", len(pages_summary))
    
    # 4. Combine into condensed context
    mode_description = "progressively summarized" if use_progressive else "sampled and summarized"
    
    condensed = f"""# Document Analysis Context

{fields_text}

## Comprehensive Document Summary

{pages_summary}

---
*This is a {mode_description} analysis of a {len(pages)}-page document (~{doc_size_kb:.1f} KB).*
*All pages have been processed to ensure complete coverage of medical and financial information.*
"""
    
    condensed_size_kb = len(condensed.encode('utf-8')) / 1024
    estimated_tokens = len(condensed) // 4  # Rough estimate
    
    logger.info(
        "Condensed context: %d characters (~%.1f KB, ~%d tokens). "
        "Reduced from %.1f KB (%.1f%% reduction)",
        len(condensed), condensed_size_kb, estimated_tokens,
        doc_size_kb, (1 - condensed_size_kb / doc_size_kb) * 100
    )
    
    return condensed, batch_summaries_list


def get_document_stats(document_markdown: str) -> Dict[str, Any]:
    """Get statistics about a document for display/debugging.
    
    Args:
        document_markdown: Full document markdown
        
    Returns:
        Dictionary with document statistics
    """
    size_bytes = len(document_markdown.encode('utf-8'))
    pages = extract_pages_from_markdown(document_markdown)
    
    return {
        "size_bytes": size_bytes,
        "size_kb": round(size_bytes / 1024, 2),
        "size_mb": round(size_bytes / (1024 * 1024), 2),
        "page_count": len(pages),
        "estimated_tokens": len(document_markdown) // 4,
        "line_count": document_markdown.count('\n'),
    }
