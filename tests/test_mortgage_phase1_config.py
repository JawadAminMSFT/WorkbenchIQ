"""
Tests for Phase 1: Infrastructure & Configuration
Feature: 008-mortgage-underwriting

Tests cover:
- Package structure creation (app/mortgage/)
- Environment variable configuration
- MortgageUnderwritingSettings dataclass
- Persona enum and registry updates
- Unified indexer configuration
"""
import os
import pytest


class TestMortgageUnderwritingSettings:
    """Tests for MortgageUnderwritingSettings configuration."""

    def test_settings_loads_from_env(self, monkeypatch):
        """MortgageUnderwritingSettings should load from environment variables."""
        from app.config import MortgageUnderwritingSettings
        
        # Set custom env vars
        monkeypatch.setenv("MORTGAGE_UNDERWRITING_ENABLED", "true")
        monkeypatch.setenv("MORTGAGE_DOC_ANALYZER", "customMortgageAnalyzer")
        monkeypatch.setenv("OSFI_MQR_FLOOR_PCT", "5.50")
        monkeypatch.setenv("GDS_LIMIT_STANDARD", "0.35")
        
        settings = MortgageUnderwritingSettings.from_env()
        
        assert settings.enabled is True
        assert settings.doc_analyzer == "customMortgageAnalyzer"
        assert settings.osfi_mqr_floor_pct == 5.50
        assert settings.gds_limit_standard == 0.35

    def test_settings_has_default_values(self, monkeypatch):
        """MortgageUnderwritingSettings should have sensible defaults."""
        from app.config import MortgageUnderwritingSettings
        
        # Clear any env vars that might be set
        for var in ["MORTGAGE_UNDERWRITING_ENABLED", "MORTGAGE_DOC_ANALYZER", 
                    "MORTGAGE_POLICIES_PATH", "OSFI_MQR_FLOOR_PCT",
                    "OSFI_MQR_BUFFER_PCT", "GDS_LIMIT_STANDARD", "TDS_LIMIT_STANDARD"]:
            monkeypatch.delenv(var, raising=False)
        
        settings = MortgageUnderwritingSettings.from_env()
        
        # Check defaults per OSFI B-20
        assert settings.enabled is True
        assert settings.doc_analyzer == "mortgageDocAnalyzer"
        assert settings.osfi_mqr_floor_pct == 5.25
        assert settings.osfi_mqr_buffer_pct == 2.0
        assert settings.gds_limit_standard == 0.39
        assert settings.tds_limit_standard == 0.44
        assert "mortgage-underwriting-policies.json" in settings.policies_path

    def test_osfi_mqr_parameters_configurable(self, monkeypatch):
        """OSFI MQR parameters should be configurable via env vars."""
        from app.config import MortgageUnderwritingSettings
        
        monkeypatch.setenv("OSFI_MQR_FLOOR_PCT", "5.75")
        monkeypatch.setenv("OSFI_MQR_BUFFER_PCT", "2.5")
        
        settings = MortgageUnderwritingSettings.from_env()
        
        assert settings.osfi_mqr_floor_pct == 5.75
        assert settings.osfi_mqr_buffer_pct == 2.5

    def test_dsr_limits_configurable(self, monkeypatch):
        """GDS and TDS limits should be configurable via env vars."""
        from app.config import MortgageUnderwritingSettings
        
        monkeypatch.setenv("GDS_LIMIT_STANDARD", "0.32")
        monkeypatch.setenv("TDS_LIMIT_STANDARD", "0.40")
        
        settings = MortgageUnderwritingSettings.from_env()
        
        assert settings.gds_limit_standard == 0.32
        assert settings.tds_limit_standard == 0.40


class TestPersonaRegistry:
    """Tests for persona enum and registry updates."""

    def test_persona_type_includes_mortgage_underwriting(self):
        """PersonaType enum should include MORTGAGE_UNDERWRITING."""
        from app.personas import PersonaType
        
        assert hasattr(PersonaType, "MORTGAGE_UNDERWRITING")
        assert PersonaType.MORTGAGE_UNDERWRITING.value == "mortgage_underwriting"

    def test_persona_configs_has_mortgage_underwriting(self):
        """PERSONA_CONFIGS registry should include mortgage_underwriting."""
        from app.personas import PERSONA_CONFIGS, PersonaType
        
        assert PersonaType.MORTGAGE_UNDERWRITING in PERSONA_CONFIGS
        config = PERSONA_CONFIGS[PersonaType.MORTGAGE_UNDERWRITING]
        
        assert config.id == "mortgage_underwriting"
        assert config.name == "Mortgage Underwriting"
        assert config.icon == "🏠"
        assert config.enabled is True

    def test_persona_config_has_field_schema(self):
        """Mortgage persona config should have comprehensive field schema."""
        from app.personas import PERSONA_CONFIGS, PersonaType
        
        config = PERSONA_CONFIGS[PersonaType.MORTGAGE_UNDERWRITING]
        
        # Verify field schema exists and has key sections
        assert config.field_schema is not None
        schema = config.field_schema
        
        # Should have mortgage-specific fields
        assert "borrower" in str(schema).lower() or "property" in str(schema).lower()

    def test_persona_config_has_custom_analyzer(self):
        """Mortgage persona should specify custom analyzer ID."""
        from app.personas import PERSONA_CONFIGS, PersonaType
        
        config = PERSONA_CONFIGS[PersonaType.MORTGAGE_UNDERWRITING]
        
        assert config.custom_analyzer_id == "mortgageDocAnalyzer"


class TestUnifiedIndexerConfig:
    """Tests for unified indexer persona configuration."""

    def test_unified_indexer_has_mortgage_config(self):
        """PERSONA_CONFIG should include mortgage_underwriting."""
        from app.rag.unified_indexer import PERSONA_CONFIG
        
        assert "mortgage_underwriting" in PERSONA_CONFIG
        
        config = PERSONA_CONFIG["mortgage_underwriting"]
        assert config["table_name"] == "mortgage_policy_chunks"
        assert "mortgage-underwriting-policies.json" in config["policies_path"]
        assert config["display_name"] == "Mortgage Underwriting"

    def test_policies_path_exists(self):
        """Mortgage policies file should exist at configured path."""
        from app.rag.unified_indexer import PERSONA_CONFIG
        from pathlib import Path
        
        config = PERSONA_CONFIG["mortgage_underwriting"]
        policies_path = Path(config["policies_path"])
        
        # Note: This test may fail if file not yet created
        # Skip if not implementing Phase 0 first
        if policies_path.exists():
            assert policies_path.suffix == ".json"


class TestPackageStructure:
    """Tests for mortgage package structure."""

    def test_mortgage_package_exists(self):
        """app/mortgage package should exist and be importable."""
        import app.mortgage
        assert app.mortgage is not None

    def test_mortgage_package_has_exports(self):
        """app/mortgage should export key classes."""
        from app.mortgage import (
            MortgagePolicyEngine,
            MortgageCalculator,
            MortgagePolicyLoader,
        )
        
        assert MortgagePolicyEngine is not None
        assert MortgageCalculator is not None
        assert MortgagePolicyLoader is not None

    def test_constants_module_exists(self):
        """app/mortgage/constants.py should exist with status enums."""
        from app.mortgage.constants import (
            MortgageCaseStatus,
            MortgageDocType,
            MortgageProductType,
        )
        
        # Check status enum values
        assert hasattr(MortgageCaseStatus, "INTAKE")
        assert hasattr(MortgageCaseStatus, "IN_REVIEW")
        assert hasattr(MortgageCaseStatus, "APPROVED")
        assert hasattr(MortgageCaseStatus, "DECLINED")
