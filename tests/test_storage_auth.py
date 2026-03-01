"""Tests for DAC-first Azure Blob Storage auth resolution and container policy.

Covers:
- StorageSettings.from_env  auth_mode / allow_create_container parsing
- AzureBlobStorageProvider auth selection (DAC → conn str → key)
- DAC failure with automatic fallback
- Container auto-creation disabled/enabled behaviour
"""

from __future__ import annotations

import os
from dataclasses import replace
from typing import Any
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.storage_providers.base import StorageBackend, StorageSettings


# ---------------------------------------------------------------------------
# StorageSettings.from_env – new fields
# ---------------------------------------------------------------------------

class TestStorageSettingsFromEnv:
    """Verify that new env vars are parsed correctly into StorageSettings."""

    def test_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No env vars → sensible defaults."""
        monkeypatch.delenv("AZURE_STORAGE_AUTH_MODE", raising=False)
        monkeypatch.delenv("AZURE_STORAGE_ALLOW_CREATE_CONTAINER", raising=False)
        monkeypatch.delenv("STORAGE_BACKEND", raising=False)

        settings = StorageSettings.from_env()
        assert settings.azure_storage_auth_mode == "default"
        assert settings.azure_storage_allow_create_container is False

    @pytest.mark.parametrize(
        "env_val, expected",
        [
            ("default", "default"),
            ("DEFAULT", "default"),
            ("connection_string", "connection_string"),
            ("CONNECTION_STRING", "connection_string"),
            ("key", "key"),
            ("KEY", "key"),
            ("bogus", "default"),  # invalid → falls back to default
        ],
    )
    def test_auth_mode_parsing(
        self, monkeypatch: pytest.MonkeyPatch, env_val: str, expected: str
    ) -> None:
        monkeypatch.setenv("AZURE_STORAGE_AUTH_MODE", env_val)
        settings = StorageSettings.from_env()
        assert settings.azure_storage_auth_mode == expected

    @pytest.mark.parametrize(
        "env_val, expected",
        [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
            ("", False),
        ],
    )
    def test_allow_create_container_parsing(
        self, monkeypatch: pytest.MonkeyPatch, env_val: str, expected: bool
    ) -> None:
        monkeypatch.setenv("AZURE_STORAGE_ALLOW_CREATE_CONTAINER", env_val)
        settings = StorageSettings.from_env()
        assert settings.azure_storage_allow_create_container is expected

    def test_existing_fields_preserved(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Existing fields (account_name, account_key, etc.) still load."""
        monkeypatch.setenv("STORAGE_BACKEND", "azure_blob")
        monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_NAME", "myacct")
        monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_KEY", "mykey")
        monkeypatch.setenv("AZURE_STORAGE_CONTAINER_NAME", "mycontainer")
        monkeypatch.setenv("AZURE_STORAGE_AUTH_MODE", "key")
        monkeypatch.setenv("AZURE_STORAGE_ALLOW_CREATE_CONTAINER", "true")

        settings = StorageSettings.from_env()
        assert settings.backend == StorageBackend.AZURE_BLOB
        assert settings.azure_account_name == "myacct"
        assert settings.azure_account_key == "mykey"
        assert settings.azure_container_name == "mycontainer"
        assert settings.azure_storage_auth_mode == "key"
        assert settings.azure_storage_allow_create_container is True


# ---------------------------------------------------------------------------
# Helpers for AzureBlobStorageProvider tests
# ---------------------------------------------------------------------------

def _base_settings(**overrides: Any) -> StorageSettings:
    """Return a minimal StorageSettings for azure_blob with overrides."""
    defaults = dict(
        backend=StorageBackend.AZURE_BLOB,
        azure_account_name="testaccount",
        azure_account_key="dGVzdGtleQ==",  # base64 placeholder
        azure_container_name="test-container",
        azure_connection_string=None,
        azure_storage_auth_mode="default",
        azure_storage_allow_create_container=False,
    )
    defaults.update(overrides)
    return StorageSettings(**defaults)


def _mock_blob_service() -> MagicMock:
    """Return a MagicMock that looks like a BlobServiceClient."""
    svc = MagicMock()
    container = MagicMock()
    svc.get_container_client.return_value = container
    svc.get_account_information.return_value = {}
    return svc


# ---------------------------------------------------------------------------
# Auth resolution – _resolve_blob_service / _resolve_default_chain
# ---------------------------------------------------------------------------

class TestAuthResolution:
    """Verify auth selection and fallback behaviour."""

    @patch("app.storage_providers.azure_blob.AzureBlobStorageProvider._ensure_container_exists")
    def test_explicit_connection_string(self, _ensure: MagicMock) -> None:
        """auth_mode=connection_string forces connection-string auth."""
        settings = _base_settings(
            azure_storage_auth_mode="connection_string",
            azure_connection_string="DefaultEndpointsProtocol=https;AccountName=x;AccountKey=y;EndpointSuffix=core.windows.net",
        )

        with patch(
            "azure.storage.blob.BlobServiceClient.from_connection_string",
            return_value=_mock_blob_service(),
        ):
            from app.storage_providers.azure_blob import AzureBlobStorageProvider
            provider = AzureBlobStorageProvider(settings)

        assert provider._resolved_auth == "connection_string"

    @patch("app.storage_providers.azure_blob.AzureBlobStorageProvider._ensure_container_exists")
    def test_explicit_key(self, _ensure: MagicMock) -> None:
        """auth_mode=key forces account-key auth."""
        settings = _base_settings(azure_storage_auth_mode="key")

        with patch(
            "azure.storage.blob.BlobServiceClient",
            return_value=_mock_blob_service(),
        ):
            from app.storage_providers.azure_blob import AzureBlobStorageProvider
            provider = AzureBlobStorageProvider(settings)

        assert provider._resolved_auth == "account_key"

    @patch("app.storage_providers.azure_blob.AzureBlobStorageProvider._ensure_container_exists")
    def test_default_mode_dac_success(self, _ensure: MagicMock) -> None:
        """Default mode succeeds with DAC when credential probe works."""
        settings = _base_settings(
            azure_storage_auth_mode="default",
            azure_account_key=None,  # no key – DAC only
            azure_connection_string=None,
        )

        mock_svc = _mock_blob_service()

        with (
            patch("azure.identity.DefaultAzureCredential", return_value=MagicMock()),
            patch(
                "azure.storage.blob.BlobServiceClient",
                return_value=mock_svc,
            ),
        ):
            from app.storage_providers.azure_blob import AzureBlobStorageProvider
            provider = AzureBlobStorageProvider(settings)

        assert provider._resolved_auth == "DefaultAzureCredential"

    @patch("app.storage_providers.azure_blob.AzureBlobStorageProvider._ensure_container_exists")
    def test_default_mode_dac_failure_falls_back_to_conn_str(
        self, _ensure: MagicMock
    ) -> None:
        """When DAC probe fails and a connection string is available, fall back."""
        settings = _base_settings(
            azure_storage_auth_mode="default",
            azure_account_key=None,
            azure_connection_string="DefaultEndpointsProtocol=https;AccountName=x;AccountKey=y;EndpointSuffix=core.windows.net",
        )

        mock_dac_svc = _mock_blob_service()
        mock_dac_svc.get_account_information.side_effect = Exception("DAC failed")

        mock_conn_svc = _mock_blob_service()

        call_count = {"n": 0}
        original_init = None

        def blob_service_side_effect(*args: Any, **kwargs: Any) -> MagicMock:
            call_count["n"] += 1
            if call_count["n"] == 1:
                return mock_dac_svc  # first call = DAC attempt
            return mock_conn_svc

        with (
            patch("azure.identity.DefaultAzureCredential", return_value=MagicMock()),
            patch(
                "azure.storage.blob.BlobServiceClient",
                side_effect=blob_service_side_effect,
            ),
            patch(
                "azure.storage.blob.BlobServiceClient.from_connection_string",
                return_value=mock_conn_svc,
            ),
        ):
            from app.storage_providers.azure_blob import AzureBlobStorageProvider
            provider = AzureBlobStorageProvider(settings)

        assert provider._resolved_auth == "connection_string"

    @patch("app.storage_providers.azure_blob.AzureBlobStorageProvider._ensure_container_exists")
    def test_default_mode_dac_failure_falls_back_to_key(
        self, _ensure: MagicMock
    ) -> None:
        """When DAC and conn str both unavailable, fall back to account key."""
        settings = _base_settings(
            azure_storage_auth_mode="default",
            azure_connection_string=None,
        )

        mock_dac_svc = _mock_blob_service()
        mock_dac_svc.get_account_information.side_effect = Exception("DAC failed")

        mock_key_svc = _mock_blob_service()

        call_count = {"n": 0}

        def blob_service_side_effect(*args: Any, **kwargs: Any) -> MagicMock:
            call_count["n"] += 1
            if call_count["n"] == 1:
                return mock_dac_svc
            return mock_key_svc

        with (
            patch("azure.identity.DefaultAzureCredential", return_value=MagicMock()),
            patch(
                "azure.storage.blob.BlobServiceClient",
                side_effect=blob_service_side_effect,
            ),
        ):
            from app.storage_providers.azure_blob import AzureBlobStorageProvider
            provider = AzureBlobStorageProvider(settings)

        assert provider._resolved_auth == "account_key"

    def test_no_credentials_at_all_raises(self) -> None:
        """When no credentials are available, raise ValueError."""
        settings = _base_settings(
            azure_storage_auth_mode="default",
            azure_account_name=None,
            azure_account_key=None,
            azure_connection_string=None,
        )

        with pytest.raises(ValueError, match="No valid Azure Blob Storage credentials"):
            from app.storage_providers.azure_blob import AzureBlobStorageProvider
            AzureBlobStorageProvider(settings)

    def test_explicit_conn_str_missing_raises(self) -> None:
        """auth_mode=connection_string but no connection string → ValueError."""
        settings = _base_settings(
            azure_storage_auth_mode="connection_string",
            azure_connection_string=None,
        )

        with pytest.raises(ValueError, match="AZURE_STORAGE_CONNECTION_STRING is not set"):
            from app.storage_providers.azure_blob import AzureBlobStorageProvider
            AzureBlobStorageProvider(settings)

    def test_explicit_key_missing_raises(self) -> None:
        """auth_mode=key but account name/key missing → ValueError."""
        settings = _base_settings(
            azure_storage_auth_mode="key",
            azure_account_name=None,
            azure_account_key=None,
        )

        with pytest.raises(ValueError, match="AZURE_STORAGE_ACCOUNT_NAME"):
            from app.storage_providers.azure_blob import AzureBlobStorageProvider
            AzureBlobStorageProvider(settings)


# ---------------------------------------------------------------------------
# Container lifecycle – _ensure_container_exists
# ---------------------------------------------------------------------------

class TestContainerLifecycle:
    """Verify container creation policy."""

    @patch("app.storage_providers.azure_blob.AzureBlobStorageProvider._resolve_blob_service")
    def test_no_create_by_default(self, mock_resolve: MagicMock) -> None:
        """allow_create_container=False (default) → no create_container call."""
        mock_svc = _mock_blob_service()
        mock_resolve.return_value = (mock_svc, "account_key")

        settings = _base_settings(azure_storage_allow_create_container=False)

        from app.storage_providers.azure_blob import AzureBlobStorageProvider
        provider = AzureBlobStorageProvider(settings)

        container_client = mock_svc.get_container_client.return_value
        container_client.create_container.assert_not_called()

    @patch("app.storage_providers.azure_blob.AzureBlobStorageProvider._resolve_blob_service")
    def test_create_when_enabled(self, mock_resolve: MagicMock) -> None:
        """allow_create_container=True → create_container is called."""
        mock_svc = _mock_blob_service()
        mock_resolve.return_value = (mock_svc, "account_key")

        settings = _base_settings(azure_storage_allow_create_container=True)

        from app.storage_providers.azure_blob import AzureBlobStorageProvider
        provider = AzureBlobStorageProvider(settings)

        container_client = mock_svc.get_container_client.return_value
        container_client.create_container.assert_called_once()

    @patch("app.storage_providers.azure_blob.AzureBlobStorageProvider._resolve_blob_service")
    def test_create_already_exists_is_fine(self, mock_resolve: MagicMock) -> None:
        """ResourceExistsError during create is silently handled."""
        from azure.core.exceptions import ResourceExistsError

        mock_svc = _mock_blob_service()
        mock_resolve.return_value = (mock_svc, "account_key")
        container_client = mock_svc.get_container_client.return_value
        container_client.create_container.side_effect = ResourceExistsError("exists")

        settings = _base_settings(azure_storage_allow_create_container=True)

        from app.storage_providers.azure_blob import AzureBlobStorageProvider
        # Should not raise
        provider = AzureBlobStorageProvider(settings)
        container_client.create_container.assert_called_once()

    @patch("app.storage_providers.azure_blob.AzureBlobStorageProvider._resolve_blob_service")
    def test_create_permission_denied_warns(self, mock_resolve: MagicMock) -> None:
        """HTTP 403 during create logs a warning but does not raise."""
        from azure.core.exceptions import HttpResponseError

        mock_svc = _mock_blob_service()
        mock_resolve.return_value = (mock_svc, "DefaultAzureCredential")
        container_client = mock_svc.get_container_client.return_value

        err = HttpResponseError(message="Forbidden")
        err.status_code = 403
        container_client.create_container.side_effect = err

        settings = _base_settings(azure_storage_allow_create_container=True)

        from app.storage_providers.azure_blob import AzureBlobStorageProvider
        # Should warn but not raise
        provider = AzureBlobStorageProvider(settings)

    @patch("app.storage_providers.azure_blob.AzureBlobStorageProvider._resolve_blob_service")
    def test_create_unexpected_error_raises(self, mock_resolve: MagicMock) -> None:
        """Non-403 HttpResponseError during create is re-raised."""
        from azure.core.exceptions import HttpResponseError

        mock_svc = _mock_blob_service()
        mock_resolve.return_value = (mock_svc, "account_key")
        container_client = mock_svc.get_container_client.return_value

        err = HttpResponseError(message="Internal Server Error")
        err.status_code = 500
        container_client.create_container.side_effect = err

        settings = _base_settings(azure_storage_allow_create_container=True)

        with pytest.raises(HttpResponseError):
            from app.storage_providers.azure_blob import AzureBlobStorageProvider
            AzureBlobStorageProvider(settings)
