"""
Client Research Engine Module

Generates AI-powered client research briefs using Bing Grounding.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any, Dict

import requests

from app.config import OpenAISettings
from app.openai_client import chat_completion
from app.utils import setup_logging

logger = setup_logging()

# Responses API configuration
_RESPONSES_API_VERSION = "2025-04-01-preview"
_RESPONSES_API_MODEL = "gpt-4.1"


class ClientResearchEngine:
    """Generates AI-powered client research briefs with web grounding."""

    def __init__(self, settings: OpenAISettings):
        """Initialize ClientResearchEngine with OpenAI settings.

        Args:
            settings: OpenAI configuration settings
        """
        self.settings = settings

    async def research_client(self, company_name: str) -> Dict[str, Any]:
        """Generate an AI-powered client research brief.

        Attempts to use Azure OpenAI Responses API with web_search_preview tool
        for grounded research. Falls back to standard chat_completion if
        Responses API is unavailable.

        Args:
            company_name: Name of the company to research

        Returns:
            Dict with research brief containing:
            - company_overview: str
            - financials_summary: str
            - industry_risk_profile: str
            - insurance_needs: List[str]
            - carrier_appetite_matches: List[str]
            - recent_news: List[Dict]
            - citations: List[str]
        """
        logger.info(f"Starting client research for: {company_name}")

        # Build research prompt
        prompt = self._build_research_prompt(company_name)

        # Try Responses API first (with Bing grounding)
        research_data = await self._try_responses_api(prompt)

        # Fall back to chat_completion if Responses API unavailable
        if not research_data:
            logger.info("Responses API unavailable, using standard chat_completion")
            research_data = await self._try_chat_completion(prompt)

        # Parse and structure the response
        return research_data

    def _build_research_prompt(self, company_name: str) -> str:
        """Build the research prompt for the company.

        Args:
            company_name: Company to research

        Returns:
            Formatted prompt string
        """
        return f"""Research the following company and provide a comprehensive insurance brokerage client brief.

**Company:** {company_name}

**Research Areas:**
1. **Company Overview**: Business description, location, size, key operations
2. **Financial Summary**: Revenue, growth trends, financial stability indicators
3. **Industry Risk Profile**: Industry sector, common risks, loss trends
4. **Insurance Needs**: Likely coverage needs based on operations (property, liability, D&O, etc.)
5. **Carrier Appetite Matches**: Types of carriers that typically write this risk class
6. **Recent News**: Any recent developments, expansions, incidents, or leadership changes

**Response Format:**
Return ONLY valid JSON with the following structure:
{{
  "company_overview": "Detailed company description...",
  "financials_summary": "Revenue, growth, financial strength...",
  "industry_risk_profile": "Industry sector, common risks, loss frequency...",
  "insurance_needs": [
    "Commercial Property - $X valuation",
    "General Liability - operations exposure",
    "D&O - public company governance",
    "..."
  ],
  "carrier_appetite_matches": [
    "Admitted carriers: XYZ Corp (large property risks)",
    "E&S carriers: ABC Specialty (high-hazard operations)",
    "..."
  ],
  "recent_news": [
    {{"date": "2024-12-15", "headline": "Company expands...", "source": "Source Name"}},
    {{"date": "2024-11-20", "headline": "New facility opened...", "source": "Source Name"}}
  ],
  "citations": [
    "https://source1.com/article",
    "https://source2.com/report"
  ]
}}

Provide current, factual information with sources. Return ONLY the JSON, no markdown or additional text."""

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
                return parsed

        except Exception as exc:
            logger.warning(f"Responses API call failed: {exc}")

        return None

    async def _try_chat_completion(self, prompt: str) -> Dict[str, Any]:
        """Fall back to standard chat_completion (LLM knowledge only).

        Args:
            prompt: Research prompt

        Returns:
            Parsed research data dict
        """
        result = await asyncio.to_thread(
            chat_completion,
            self.settings,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert commercial insurance market researcher. Provide comprehensive company intelligence for insurance brokerage placement.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=3000,
        )

        raw_content = result.get("content", "")
        logger.info(
            f"chat_completion returned {len(raw_content)} chars for client research"
        )

        # Parse JSON from response
        parsed = self._parse_json_response(raw_content)
        
        # Add disclaimer if using LLM knowledge only
        if "_error" not in parsed:
            if "citations" not in parsed or not parsed["citations"]:
                parsed["citations"] = ["Note: Research based on LLM training data, not live web search"]

        return parsed

    def _parse_json_response(self, raw_content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling code fences and comments.

        Args:
            raw_content: Raw LLM response text

        Returns:
            Parsed JSON dict (or error dict if parsing fails)
        """
        content_to_parse = raw_content.strip()

        # Strip markdown code fences
        content_to_parse = re.sub(r"^```(?:json)?\s*", "", content_to_parse)
        content_to_parse = re.sub(r"\s*```$", "", content_to_parse.strip())

        # Strip JS-style comments
        content_to_parse = re.sub(r"//[^\n]*", "", content_to_parse)

        try:
            parsed = json.loads(content_to_parse)
            
            # Validate required fields
            required_fields = [
                "company_overview",
                "financials_summary",
                "industry_risk_profile",
                "insurance_needs",
                "carrier_appetite_matches",
            ]
            
            for field in required_fields:
                if field not in parsed:
                    logger.warning(f"Missing required field in research response: {field}")
                    parsed[field] = "" if field in ["company_overview", "financials_summary", "industry_risk_profile"] else []
            
            # Ensure optional fields have defaults
            parsed.setdefault("recent_news", [])
            parsed.setdefault("citations", [])
            
            return parsed

        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse research JSON: {exc}")
            return {
                "company_overview": "",
                "financials_summary": "",
                "industry_risk_profile": "",
                "insurance_needs": [],
                "carrier_appetite_matches": [],
                "recent_news": [],
                "citations": [],
                "_error": f"Failed to parse JSON response: {str(exc)}",
                "_raw": raw_content[:500],
            }
