# Tasks: Automotive Claims Multimodal Processing

**Input**: Design documents from `/specs/007-automotive-claims-multimodal/`  
**Prerequisites**: spec.md ✅, data-model.md ✅

---

## Format: `[ID] [Priority] [Phase] Description`

- **[P]**: Can run in parallel with other [P] tasks (different files, no dependencies)
- **[Phase]**: Which phase this task belongs to
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `app/` at repository root
- **Multimodal**: `app/multimodal/` (new package)
- **Claims Engine**: `app/claims/` (new package)
- **Analyzers**: `scripts/setup_automotive_analyzers.py`
- **Policies**: `data/automotive-claims-policies.json`
- **Tests**: `tests/` at repository root

---

## Phase 1: Infrastructure & Configuration

**Purpose**: Set up package structure, environment variables, and persona configuration

**Test File**: `tests/test_auto_claims_phase1_config.py`

### Package Structure

- [ ] T001 Create `app/multimodal/` package directory
- [ ] T002 [P] Create `app/multimodal/__init__.py` with public exports
- [ ] T003 [P] Create `app/claims/` package directory
- [ ] T004 [P] Create `app/claims/__init__.py` with public exports

### Configuration

- [ ] T005 Add automotive claims environment variables to `app/config.py`:
  - `AUTO_CLAIMS_ENABLED`
  - `AUTO_CLAIMS_DOC_ANALYZER`
  - `AUTO_CLAIMS_IMAGE_ANALYZER`
  - `AUTO_CLAIMS_VIDEO_ANALYZER`
  - `AUTO_CLAIMS_POLICIES_PATH`
  - `VIDEO_MAX_DURATION_MINUTES`
  - `IMAGE_MAX_SIZE_MB`
- [ ] T006 Create `app/config.py::AutomotiveClaimsSettings` dataclass with from_env pattern

### Persona Update

- [ ] T007 Update `PersonaType` enum in `app/personas.py`:
  - Change `PROPERTY_CASUALTY_CLAIMS` to `AUTOMOTIVE_CLAIMS` (with backward compatibility alias)
- [ ] T008 Create `AUTOMOTIVE_CLAIMS_FIELD_SCHEMA` in `app/personas.py` per spec data model
- [ ] T009 Create `AUTOMOTIVE_CLAIMS_DEFAULT_PROMPTS` in `app/personas.py`
- [ ] T010 Update `PERSONA_CONFIGS` registry with new automotive claims persona config

### Frontend Persona Update

- [ ] T011 Update `PersonaId` type in `frontend/src/lib/personas.ts` to include `automotive_claims`
- [ ] T012 Update `PERSONAS` object with automotive_claims configuration
- [ ] T013 Create `AutomotiveClaimsOverview` component stub in `frontend/src/components/claims/`

**Checkpoint**: Configuration validated, persona appears in UI dropdown

---

## Phase 2: Multimodal Router & MIME Detection

**Purpose**: Implement file type detection and analyzer routing

**Test File**: `tests/test_auto_claims_phase2_router.py`

### MIME Detection

- [ ] T014 Create `app/multimodal/mime_detector.py` with `MimeDetector` class
- [ ] T015 Implement `detect_media_type(file_bytes, filename)` returning `document | image | video`
- [ ] T016 Define MIME type mappings:
  - Documents: `application/pdf`, `application/msword`, `application/vnd.openxmlformats-*`
  - Images: `image/jpeg`, `image/png`, `image/gif`, `image/webp`
  - Videos: `video/mp4`, `video/quicktime`, `video/x-msvideo`, `video/webm`
- [ ] T017 Add file extension fallback detection

### Analyzer Router

- [ ] T018 Create `app/multimodal/router.py` with `AnalyzerRouter` class
- [ ] T019 Implement `get_analyzer_id(media_type, settings)` routing logic:
  - `document` → `autoClaimsDocAnalyzer` (or `prebuilt-documentSearch` fallback)
  - `image` → `autoClaimsImageAnalyzer` (or `prebuilt-imageSearch` fallback)
  - `video` → `autoClaimsVideoAnalyzer` (or `prebuilt-videoSearch` fallback)
- [ ] T020 Implement `route_file(file_bytes, filename, settings)` returning `(media_type, analyzer_id)`
- [ ] T021 Add validation for file size limits (images, videos)

### Content Understanding Extensions

- [ ] T022 Extend `app/content_understanding_client.py` with `analyze_image()` function
- [ ] T023 Extend `app/content_understanding_client.py` with `analyze_video()` function
- [ ] T024 Implement video keyframe URL extraction from CU response
- [ ] T025 Implement video transcript extraction from CU response
- [ ] T026 Implement video segment/chapter extraction from CU response

**Checkpoint**: Files correctly classified and routed to appropriate analyzer

---

## Phase 3: Custom Analyzer Setup

**Purpose**: Create and deploy custom Azure CU analyzers for automotive claims

**Test File**: `tests/test_auto_claims_phase3_analyzers.py`

### Analyzer Schemas

- [ ] T027 Create `scripts/setup_automotive_analyzers.py` CLI script
- [ ] T028 Define `autoClaimsDocAnalyzer` schema extending `prebuilt-document`:
  - Field schema per spec (vehicle info, incident info, repair estimate, parties)
- [ ] T029 Define `autoClaimsImageAnalyzer` schema extending `prebuilt-image`:
  - Damage detection fields (location, type, severity, components)
- [ ] T030 Define `autoClaimsVideoAnalyzer` schema extending `prebuilt-video`:
  - Incident analysis fields (impact detection, pre/post incident, transcript)

### Analyzer Deployment

- [ ] T031 Implement `create_analyzer(settings, analyzer_id, schema)` in setup script
- [ ] T032 Implement `get_analyzer(settings, analyzer_id)` to check if exists
- [ ] T033 Implement `update_analyzer(settings, analyzer_id, schema)` for updates
- [ ] T034 Add idempotent deployment (create if not exists, update if changed)
- [ ] T035 Add verification step that tests each analyzer with sample content

**Checkpoint**: Custom analyzers deployed and responding in Azure

---

## Phase 4: Multimodal Processing Pipeline

**Purpose**: Implement parallel file processing with result aggregation

**Test File**: `tests/test_auto_claims_phase4_processing.py`

### Processing Service

- [ ] T036 Create `app/multimodal/processor.py` with `MultimodalProcessor` class
- [ ] T037 Implement `process_file(file_info, settings)` for single file processing
- [ ] T038 Implement `process_files_parallel(files, settings)` for concurrent processing
- [ ] T039 Add progress tracking callback for UI updates
- [ ] T040 Add retry logic with exponential backoff for failed analyses

### Result Extraction

- [ ] T041 Create `app/multimodal/extractors/document_extractor.py`
- [ ] T042 Implement `extract_document_fields(cu_result)` returning structured fields
- [ ] T043 [P] Create `app/multimodal/extractors/image_extractor.py`
- [ ] T044 Implement `extract_damage_areas(cu_result)` returning damage list
- [ ] T045 [P] Create `app/multimodal/extractors/video_extractor.py`
- [ ] T046 Implement `extract_video_segments(cu_result)` returning segments, keyframes, transcript

### Result Aggregation

- [ ] T047 Create `app/multimodal/aggregator.py` with `ResultAggregator` class
- [ ] T048 Implement `aggregate_results(media_results)` merging fields from all sources
- [ ] T049 Implement field conflict resolution (same field, different sources)
- [ ] T050 Implement source attribution tracking for each field value
- [ ] T051 Implement overall damage severity calculation from individual damage areas

### Database Integration

- [ ] T052 Create `app/multimodal/repository.py` with database operations
- [ ] T053 Implement `save_claim_media(media_data)` persisting to `claim_media` table
- [ ] T054 Implement `save_keyframes(keyframes)` persisting to `claim_keyframes` table
- [ ] T055 Implement `save_damage_areas(areas)` persisting to `claim_damage_areas` table
- [ ] T056 Implement `save_repair_items(items)` persisting to `claim_repair_items` table

**Checkpoint**: Mixed media uploads processed, extracted data stored in database

---

## Phase 5: Claims Policy Engine

**Purpose**: Implement policy-based claims rating and payout calculation

**Test File**: `tests/test_auto_claims_phase5_policy_engine.py`

### Policy Data

- [ ] T057 Create `data/automotive-claims-policies.json` with policies per spec
- [ ] T058 Create `app/claims/policies.py` with `ClaimsPolicyLoader` class
- [ ] T059 Implement `load_policies(path)` returning structured policy objects
- [ ] T060 Implement `get_policies_by_category(category)` filtering

### Policy Engine

- [ ] T061 Create `app/claims/engine.py` with `ClaimsPolicyEngine` class
- [ ] T062 Implement `evaluate_damage_severity(damage_areas)` applying DMG-SEV policies
- [ ] T063 Implement `evaluate_liability(evidence)` applying LIA policies
- [ ] T064 Implement `evaluate_fraud_risk(claim_data)` applying FRD policies
- [ ] T065 Implement `validate_estimate(estimate, damage_assessment)` applying PAY policies
- [ ] T066 Implement `calculate_payout_recommendation(claim_data)` computing range

### Policy Citations

- [ ] T067 Implement policy rule tracking - which rules were triggered
- [ ] T068 Implement rationale generation explaining each determination
- [ ] T069 Create `ClaimAssessment` dataclass with all policy engine outputs

### Assessment Persistence

- [ ] T070 Implement `save_claim_assessment(assessment)` to `claim_assessments` table
- [ ] T071 Implement `get_claim_assessment(application_id)` retrieval
- [ ] T072 Implement `update_adjuster_decision(id, decision, notes)` for adjuster actions

**Checkpoint**: Policy engine rates claims and generates payout recommendations

---

## Phase 6: RAG for Claims Policies

**Purpose**: Enable semantic search over automotive claims policies in Ask IQ

**Test File**: `tests/test_auto_claims_phase6_rag.py`

### Policy Chunking

- [ ] T073 Create `app/claims/chunker.py` with `ClaimsPolicyChunker` class
- [ ] T074 Implement `chunk_policy(policy)` creating semantic chunks
- [ ] T075 Implement chunking for all chunk types: header, criteria, modifying_factor

### Embedding & Indexing

- [ ] T076 Create `app/claims/indexer.py` with `ClaimsPolicyIndexer` class
- [ ] T077 Implement `index_policies(policies)` - chunk → embed → store pipeline
- [ ] T078 Implement embedding using existing `EmbeddingService` from `app/rag/`
- [ ] T079 Store chunks in `claim_policy_chunks` table with embeddings

### Search Integration

- [ ] T080 Create `app/claims/search.py` with `ClaimsPolicySearchService`
- [ ] T081 Implement `semantic_search(query, category_filter)` for claims policies
- [ ] T082 Implement hybrid search (keyword + semantic) for claims policies
- [ ] T083 Integrate with Ask IQ chat endpoint for automotive claims persona

### Indexing Script

- [ ] T084 Create `scripts/index_claims_policies.py` CLI for manual indexing
- [ ] T085 Add progress logging and validation

**Checkpoint**: Ask IQ retrieves relevant claims policies for automotive claims questions

---

## Phase 7: API Endpoints

**Purpose**: Expose multimodal processing and claims assessment via REST API

**Test File**: `tests/test_auto_claims_phase7_api.py`

### Upload Endpoint Updates

- [ ] T086 Modify `POST /api/applications/{id}/upload` to accept multiple file types
- [ ] T087 Add multimodal router to upload handler for automotive_claims persona
- [ ] T088 Add media type metadata to upload response

### Processing Endpoint

- [ ] T089 Create `POST /api/applications/{id}/process-multimodal` endpoint
- [ ] T090 Implement parallel processing trigger for all uploaded media
- [ ] T091 Add WebSocket or polling endpoint for processing progress

### Assessment Endpoints

- [ ] T092 Create `GET /api/applications/{id}/assessment` endpoint
- [ ] T093 Create `PUT /api/applications/{id}/assessment/decision` for adjuster action
- [ ] T094 Add policy citations to assessment response

### Media Endpoints

- [ ] T095 Create `GET /api/applications/{id}/media` listing all media for claim
- [ ] T096 Create `GET /api/applications/{id}/media/{mediaId}/keyframes` for video keyframes
- [ ] T097 Create `GET /api/applications/{id}/media/{mediaId}/damage-areas` for image damage
- [ ] T098 Add keyframe URL signing for secure access

**Checkpoint**: Full API functional, can process claims and retrieve assessments

---

## Phase 8: Frontend UX

**Purpose**: Build claims adjuster interface for evidence review and decision making. File uploads, policy changes, and analyzer updates are handled via the existing Admin View pattern (consistent with other personas).

**Test File**: Manual testing / E2E tests

**Note**: This phase focuses on the claims adjuster review experience. File uploads are done via Admin View, not a user-facing upload UI.

### Evidence Gallery

- [ ] T099 Create `frontend/src/components/claims/EvidenceGallery.tsx`
- [ ] T100 Implement image grid with thumbnails and damage badges
- [ ] T101 Implement video card with keyframe preview and duration
- [ ] T102 Implement document list with file type icons
- [ ] T103 Add click-to-expand for full-size image/video viewer

### Damage Assessment View

- [ ] T104 Create `frontend/src/components/claims/DamageAssessmentView.tsx`
- [ ] T105 Implement damage area list with location, type, severity chips
- [ ] T106 Implement severity badge coloring (green/yellow/orange/red)
- [ ] T107 Add adjuster override controls for severity
- [ ] T108 Display AI-generated damage descriptions

### Video Timeline

- [ ] T109 Create `frontend/src/components/claims/VideoTimeline.tsx`
- [ ] T110 Implement keyframe strip with clickable thumbnails
- [ ] T111 Implement segment markers with descriptions
- [ ] T112 Add impact frame highlighting
- [ ] T113 Display transcript panel (collapsible)

### Assessment Panel

- [ ] T114 Create `frontend/src/components/claims/AssessmentPanel.tsx`
- [ ] T115 Implement severity rating display with rationale
- [ ] T116 Implement payout recommendation with range slider
- [ ] T117 Implement policy citations accordion
- [ ] T118 Implement fraud indicators alert (if any)
- [ ] T119 Add adjuster decision buttons (Approve, Adjust, Deny, Investigate)

### Automotive Claims Overview

- [ ] T120 Create `frontend/src/components/claims/AutomotiveClaimsOverview.tsx`
- [ ] T121 Implement tabbed layout: Evidence | Damage | Assessment | Timeline
- [ ] T122 Add summary cards: Vehicle info, Incident date, Severity, Payout
- [ ] T123 Integrate with existing application detail page structure

### Persona Page Updates

- [ ] T124 Update `frontend/src/app/page.tsx` to render `AutomotiveClaimsOverview` for automotive_claims
- [ ] T125 Add automotive_claims to persona selector with Car icon

**Checkpoint**: Full UX complete, adjusters can review and approve claims (uploads via Admin View)

---

## Admin View Notes

The following operations use the existing Admin View pattern (consistent with other personas):

1. **File Uploads** - Documents, images, and videos are uploaded via Admin View
2. **Policy Updates** - `automotive-claims-policies.json` updates via Admin View file management
3. **Analyzer Configuration** - Custom analyzer settings managed via Admin View or CLI scripts
4. **Claim Creation** - New automotive claims created via Admin View

No changes to Admin View are required beyond supporting the new `automotive_claims` persona in the persona dropdown.

---

## Phase 9: Database Migrations

**Purpose**: Deploy all new tables to PostgreSQL

**Test File**: `tests/test_auto_claims_phase9_migrations.py`

### Migration Files

- [ ] T126 Create `migrations/006_create_claim_media.sql`
- [ ] T127 Create `migrations/007_create_claim_keyframes.sql`
- [ ] T128 Create `migrations/008_create_claim_damage_areas.sql`
- [ ] T129 Create `migrations/009_create_claim_repair_items.sql`
- [ ] T130 Create `migrations/010_create_claim_policy_chunks.sql`
- [ ] T131 Create `migrations/011_create_claim_assessments.sql`
- [ ] T132 Update `app/database/migrate.py` to include new migrations

### Verification

- [ ] T133 Create migration verification script
- [ ] T134 Add rollback scripts for each migration

**Checkpoint**: All tables created and verified in PostgreSQL

---

## Validation Checklist

After Phase 8 completion (MVP):

- [ ] V001 Images correctly routed to image analyzer and damage extracted
- [ ] V002 Videos correctly routed to video analyzer, keyframes/transcript extracted
- [ ] V003 Documents correctly routed to document analyzer, fields extracted
- [ ] V004 Policy engine rates severity correctly based on damage
- [ ] V005 Policy engine calculates payout recommendation
- [ ] V006 Fraud indicators detected when criteria match
- [ ] V007 Ask IQ retrieves relevant claims policies
- [ ] V008 Frontend displays evidence gallery with all media types
- [ ] V009 Frontend displays assessment with policy citations
- [ ] V010 Adjuster can approve/adjust/deny claims

---

## Test File Mapping

| Phase | Test File | Description |
|-------|-----------|-------------|
| Phase 1 | `tests/test_auto_claims_phase1_config.py` | Config loading, persona registry |
| Phase 2 | `tests/test_auto_claims_phase2_router.py` | MIME detection, analyzer routing |
| Phase 3 | `tests/test_auto_claims_phase3_analyzers.py` | Analyzer creation/verification |
| Phase 4 | `tests/test_auto_claims_phase4_processing.py` | File processing, extraction |
| Phase 5 | `tests/test_auto_claims_phase5_policy_engine.py` | Policy evaluation, payout calc |
| Phase 6 | `tests/test_auto_claims_phase6_rag.py` | Policy chunking, search |
| Phase 7 | `tests/test_auto_claims_phase7_api.py` | REST API endpoints |
| Phase 8 | Manual / E2E | Frontend UX testing |
| Phase 9 | `tests/test_auto_claims_phase9_migrations.py` | Database migrations |

---

## Learnings & Notes

*(To be updated during implementation)*

### Azure CU Image Analyzer
- `prebuilt-imageSearch` generates a description but does NOT do damage detection
- Custom analyzer with explicit damage detection prompts required
- Face blurring is enabled by default, disable with `disableFaceBlurring: true`

### Azure CU Video Analyzer
- `prebuilt-videoSearch` provides segments, keyframes, and transcripts
- Keyframes returned as URLs that must be downloaded separately
- Video processing time scales with duration (~1-2 min per minute of video)
- Maximum video duration depends on Azure tier

### Field Schema Design
- Use `method: "generate"` for AI-inferred fields (damage severity)
- Use `method: "extract"` for OCR-based fields (VIN, dates)
- `estimateSourceAndConfidence: true` enables source attribution
