"""
Submission Package Generator

Generates submission packages from ACORD fields, client data, and
attached documents.  Includes LLM-powered cover email generation
and per-carrier email compilation.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.broker.acord_forms import (
    ACORD_125_FIELDS,
    ACORD_140_FIELDS,
    SOV_FIELDS,
    get_acord_form_template,
)
from app.config import OpenAISettings
from app.openai_client import chat_completion
from app.utils import setup_logging

logger = setup_logging()


class SubmissionPackageGenerator:
    """Generates submission packages from ACORD fields and documents."""

    def __init__(self, settings: OpenAISettings) -> None:
        self.settings = settings

    # ------------------------------------------------------------------
    # Cover email generation
    # ------------------------------------------------------------------

    async def generate_cover_email(
        self,
        client: Dict[str, Any],
        submission: Dict[str, Any],
        carriers: List[str],
    ) -> str:
        """Generate a professional submission cover email via LLM.

        Args:
            client: Client record dict.
            submission: Submission record dict.
            carriers: List of carrier names the submission targets.

        Returns:
            Draft email body as a string.
        """
        client_name = client.get("name", "the client")
        effective_date = submission.get("effective_date", "TBD")
        tiv = submission.get("total_insured_value", "TBD")
        lob = submission.get("line_of_business", "Commercial Property")
        acord_125 = submission.get("acord_125_fields", {})
        acord_140 = submission.get("acord_140_fields", {})

        # Build a document list for the email
        doc_names = [
            d.get("file_name", "Unknown")
            for d in submission.get("documents", [])
        ]
        doc_list = "\n".join(f"  - {n}" for n in doc_names) if doc_names else "  (No documents attached)"

        # Build location summary from ACORD 140
        locations = acord_140.get("property_locations", [])
        num_locations = len(locations) if isinstance(locations, list) else 0

        carrier_list = ", ".join(carriers) if carriers else "carriers"

        prompt = f"""Write a professional commercial insurance submission cover email.

**Context:**
- Client: {client_name}
- Line of Business: {lob}
- Effective Date: {effective_date}
- Total Insured Value: {tiv}
- Number of Property Locations: {num_locations}
- Target Carriers: {carrier_list}
- Attached Documents:
{doc_list}

**Requirements:**
- Address it generically (not to a specific carrier — the broker will customize per carrier)
- Include: client name, coverage type requested, effective date, TIV, and attached documents list
- Professional, concise tone appropriate for carrier underwriters
- Include a brief risk summary if ACORD data is available
- Close with a request for a competitive quote and timeline
- Do NOT include subject line — just the email body
- Keep it under 300 words

Return ONLY the email body text, no markdown formatting."""

        try:
            result = await asyncio.to_thread(
                chat_completion,
                self.settings,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an experienced commercial insurance broker drafting "
                            "submission emails to carrier underwriters."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=2000,
            )
            return result.get("content", "").strip()
        except Exception as exc:
            logger.error("LLM cover email generation failed: %s", exc, exc_info=True)
            # Fallback to a simple template
            return self._fallback_cover_email(client_name, lob, effective_date, tiv, doc_list)

    # ------------------------------------------------------------------
    # Package compilation
    # ------------------------------------------------------------------

    def compile_package(
        self,
        client: Dict[str, Any],
        submission: Dict[str, Any],
        cover_email: str = "",
    ) -> Dict[str, Any]:
        """Compile the full submission package.

        Args:
            client: Client record dict.
            submission: Submission record dict.
            cover_email: Pre-generated cover email text.

        Returns:
            Package dict with cover_email, acord_125, acord_140, sov,
            documents, and carriers.
        """
        acord_125 = submission.get("acord_125_fields", {})
        acord_140 = submission.get("acord_140_fields", {})
        confidence = submission.get("acord_field_confidence", {})

        # Build SOV from ACORD 140 property_locations
        sov_locations = self._build_sov(acord_140)

        documents = [
            {
                "id": d.get("id", ""),
                "document_type": d.get("document_type", ""),
                "file_name": d.get("file_name", ""),
                "uploaded_at": d.get("uploaded_at", ""),
            }
            for d in submission.get("documents", [])
        ]

        return {
            "submission_id": submission.get("id", ""),
            "generated_at": datetime.utcnow().isoformat(),
            "cover_email": cover_email,
            "acord_125": acord_125,
            "acord_140": acord_140,
            "sov": sov_locations,
            "confidence": confidence,
            "documents": documents,
            "carriers": submission.get("submitted_carriers", []),
            "client": {
                "id": client.get("id", ""),
                "name": client.get("name", ""),
                "headquarters_address": client.get("headquarters_address", ""),
            },
            "submission_details": {
                "line_of_business": submission.get("line_of_business", ""),
                "effective_date": submission.get("effective_date"),
                "expiration_date": submission.get("expiration_date"),
                "total_insured_value": submission.get("total_insured_value", ""),
            },
        }

    # ------------------------------------------------------------------
    # Per-carrier email generation
    # ------------------------------------------------------------------

    async def generate_carrier_emails(
        self,
        package: Dict[str, Any],
        carriers: List[str],
    ) -> List[Dict[str, Any]]:
        """Generate individual carrier submission emails.

        Args:
            package: Compiled package from :meth:`compile_package`.
            carriers: List of carrier names.

        Returns:
            List of dicts, each with carrier, email_subject, email_body,
            and attachments.
        """
        client_name = package.get("client", {}).get("name", "the client")
        effective_date = package.get("submission_details", {}).get("effective_date", "TBD")
        lob = package.get("submission_details", {}).get("line_of_business", "Commercial Property")
        base_email = package.get("cover_email", "")
        doc_names = [d.get("file_name", "") for d in package.get("documents", [])]

        emails: List[Dict[str, Any]] = []
        for carrier in carriers:
            subject = (
                f"New Submission — {client_name} — "
                f"{lob.replace('_', ' ').title()} — Eff. {effective_date}"
            )
            # Personalise the base email for this carrier
            body = base_email.replace("Dear Underwriter", f"Dear {carrier} Underwriting Team")
            if "Dear " not in body:
                body = f"Dear {carrier} Underwriting Team,\n\n{body}"

            emails.append({
                "carrier": carrier,
                "email_subject": subject,
                "email_body": body,
                "attachments": doc_names,
            })

        return emails

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_sov(self, acord_140: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build an SOV locations list from ACORD 140 property_locations."""
        locations = acord_140.get("property_locations", [])
        if not isinstance(locations, list):
            return []

        sov: List[Dict[str, Any]] = []
        for idx, loc in enumerate(locations, start=1):
            building = loc.get("building_value", "$0")
            contents = loc.get("contents_value", "$0")
            bi = loc.get("bi_value", "$0")

            # Compute TIV as sum of building + contents + BI
            tiv = self._sum_dollar_values(building, contents, bi)

            sov.append({
                "SiteNumber": str(idx),
                "Address": loc.get("address", ""),
                "BuildingDescription": loc.get("occupancy", ""),
                "TotalInsuredValue": tiv,
                "BuildingValue": building,
                "ContentsValue": contents,
                "BIValue": bi,
            })
        return sov

    @staticmethod
    def _sum_dollar_values(*values: str) -> str:
        """Sum dollar-formatted strings and return as formatted dollar string."""
        total = 0.0
        for v in values:
            try:
                total += float(str(v).replace("$", "").replace(",", ""))
            except (ValueError, TypeError):
                pass
        return f"${total:,.0f}"

    @staticmethod
    def _fallback_cover_email(
        client_name: str,
        lob: str,
        effective_date: str,
        tiv: str,
        doc_list: str,
    ) -> str:
        """Simple fallback email when LLM is unavailable."""
        return f"""Dear Underwriter,

We are pleased to submit the following new business application for your review and competitive quotation.

Client: {client_name}
Line of Business: {lob.replace('_', ' ').title()}
Requested Effective Date: {effective_date}
Total Insured Value: {tiv}

Please find the following documents attached:
{doc_list}

We would appreciate your most competitive terms at your earliest convenience. Please do not hesitate to reach out with any questions or if additional information is needed.

Best regards,
Commercial Brokerage Team"""
