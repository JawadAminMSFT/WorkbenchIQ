"""
Tests for Phase 4: Document Processing & Extraction
Feature: 008-mortgage-underwriting

Tests cover:
- Document processing service
- Field extraction from Content Understanding results
- Result aggregation across multiple documents
- Provenance tracking for extracted fields
- JSON storage integration
"""
import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


class TestMortgageDocProcessor:
    """Tests for MortgageDocProcessor document processing."""

    @pytest.fixture
    def processor(self):
        """Return a MortgageDocProcessor instance."""
        from app.mortgage.processor import MortgageDocProcessor
        return MortgageDocProcessor()

    @pytest.fixture
    def sample_cu_result(self):
        """Return sample Content Understanding extraction result."""
        return {
            "fields": {
                "BorrowerFullName": {"value": "Jane Smith", "confidence": 0.95},
                "GrossAnnualSalary": {"value": "125000", "confidence": 0.92},
                "EmployerName": {"value": "TechCorp Inc", "confidence": 0.88},
                "PositionTitle": {"value": "Senior Developer", "confidence": 0.90},
            },
            "pages": [{"pageNumber": 1}]
        }

    def test_process_document_returns_extraction(self, processor, sample_cu_result):
        """process_document should return extraction results."""
        with patch.object(processor, "_call_content_understanding", return_value=sample_cu_result):
            doc_info = {"file_path": "test.pdf", "doc_type": "t4"}
            result = processor.process_document(doc_info, MagicMock())
            
            assert result is not None
            assert "fields" in result or hasattr(result, "fields")

    def test_process_package_processes_all_documents(self, processor):
        """process_package should process all documents in package."""
        documents = [
            {"file_path": "t4.pdf", "doc_type": "t4"},
            {"file_path": "paystub.pdf", "doc_type": "pay_stub"},
            {"file_path": "employment.pdf", "doc_type": "employment_letter"},
        ]
        
        with patch.object(processor, "process_document", return_value={"fields": {}}):
            results = processor.process_package(documents, MagicMock())
            
            assert len(results) == 3


class TestFieldExtractors:
    """Tests for field extraction from CU results."""

    @pytest.fixture
    def sample_cu_result(self):
        """Return comprehensive CU result for testing."""
        return {
            "fields": {
                "BorrowerFullName": {"value": "Jane Smith", "confidence": 0.95},
                "BorrowerDateOfBirth": {"value": "1988-03-15", "confidence": 0.90},
                "GrossAnnualSalary": {"value": "$125,000.00", "confidence": 0.92},
                "GrossPayPeriodAmount": {"value": "$4,807.69", "confidence": 0.88},
                "PayPeriodFrequency": {"value": "Bi-weekly", "confidence": 0.85},
                "EmployerName": {"value": "TechCorp Inc", "confidence": 0.90},
                "EmploymentStartDate": {"value": "2020-06-01", "confidence": 0.87},
                "PropertyAddress": {"value": "123 Maple St, Toronto ON M5V 1A1", "confidence": 0.93},
                "PurchasePrice": {"value": "$650,000", "confidence": 0.95},
            }
        }

    def test_extract_borrower_fields(self, sample_cu_result):
        """Should extract borrower identity fields."""
        from app.mortgage.extractors.borrower_extractor import extract_borrower_fields
        
        result = extract_borrower_fields(sample_cu_result)
        
        assert result["fullName"] == "Jane Smith"
        assert result["dateOfBirth"] == "1988-03-15"

    def test_extract_income_fields_with_annualization(self, sample_cu_result):
        """Should extract income fields and annualize if needed."""
        from app.mortgage.extractors.income_extractor import extract_income_fields
        
        result = extract_income_fields(sample_cu_result)
        
        # Should parse currency and extract numeric value
        assert result["grossAnnualSalary"] == 125000 or result["grossAnnualSalary"] == 125000.0
        
        # Should annualize bi-weekly if annual not provided
        # Bi-weekly: $4,807.69 * 26 = $124,999.94 ≈ $125,000
        if "annualizedIncome" in result:
            assert abs(result["annualizedIncome"] - 125000) < 100

    def test_extract_property_fields(self, sample_cu_result):
        """Should extract property fields."""
        from app.mortgage.extractors.property_extractor import extract_property_fields
        
        result = extract_property_fields(sample_cu_result)
        
        assert "address" in result
        assert result["purchasePrice"] == 650000 or result["purchasePrice"] == 650000.0

    def test_extract_loan_fields(self):
        """Should extract loan fields."""
        from app.mortgage.extractors.loan_extractor import extract_loan_fields
        
        cu_result = {
            "fields": {
                "RequestedLoanAmount": {"value": "$520,000", "confidence": 0.95},
                "RequestedAmortization": {"value": "25 years", "confidence": 0.90},
                "InterestRate": {"value": "5.25%", "confidence": 0.92},
            }
        }
        
        result = extract_loan_fields(cu_result)
        
        assert result["loanAmount"] == 520000
        assert result["amortizationYears"] == 25
        assert result["interestRate"] == 5.25

    def test_extract_credit_fields(self):
        """Should extract credit fields with normalization."""
        from app.mortgage.extractors.credit_extractor import extract_credit_fields
        
        cu_result = {
            "fields": {
                "CreditScore": {"value": 742, "confidence": 0.95},
                "CreditBureau": {"value": "Equifax", "confidence": 0.90},
            }
        }
        
        result = extract_credit_fields(cu_result)
        
        assert result["bureauScore"] == 742
        assert result["bureauAgency"].lower() == "equifax"


class TestMortgageCaseAggregator:
    """Tests for aggregating data across multiple documents."""

    @pytest.fixture
    def aggregator(self):
        """Return a MortgageCaseAggregator instance."""
        from app.mortgage.aggregator import MortgageCaseAggregator
        return MortgageCaseAggregator()

    def test_aggregate_borrower_data_merges_sources(self, aggregator):
        """Should merge borrower data from multiple documents."""
        docs = [
            {"doc_type": "application_summary", "borrower": {"fullName": "Jane Smith"}},
            {"doc_type": "t4", "borrower": {"sin": "***-***-789"}},
        ]
        
        result = aggregator.aggregate_borrower_data(docs)
        
        assert result["fullName"] == "Jane Smith"
        assert result["sin"] == "***-***-789"

    def test_aggregate_income_data_combines_sources(self, aggregator):
        """Should combine income from multiple sources."""
        docs = [
            {"doc_type": "t4", "income": {"type": "salary", "amount": 125000}},
            {"doc_type": "pay_stub", "income": {"type": "salary", "amount": 124500}},
        ]
        
        result = aggregator.aggregate_income_data(docs)
        
        # Should combine or reconcile the amounts
        assert len(result) >= 1

    def test_detect_inconsistencies_flags_variances(self, aggregator):
        """Should flag inconsistencies when variance exceeds threshold."""
        case_data = {
            "income_from_t4": 125000,
            "income_from_paystub": 110000,  # 12% variance - exceeds 5% threshold
        }
        
        inconsistencies = aggregator.detect_inconsistencies(case_data)
        
        assert len(inconsistencies) > 0
        assert any("income" in str(i).lower() for i in inconsistencies)

    def test_build_canonical_case_creates_unified_model(self, aggregator):
        """Should build canonical case model per schema."""
        docs = [
            {"doc_type": "t4", "fields": {"GrossAnnualSalary": 125000}},
            {"doc_type": "appraisal_report", "fields": {"AppraisedValue": 650000}},
        ]
        
        case = aggregator.build_canonical_case(docs)
        
        # Should have required structure
        assert "borrowers" in case or "application" in case or "property" in case


class TestProvenanceTracker:
    """Tests for field provenance tracking."""

    @pytest.fixture
    def tracker(self):
        """Return a ProvenanceTracker instance."""
        from app.mortgage.provenance import ProvenanceTracker
        return ProvenanceTracker()

    def test_track_field_stores_attribution(self, tracker):
        """track_field should store field attribution."""
        tracker.track_field(
            field_name="grossAnnualSalary",
            value=125000,
            doc_id="t4_B1",
            page=1,
            region={"x": 100, "y": 200, "width": 100, "height": 20}
        )
        
        sources = tracker.get_field_sources("grossAnnualSalary")
        
        assert len(sources) == 1
        assert sources[0]["doc_id"] == "t4_B1"
        assert sources[0]["value"] == 125000

    def test_track_field_multiple_sources(self, tracker):
        """Should track multiple sources for same field."""
        tracker.track_field("grossAnnualSalary", 125000, "t4_B1", 1, {})
        tracker.track_field("grossAnnualSalary", 124500, "paystub_B1", 1, {})
        
        sources = tracker.get_field_sources("grossAnnualSalary")
        
        assert len(sources) == 2

    def test_resolve_conflict_records_resolution(self, tracker):
        """resolve_conflict should record conflict resolution."""
        tracker.track_field("grossAnnualSalary", 125000, "t4_B1", 1, {})
        tracker.track_field("grossAnnualSalary", 110000, "paystub_B1", 1, {})
        
        tracker.resolve_conflict(
            field_name="grossAnnualSalary",
            winner_doc_id="t4_B1",
            note="T4 is authoritative tax document"
        )
        
        resolution = tracker.get_resolution("grossAnnualSalary")
        assert resolution["winner_doc_id"] == "t4_B1"


class TestMortgageJSONStorage:
    """Tests for JSON storage integration."""

    @pytest.fixture
    def storage(self):
        """Return mortgage storage instance."""
        from app.mortgage.storage import MortgageStorage
        return MortgageStorage()

    def test_save_mortgage_case_creates_metadata_json(self, storage, tmp_path):
        """save_mortgage_case should create metadata.json."""
        case_id = "mtg-test-001"
        case_data = {
            "caseId": case_id,
            "status": "intake",
            "application": {"purpose": "purchase"},
        }
        
        with patch("app.mortgage.storage.DATA_PATH", tmp_path):
            storage.save_mortgage_case(case_id, case_data)
            
            metadata_path = tmp_path / "applications" / case_id / "metadata.json"
            assert metadata_path.exists()
            
            saved = json.loads(metadata_path.read_text())
            assert saved["mortgage_case"]["caseId"] == case_id

    def test_save_content_understanding_creates_file(self, storage, tmp_path):
        """save_content_understanding should create content_understanding.json."""
        case_id = "mtg-test-001"
        extraction_result = {"documents": [{"fields": {}}]}
        
        with patch("app.mortgage.storage.DATA_PATH", tmp_path):
            # Ensure case directory exists
            (tmp_path / "applications" / case_id).mkdir(parents=True)
            
            storage.save_content_understanding(case_id, extraction_result)
            
            cu_path = tmp_path / "applications" / case_id / "content_understanding.json"
            assert cu_path.exists()

    def test_get_mortgage_case_loads_from_json(self, storage, tmp_path):
        """get_mortgage_case should load case from JSON."""
        case_id = "mtg-test-001"
        case_data = {"mortgage_case": {"caseId": case_id, "status": "in_review"}}
        
        # Create test file
        case_dir = tmp_path / "applications" / case_id
        case_dir.mkdir(parents=True)
        (case_dir / "metadata.json").write_text(json.dumps(case_data))
        
        with patch("app.mortgage.storage.DATA_PATH", tmp_path):
            loaded = storage.get_mortgage_case(case_id)
            
            assert loaded["mortgage_case"]["caseId"] == case_id
            assert loaded["mortgage_case"]["status"] == "in_review"

    def test_update_mortgage_case_merges_updates(self, storage, tmp_path):
        """update_mortgage_case should merge updates into existing case."""
        case_id = "mtg-test-001"
        initial = {"mortgage_case": {"caseId": case_id, "status": "intake"}}
        
        case_dir = tmp_path / "applications" / case_id
        case_dir.mkdir(parents=True)
        (case_dir / "metadata.json").write_text(json.dumps(initial))
        
        with patch("app.mortgage.storage.DATA_PATH", tmp_path):
            storage.update_mortgage_case(case_id, {"status": "in_review"})
            
            loaded = storage.get_mortgage_case(case_id)
            assert loaded["mortgage_case"]["status"] == "in_review"
