# Large Document Processing - Implementation Plan

## Summary

After analyzing the spec, I recommend a **pragmatic MVP approach** that can be implemented quickly while maintaining quality.

## Key Insight

For a 24MB document with ~480 pages:
- Full summarization: Too slow (hours)
- Better approach: **Extract and use structured CU fields + page-level summaries for key sections only**

Content Understanding already extracts structured fields with confidence scores. We should leverage this rather than re-processing the entire raw markdown.

---

## MVP Implementation (Recommended)

### Approach: Fields + Smart Sampling

Instead of summarizing the entire 24MB document:

1. **Use CU extracted fields** as the primary data source (already structured)
2. **Sample key pages** for additional context (first 10 pages + pages with high-confidence medical data)
3. **Build condensed context** from fields + sampled page summaries
4. **Run prompts** against this ~15K token context

### Token Budget (Large Doc Mode)
| Component | Tokens |
|-----------|--------|
| CU extracted fields (formatted) | ~3,000 |
| First 5 pages summary | ~2,500 |
| Medical section summary (detected pages) | ~2,500 |
| Financial/policy section summary | ~2,000 |
| **Total context** | **~10,000** |

This fits easily within rate limits!

---

## Files to Modify/Create

### 1. New Files
```
app/
  large_document_processor.py    # New module for large doc handling
prompts/
  large-document-prompts.json    # Chunk/aggregate prompts
```

### 2. Modified Files
```
app/config.py                    # Add ProcessingSettings
app/processing.py                # Add mode detection, integrate large doc flow
app/storage.py                   # Add processing_mode, condensed_context fields
api_server.py                    # Add processing_mode parameter
frontend/src/components/AdminPanel.tsx  # Add toggle (Phase 2)
```

---

## Implementation Steps

### Step 1: Add Configuration (15 min)

```python
# app/config.py - Add to Settings

@dataclass
class ProcessingSettings:
    large_doc_threshold_kb: int = 100
    chunk_size_chars: int = 50000
    max_condensed_tokens: int = 12000
    sample_pages: int = 10  # First N pages to always include

# In load_settings():
processing = ProcessingSettings(
    large_doc_threshold_kb=int(os.getenv("LARGE_DOC_THRESHOLD_KB", "100")),
    ...
)
```

### Step 2: Create Large Document Processor (1-2 hours)

```python
# app/large_document_processor.py

from typing import Dict, Any, List, Optional
from .config import Settings
from .openai_client import chat_completion
from .utils import setup_logging

logger = setup_logging()

def detect_processing_mode(document_markdown: str, threshold_kb: int = 100) -> str:
    """Determine if document needs large document processing."""
    size_kb = len(document_markdown.encode('utf-8')) / 1024
    return "large_document" if size_kb >= threshold_kb else "standard"


def extract_pages_from_markdown(markdown: str) -> List[Dict[str, Any]]:
    """Extract individual pages from document markdown."""
    # Pages are typically marked with "# File: ... – Page N" headers
    pages = []
    current_page = {"number": 0, "content": "", "file": ""}
    
    for line in markdown.split('\n'):
        if line.startswith('# File:') and '– Page' in line:
            if current_page["content"]:
                pages.append(current_page)
            # Parse "# File: document.pdf – Page 5"
            parts = line.split('– Page')
            file_part = parts[0].replace('# File:', '').strip()
            page_num = int(parts[1].strip()) if len(parts) > 1 else len(pages) + 1
            current_page = {"number": page_num, "content": "", "file": file_part}
        else:
            current_page["content"] += line + "\n"
    
    if current_page["content"]:
        pages.append(current_page)
    
    return pages


def format_extracted_fields(cu_result: Dict[str, Any]) -> str:
    """Format CU extracted fields as readable text for prompts."""
    fields_text = "## Extracted Document Fields\n\n"
    
    result = cu_result.get("result", {})
    contents = result.get("contents", [])
    
    for content in contents:
        content_fields = content.get("fields", {})
        for field_name, field_data in content_fields.items():
            value = field_data.get("valueString") or field_data.get("value", "")
            confidence = field_data.get("confidence", 0)
            if value:
                fields_text += f"**{field_name}**: {value}"
                if confidence:
                    fields_text += f" (confidence: {confidence:.0%})"
                fields_text += "\n"
    
    return fields_text


def select_key_pages(
    pages: List[Dict[str, Any]], 
    max_pages: int = 15
) -> List[Dict[str, Any]]:
    """Select the most relevant pages for summarization."""
    if len(pages) <= max_pages:
        return pages
    
    selected = []
    
    # Always include first 5 pages (application form, cover sheet)
    selected.extend(pages[:5])
    
    # Look for medical-related pages
    medical_keywords = ['medical', 'diagnosis', 'treatment', 'medication', 'lab', 'blood', 'health']
    for page in pages[5:]:
        content_lower = page["content"].lower()
        if any(kw in content_lower for kw in medical_keywords):
            selected.append(page)
            if len(selected) >= max_pages:
                break
    
    # Fill remaining slots with evenly spaced pages
    if len(selected) < max_pages:
        remaining_pages = [p for p in pages[5:] if p not in selected]
        step = max(1, len(remaining_pages) // (max_pages - len(selected)))
        for i in range(0, len(remaining_pages), step):
            if len(selected) >= max_pages:
                break
            selected.append(remaining_pages[i])
    
    return sorted(selected, key=lambda p: p["number"])


def summarize_pages(
    settings: Settings,
    pages: List[Dict[str, Any]],
) -> str:
    """Create a summary of selected pages."""
    pages_text = ""
    for page in pages:
        pages_text += f"\n---\n## Page {page['number']}\n{page['content'][:10000]}\n"
    
    # Truncate if too long
    if len(pages_text) > 50000:
        pages_text = pages_text[:50000] + "\n...[truncated]..."
    
    prompt = f"""Summarize the following document pages for an underwriting analysis.
Focus on:
1. Applicant information (name, DOB, address, occupation)
2. Medical conditions, diagnoses, medications
3. Lab results and vital signs
4. Policy details and coverage requested
5. Risk factors and lifestyle information
6. Family medical history

Document Pages:
{pages_text}

Provide a comprehensive summary in a structured format."""

    messages = [
        {"role": "system", "content": "You are an expert insurance underwriting analyst."},
        {"role": "user", "content": prompt},
    ]
    
    result = chat_completion(settings.openai, messages, max_tokens=2000)
    return result["content"]


def build_condensed_context(
    settings: Settings,
    document_markdown: str,
    cu_result: Dict[str, Any],
) -> str:
    """Build a condensed context suitable for prompt analysis."""
    logger.info("Building condensed context for large document...")
    
    # 1. Format extracted fields from CU
    fields_text = format_extracted_fields(cu_result)
    logger.info("Extracted %d characters of structured fields", len(fields_text))
    
    # 2. Extract and select key pages
    pages = extract_pages_from_markdown(document_markdown)
    logger.info("Document has %d pages", len(pages))
    
    selected_pages = select_key_pages(pages, max_pages=15)
    logger.info("Selected %d key pages for summarization", len(selected_pages))
    
    # 3. Summarize selected pages
    pages_summary = summarize_pages(settings, selected_pages)
    logger.info("Generated page summary: %d characters", len(pages_summary))
    
    # 4. Combine into condensed context
    condensed = f"""# Document Analysis Context

{fields_text}

## Document Summary
{pages_summary}

---
*This is a condensed summary of a {len(pages)}-page document. Key information has been extracted and summarized for underwriting analysis.*
"""
    
    logger.info("Condensed context: %d characters (~%d tokens)", 
                len(condensed), len(condensed) // 4)
    
    return condensed
```

### Step 3: Integrate with Processing Flow (30 min)

```python
# app/processing.py - Modify run_underwriting_prompts

from .large_document_processor import detect_processing_mode, build_condensed_context

def run_underwriting_prompts(
    settings: Settings,
    app_md: ApplicationMetadata,
    cu_result: Optional[Dict[str, Any]] = None,  # Add this parameter
    processing_mode_override: Optional[str] = None,  # 'auto', 'standard', 'large_document'
    ...
) -> ApplicationMetadata:
    """Execute prompts with automatic mode detection."""
    
    if not app_md.document_markdown:
        logger.warning("No document markdown available")
        return app_md
    
    # Detect or use override mode
    if processing_mode_override and processing_mode_override != 'auto':
        mode = processing_mode_override
    else:
        mode = detect_processing_mode(
            app_md.document_markdown,
            settings.processing.large_doc_threshold_kb
        )
    
    logger.info("Processing mode: %s (doc size: %d KB)", 
                mode, len(app_md.document_markdown) // 1024)
    
    # Build appropriate context
    if mode == "large_document" and cu_result:
        document_context = build_condensed_context(
            settings, 
            app_md.document_markdown,
            cu_result
        )
        app_md.processing_mode = "large_document"
        app_md.condensed_context = document_context
    else:
        document_context = app_md.document_markdown
        app_md.processing_mode = "standard"
    
    # Continue with existing prompt execution using document_context...
```

### Step 4: Update Storage Schema (15 min)

```python
# app/storage.py - Add to ApplicationMetadata

@dataclass
class ApplicationMetadata:
    ...
    processing_mode: Optional[str] = None  # 'standard' or 'large_document'
    condensed_context: Optional[str] = None
```

### Step 5: Update API (15 min)

```python
# api_server.py - Add mode parameter

@app.post("/api/applications/{app_id}/analyze")
async def analyze_application(
    app_id: str,
    processing_mode: Optional[str] = Query(None, regex="^(auto|standard|large_document)$"),
    ...
):
    # Pass mode to run_underwriting_prompts
```

---

## Testing Plan

1. **Small document test** (< 100KB)
   - Should use standard mode
   - Existing behavior preserved

2. **Large document test** (24MB test file)
   - Should detect large_document mode
   - Should build condensed context
   - Should complete without rate limit errors

3. **Mode override test**
   - Force standard mode on large doc (should still work but slower)
   - Force large_document mode on small doc (should work)

---

## Estimated Effort

| Task | Time |
|------|------|
| Add configuration | 15 min |
| Create large_document_processor.py | 1.5 hours |
| Integrate with processing.py | 30 min |
| Update storage schema | 15 min |
| Update API | 15 min |
| Testing | 1 hour |
| **Total** | **~4 hours** |

---

## Future Enhancements (Phase 2+)

1. **Admin UI toggle** for processing mode
2. **Progress tracking** for large document processing
3. **Caching** of condensed contexts
4. **Intelligent page detection** using ML
5. **Resume capability** for interrupted processing
