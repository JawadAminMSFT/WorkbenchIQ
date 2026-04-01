"""
Document processor for Commercial Brokerage Content Understanding.

Handles document analysis via Azure Content Understanding, field extraction
with confidence scoring, and result normalization.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from app.config import BrokerSettings, ContentUnderstandingSettings

logger = logging.getLogger(__name__)


def _normalize_cu_value(value: Any) -> Any:
    """Normalize a CU field value to a plain Python value.

    CU returns structured objects for fields (with 'type', 'valueString',
    'spans', 'confidence', 'source').  This function extracts the actual
    value so downstream code can work with simple strings / lists.
    """
    if value is None:
        return value

    # Single structured field object → extract valueString / valueNumber etc.
    if isinstance(value, dict):
        for key in ("valueString", "valueDate", "valueNumber",
                     "valueBoolean", "value", "content", "text"):
            if key in value:
                return value[key]
        # If it has 'valueObject' or 'valueArray', recurse
        if "valueObject" in value:
            return _normalize_cu_value(value["valueObject"])
        if "valueArray" in value:
            return _normalize_cu_value(value["valueArray"])
        # Object with 'properties' → normalise each property
        if "properties" in value and isinstance(value["properties"], dict):
            return {k: _normalize_cu_value(v) for k, v in value["properties"].items()}
        return value

    # List of structured items → extract valueString from each
    if isinstance(value, list):
        normalized = []
        for item in value:
            if isinstance(item, dict):
                # Try to get the plain value
                plain = None
                for key in ("valueString", "valueDate", "valueNumber",
                             "valueBoolean", "value", "content", "text"):
                    if key in item:
                        plain = item[key]
                        break
                # If it's an object type with properties, normalise them
                if plain is None and "valueObject" in item:
                    obj = item["valueObject"]
                    if isinstance(obj, dict):
                        plain = {k: _normalize_cu_value(v) for k, v in obj.items()}
                if plain is None and "properties" in item:
                    props = item["properties"]
                    if isinstance(props, dict):
                        plain = {k: _normalize_cu_value(v) for k, v in props.items()}
                normalized.append(plain if plain is not None else item)
            else:
                normalized.append(item)
        return normalized

    return value


class BrokerCUProcessor:
    """
    Processes broker documents through Azure Content Understanding.

    Provides:
    - Document analysis via CU binary upload
    - Field extraction with confidence scores
    - Markdown content extraction
    - Availability checking
    """

    def __init__(
        self,
        cu_settings: ContentUnderstandingSettings,
        broker_settings: BrokerSettings,
    ) -> None:
        self._cu_settings = cu_settings
        self._broker_settings = broker_settings

    def is_available(self) -> bool:
        """Check whether the CU endpoint is configured and broker CU is enabled."""
        return bool(
            self._broker_settings.enabled
            and self._cu_settings.endpoint
        )

    async def analyze_document(
        self,
        file_content: bytes,
        file_name: str,
        document_type: str,
        analyzer_id: str,
    ) -> Dict[str, Any]:
        """
        Analyze a document using Azure Content Understanding.

        Args:
            file_content: Raw document bytes
            file_name: Original filename (used for logging/context)
            document_type: Classified document type
            analyzer_id: CU analyzer ID to use

        Returns:
            Dictionary with keys:
                fields   - extracted field values
                confidence - per-field confidence scores
                markdown - markdown representation of the document
                raw_result - full CU response payload
        """
        from app.content_understanding_client import (
            ContentUnderstandingError,
            analyze_document,
            extract_fields_with_confidence,
        )

        logger.info(
            "Analyzing document '%s' (type=%s) with analyzer '%s'",
            file_name,
            document_type,
            analyzer_id,
        )

        try:
            # Override the analyzer_id on a copy of settings so we target
            # the correct custom analyzer for this document type.
            cu_settings = ContentUnderstandingSettings(
                endpoint=self._cu_settings.endpoint,
                api_key=self._cu_settings.api_key,
                analyzer_id=analyzer_id,
                api_version=self._cu_settings.api_version,
                completion_deployment=self._cu_settings.completion_deployment,
                embedding_deployment=self._cu_settings.embedding_deployment,
                use_azure_ad=self._cu_settings.use_azure_ad,
                enable_confidence_scores=self._cu_settings.enable_confidence_scores,
                custom_analyzer_id=analyzer_id,
            )

            raw_result = await asyncio.to_thread(
                analyze_document,
                settings=cu_settings,
                file_path=file_name,
                file_bytes=file_content,
                output_markdown=True,
            )

            # Extract fields with confidence scores
            field_confidences = extract_fields_with_confidence(raw_result)

            fields: Dict[str, Any] = {}
            confidence: Dict[str, float] = {}
            for name, fc in field_confidences.items():
                fields[name] = _normalize_cu_value(fc.value)
                confidence[name] = fc.confidence

            # Extract markdown content from the raw result
            markdown = self._extract_markdown(raw_result)

            logger.info(
                "Successfully extracted %d fields from '%s'",
                len(fields),
                file_name,
            )

            return {
                "fields": fields,
                "confidence": confidence,
                "markdown": markdown,
                "raw_result": raw_result,
            }

        except ContentUnderstandingError:
            logger.exception(
                "Content Understanding error analyzing '%s'", file_name
            )
            raise
        except Exception:
            logger.exception(
                "Unexpected error analyzing '%s'", file_name
            )
            raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_markdown(raw_result: Dict[str, Any]) -> str:
        """Pull the markdown representation out of the CU response."""
        result = raw_result.get("result", {})

        # Check for markdown in contents
        for content in result.get("contents", []):
            md = content.get("markdown") or content.get("text")
            if md:
                return md

        # Fallback: top-level markdown
        return result.get("markdown", "")
