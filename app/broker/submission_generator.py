"""
Submission Generator Module

Extracts ACORD 125 and ACORD 140 fields from client submission documents.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Dict, List, Tuple

from app.broker.models import BrokerDocument
from app.config import OpenAISettings
from app.openai_client import chat_completion
from app.utils import setup_logging

logger = setup_logging()


class SubmissionGenerator:
    """Extracts ACORD form fields from client submission documents."""

    def __init__(self, settings: OpenAISettings):
        """Initialize SubmissionGenerator with OpenAI settings.

        Args:
            settings: OpenAI configuration settings
        """
        self.settings = settings

    async def extract_acord_fields(
        self, documents: List[BrokerDocument]
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, float]]:
        """Extract ACORD 125 and ACORD 140 fields from uploaded client documents.

        Args:
            documents: List of BrokerDocument objects with client submission data

        Returns:
            Tuple of (acord_125_fields, acord_140_fields, confidence_scores)
            - acord_125_fields: Dict with ACORD 125 General Application fields
            - acord_140_fields: Dict with ACORD 140 Property Section fields
            - confidence_scores: Dict mapping field names to confidence 0.0-1.0
        """
        logger.info(f"Extracting ACORD fields from {len(documents)} documents")

        # Aggregate document content
        document_context = self._build_document_context(documents)

        # Build extraction prompt
        prompt = self._build_extraction_prompt(document_context)

        # Call LLM in thread pool
        result = await asyncio.to_thread(
            chat_completion,
            self.settings,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert commercial insurance submission analyst. Extract ACORD form fields accurately from client documents.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=8000,
        )

        raw_content = result.get("content", "")
        logger.debug(f"Received LLM response for ACORD extraction: {len(raw_content)} chars")

        # Parse JSON response
        parsed = self._parse_json_response(raw_content)

        # Extract structured data
        acord_125 = parsed.get("acord_125", {})
        acord_140 = parsed.get("acord_140", {})
        confidence = parsed.get("confidence", {})

        # Log low-confidence fields
        low_confidence = [field for field, score in confidence.items() if score < 0.60]
        if low_confidence:
            logger.warning(f"Low confidence ACORD fields: {low_confidence}")

        return acord_125, acord_140, confidence

    def _build_document_context(self, documents: List[BrokerDocument]) -> str:
        """Build aggregated document context for extraction.

        Args:
            documents: List of documents to process

        Returns:
            Formatted context string with document content
        """
        context_parts = []

        for doc in documents:
            doc_info = f"\n=== Document: {doc.file_name} (Type: {doc.document_type}) ===\n"
            
            # Include extracted fields if available
            if doc.extracted_fields:
                doc_info += "Extracted Fields:\n"
                doc_info += json.dumps(doc.extracted_fields, indent=2)[:5000]
                doc_info += "\n"

            context_parts.append(doc_info)

        return "\n".join(context_parts)

    def _build_extraction_prompt(self, document_context: str) -> str:
        """Build the ACORD field extraction prompt.

        Args:
            document_context: Aggregated document content

        Returns:
            Formatted prompt string
        """
        return f"""Extract ACORD 125 (General Application) and ACORD 140 (Property Section) fields from these client submission documents.

**Document Context:**
{document_context[:25000]}

**ACORD 125 Fields to Extract (13 fields per spec):**
1. applicant_name - Named insured / business name
2. fein - Federal Employer Identification Number
3. business_phone - Primary contact phone
4. mailing_address - Full mailing address
5. business_type - Type of business/entity (Corporation, LLC, etc.)
6. years_in_business - Years the business has been operating
7. sic_code - Standard Industry Classification code
8. annual_gross_revenue - Annual gross revenue
9. number_of_employees - Full-time + part-time headcount
10. prior_carrier - Current/prior insurance carrier name
11. prior_premium - Current/prior annual premium
12. effective_date_requested - Requested policy effective date (ISO format YYYY-MM-DD)
13. lines_of_business_requested - List of coverage types (Property, GL, Umbrella, etc.)

**ACORD 140 Fields to Extract:**
        **ACORD 140 Fields to Extract (15+ fields per spec):**
1. property_locations - Array of property locations with:
   - address: Full street address
   - occupancy: Building occupancy/use
   - construction_type: Construction class (frame, masonry, fire-resistive, etc.)
   - year_built: Year building was constructed
   - square_footage: Total building square footage
   - building_value: Building replacement value
   - contents_value: Business personal property value
   - bi_value: Business income/interruption value
   - protection_class: Fire protection class (1-10)
2. loss_history - Property loss history (date, cause, amount, description)
3. prior_policy_number - Expiring policy number
4. prior_expiration_date - Current policy expiry date
5. total_insured_value - Sum of all property values
6. requested_limits - Requested coverage limits (building, contents, BI)
7. deductibles - Requested deductible amounts
8. special_conditions - Any special conditions or requirements
9. mortgagee_info - Mortgagee/additional insured information

**Response Format:**
Return ONLY valid JSON with three keys:
{{
  "acord_125": {{
    "applicant_name": "Business Name Inc.",
    "fein": "12-3456789",
    "business_phone": "(555) 123-4567",
    "mailing_address": "123 Main St, City, ST 12345",
    "business_type": "Corporation",
    "years_in_business": 15,
    "sic_code": "5411",
    "annual_gross_revenue": "$12,500,000",
    "number_of_employees": 85,
    "prior_carrier": "ABC Insurance Co.",
    "prior_premium": "$85,000",
    "effective_date_requested": "2025-01-01",
    "lines_of_business_requested": ["Commercial Property", "General Liability", "Business Auto", "Umbrella"]
  }},
  "acord_140": {{
    "property_locations": [
      {{
        "address": "123 Main St, City, ST 12345",
        "occupancy": "Office",
        "construction_type": "Masonry Noncombustible",
        "year_built": 1995,
        "square_footage": 10000,
        "building_value": "$2,500,000",
        "contents_value": "$500,000",
        "bi_value": "$750,000",
        "protection_class": "3"
      }},
      {{
        "address": "456 Oak Ave, City, ST 12345",
        "occupancy": "Warehouse",
        "construction_type": "Steel Frame",
        "year_built": 2010,
        "square_footage": 25000,
        "building_value": "$3,000,000",
        "contents_value": "$1,000,000",
        "bi_value": "$500,000",
        "protection_class": "4"
      }}
    ],
    "loss_history": [
      {{"date": "2023-05-15", "location": "123 Main St", "cause": "Water Damage", "amount": "$12,500", "description": "Roof leak during storm", "status": "Closed"}}
    ],
    "prior_policy_number": "POL-123456",
    "prior_expiration_date": "2024-12-31",
    "total_insured_value": "$8,250,000",
    "requested_limits": {{
      "building": "$5,500,000",
      "contents": "$1,500,000",
      "business_interruption": "$1,250,000"
    }},
    "deductibles": {{
      "property": "$5,000",
      "wind_hail": "$25,000"
    }},
    "special_conditions": [
      "Sprinkler system required",
      "24/7 security monitoring in place"
    ],
    "mortgagee_info": [
      {{"name": "First National Bank", "loan_number": "LOAN-789456", "address": "789 Bank St, City, ST 12345"}}
    ]
  }},
  "confidence": {{
    "applicant_name": 0.98,
    "fein": 0.95,
    "business_phone": 0.93,
    "mailing_address": 0.95,
    "business_type": 0.90,
    "years_in_business": 0.85,
    "sic_code": 0.88,
    "annual_gross_revenue": 0.87,
    "number_of_employees": 0.82,
    "prior_carrier": 0.88,
    "prior_premium": 0.82,
    "effective_date_requested": 0.92,
    "lines_of_business_requested": 0.90,
    "property_locations": 0.88,
    "loss_history": 0.78,
    "prior_policy_number": 0.85,
    "prior_expiration_date": 0.90,
    "total_insured_value": 0.92,
    "requested_limits": 0.85,
    "deductibles": 0.80,
    "special_conditions": 0.70,
    "mortgagee_info": 0.75
  }}
}}

Use empty string "" for missing text fields, empty array [] for missing lists, and null for missing objects.
Return ONLY the JSON, no markdown fences or additional text."""

    def _parse_json_response(self, raw_content: str) -> Dict[str, Any]:
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

        # Strip JS-style comments
        content_to_parse = re.sub(r"//[^\n]*", "", content_to_parse)

        try:
            parsed = json.loads(content_to_parse)

            # Validate structure
            if "acord_125" not in parsed:
                parsed["acord_125"] = {}
            if "acord_140" not in parsed:
                parsed["acord_140"] = {}
            if "confidence" not in parsed:
                parsed["confidence"] = {}

            return parsed

        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse ACORD JSON: {exc}")
            return {
                "acord_125": {},
                "acord_140": {},
                "confidence": {},
                "_error": f"Failed to parse JSON response: {str(exc)}",
                "_raw": raw_content[:500],
            }
