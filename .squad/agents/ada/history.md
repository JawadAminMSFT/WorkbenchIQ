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

### 2025-01-XX: Commercial Brokerage Spec Compliance Review

Conducted comprehensive spec compliance review of commercial brokerage persona against `specs/012-commercial-brokerage/spec-commercial-brokerage.md`.

**Fixes Applied:**

1. **Prompt Quality (`app/personas.py`)**:
   - Enhanced `client_research` prompt to include AM Best/S&P carrier data fields and explicit confidence indicators per US-2
   - Updated `quote_extraction` prompt to list all 15 canonical fields explicitly and reference FR-020 confidence threshold
   - Enriched `placement_recommendation` prompt with detailed OPT-001 scoring factors (FSR tier scoring: A++=100, A+=100, A=85, A-=70, B++=50, B+=25, unrated=10) and combined ratio bands (<95%=+10, 95-102=0, 103-108=-10, >108=-20), plus FSR-001 gate rules
   - Expanded `acord_extraction` prompt to specify 13 ACORD 125 fields, 15+ ACORD 140 fields, and SOV fields with all subfields

2. **Field Schema (`app/personas.py`)**:
   - Added missing quote fields: `ExpiryDate`, `Underwriter`, `QuoteReferenceNumber` (already in models but missing from schema)
   - Added SOV fields: `SOVSiteNumber`, `SOVBuildingDescription`, `SOVTotalInsuredValue`, `TotalSOVValue`
   - Added `ClientContacts` array field for client contact persons

3. **Data Models (`app/broker/models.py`)**:
   - Expanded `CarrierProfile` with 16 missing MD&A fields: `dwp_growth_rate`, `net_premiums_earned`, `total_admitted_assets`, `total_invested_assets`, `loss_and_lae_reserves`, `unearned_premiums`, `rbc_total_adjusted_capital`, `rbc_control_level`, `reinsurance_per_risk_retention`, `cat_retention`, `reinsurance_cession_rate`, `mda_year`, `net_income`, `underwriting_gain_loss`, `net_investment_income`

4. **Placement Engine (`app/broker/placement_engine.py`)**:
   - Updated `_calculate_financial_score()` to match spec OPT-001 exactly: combined ratio bands <95%=+10, 95-102=0, 103-108=-10, >108=-20 (previously used continuous formula)
   - Added `COMBINED_RATIO_BANDS` constant with spec-defined thresholds
   - FSR scoring already correct (A++=100, A+=100, A=85, A-=70, B++=50, B+=25, unrated=10)

5. **Submission Generator (`app/broker/submission_generator.py`)**:
   - Updated ACORD 125 extraction to include all 13 spec fields: added `fein`, `business_phone`, `sic_code`, `annual_gross_revenue`, `number_of_employees`
   - Updated ACORD 140 extraction to include all 15+ spec fields in correct order: moved `loss_history` to position 2, added `prior_policy_number` and `prior_expiration_date`
   - Updated example JSON to reflect complete field set

**Compliance Status:**
- ✅ Prompt quality: All 4 prompts now align with spec requirements (system, client_research, quote_extraction, placement_recommendation, acord_extraction)
- ✅ Field schema: All missing fields added (quote fields, SOV fields, client contacts)
- ✅ Data models: CarrierProfile complete with 17 AMB + 16 MD&A fields; all other models aligned
- ✅ Engine logic: Placement engine scoring matches OPT-001 exactly; quote extractor covers all 15 fields; submission generator covers ACORD 125 (13) + ACORD 140 (15+) fields
- ✅ Policy files: Both `data/commercial-brokerage-policies.json` and `prompts/commercial-brokerage-policies.json` contain all 6 rule categories

**Spec References:**
- Quote extraction: 15 canonical fields per spec table at line 327-345
- FSR scoring: OPT-001 at line 652-678 (weights: 35/30/20/15, FSR tiers, combined ratio bands)
- ACORD 125: 13 fields per spec table at line 448-464
- ACORD 140: 15+ fields per spec table at line 466-486
- CarrierProfile: AMB Credit Report (17 fields) at line 377-402 + MD&A (16 fields) at line 404-428
- Confidence threshold: FR-020 at line 715 (< 60% = "Needs Review")
