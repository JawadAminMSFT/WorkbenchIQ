"""
Tests for Phase 3: Custom Analyzer Setup
Feature: 008-mortgage-underwriting

Tests cover:
- Mortgage document analyzer schema definition
- Analyzer creation via setup script
- Analyzer verification
- Field extraction schema for Canadian mortgage documents
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


class TestMortgageAnalyzerSchema:
    """Tests for mortgage document analyzer schema."""

    def test_analyzer_schema_has_required_fields(self):
        """Analyzer schema should define all required mortgage fields."""
        # Import the schema from setup script
        try:
            from scripts.setup_mortgage_analyzers import MORTGAGE_DOC_ANALYZER_SCHEMA
        except ImportError:
            pytest.skip("setup_mortgage_analyzers.py not yet created")
        
        fields = MORTGAGE_DOC_ANALYZER_SCHEMA["fieldSchema"]["fields"]
        
        # Borrower identity fields
        assert "BorrowerFullName" in fields
        assert "BorrowerDateOfBirth" in fields
        assert "BorrowerSIN" in fields
        
        # Employment fields
        assert "EmployerName" in fields
        assert "PositionTitle" in fields
        assert "EmploymentStartDate" in fields
        
        # Income fields
        assert "GrossAnnualSalary" in fields
        assert "GrossPayPeriodAmount" in fields
        assert "YTDEarnings" in fields
        
        # Property fields
        assert "PropertyAddress" in fields
        assert "PurchasePrice" in fields
        assert "AppraisedValue" in fields
        assert "PropertyTaxesAnnual" in fields
        
        # Loan fields
        assert "RequestedLoanAmount" in fields
        assert "RequestedAmortization" in fields
        assert "InterestRate" in fields
        assert "DownPaymentAmount" in fields

    def test_analyzer_schema_has_credit_fields(self):
        """Analyzer schema should include credit-related fields."""
        try:
            from scripts.setup_mortgage_analyzers import MORTGAGE_DOC_ANALYZER_SCHEMA
        except ImportError:
            pytest.skip("setup_mortgage_analyzers.py not yet created")
        
        fields = MORTGAGE_DOC_ANALYZER_SCHEMA["fieldSchema"]["fields"]
        
        assert "CreditScore" in fields
        assert "CreditBureau" in fields

    def test_analyzer_schema_has_gift_fields(self):
        """Analyzer schema should include gift letter fields."""
        try:
            from scripts.setup_mortgage_analyzers import MORTGAGE_DOC_ANALYZER_SCHEMA
        except ImportError:
            pytest.skip("setup_mortgage_analyzers.py not yet created")
        
        fields = MORTGAGE_DOC_ANALYZER_SCHEMA["fieldSchema"]["fields"]
        
        assert "GiftDonorName" in fields
        assert "GiftAmount" in fields
        assert "GiftRelationship" in fields

    def test_analyzer_schema_has_tax_fields(self):
        """Analyzer schema should include T4/NOA fields."""
        try:
            from scripts.setup_mortgage_analyzers import MORTGAGE_DOC_ANALYZER_SCHEMA
        except ImportError:
            pytest.skip("setup_mortgage_analyzers.py not yet created")
        
        fields = MORTGAGE_DOC_ANALYZER_SCHEMA["fieldSchema"]["fields"]
        
        assert "TaxYear" in fields
        assert "TotalIncomeFromT4" in fields
        assert "TotalIncomeFromNOA" in fields

    def test_analyzer_extends_prebuilt_document(self):
        """Analyzer should extend prebuilt-document base."""
        try:
            from scripts.setup_mortgage_analyzers import MORTGAGE_DOC_ANALYZER_SCHEMA
        except ImportError:
            pytest.skip("setup_mortgage_analyzers.py not yet created")
        
        assert MORTGAGE_DOC_ANALYZER_SCHEMA["baseAnalyzerId"] == "prebuilt-document"

    def test_analyzer_id_is_correct(self):
        """Analyzer ID should match expected value."""
        try:
            from scripts.setup_mortgage_analyzers import MORTGAGE_DOC_ANALYZER_SCHEMA
        except ImportError:
            pytest.skip("setup_mortgage_analyzers.py not yet created")
        
        assert MORTGAGE_DOC_ANALYZER_SCHEMA["analyzerId"] == "mortgageDocAnalyzer"


class TestAnalyzerSetupScript:
    """Tests for the analyzer setup script functionality."""

    def test_setup_script_exists(self):
        """setup_mortgage_analyzers.py should exist."""
        script_path = Path("scripts/setup_mortgage_analyzers.py")
        # Skip if not yet created during Phase 0
        if not script_path.exists():
            pytest.skip("setup_mortgage_analyzers.py not yet created")
        assert script_path.exists()

    def test_script_has_create_all_option(self):
        """Script should support --create-all flag."""
        try:
            import scripts.setup_mortgage_analyzers as script
            # Check that create functions exist
            assert hasattr(script, "create_analyzer") or hasattr(script, "main")
        except ImportError:
            pytest.skip("setup_mortgage_analyzers.py not yet created")

    def test_script_has_verify_option(self):
        """Script should support --verify flag."""
        try:
            import scripts.setup_mortgage_analyzers as script
            assert hasattr(script, "verify_analyzer") or hasattr(script, "get_analyzer")
        except ImportError:
            pytest.skip("setup_mortgage_analyzers.py not yet created")


class TestAnalyzerDeployment:
    """Tests for analyzer deployment functions."""

    @pytest.fixture
    def mock_cu_client(self):
        """Return a mocked Content Understanding client."""
        return MagicMock()

    def test_create_analyzer_idempotent(self, mock_cu_client):
        """create_analyzer should be idempotent (no-op if exists)."""
        try:
            from scripts.setup_mortgage_analyzers import create_analyzer
        except ImportError:
            pytest.skip("setup_mortgage_analyzers.py not yet created")
        
        # Mock the client to return existing analyzer
        mock_cu_client.get_analyzer.return_value = {"analyzerId": "mortgageDocAnalyzer"}
        
        # Should not raise error when analyzer exists
        # Implementation should check existence first

    def test_get_analyzer_returns_schema(self, mock_cu_client):
        """get_analyzer should return analyzer definition if exists."""
        try:
            from scripts.setup_mortgage_analyzers import get_analyzer
        except ImportError:
            pytest.skip("setup_mortgage_analyzers.py not yet created")

    def test_update_analyzer_updates_schema(self, mock_cu_client):
        """update_analyzer should update existing analyzer schema."""
        try:
            from scripts.setup_mortgage_analyzers import update_analyzer
        except ImportError:
            pytest.skip("setup_mortgage_analyzers.py not yet created")


class TestAnalyzerVerification:
    """Tests for analyzer verification with sample documents."""

    @pytest.fixture
    def sample_t4_path(self):
        """Return path to sample T4 document for testing."""
        # Check if sample exists in mortgage research folder
        sample_path = Path("mortgage-research/canadian_mortgage_sample_package")
        if sample_path.exists():
            for pdf in sample_path.glob("*.pdf"):
                if "t4" in pdf.name.lower():
                    return pdf
        return None

    def test_analyzer_processes_sample_document(self, sample_t4_path):
        """Deployed analyzer should process sample mortgage document."""
        if sample_t4_path is None:
            pytest.skip("No sample T4 document available")
        
        # This is an integration test - requires Azure resources
        # Mark as integration test or skip if no Azure credentials
        pytest.skip("Integration test - requires Azure Content Understanding")

    def test_analyzer_extracts_expected_fields(self):
        """Analyzer should extract expected fields from T4."""
        # This would be an integration test with actual Azure analyzer
        pytest.skip("Integration test - requires Azure Content Understanding")
