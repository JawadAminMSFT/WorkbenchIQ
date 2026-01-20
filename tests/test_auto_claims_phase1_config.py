"""
Tests for Phase 1: Infrastructure & Configuration
Feature: 007-automotive-claims-multimodal

Tests cover:
- Package structure creation (app/multimodal/, app/claims/)
- Environment variable configuration
- AutomotiveClaimsSettings dataclass
- Persona enum and registry updates
"""
import os
import pytest


class TestAutomotiveClaimsSettings:
    """Tests for AutomotiveClaimsSettings configuration."""

    def test_settings_loads_from_env(self, monkeypatch):
        """AutomotiveClaimsSettings should load from environment variables."""
        from app.config import AutomotiveClaimsSettings
        
        # Set custom env vars
        monkeypatch.setenv("AUTO_CLAIMS_ENABLED", "true")
        monkeypatch.setenv("AUTO_CLAIMS_DOC_ANALYZER", "customDocAnalyzer")
        monkeypatch.setenv("AUTO_CLAIMS_IMAGE_ANALYZER", "customImageAnalyzer")
        monkeypatch.setenv("AUTO_CLAIMS_VIDEO_ANALYZER", "customVideoAnalyzer")
        
        settings = AutomotiveClaimsSettings.from_env()
        
        assert settings.enabled is True
        assert settings.doc_analyzer == "customDocAnalyzer"
        assert settings.image_analyzer == "customImageAnalyzer"
        assert settings.video_analyzer == "customVideoAnalyzer"

    def test_settings_has_default_values(self, monkeypatch):
        """AutomotiveClaimsSettings should have sensible defaults."""
        from app.config import AutomotiveClaimsSettings
        
        # Clear any env vars that might be set
        for var in ["AUTO_CLAIMS_ENABLED", "AUTO_CLAIMS_DOC_ANALYZER", 
                    "AUTO_CLAIMS_IMAGE_ANALYZER", "AUTO_CLAIMS_VIDEO_ANALYZER",
                    "AUTO_CLAIMS_POLICIES_PATH"]:
            monkeypatch.delenv(var, raising=False)
        
        settings = AutomotiveClaimsSettings.from_env()
        
        # Check defaults
        assert settings.enabled is True  # Default enabled
        assert settings.doc_analyzer == "autoClaimsDocAnalyzer"
        assert settings.image_analyzer == "autoClaimsImageAnalyzer"
        assert settings.video_analyzer == "autoClaimsVideoAnalyzer"
        assert "automotive-claims-policies.json" in settings.policies_path

    def test_auto_claims_enabled_default_true(self, monkeypatch):
        """AUTO_CLAIMS_ENABLED should default to True."""
        from app.config import AutomotiveClaimsSettings
        
        monkeypatch.delenv("AUTO_CLAIMS_ENABLED", raising=False)
        settings = AutomotiveClaimsSettings.from_env()
        
        assert settings.enabled is True

    def test_analyzer_ids_configurable(self, monkeypatch):
        """Custom analyzer IDs should be configurable via env vars."""
        from app.config import AutomotiveClaimsSettings
        
        monkeypatch.setenv("AUTO_CLAIMS_DOC_ANALYZER", "myCustomDocAnalyzer")
        monkeypatch.setenv("AUTO_CLAIMS_IMAGE_ANALYZER", "myCustomImageAnalyzer")
        monkeypatch.setenv("AUTO_CLAIMS_VIDEO_ANALYZER", "myCustomVideoAnalyzer")
        
        settings = AutomotiveClaimsSettings.from_env()
        
        assert settings.doc_analyzer == "myCustomDocAnalyzer"
        assert settings.image_analyzer == "myCustomImageAnalyzer"
        assert settings.video_analyzer == "myCustomVideoAnalyzer"


class TestPersonaRegistry:
    """Tests for persona enum and registry updates."""

    def test_persona_type_includes_automotive_claims(self):
        """PersonaType enum should include AUTOMOTIVE_CLAIMS."""
        from app.personas import PersonaType
        
        assert hasattr(PersonaType, "AUTOMOTIVE_CLAIMS")
        assert PersonaType.AUTOMOTIVE_CLAIMS.value == "automotive_claims"

    def test_backward_compatibility_alias(self):
        """PROPERTY_CASUALTY_CLAIMS should alias to AUTOMOTIVE_CLAIMS."""
        from app.personas import PersonaType
        
        # PROPERTY_CASUALTY_CLAIMS should exist as legacy alias
        assert hasattr(PersonaType, "PROPERTY_CASUALTY_CLAIMS")
        # Legacy persona still has its own value
        assert PersonaType.PROPERTY_CASUALTY_CLAIMS.value == "property_casualty_claims"

    def test_persona_configs_has_automotive_claims(self):
        """PERSONA_CONFIGS registry should include automotive_claims."""
        from app.personas import PERSONA_CONFIGS, PersonaType
        
        assert PersonaType.AUTOMOTIVE_CLAIMS in PERSONA_CONFIGS
        config = PERSONA_CONFIGS[PersonaType.AUTOMOTIVE_CLAIMS]
        
        # PersonaConfig is a dataclass, use attribute access
        assert config.id == "automotive_claims"
        assert config.name == "Automotive Claims"
        assert "multimodal" in config.description.lower() or "automotive" in config.description.lower()

    def test_automotive_claims_field_schema_exists(self):
        """AUTOMOTIVE_CLAIMS_FIELD_SCHEMA should be defined."""
        from app.personas import AUTOMOTIVE_CLAIMS_FIELD_SCHEMA
        
        assert AUTOMOTIVE_CLAIMS_FIELD_SCHEMA is not None
        # Field schema is a dict with 'fields' key
        assert isinstance(AUTOMOTIVE_CLAIMS_FIELD_SCHEMA, dict)
        assert "fields" in AUTOMOTIVE_CLAIMS_FIELD_SCHEMA
        assert len(AUTOMOTIVE_CLAIMS_FIELD_SCHEMA["fields"]) > 0

    def test_field_schema_has_damage_fields(self):
        """Field schema should include damage assessment fields."""
        from app.personas import AUTOMOTIVE_CLAIMS_FIELD_SCHEMA
        
        fields = AUTOMOTIVE_CLAIMS_FIELD_SCHEMA.get("fields", {})
        field_names = list(fields.keys())
        
        # Check for key damage assessment fields
        assert "DamageAreas" in field_names or any("damage" in name.lower() for name in field_names)
        assert "OverallDamageSeverity" in field_names or any("severity" in name.lower() for name in field_names)

    def test_field_schema_has_video_fields(self):
        """Field schema should include video evidence fields."""
        from app.personas import AUTOMOTIVE_CLAIMS_FIELD_SCHEMA
        
        fields = AUTOMOTIVE_CLAIMS_FIELD_SCHEMA.get("fields", {})
        field_names = list(fields.keys())
        
        # Check for video evidence fields
        assert "VideoSegments" in field_names or any("video" in name.lower() for name in field_names)

    def test_automotive_claims_prompts_exist(self):
        """AUTOMOTIVE_CLAIMS_DEFAULT_PROMPTS should be defined."""
        from app.personas import AUTOMOTIVE_CLAIMS_DEFAULT_PROMPTS
        
        assert AUTOMOTIVE_CLAIMS_DEFAULT_PROMPTS is not None
        assert isinstance(AUTOMOTIVE_CLAIMS_DEFAULT_PROMPTS, dict)
        
        # Check for expected prompt categories
        assert "damage_assessment" in AUTOMOTIVE_CLAIMS_DEFAULT_PROMPTS
        assert "liability_assessment" in AUTOMOTIVE_CLAIMS_DEFAULT_PROMPTS
        assert "fraud_detection" in AUTOMOTIVE_CLAIMS_DEFAULT_PROMPTS


class TestPackageStructure:
    """Tests for package directory structure."""

    def test_multimodal_package_exists(self):
        """app/multimodal/ package should exist and be importable."""
        import app.multimodal
        
        # Check that media type constants are exported
        assert hasattr(app.multimodal, "MEDIA_TYPE_DOCUMENT")
        assert hasattr(app.multimodal, "MEDIA_TYPE_IMAGE")
        assert hasattr(app.multimodal, "MEDIA_TYPE_VIDEO")

    def test_claims_package_exists(self):
        """app/claims/ package should exist and be importable."""
        import app.claims
        
        # Check that constants are exported
        assert hasattr(app.claims, "SEVERITY_MINOR")
        assert hasattr(app.claims, "SEVERITY_MODERATE")
        assert hasattr(app.claims, "SEVERITY_HEAVY")
