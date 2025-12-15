# Tasks: Azure Blob Storage Integration

**Input**: Design documents from `/specs/003-azure-blob-storage-integration/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Not explicitly requested in feature specification. Tests are not included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `app/` at repository root (existing structure)
- **Tests**: `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new dependency and create storage provider package structure

- [X] T001 Add `azure-storage-blob>=12.19.0` to requirements.txt
- [X] T002 Create storage providers package directory at app/storage_providers/
- [X] T003 [P] Create app/storage_providers/__init__.py with public exports

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Add StorageBackend enum to app/storage_providers/base.py per data-model.md
- [X] T005 Add StorageProvider Protocol to app/storage_providers/base.py per contracts/api-contract.md
- [X] T006 Add StorageSettings dataclass to app/storage_providers/base.py per data-model.md (note: placed in base.py instead of config.py for better modularity)
- [X] T007 Update load_settings() in app/storage_providers/base.py via StorageSettings.from_env()
- [X] T008 Update validate_settings() - validation done in provider __init__ with clear error messages

**Checkpoint**: Configuration infrastructure ready - storage provider implementations can now begin

---

## Phase 3: User Story 1 - Configure Azure Blob Storage Backend (Priority: P1) 🎯 MVP

**Goal**: Enable Azure Blob Storage as a configurable storage backend via environment variables

**Independent Test**: Set `STORAGE_BACKEND=azure_blob` with Azure credentials, upload a document, verify it appears in the blob container

### Implementation for User Story 1

- [X] T009 [US1] Create AzureBlobStorageProvider class in app/storage_providers/azure_blob.py with BlobServiceClient initialization
- [X] T010 [US1] Implement save_file() method in AzureBlobStorageProvider with retry policy per research.md §2
- [X] T011 [US1] Implement load_file() method in AzureBlobStorageProvider
- [X] T012 [US1] Implement save_metadata() method in AzureBlobStorageProvider
- [X] T013 [US1] Implement load_metadata() method in AzureBlobStorageProvider
- [X] T014 [US1] Implement list_applications() method in AzureBlobStorageProvider with persona filtering
- [X] T015 [US1] Implement save_cu_result() method in AzureBlobStorageProvider
- [X] T016 [US1] Implement application_exists() method in AzureBlobStorageProvider (via load_metadata)
- [X] T017 [US1] Implement get_file_url() method in AzureBlobStorageProvider
- [X] T018 [US1] Add container auto-creation in AzureBlobStorageProvider using create_if_not_exists() per research.md §4
- [X] T019 [US1] Create get_storage_provider() factory function in app/storage_providers/__init__.py to return provider based on settings
- [X] T020 [US1] Refactor app/storage.py to use get_storage_provider() instead of direct filesystem operations
- [X] T021 [US1] Update api_server.py to initialize storage provider at startup

**Checkpoint**: At this point, User Story 1 should be fully functional - Azure Blob Storage backend works when configured

---

## Phase 4: User Story 2 - Default to Local Storage (Priority: P2)

**Goal**: Maintain backward compatibility with local filesystem storage as the default

**Independent Test**: Start application without storage environment variables, upload a document, verify it saves to local `data/` directory

### Implementation for User Story 2

- [X] T022 [US2] Create LocalStorageProvider class in app/storage_providers/local.py
- [X] T023 [US2] Implement save_file() method in LocalStorageProvider (extract logic from current storage.py)
- [X] T024 [US2] Implement load_file() method in LocalStorageProvider
- [X] T025 [US2] Implement save_metadata() method in LocalStorageProvider (extract from save_application_metadata)
- [X] T026 [US2] Implement load_metadata() method in LocalStorageProvider (extract from load_application)
- [X] T027 [US2] Implement list_applications() method in LocalStorageProvider (extract from existing function)
- [X] T028 [US2] Implement save_cu_result() method in LocalStorageProvider (extract from save_cu_raw_result)
- [X] T029 [US2] Implement application_exists() method in LocalStorageProvider (via load_metadata)
- [X] T030 [US2] Implement get_file_url() method in LocalStorageProvider
- [X] T031 [US2] Update get_storage_provider() factory to return LocalStorageProvider when backend is 'local'
- [X] T032 [US2] Verify default configuration (no env vars) returns LocalStorageProvider

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - application defaults to local storage, can be switched to Azure Blob

---

## Phase 5: User Story 3 - Validate Storage Configuration at Startup (Priority: P3)

**Goal**: Provide clear error messages for storage misconfigurations at startup

**Independent Test**: Set `STORAGE_BACKEND=azure_blob` without credentials, verify specific error message on startup

### Implementation for User Story 3

- [X] T033 [US3] Add storage validation errors for missing AZURE_STORAGE_ACCOUNT_NAME (in AzureBlobStorageProvider.__init__)
- [X] T034 [US3] Add storage validation errors for missing AZURE_STORAGE_ACCOUNT_KEY (in AzureBlobStorageProvider.__init__)
- [X] T035 [US3] Add storage validation errors for invalid STORAGE_BACKEND value (defaults to 'local' in StorageSettings.from_env)
- [X] T036 [US3] Update api_server.py startup to fail fast with clear messages when storage validation fails
- [X] T037 [US3] Add startup logging to indicate which storage backend is active

**Checkpoint**: All user stories should now be independently functional - full feature complete

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and cleanup

- [X] T038 [P] Update README.md with Azure Blob Storage configuration section
- [X] T039 [P] Add .env.example entries for new storage environment variables
- [X] T040 Remove deprecated direct filesystem calls from app/storage.py (keep only provider-based API) - Legacy fallback retained for backward compatibility
- [X] T041 Verify quickstart.md instructions work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on T001 (azure-storage-blob package) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on T004-T008 (Foundational) completion
- **User Story 2 (Phase 4)**: Depends on T004-T008 (Foundational) completion - Can run parallel to US1
- **User Story 3 (Phase 5)**: Depends on T007-T008 (config validation infrastructure)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - Core Azure Blob implementation
- **User Story 2 (P2)**: Can start after Foundational - Can run parallel to US1 (different files)
- **User Story 3 (P3)**: Can start after T007-T008 - Extends validation logic

### Within Each User Story

- Provider class creation before method implementations
- All methods within a provider can be implemented in sequence
- Factory function after both providers exist
- Integration (storage.py refactor) after factory function

### Parallel Opportunities

Within Phase 2 (Foundational):
```
T004 + T005 can run in parallel (both in base.py but independent sections)
T006 + T007 + T008 are sequential (same file, dependent changes)
```

User Stories 1 and 2 can run in parallel:
```
US1: T009-T021 in app/storage_providers/azure_blob.py
US2: T022-T032 in app/storage_providers/local.py
(Different files, no dependencies between stories)
```

Phase 6 (Polish):
```
T038 + T039 can run in parallel (different files)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T008)
3. Complete Phase 3: User Story 1 (T009-T021)
4. **STOP and VALIDATE**: Test with Azure Blob Storage configuration
5. Deploy/demo if Azure-only deployment is acceptable

### Full Feature Delivery

1. Complete Setup + Foundational
2. Complete User Story 1 (Azure Blob) - MVP for cloud deployment
3. Complete User Story 2 (Local Storage) - Backward compatibility
4. Complete User Story 3 (Validation) - Operational excellence
5. Complete Polish - Documentation and cleanup

### Parallel Team Strategy

With two developers:
```
Developer A: User Story 1 (T009-T021) - Azure Blob provider
Developer B: User Story 2 (T022-T032) - Local provider
Then: Merge and complete User Story 3 together
```

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Tasks** | 41 |
| **Setup Phase** | 3 |
| **Foundational Phase** | 5 |
| **User Story 1 (P1)** | 13 |
| **User Story 2 (P2)** | 11 |
| **User Story 3 (P3)** | 5 |
| **Polish Phase** | 4 |
| **Parallel Opportunities** | US1 ∥ US2, T038 ∥ T039 |

### Independent Test Criteria per Story

| Story | Independent Test |
|-------|-----------------|
| US1 | Set `STORAGE_BACKEND=azure_blob` + credentials → upload doc → verify in Azure Portal |
| US2 | No env vars → upload doc → verify in local `data/applications/` directory |
| US3 | Set `STORAGE_BACKEND=azure_blob` without credentials → verify error message on startup |

### Suggested MVP Scope

**Minimum Viable Product**: Phases 1-3 (T001-T021)
- Delivers Azure Blob Storage capability for production Azure deployments
- 21 tasks total for MVP

**Full Feature**: All phases (T001-T041)
- Adds backward compatibility and operational polish
- 41 tasks total
