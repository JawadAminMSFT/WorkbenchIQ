"""
Document router for Commercial Brokerage.

Routes classified documents to the appropriate Azure Content Understanding analyzer
based on document type (quote, ACORD/submission, or research).
"""

import os
import re
from typing import Tuple

from app.config import BrokerSettings


class BrokerDocRouter:
    """
    Routes broker documents to the appropriate CU analyzer based on document type.

    Analyzer mapping:
    - Quote analyzer: carrier quote documents
    - ACORD analyzer: SOV, loss runs, prior declarations, ACORD 125/140
    - Research analyzer: AM Best, annual reports, financial statements, S&P reports
    """

    QUOTE_TYPES = {"carrier_quote"}
    ACORD_TYPES = {"sov", "loss_runs", "prior_declaration", "acord_125", "acord_140"}
    RESEARCH_TYPES = {"am_best", "annual_report", "financial_statement", "sp_report"}

    SUPPORTED_EXTENSIONS = {
        ".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif",
        ".docx", ".doc", ".txt", ".xlsx", ".xls",
    }

    # Filename patterns for auto-detection
    _FILENAME_PATTERNS = [
        (re.compile(r"quote|proposal|indication|premium", re.IGNORECASE), "carrier_quote"),
        (re.compile(r"sov|schedule.of.value", re.IGNORECASE), "sov"),
        (re.compile(r"loss.run|loss.history|claims.history", re.IGNORECASE), "loss_runs"),
        (re.compile(r"prior.dec|expiring.dec|declaration", re.IGNORECASE), "prior_declaration"),
        (re.compile(r"acord.?125", re.IGNORECASE), "acord_125"),
        (re.compile(r"acord.?140", re.IGNORECASE), "acord_140"),
        (re.compile(r"am.?best|best.?credit|best.?rating|amb.?credit", re.IGNORECASE), "am_best"),
        (re.compile(r"md.?&?.?a\b|management.*discussion", re.IGNORECASE), "annual_report"),
        (re.compile(r"annual.report", re.IGNORECASE), "annual_report"),
        (re.compile(r"financial.statement|10-K|10K", re.IGNORECASE), "financial_statement"),
        (re.compile(r"s&p|s.p.report|standard.*poor", re.IGNORECASE), "sp_report"),
    ]

    def route_document(
        self,
        file_name: str,
        document_type: str,
    ) -> Tuple[str, str]:
        """
        Route a document to the appropriate analyzer.

        Args:
            file_name: Original filename
            document_type: Document type label (or "other" for auto-detection)

        Returns:
            Tuple of (doc_category, analyzer_id_key) where analyzer_id_key is
            one of "quote", "acord", or "research".
        """
        if document_type == "other" or not document_type:
            document_type = self._detect_type_from_filename(file_name)

        doc_category = self.get_document_category(document_type)
        analyzer_key = self._category_to_analyzer_key(doc_category)
        return (doc_category, analyzer_key)

    def get_analyzer_id(
        self,
        document_type: str,
        settings: BrokerSettings,
    ) -> str:
        """
        Get the concrete analyzer ID for a given document type.

        Args:
            document_type: Document type label
            settings: Broker settings with analyzer IDs

        Returns:
            Azure Content Understanding analyzer ID
        """
        if document_type in self.QUOTE_TYPES:
            return settings.quote_analyzer
        if document_type in self.RESEARCH_TYPES:
            return settings.research_analyzer
        # ACORD types and anything else default to the ACORD analyzer
        return settings.acord_analyzer

    def get_document_category(self, document_type: str) -> str:
        """
        Get the high-level category for a document type.

        Returns:
            "quote", "acord", "research", or "other"
        """
        if document_type in self.QUOTE_TYPES:
            return "quote"
        if document_type in self.ACORD_TYPES:
            return "acord"
        if document_type in self.RESEARCH_TYPES:
            return "research"
        return "other"

    def validate_file_type(self, filename: str) -> bool:
        """Check whether the file extension is supported."""
        ext = os.path.splitext(filename.lower())[1]
        return ext in self.SUPPORTED_EXTENSIONS

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_type_from_filename(self, filename: str) -> str:
        """Attempt to infer document type from the filename."""
        for pattern, doc_type in self._FILENAME_PATTERNS:
            if pattern.search(filename):
                return doc_type
        return "other"

    @staticmethod
    def _category_to_analyzer_key(category: str) -> str:
        """Map a category to an analyzer settings key."""
        if category == "quote":
            return "quote"
        if category == "research":
            return "research"
        return "acord"
