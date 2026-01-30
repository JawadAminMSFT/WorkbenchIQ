# Large Document Processing Mode

## Problem Statement

When processing large documents (>50 pages), the extracted markdown can exceed 20MB+ (~1.5-2 million tokens). This causes:

1. **Rate limiting** - Each prompt sends the full document, exceeding Azure OpenAI's TPM (tokens-per-minute) quota
2. **Timeout failures** - Requests take too long and fail
3. **Cascading failures** - Even with retries and fallback endpoints, all quotas get exhausted

### Current Document Size Example
- Content Understanding extracted: 14MB JSON
- Document markdown: 24MB (~6 million characters, ~1.5M tokens)
- Azure S0 TPM limit: ~60K tokens/minute
- Result: 100% failure rate on large documents

## Solution Overview

Implement a **two-tier processing mode** that automatically detects document size and uses the appropriate strategy:

### Tier 1: Standard Mode (Existing)
- **Trigger**: Document markdown < 100KB (~25K tokens)
- **Behavior**: Current parallel prompt execution with full markdown context
- **Performance**: Fast, parallel processing

### Tier 2: Large Document Mode
- **Trigger**: Document markdown >= 100KB
- **Behavior**: 
  1. Extract structured fields from Content Understanding result
  2. Create chunked summaries of the document
  3. Aggregate summaries into a condensed context (~10K tokens)
  4. Run analysis prompts against condensed context
- **Performance**: Slower but reliable

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Document Processing                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Upload Document                                                           │
│         │                                                                   │
│         ▼                                                                   │
│   Content Understanding                                                     │
│   (Extract markdown + fields)                                               │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────┐                                                       │
│   │ Size Check      │                                                       │
│   │ markdown < 100KB│                                                       │
│   └────────┬────────┘                                                       │
│            │                                                                │
│     ┌──────┴──────┐                                                         │
│     │             │                                                         │
│     ▼             ▼                                                         │
│ ┌───────────┐ ┌──────────────────────────────────────┐                      │
│ │ STANDARD  │ │          LARGE DOCUMENT              │                      │
│ │   MODE    │ │             MODE                     │                      │
│ ├───────────┤ ├──────────────────────────────────────┤                      │
│ │           │ │                                      │                      │
│ │ Full      │ │  1. Extract CU Fields                │                      │
│ │ Markdown  │ │       │                              │                      │
│ │    +      │ │       ▼                              │                      │
│ │ Parallel  │ │  2. Chunk Document (50K chars each)  │                      │
│ │ Prompts   │ │       │                              │                      │
│ │           │ │       ▼                              │                      │
│ │           │ │  3. Summarize Each Chunk             │                      │
│ │           │ │     (Sequential, 1 per minute)       │                      │
│ │           │ │       │                              │                      │
│ │           │ │       ▼                              │                      │
│ │           │ │  4. Aggregate Summaries              │                      │
│ │           │ │       │                              │                      │
│ │           │ │       ▼                              │                      │
│ │           │ │  5. Build Condensed Context          │                      │
│ │           │ │     (~10K tokens)                    │                      │
│ │           │ │       │                              │                      │
│ │           │ │       ▼                              │                      │
│ │           │ │  6. Run Analysis Prompts             │                      │
│ │           │ │     (Parallel, fits in quota)        │                      │
│ └───────────┘ └──────────────────────────────────────┘                      │
│       │                     │                                               │
│       └──────────┬──────────┘                                               │
│                  ▼                                                          │
│           Analysis Results                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Design

### 1. Size Threshold Configuration

```python
# app/config.py
@dataclass
class ProcessingSettings:
    large_doc_threshold_kb: int = 100  # Documents >= 100KB use large doc mode
    chunk_size_chars: int = 50000      # ~12.5K tokens per chunk
    chunk_overlap_chars: int = 1000    # Overlap for context continuity
    summary_max_tokens: int = 500      # Max tokens per chunk summary
    condensed_context_max_tokens: int = 10000  # Final context size target
```

Environment variables:
```env
LARGE_DOC_THRESHOLD_KB=100
CHUNK_SIZE_CHARS=50000
SUMMARY_MAX_TOKENS=500
```

### 2. Processing Mode Detection

```python
# app/processing.py

def detect_processing_mode(document_markdown: str) -> str:
    """Determine processing mode based on document size."""
    size_kb = len(document_markdown.encode('utf-8')) / 1024
    
    if size_kb >= settings.processing.large_doc_threshold_kb:
        return "large_document"
    return "standard"
```

### 3. Document Chunking

```python
# app/processing.py (new function)

def chunk_document(markdown: str, chunk_size: int = 50000, overlap: int = 1000) -> List[str]:
    """Split document into overlapping chunks for summarization."""
    chunks = []
    start = 0
    
    while start < len(markdown):
        end = start + chunk_size
        
        # Try to break at a paragraph boundary
        if end < len(markdown):
            # Look for paragraph break within last 20% of chunk
            search_start = end - int(chunk_size * 0.2)
            break_point = markdown.rfind('\n\n', search_start, end)
            if break_point > search_start:
                end = break_point
        
        chunks.append(markdown[start:end])
        start = end - overlap if end < len(markdown) else end
    
    return chunks
```

### 4. Chunk Summarization Prompt

```json
{
  "large_document": {
    "chunk_summary": {
      "prompt": "You are an expert document analyzer. Summarize the following document section, preserving all key facts, names, dates, medical conditions, financial figures, and policy-relevant details.\n\nDocument Section:\n{chunk}\n\nProvide a comprehensive but condensed summary in JSON format:\n{\n  \"key_facts\": [...],\n  \"entities\": {\"people\": [...], \"organizations\": [...], \"dates\": [...]},\n  \"medical_info\": [...],\n  \"financial_info\": [...],\n  \"policy_details\": [...],\n  \"summary\": \"...\"\n}"
    },
    "aggregate_summaries": {
      "prompt": "You are an expert underwriting analyst. Combine these section summaries into a unified document summary suitable for underwriting analysis.\n\nSection Summaries:\n{summaries}\n\nExtracted Fields:\n{fields}\n\nCreate a comprehensive summary that includes:\n1. Applicant profile\n2. Medical history and conditions\n3. Risk factors\n4. Policy details\n5. Key findings\n\nOutput as JSON with clear sections."
    }
  }
}
```

### 5. Large Document Processing Flow

```python
# app/processing.py (new function)

async def process_large_document(
    settings: Settings,
    app_md: ApplicationMetadata,
    cu_result: Dict[str, Any],
) -> str:
    """Process large document using chunk-and-summarize strategy."""
    
    # Step 1: Extract structured fields from CU result
    fields = extract_fields_from_cu(cu_result)
    fields_text = format_fields_as_text(fields)
    
    # Step 2: Chunk the document
    chunks = chunk_document(app_md.document_markdown)
    logger.info("Split document into %d chunks", len(chunks))
    
    # Step 3: Summarize each chunk (sequential to respect rate limits)
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        logger.info("Summarizing chunk %d/%d", i + 1, len(chunks))
        summary = await summarize_chunk(settings, chunk)
        chunk_summaries.append(summary)
        
        # Wait between chunks to respect rate limits
        if i < len(chunks) - 1:
            await asyncio.sleep(30)  # 30s between chunks
    
    # Step 4: Aggregate summaries into condensed context
    condensed_context = await aggregate_summaries(
        settings, 
        chunk_summaries, 
        fields_text
    )
    
    # Step 5: Store condensed context for use by prompts
    return condensed_context
```

### 6. Modified Prompt Execution

```python
# app/processing.py (modify run_underwriting_prompts)

def run_underwriting_prompts(
    settings: Settings,
    app_md: ApplicationMetadata,
    ...
) -> ApplicationMetadata:
    """Execute prompts with automatic mode detection."""
    
    # Detect processing mode
    mode = detect_processing_mode(app_md.document_markdown)
    logger.info("Processing mode: %s", mode)
    
    if mode == "large_document":
        # Use condensed context instead of full markdown
        condensed_context = process_large_document(settings, app_md, cu_result)
        document_context = condensed_context
    else:
        # Use full markdown (existing behavior)
        document_context = app_md.document_markdown
    
    # Continue with existing prompt execution...
    for section_key in section_keys:
        results = _run_section_prompts(
            settings=settings,
            section=section_key,
            prompts=section_prompts,
            document_markdown=document_context,  # Uses appropriate context
            ...
        )
```

### 7. Admin UI Toggle

Add a toggle in the Admin panel to allow manual override:

```typescript
// frontend/src/components/AdminPanel.tsx

interface ProcessingSettings {
  autoDetectMode: boolean;
  forceMode: 'standard' | 'large_document' | 'auto';
  largeDocThresholdKb: number;
}

// Toggle component
<FormControl>
  <FormLabel>Processing Mode</FormLabel>
  <Select value={processingMode} onChange={handleModeChange}>
    <option value="auto">Auto-detect (recommended)</option>
    <option value="standard">Standard (small documents)</option>
    <option value="large_document">Large Document Mode</option>
  </Select>
  <FormHelperText>
    Auto-detect uses standard mode for documents under {thresholdKb}KB
  </FormHelperText>
</FormControl>
```

### 8. API Changes

```python
# api_server.py

@app.post("/api/applications/{app_id}/process")
async def process_application(
    app_id: str,
    processing_mode: Optional[str] = None,  # 'auto', 'standard', 'large_document'
    ...
):
    """Process application with optional mode override."""
    ...
```

## Database Schema Changes

Add processing mode tracking to application metadata:

```python
# app/storage.py

@dataclass
class ApplicationMetadata:
    ...
    processing_mode: Optional[str] = None  # 'standard' or 'large_document'
    condensed_context: Optional[str] = None  # For large docs, store the condensed version
    chunk_summaries: Optional[List[str]] = None  # Individual chunk summaries
```

## Performance Estimates

### Standard Mode (< 100KB)
- Time: 30-60 seconds
- API calls: 8 (parallel)
- Token usage: ~200K total

### Large Document Mode (24MB example)
- Chunking: 480 chunks @ 50K chars each
- Summarization: 480 calls × 30s spacing = ~4 hours
- Wait, that's too long...

### Revised Large Document Mode
- **Aggressive chunking**: 200K chars per chunk = ~120 chunks for 24MB
- **Batch summarization**: Process 3 chunks at a time with 60s wait
- **Time estimate**: ~40 minutes for very large documents
- **Or**: Use shorter summaries and fewer chunks

### Alternative: Extract Key Sections Only
For underwriting, we really only need:
1. Application form data (first few pages)
2. Medical records summary
3. Lab results
4. Declarations

We could intelligently extract just these sections rather than summarizing everything.

## Implementation Phases

### Phase 1: Core Infrastructure (MVP)
- [ ] Add size detection
- [ ] Implement document chunking
- [ ] Create chunk summarization prompt
- [ ] Add aggregate summarization
- [ ] Integrate with existing prompt flow
- [ ] Add processing mode to metadata

### Phase 2: Admin Controls
- [ ] Add processing mode toggle to Admin UI
- [ ] Add threshold configuration
- [ ] Display processing mode on application details

### Phase 3: Optimization
- [ ] Intelligent section extraction (skip irrelevant pages)
- [ ] Caching of chunk summaries
- [ ] Progress tracking for long-running jobs
- [ ] Resume capability for interrupted processing

## Testing

### Test Cases
1. Small document (< 100KB) - should use standard mode
2. Medium document (100KB - 1MB) - should use large doc mode
3. Very large document (> 10MB) - should complete without timeout
4. Mode override via API
5. Mode override via Admin UI

### Test Documents
- Create test fixtures at various sizes
- Use real anonymized underwriting documents

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Chunk summaries lose critical details | Include extracted CU fields as ground truth |
| Processing takes too long | Add progress tracking, allow cancellation |
| Rate limits still hit during summarization | Sequential processing with generous delays |
| Condensed context still too large | Enforce max token limit, prioritize recent/relevant info |

## Success Metrics

1. **Reliability**: 95%+ success rate for documents of any size
2. **Latency**: < 5 minutes for documents under 1MB
3. **Quality**: Analysis quality comparable to standard mode (manual review)
4. **User Experience**: Clear progress indication, no silent failures
