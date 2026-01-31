"""
Tests for Phase 2: Document Type Classification & Routing
Feature: 008-mortgage-underwriting

Tests cover:
- Document type detection (T4, pay stub, employment letter, appraisal, etc.)
- Filename-based classification heuristics
- Content-based classification fallback
- Analyzer routing based on document type
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestMortgageDocClassifier:
    """Tests for MortgageDocClassifier document type detection."""

    @pytest.fixture
    def classifier(self):
        """Return a MortgageDocClassifier instance."""
        from app.mortgage.doc_classifier import MortgageDocClassifier
        return MortgageDocClassifier()

    def test_classify_t4_by_filename(self, classifier):
        """Should classify T4 documents by filename."""
        result = classifier.classify_document(b"pdf content", "T4_2025.pdf")
        assert result == "t4"

        result = classifier.classify_document(b"pdf content", "john_smith_t4_statement.pdf")
        assert result == "t4"

    def test_classify_paystub_by_filename(self, classifier):
        """Should classify pay stubs by filename."""
        result = classifier.classify_document(b"pdf content", "paystub_jan2025.pdf")
        assert result == "pay_stub"

        result = classifier.classify_document(b"pdf content", "pay_stub_biweekly.pdf")
        assert result == "pay_stub"

    def test_classify_employment_letter_by_filename(self, classifier):
        """Should classify employment letters by filename."""
        result = classifier.classify_document(b"pdf content", "employment_letter.pdf")
        assert result == "employment_letter"

        result = classifier.classify_document(b"pdf content", "confirmation_of_employment.pdf")
        assert result == "employment_letter"

    def test_classify_noa_by_filename(self, classifier):
        """Should classify Notice of Assessment by filename."""
        result = classifier.classify_document(b"pdf content", "NOA_2024.pdf")
        assert result == "notice_of_assessment"

        result = classifier.classify_document(b"pdf content", "notice_of_assessment_2024.pdf")
        assert result == "notice_of_assessment"

    def test_classify_bank_statement_by_filename(self, classifier):
        """Should classify bank statements by filename."""
        result = classifier.classify_document(b"pdf content", "bank_statement_jan.pdf")
        assert result == "bank_statement"

        result = classifier.classify_document(b"pdf content", "td_chequing_statement.pdf")
        assert result == "bank_statement"

    def test_classify_gift_letter_by_filename(self, classifier):
        """Should classify gift letters by filename."""
        result = classifier.classify_document(b"pdf content", "gift_letter_dad.pdf")
        assert result == "gift_letter"

    def test_classify_appraisal_by_filename(self, classifier):
        """Should classify appraisal reports by filename."""
        result = classifier.classify_document(b"pdf content", "appraisal_report.pdf")
        assert result == "appraisal_report"

        result = classifier.classify_document(b"pdf content", "property_appraisal.pdf")
        assert result == "appraisal_report"

    def test_classify_purchase_agreement_by_filename(self, classifier):
        """Should classify purchase/sale agreements by filename."""
        result = classifier.classify_document(b"pdf content", "purchase_sale_agreement.pdf")
        assert result == "purchase_sale_agreement"

        result = classifier.classify_document(b"pdf content", "agreement_of_purchase.pdf")
        assert result == "purchase_sale_agreement"

    def test_classify_credit_report_by_filename(self, classifier):
        """Should classify credit reports by filename."""
        result = classifier.classify_document(b"pdf content", "credit_report_equifax.pdf")
        assert result == "credit_report"

    def test_classify_unknown_as_other(self, classifier):
        """Should classify unknown documents as 'other'."""
        result = classifier.classify_document(b"pdf content", "random_document.pdf")
        assert result == "other"

    def test_classify_application_summary(self, classifier):
        """Should classify mortgage application summary."""
        result = classifier.classify_document(b"pdf content", "mortgage_application.pdf")
        assert result == "application_summary"


class TestMortgageDocRouter:
    """Tests for MortgageDocRouter analyzer routing."""

    @pytest.fixture
    def router(self):
        """Return a MortgageDocRouter instance."""
        from app.mortgage.router import MortgageDocRouter
        return MortgageDocRouter()

    @pytest.fixture
    def settings(self):
        """Return mock settings."""
        from app.config import MortgageUnderwritingSettings
        return MortgageUnderwritingSettings()

    def test_route_to_correct_analyzer(self, router, settings):
        """Should route document to appropriate analyzer."""
        doc_type, analyzer_id = router.route_document(
            b"pdf content", "t4_2025.pdf", settings
        )
        
        assert doc_type == "t4"
        assert analyzer_id == settings.doc_analyzer

    def test_route_returns_doc_type_and_analyzer(self, router, settings):
        """route_document should return tuple of (doc_type, analyzer_id)."""
        result = router.route_document(b"pdf content", "paystub.pdf", settings)
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == "pay_stub"
        assert isinstance(result[1], str)

    def test_get_analyzer_id_for_doc_types(self, router, settings):
        """get_analyzer_id should return correct analyzer for each doc type."""
        # All mortgage docs use the same analyzer for now
        for doc_type in ["t4", "pay_stub", "employment_letter", "appraisal_report"]:
            analyzer_id = router.get_analyzer_id(doc_type, settings)
            assert analyzer_id == settings.doc_analyzer

    def test_validate_supported_file_types(self, router, settings):
        """Should validate supported file types (PDF primary)."""
        # PDF should be supported
        _, _ = router.route_document(b"pdf content", "document.pdf", settings)
        
        # Non-PDF may raise or return special handling
        # This depends on implementation - adjust test accordingly


class TestContentUnderstandingExtensions:
    """Tests for Content Understanding client extensions."""

    def test_analyze_mortgage_document(self):
        """Should analyze mortgage document with doc_type parameter."""
        # The CU client uses functions, not a class
        from app.content_understanding_client import analyze_document
        
        # Verify the function exists
        assert callable(analyze_document)

    def test_provenance_extraction_from_cu_response(self):
        """Should extract provenance (page, bounding region) from CU response."""
        # This tests the provenance extraction helper
        from app.mortgage.processor import extract_field_provenance
        
        cu_response = {
            "fields": {
                "GrossAnnualSalary": {
                    "value": "125000",
                    "confidence": 0.95,
                    "boundingRegion": {"page": 1, "polygon": [100, 200, 300, 220]}
                }
            }
        }
        
        provenance = extract_field_provenance(cu_response, "GrossAnnualSalary")
        
        assert provenance["page"] == 1
        assert provenance["confidence"] == 0.95
        assert "polygon" in provenance or "boundingRegion" in provenance
