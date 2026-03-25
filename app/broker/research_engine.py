"""
Client Research Engine Module

Generates AI-powered client research briefs using Bing Grounding.
Returns structured ResearchBrief data, not free-text markdown.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from app.config import OpenAISettings
from app.openai_client import chat_completion
from app.utils import setup_logging

logger = setup_logging()

# Responses API configuration
_RESPONSES_API_VERSION = "2025-04-01-preview"
_RESPONSES_API_MODEL = "gpt-4.1"

# JSON schema that the LLM must return — mirrors ResearchBrief dataclass
_RESEARCH_BRIEF_SCHEMA = """{
  "company_name": "string — full legal or trade name",
  "business_description": "string — what the company does, its market position",
  "headquarters": "string — city, state",
  "year_founded": "integer or null",
  "employee_count": "integer or null",
  "ownership_type": "string — Public, Private, Mutual, LLC, etc.",
  "key_operations": ["string — each major business activity"],
  "annual_revenue": "string — e.g. '$12,000,000'",
  "revenue_trend": "string — Growing, Stable, or Declining",
  "credit_rating": "string — e.g. 'BBB+' or 'Not rated'",
  "financial_highlights": ["string — notable financial facts"],
  "naics_code": "string — primary NAICS code",
  "industry_sector": "string — e.g. 'Commercial Real Estate'",
  "common_perils": ["string — perils typical for this industry"],
  "loss_frequency": "string — Low, Moderate, or High",
  "risk_factors": ["string — company-specific risk factors"],
  "insurance_needs": [
    {"line": "string — line of business", "priority": "Primary|Required|Recommended|Optional", "estimated_premium": "string — range", "rationale": "string — why this coverage"}
  ],
  "carrier_matches": [
    {"carrier": "string — carrier name", "rating": "string — AM Best rating", "appetite": "Strong|Good|Moderate|Limited", "rationale": "string — why this carrier fits"}
  ],
  "recent_news": [
    {"date": "string — YYYY-MM-DD", "headline": "string", "source": "string"}
  ],
  "citations": ["string — source URLs or references"],
  "confidence_level": "High|Medium|Low"
}"""


class ClientResearchEngine:
    """Generates AI-powered client research briefs with web grounding."""

    def __init__(self, settings: OpenAISettings):
        self.settings = settings

    async def research_client(
        self,
        company_name: str,
        uploaded_docs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate a structured client research brief.

        Uses Bing web grounding via Azure OpenAI Responses API.
        Falls back to standard chat_completion when unavailable.

        Args:
            company_name: Name of the company to research
            uploaded_docs: Optional list of uploaded document text content
                to incorporate as primary sources

        Returns:
            Dict matching the ResearchBrief schema.
        """
        logger.info(f"Starting client research for: {company_name}")

        prompt = self._build_research_prompt(company_name, uploaded_docs)

        # Try Responses API first (with Bing grounding)
        research_data = await self._try_responses_api(prompt)

        # Fall back to chat_completion if Responses API unavailable
        if not research_data:
            logger.info("Responses API unavailable, using standard chat_completion")
            research_data = await self._try_chat_completion(prompt, uploaded_docs)

        # Ensure metadata is populated
        research_data.setdefault("company_name", company_name)
        research_data.setdefault("generated_at", datetime.utcnow().isoformat())

        # Track data sources
        data_sources = research_data.get("data_sources", [])
        if uploaded_docs:
            if not any("Uploaded" in s for s in data_sources):
                data_sources.append(f"Uploaded Documents ({len(uploaded_docs)})")
        research_data["data_sources"] = data_sources

        return research_data

    def _build_research_prompt(
        self,
        company_name: str,
        uploaded_docs: Optional[List[str]] = None,
    ) -> str:
        """Build the structured research prompt.

        Args:
            company_name: Company to research
            uploaded_docs: Optional uploaded document texts

        Returns:
            Formatted prompt string
        """
        parts: list[str] = []

        # Prepend uploaded document context when available
        if uploaded_docs:
            parts.append(
                "The following documents have been uploaded for this client. "
                "Use them as PRIMARY sources — extract concrete financials, "
                "ratings, and facts before supplementing with web search.\n"
            )
            for i, doc_text in enumerate(uploaded_docs, 1):
                # Limit each doc to 12 000 chars to stay within context
                truncated = doc_text[:12_000]
                parts.append(f"--- Document {i} ---\n{truncated}\n--- End Document {i} ---\n")
            parts.append("")

        parts.append(f"""Research the company **{company_name}** and return a structured insurance brokerage client brief.

**Research Areas (all required):**
1. Business Overview — description, headquarters, founding year, employee count, ownership, key operations
2. Financial Summary — annual revenue, revenue trend, credit rating, highlights
3. Industry Risk Profile — NAICS code, sector, common perils, loss frequency, company-specific risk factors
4. Insurance Needs — estimated coverage lines with priority, premium range, and rationale
5. Carrier Appetite Matches — carriers suited for this risk with AM Best rating, appetite level, and rationale
6. Recent News — date, headline, source for each item

**CRITICAL — Return ONLY valid JSON matching this exact schema:**
{_RESEARCH_BRIEF_SCHEMA}

Rules:
- Every field is required; use empty string, null, or empty array if unknown.
- confidence_level must be "High", "Medium", or "Low".
- insurance_needs and carrier_matches must be arrays of objects with the exact keys shown.
- Do NOT wrap in markdown code fences.
- Do NOT include comments or trailing commas.
- Provide current, factual information with source citations.""")

        return "\n".join(parts)

    async def _try_responses_api(self, prompt: str) -> Dict[str, Any] | None:
        """Attempt to call Azure OpenAI Responses API with web search.

        Args:
            prompt: Research prompt

        Returns:
            Parsed research data dict or None if API unavailable
        """
        endpoint = os.environ.get("AZURE_RESPONSES_API_ENDPOINT", "").rstrip("/")
        if not endpoint:
            logger.debug("AZURE_RESPONSES_API_ENDPOINT not set, skipping Responses API")
            return None

        try:
            from azure.identity import DefaultAzureCredential

            credential = DefaultAzureCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
        except Exception as exc:
            logger.warning(f"Azure AD auth failed for Responses API: {exc}")
            return None

        url = f"{endpoint}/openai/responses"
        headers = {
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json",
        }
        body = {
            "model": _RESPONSES_API_MODEL,
            "tools": [{"type": "web_search_preview"}],
            "input": prompt,
        }

        try:
            # Run request in thread pool to avoid blocking
            def _make_request():
                resp = requests.post(
                    url,
                    params={"api-version": _RESPONSES_API_VERSION},
                    headers=headers,
                    json=body,
                    timeout=90,
                )
                resp.raise_for_status()
                return resp.json()

            result = await asyncio.to_thread(_make_request)

            # Extract text from Responses API output structure
            content = None
            for item in result.get("output", []):
                if item.get("type") == "message":
                    for content_item in item.get("content", []):
                        if content_item.get("type") == "output_text":
                            content = content_item.get("text", "")
                            break
                if content:
                    break

            if not content:
                logger.warning("No content extracted from Responses API response")
                return None

            logger.info(
                f"Responses API returned {len(content)} chars for client research"
            )

            # Parse JSON from response
            parsed = self._parse_json_response(content)
            if "_error" not in parsed:
                # Tag Bing as a data source
                sources = parsed.get("data_sources", [])
                if "Bing Web Search" not in sources:
                    sources.append("Bing Web Search")
                parsed["data_sources"] = sources
                return parsed

        except Exception as exc:
            logger.warning(f"Responses API call failed: {exc}")

        return None

    async def _try_chat_completion(
        self,
        prompt: str,
        uploaded_docs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Fall back to standard chat_completion (LLM knowledge only).

        Args:
            prompt: Research prompt
            uploaded_docs: Whether uploaded docs were included (for source tagging)

        Returns:
            Parsed research data dict
        """
        system_msg = (
            "You are an expert commercial insurance market researcher. "
            "Return ONLY valid JSON matching the requested schema. "
            "Do not include markdown code fences or commentary."
        )

        result = await asyncio.to_thread(
            chat_completion,
            self.settings,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4000,
        )

        raw_content = result.get("content", "")
        logger.info(
            f"chat_completion returned {len(raw_content)} chars for client research"
        )

        parsed = self._parse_json_response(raw_content)

        # Tag data sources
        if "_error" not in parsed:
            sources = parsed.get("data_sources", [])
            if "Bing Web Search" not in sources:
                sources.append("LLM Training Data (no live web search)")
            parsed["data_sources"] = sources

            if not parsed.get("citations"):
                parsed["citations"] = [
                    "Note: Research based on LLM training data, not live web search"
                ]

        return parsed

    def _parse_json_response(self, raw_content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling code fences, comments, and malformed JSON.

        Args:
            raw_content: Raw LLM response text

        Returns:
            Parsed JSON dict matching ResearchBrief schema (or error dict)
        """
        content_to_parse = raw_content.strip()

        # Strip markdown code fences
        content_to_parse = re.sub(r"^```(?:json)?\s*", "", content_to_parse)
        content_to_parse = re.sub(r"\s*```$", "", content_to_parse.strip())

        # Strip JS-style comments
        content_to_parse = re.sub(r"//[^\n]*", "", content_to_parse)

        # Sanitize control characters
        content_to_parse = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', ' ', content_to_parse)

        # Fix common LLM JSON issues: trailing commas before } or ]
        content_to_parse = re.sub(r',\s*([}\]])', r'\1', content_to_parse)

        # Extract JSON object if there's text before/after it
        json_match = re.search(r'\{.*\}', content_to_parse, re.DOTALL)
        if json_match:
            content_to_parse = json_match.group()

        # Try parsing with strict=False (allows control chars in strings)
        parsed = None
        for attempt in range(2):
            try:
                parsed = json.loads(content_to_parse, strict=False)
                break
            except json.JSONDecodeError as exc:
                if attempt == 0:
                    # Second attempt: truncate at error position and close JSON
                    logger.warning(f"JSON parse attempt 1 failed at pos {exc.pos}, trying repair")
                    truncated = content_to_parse[:exc.pos]
                    open_braces = truncated.count('{') - truncated.count('}')
                    open_brackets = truncated.count('[') - truncated.count(']')
                    truncated = truncated.rstrip().rstrip(',')
                    content_to_parse = truncated + ']' * open_brackets + '}' * open_braces
                else:
                    logger.error(f"Failed to parse research JSON after repair: {exc}")

        if parsed is None:
            return self._empty_brief_with_error(
                "Failed to parse JSON response", raw_content[:500]
            )

        # Normalize the parsed data to match ResearchBrief schema
        return self._normalize_brief(parsed)

    def _normalize_brief(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize parsed JSON to match ResearchBrief schema.

        Handles both the new structured schema and legacy free-text fields
        by mapping old field names to new ones where possible.
        """
        result: Dict[str, Any] = {}

        # Map legacy fields to new schema where applicable
        result["company_name"] = parsed.get("company_name", "")
        result["business_description"] = (
            parsed.get("business_description", "")
            or parsed.get("company_overview", "")
        )
        result["headquarters"] = parsed.get("headquarters", "")
        result["year_founded"] = parsed.get("year_founded")
        result["employee_count"] = parsed.get("employee_count")
        result["ownership_type"] = parsed.get("ownership_type", "")
        result["key_operations"] = parsed.get("key_operations", [])

        # Financial Summary
        result["annual_revenue"] = parsed.get("annual_revenue", "")
        result["revenue_trend"] = parsed.get("revenue_trend", "")
        result["credit_rating"] = parsed.get("credit_rating", "")
        result["financial_highlights"] = parsed.get("financial_highlights", [])

        # Industry Risk Profile
        result["naics_code"] = parsed.get("naics_code", "")
        result["industry_sector"] = parsed.get("industry_sector", "")
        result["common_perils"] = parsed.get("common_perils", [])
        result["loss_frequency"] = parsed.get("loss_frequency", "")
        result["risk_factors"] = parsed.get("risk_factors", [])

        # Insurance Needs — accept structured list or legacy string list
        raw_needs = parsed.get("insurance_needs", [])
        if raw_needs and isinstance(raw_needs[0], str):
            result["insurance_needs"] = [
                {"line": need, "priority": "", "estimated_premium": "", "rationale": ""}
                for need in raw_needs
            ]
        else:
            result["insurance_needs"] = raw_needs

        # Carrier Matches — accept structured list or legacy string list
        raw_carriers = parsed.get("carrier_matches", parsed.get("carrier_appetite_matches", []))
        if raw_carriers and isinstance(raw_carriers[0], str):
            result["carrier_matches"] = [
                {"carrier": c, "rating": "", "appetite": "", "rationale": ""}
                for c in raw_carriers
            ]
        else:
            result["carrier_matches"] = raw_carriers

        # Recent News & Citations
        result["recent_news"] = parsed.get("recent_news", [])
        result["citations"] = parsed.get("citations", [])
        result["confidence_level"] = parsed.get("confidence_level", "Medium")
        result["data_sources"] = parsed.get("data_sources", [])
        result["generated_at"] = parsed.get(
            "generated_at", datetime.utcnow().isoformat()
        )

        return result

    @staticmethod
    def _empty_brief_with_error(error: str, raw: str) -> Dict[str, Any]:
        """Return an empty ResearchBrief-shaped dict with error metadata."""
        return {
            "company_name": "",
            "business_description": "",
            "headquarters": "",
            "year_founded": None,
            "employee_count": None,
            "ownership_type": "",
            "key_operations": [],
            "annual_revenue": "",
            "revenue_trend": "",
            "credit_rating": "",
            "financial_highlights": [],
            "naics_code": "",
            "industry_sector": "",
            "common_perils": [],
            "loss_frequency": "",
            "risk_factors": [],
            "insurance_needs": [],
            "carrier_matches": [],
            "recent_news": [],
            "citations": [],
            "confidence_level": "Low",
            "data_sources": [],
            "generated_at": datetime.utcnow().isoformat(),
            "_error": error,
            "_raw": raw,
        }
