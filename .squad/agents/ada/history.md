# Ada — History

## Project Context

underwriting-assistant uses Azure OpenAI for LLM-powered document analysis. Key AI features: document extraction, underwriting scoring, property deep dives (with Bing Grounding), medical record analysis. Custom OpenAI client returns {'content', 'usage'} format. Prompts stored in prompts/ directory.

## Learnings

### 2025-01-XX: Commercial Broker Processing Engines

Created four AI-powered backend processing modules for the commercial brokerage persona in `app/broker/`:

**Key Patterns Established:**
- `chat_completion()` from `app.openai_client` returns `{'content': '...', 'usage': {...}}` format (NOT standard OpenAI)
- JSON parsing must handle code fences (`\`\`\`json`) and JS-style comments (`//`)
- All async methods wrap synchronous `chat_completion()` with `asyncio.to_thread()`
- Azure Responses API (Bing Grounding) uses separate endpoint with `web_search_preview` tool
- Responses API pattern: DefaultAzureCredential → POST to `/openai/responses?api-version=2025-04-01-preview` → extract from `output[].content[].text`
- Settings loaded via `load_settings()` from `app.config` → `settings.openai` is the OpenAISettings instance

**Modules Created:**
1. `quote_extractor.py` - QuoteExtractor class: Extracts 15 canonical quote fields (premium, limits, sublimits, exclusions, etc.) from carrier documents
2. `placement_engine.py` - PlacementEngine class: Pure computation scoring engine (no LLM calls) with composite scoring: premium 35%, coverage 30%, financial strength 20%, completeness 15%
3. `research_engine.py` - ClientResearchEngine class: AI-powered client research briefs using Responses API (Bing) with fallback to standard chat_completion
4. `submission_generator.py` - SubmissionGenerator class: Extracts ACORD 125 and ACORD 140 fields from client submission documents

**File Paths:**
- Engine modules: `app/broker/*.py`
- Data models: `app/broker/models.py`
- Constants: `app/broker/constants.py`
- Exports: `app/broker/__init__.py`

**Token Management:**
- Quote extraction: max_tokens=4000
- Client research: max_tokens=3000
- ACORD extraction: max_tokens=8000 (large documents)
- Timeout scales with max_tokens: 120s base + 1s per 100 tokens over 1200

**Prompt Engineering:**
- Always request JSON-only output with explicit schema
- Include confidence scores (0.0-1.0) for field extraction
- Use structured examples in prompts
- Handle truncated responses gracefully
