# Leo — History

## Project Context

underwriting-assistant is an AI-powered underwriting assistant for mortgage and insurance workflows. Built with a Python (FastAPI) backend and Next.js frontend, using Azure OpenAI for document analysis and scoring.

## Learnings

### 2026-01-27: Commercial Brokerage MVP Review

**Context:** Comprehensive architecture review of the Commercial Brokerage persona implementation against spec `specs/012-commercial-brokerage/spec-commercial-brokerage.md`.

**Key Findings:**
- **Architecture:** Production-quality scaffolding — all P0 features have complete implementations
- **Data models:** Fully aligned with spec, no schema gaps
- **Engines:** PlacementEngine, QuoteExtractor, ClientResearchEngine, SubmissionGenerator all complete and production-ready
- **Integration gap:** API endpoints return mock data instead of calling engines (4 endpoints need wiring)
- **Frontend:** Complete component structure, but frontend types don't match backend models exactly

**Decision:** MVP is ship-ready after ~2 hours of engine wiring work

**Patterns Observed:**
- Placement scoring uses composite weights (premium 35%, coverage 30%, financial 20%, completeness 15%)
- Quote extraction uses LLM with structured JSON prompt (confidence scoring built-in)
- Client research uses Azure Responses API with web_search_preview for Bing grounding, falls back to chat_completion
- Carrier financial strength gating follows AM Best FSR tiers (A++ through B+, with combined ratio adjustments)

**File Paths:**
- Backend models: `app/broker/models.py`
- API router: `app/broker/api.py`
- Engines: `app/broker/placement_engine.py`, `quote_extractor.py`, `research_engine.py`, `submission_generator.py`
- Frontend workbench: `frontend/src/components/broker/BrokerWorkbench.tsx`
- Placement policies: `prompts/commercial-brokerage-policies.json`, `data/commercial-brokerage-policies.json`
- Persona config: `app/personas.py` (lines 3488-3894), `frontend/src/lib/personas.ts` (lines 86-96)

**Technical Debt:**
- Frontend types need alignment with backend models
- Storage layer is in-memory (needs PostgreSQL persistence)
- No input validation on file uploads
- QuoteExtractor has 15KB document limit (needs chunking for large docs)

**User Preference:**
- Jawad wants thorough reviews with clear ship/no-ship verdict
- Concise summaries preferred (2-3 sentences at end, not verbose progress updates)
