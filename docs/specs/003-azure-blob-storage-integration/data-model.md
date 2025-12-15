# Data Model: Azure Blob Storage Integration

**Feature**: 003-azure-blob-storage-integration  
**Date**: 2025-12-08  
**Source**: Feature spec entities + research findings

## Entities

### StorageBackend (Enum)

Enumeration of supported storage backend types.

| Value | Description |
|-------|-------------|
| `local` | Local filesystem storage (default) |
| `azure_blob` | Azure Blob Storage |

**Validation Rules**:
- Must be one of the defined values
- Case-insensitive comparison on input (normalized to lowercase)

### StorageSettings (Configuration)

Configuration container for storage backend settings.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `backend` | StorageBackend | No | `local` | Selected storage backend |
| `local_root` | str | If local | `"data"` | Root directory for local storage |
| `azure_account_name` | str | If azure_blob | - | Azure Storage account name |
| `azure_account_key` | str | If azure_blob | - | Azure Storage account key |
| `azure_container_name` | str | No | `"workbenchiq-data"` | Blob container name |
| `azure_timeout_seconds` | int | No | `30` | Per-operation timeout |
| `azure_retry_total` | int | No | `3` | Maximum retry attempts |

**Validation Rules**:
- If `backend` is `azure_blob`, both `azure_account_name` and `azure_account_key` are required
- `azure_container_name` must be 3-63 characters, lowercase letters, numbers, and hyphens only
- `azure_timeout_seconds` must be positive integer
- `azure_retry_total` must be non-negative integer

**State Transitions**: N/A (immutable configuration loaded at startup)

### StorageProvider (Protocol/Interface)

Abstract interface for storage operations. Not a data entity, but defines the contract that implementations must satisfy.

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `save_file` | `app_id: str, filename: str, content: bytes` | `str` (path/URL) | Save uploaded file |
| `load_file` | `app_id: str, filename: str` | `Optional[bytes]` | Load file content |
| `save_metadata` | `app_id: str, metadata: dict` | `None` | Save application metadata |
| `load_metadata` | `app_id: str` | `Optional[dict]` | Load application metadata |
| `list_applications` | `persona: Optional[str]` | `List[dict]` | List applications |
| `save_cu_result` | `app_id: str, payload: dict` | `str` (path) | Save Content Understanding result |
| `application_exists` | `app_id: str` | `bool` | Check if application exists |
| `get_file_url` | `app_id: str, filename: str` | `Optional[str]` | Get public URL if available |

## Relationships

```
Settings (existing)
    └── storage: StorageSettings (new)
            └── backend: StorageBackend
            
StorageProvider (protocol)
    ├── LocalStorageProvider (implements)
    │       └── uses: StorageSettings.local_root
    └── AzureBlobStorageProvider (implements)
            └── uses: StorageSettings.azure_*
            
ApplicationMetadata (existing, unchanged)
    └── files: List[StoredFile]
            └── path: str  # Now may be blob path or local path
            └── url: Optional[str]  # Now may be blob URL
```

## Storage Path Schema

Both backends use identical logical path structure:

```
applications/
└── {app_id}/
    ├── files/
    │   ├── {filename_1}
    │   ├── {filename_2}
    │   └── ...
    ├── metadata.json
    └── content_understanding.json
```

### Local Storage Physical Paths

```
{storage_root}/applications/{app_id}/files/{filename}
{storage_root}/applications/{app_id}/metadata.json
{storage_root}/applications/{app_id}/content_understanding.json
```

Where `{storage_root}` defaults to `data/`.

### Azure Blob Storage Paths

```
Container: {container_name}
Blob paths:
  applications/{app_id}/files/{filename}
  applications/{app_id}/metadata.json
  applications/{app_id}/content_understanding.json
```

Where `{container_name}` defaults to `workbenchiq-data`.

## Environment Variable Mapping

| Environment Variable | Maps To | Notes |
|---------------------|---------|-------|
| `STORAGE_BACKEND` | `StorageSettings.backend` | Parsed as StorageBackend enum |
| `UW_APP_STORAGE_ROOT` | `StorageSettings.local_root` | Existing variable, unchanged |
| `AZURE_STORAGE_ACCOUNT_NAME` | `StorageSettings.azure_account_name` | New |
| `AZURE_STORAGE_ACCOUNT_KEY` | `StorageSettings.azure_account_key` | New, sensitive |
| `AZURE_STORAGE_CONTAINER_NAME` | `StorageSettings.azure_container_name` | New, optional |

## Data Migration Notes

This feature does NOT include data migration. When switching from local to Azure Blob:
- Existing local data remains in place but is not accessible via the API
- New uploads go to Azure Blob Storage
- Manual migration (copying files) is an operational task outside this feature's scope

## Unchanged Entities

The following existing entities are NOT modified by this feature:

- `ApplicationMetadata`: Structure unchanged; `path` field may now contain blob paths
- `StoredFile`: Structure unchanged; `url` field may now contain blob URLs
- `ExtractedFieldConfidence`: No changes
- `ConfidenceSummary`: No changes
