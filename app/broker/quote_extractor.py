"""
Quote Extractor Module

Extracts structured quote fields from carrier documents using LLM parsing.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Dict, Tuple

from app.broker.models import QuoteFields
from app.config import OpenAISettings
from app.openai_client import chat_completion
from app.utils import setup_logging

logger = setup_logging()


class QuoteExtractor:
    """Extracts quote fields from carrier documents."""

    def __init__(self, settings: OpenAISettings):
        """Initialize QuoteExtractor with OpenAI settings.
        
        Args:
            settings: OpenAI configuration settings
        """
        self.settings = settings

    async def extract_quote(
        self, file_content: bytes, file_name: str, carrier_name: str
    ) -> Tuple[QuoteFields, Dict[str, float]]:
        """Extract quote fields from uploaded carrier document.
        
        Args:
            file_content: Raw bytes of the carrier document
            file_name: Original filename
            carrier_name: Name of the carrier providing the quote
            
        Returns:
            Tuple of (QuoteFields dataclass, confidence_scores dict)
            Confidence scores map field names to 0.0-1.0 values
        """
        # Decode file content to string
        try:
            text_content = file_content.decode("utf-8")
        except UnicodeDecodeError:
            logger.warning(f"UTF-8 decode failed for {file_name}, trying latin-1")
            text_content = file_content.decode("latin-1")

        # Build extraction prompt
        prompt = self._build_extraction_prompt(text_content, carrier_name)

        # Call LLM in thread pool to avoid blocking
        result = await asyncio.to_thread(
            chat_completion,
            self.settings,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert commercial insurance quote parser. Extract quote fields accurately and provide confidence scores.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=4000,
        )

        raw_content = result.get("content", "")
        logger.debug(f"Received LLM response for quote extraction: {len(raw_content)} chars")

        # Parse JSON response
        parsed = self._parse_json_response(raw_content)

        # Map to QuoteFields dataclass
        fields_dict = parsed.get("fields", {})
        confidence = parsed.get("confidence", {})

        quote_fields = QuoteFields(
            annual_premium=fields_dict.get("annual_premium", ""),
            total_insured_value=fields_dict.get("total_insured_value", ""),
            building_limit=fields_dict.get("building_limit", ""),
            contents_limit=fields_dict.get("contents_limit", ""),
            business_interruption_limit=fields_dict.get("business_interruption_limit", ""),
            deductible=fields_dict.get("deductible", ""),
            flood_sublimit=fields_dict.get("flood_sublimit", ""),
            earthquake_sublimit=fields_dict.get("earthquake_sublimit", ""),
            named_perils_exclusions=fields_dict.get("named_perils_exclusions", []),
            special_conditions=fields_dict.get("special_conditions", []),
            policy_period=fields_dict.get("policy_period", ""),
            carrier_am_best_rating=fields_dict.get("carrier_am_best_rating", ""),
            quote_reference_number=fields_dict.get("quote_reference_number", ""),
            expiry_date=fields_dict.get("expiry_date"),
            underwriter=fields_dict.get("underwriter", ""),
        )

        # Flag low-confidence fields
        low_confidence_fields = [
            field for field, score in confidence.items() if score < 0.60
        ]
        if low_confidence_fields:
            logger.warning(
                f"Low confidence fields for {carrier_name}: {low_confidence_fields}"
            )

        return quote_fields, confidence

    def _build_extraction_prompt(self, text_content: str, carrier_name: str) -> str:
        """Build the prompt for quote field extraction.
        
        Args:
            text_content: Document text
            carrier_name: Carrier providing the quote
            
        Returns:
            Formatted prompt string
        """
        return f"""Extract the following fields from this {carrier_name} insurance quote document.

**Document Content:**
{text_content[:15000]}

**Fields to Extract:**
1. annual_premium - Total annual premium amount
2. total_insured_value - Total insured value across all coverages
3. building_limit - Building coverage limit
4. contents_limit - Contents/BPP coverage limit
5. business_interruption_limit - Business interruption coverage limit
6. deductible - Deductible amount(s)
7. flood_sublimit - Flood coverage sublimit
8. earthquake_sublimit - Earthquake coverage sublimit
9. named_perils_exclusions - List of excluded perils or conditions
10. special_conditions - List of special policy conditions or endorsements
11. policy_period - Policy effective dates
12. carrier_am_best_rating - AM Best financial strength rating
13. quote_reference_number - Quote or proposal reference number
14. expiry_date - Quote expiration date
15. underwriter - Name of underwriter

**Response Format:**
Return ONLY valid JSON with two keys:
- "fields": object with extracted field values (use empty string "" for missing text fields, empty array [] for list fields)
- "confidence": object with confidence scores 0.0-1.0 for each field

Example:
{{
  "fields": {{
    "annual_premium": "$125,000",
    "total_insured_value": "$5,000,000",
    "building_limit": "$3,000,000",
    "contents_limit": "$1,500,000",
    "business_interruption_limit": "$500,000",
    "deductible": "$5,000",
    "flood_sublimit": "$100,000",
    "earthquake_sublimit": "$250,000",
    "named_perils_exclusions": ["Flood outside sublimit", "Nuclear"],
    "special_conditions": ["Sprinkler warranty", "Alarm warranty"],
    "policy_period": "01/01/2025 - 01/01/2026",
    "carrier_am_best_rating": "A+",
    "quote_reference_number": "Q-2025-12345",
    "expiry_date": "2025-02-15",
    "underwriter": "John Smith"
  }},
  "confidence": {{
    "annual_premium": 0.95,
    "total_insured_value": 0.90,
    "building_limit": 0.88,
    "contents_limit": 0.85,
    "business_interruption_limit": 0.82,
    "deductible": 0.93,
    "flood_sublimit": 0.75,
    "earthquake_sublimit": 0.70,
    "named_perils_exclusions": 0.80,
    "special_conditions": 0.78,
    "policy_period": 0.95,
    "carrier_am_best_rating": 0.65,
    "quote_reference_number": 0.98,
    "expiry_date": 0.92,
    "underwriter": 0.85
  }}
}}

Return ONLY the JSON, no markdown fences or additional text."""

    def _parse_json_response(self, raw_content: str) -> Dict:
        """Parse JSON from LLM response, handling code fences and comments.
        
        Args:
            raw_content: Raw LLM response text
            
        Returns:
            Parsed JSON dict (or error dict if parsing fails)
        """
        content_to_parse = raw_content.strip()

        # Strip markdown code fences
        if content_to_parse.startswith("```"):
            first_newline = content_to_parse.find("\n")
            if first_newline != -1:
                content_to_parse = content_to_parse[first_newline + 1 :]
            closing_idx = content_to_parse.rfind("```")
            if closing_idx != -1:
                content_to_parse = content_to_parse[:closing_idx].strip()

        try:
            parsed = json.loads(content_to_parse)
        except json.JSONDecodeError:
            # Strip JS-style comments and try again
            stripped = re.sub(r"//[^\n]*", "", content_to_parse)
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response: {content_to_parse[:200]}")
                parsed = {
                    "fields": {},
                    "confidence": {},
                    "_error": "Failed to parse JSON response",
                }

        return parsed
