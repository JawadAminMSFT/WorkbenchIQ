# Ben — History

## Project Context

underwriting-assistant backend is a Python FastAPI application. Uses Azure OpenAI for LLM-powered document analysis. Key modules include document processing, scoring engine, mortgage analysis, and API server. Background processing uses status tracking (extracting/analyzing/error).

## Learnings

### 2025-01-XX: Wired Backend Engines into API Router

**Task:** Wire 4 backend engines (QuoteExtractor, PlacementEngine, ClientResearchEngine, BrokerStorage) into the API router at `app/broker/api.py`.

**Key Files:**
- `app/broker/api.py` — Main API router with endpoints
- `app/broker/quote_extractor.py` — QuoteExtractor class for LLM-powered quote field extraction
- `app/broker/placement_engine.py` — PlacementEngine for scoring and ranking quotes
- `app/broker/research_engine.py` — ClientResearchEngine for AI-powered client research
- `app/broker/storage.py` — BrokerStorage for data persistence

**Implementations:**

1. **QuoteExtractor Integration** (Upload Quote Endpoint)
   - Wired into `POST /api/broker/submissions/{submission_id}/quotes`
   - After file upload, calls `QuoteExtractor.extract_quote()` to extract structured fields
   - Requires OpenAISettings from config
   - Updates quote status: RAW → EXTRACTED (or stays RAW if extraction fails)
   - Graceful fallback: if extraction fails, quote is still saved but status remains RAW

2. **PlacementEngine Integration** (Compare Quotes Endpoint)
   - Wired into `POST /api/broker/submissions/{submission_id}/compare`
   - Loads carrier profiles using `storage.get_carrier_profile_by_name()`
   - Converts dict data to dataclass instances (Quote, Submission, CarrierProfile)
   - Calls `PlacementEngine.score_quotes()` to compute placement scores
   - Calls `PlacementEngine.generate_recommendation()` for top-ranked quote
   - Saves scored quotes back to storage
   - Graceful fallback: if engine fails, returns basic comparison with manual review message

3. **ClientResearchEngine Integration** (Research Client Endpoint)
   - Wired into `POST /api/broker/clients/{client_id}/research`
   - Calls `ClientResearchEngine.research_client()` for AI-powered research
   - Saves research brief to client record (`client.research_brief`)
   - Formats structured research data into markdown brief for response
   - Graceful fallback: if research engine fails, returns basic client data from storage

4. **BrokerStorage Enhancement**
   - Added `get_carrier_profile_by_name()` method for case-insensitive carrier lookup
   - Used by PlacementEngine to load carrier profiles for FSR scoring

**Patterns & Conventions:**
- All engines require `OpenAISettings` from `load_settings()`
- API endpoints convert between dict (storage) ↔ dataclass (engine) representations
- Graceful degradation: engines wrapped in try/except, API stays functional even if AI features fail
- Status tracking: quotes go through RAW → EXTRACTED lifecycle
- Async/await pattern: engines use `async def` and `await` for non-blocking LLM calls

**Error Handling:**
- Engine failures logged but don't crash the API
- Partial success: e.g., quote uploaded even if extraction fails
- Fallback responses: mock/basic data returned if AI engines unavailable
