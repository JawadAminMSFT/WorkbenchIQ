
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, List

try:
    # Load .env if python-dotenv is installed; fail silently otherwise.
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


# Import field schema from personas module for backward compatibility
from app.personas import UNDERWRITING_FIELD_SCHEMA, get_field_schema, get_persona_config

# Re-export for backward compatibility
__all__ = ["UNDERWRITING_FIELD_SCHEMA", "get_field_schema", "get_persona_config"]


@dataclass
class ContentUnderstandingSettings:
    endpoint: str
    api_key: Optional[str]
    analyzer_id: str
    api_version: str = "2025-11-01"
    completion_deployment: Optional[str] = None
    embedding_deployment: Optional[str] = None
    use_azure_ad: bool = False  # Use Azure AD authentication instead of subscription key
    enable_confidence_scores: bool = True  # Enable confidence scoring for field extraction
    custom_analyzer_id: str = "underwritingAnalyzer"  # Default custom analyzer (persona-specific)


# Note: Field schemas are now managed in app/personas.py
# UNDERWRITING_FIELD_SCHEMA is imported from there for backward compatibility


@dataclass
class OpenAISettings:
    endpoint: str
    api_key: str
    deployment_name: str
    api_version: str = "2024-10-21"
    model_name: str = "gpt-4.1"
    # Chat-specific settings (for Ask IQ feature)
    # If not set, falls back to main deployment
    chat_deployment_name: Optional[str] = None
    chat_model_name: Optional[str] = None
    chat_api_version: Optional[str] = None


@dataclass
class AppSettings:
    storage_root: str = "data"
    prompts_root: str = "prompts"  # Git-tracked folder for prompts and policies
    public_files_base_url: Optional[str] = None


@dataclass
class Settings:
    content_understanding: ContentUnderstandingSettings
    openai: OpenAISettings
    app: AppSettings


def load_settings() -> Settings:
    """Load configuration from environment variables."""

    use_azure_ad = os.getenv("AZURE_CONTENT_UNDERSTANDING_USE_AZURE_AD", "true").lower() == "true"
    api_key = os.getenv("AZURE_CONTENT_UNDERSTANDING_API_KEY") or None
    
    cu = ContentUnderstandingSettings(
        endpoint=os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT", "").rstrip("/"),
        api_key=api_key,
        analyzer_id=os.getenv("AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID", "prebuilt-documentSearch"),
        api_version=os.getenv("AZURE_CONTENT_UNDERSTANDING_API_VERSION", "2025-11-01"),
        completion_deployment=os.getenv("AZURE_CONTENT_UNDERSTANDING_COMPLETION_DEPLOYMENT") or None,
        embedding_deployment=os.getenv("AZURE_CONTENT_UNDERSTANDING_EMBEDDING_DEPLOYMENT") or None,
        use_azure_ad=use_azure_ad,
    )

    oa = OpenAISettings(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", ""),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        model_name=os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4.1"),
        # Chat-specific settings for Ask IQ (defaults to main model if not set)
        chat_deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME") or None,
        chat_model_name=os.getenv("AZURE_OPENAI_CHAT_MODEL_NAME") or None,
        chat_api_version=os.getenv("AZURE_OPENAI_CHAT_API_VERSION") or None,
    )

    app = AppSettings(
        storage_root=os.getenv("UW_APP_STORAGE_ROOT", "data"),
        prompts_root=os.getenv("UW_APP_PROMPTS_ROOT", "prompts"),
        public_files_base_url=os.getenv("PUBLIC_FILES_BASE_URL") or None,
    )

    return Settings(content_understanding=cu, openai=oa, app=app)


def validate_settings(settings: Settings) -> List[str]:
    """Validate configuration and return a list of human-readable error messages."""
    errors: List[str] = []

    # Content Understanding
    if not settings.content_understanding.endpoint:
        errors.append("AZURE_CONTENT_UNDERSTANDING_ENDPOINT is not set.")
    if not settings.content_understanding.use_azure_ad and not settings.content_understanding.api_key:
        errors.append("AZURE_CONTENT_UNDERSTANDING_API_KEY is not set (required when not using Azure AD auth).")
    if not settings.content_understanding.analyzer_id:
        errors.append("AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID is not set.")

    # OpenAI
    if not settings.openai.endpoint:
        errors.append("AZURE_OPENAI_ENDPOINT is not set.")
    if not settings.openai.api_key:
        errors.append("AZURE_OPENAI_API_KEY is not set.")
    if not settings.openai.deployment_name:
        errors.append("AZURE_OPENAI_DEPLOYMENT_NAME is not set.")

    # App
    if not settings.app.storage_root:
        errors.append("UW_APP_STORAGE_ROOT is not set or empty.")

    return errors
