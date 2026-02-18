"""
Tests for Phase 3: Custom Analyzer Setup
Feature: 007-automotive-claims-multimodal

Tests cover:
- Custom analyzer schema definitions
- Analyzer creation via Azure CU API
- Analyzer verification and testing
- Idempotent deployment
"""
import pytest
import sys
from pathlib import Path

# Add scripts to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestAnalyzerSchemas:
    """Tests for custom analyzer schema definitions."""

    def test_doc_analyzer_schema_valid(self):
        """autoClaimsDocAnalyzer schema should be valid."""
        from setup_automotive_analyzers import AUTO_CLAIMS_DOC_ANALYZER_SCHEMA
        
        assert AUTO_CLAIMS_DOC_ANALYZER_SCHEMA is not None
        assert "name" in AUTO_CLAIMS_DOC_ANALYZER_SCHEMA
        assert "fields" in AUTO_CLAIMS_DOC_ANALYZER_SCHEMA
        assert len(AUTO_CLAIMS_DOC_ANALYZER_SCHEMA["fields"]) > 0

    def test_doc_analyzer_extends_prebuilt_document(self):
        """Document analyzer should extend prebuilt-document."""
        from setup_automotive_analyzers import get_analyzer_configs
        
        configs = get_analyzer_configs()
        doc_config = configs.get("autoClaimsDocAnalyzer")
        
        assert doc_config is not None
        assert doc_config["baseAnalyzerId"] == "prebuilt-document"

    def test_doc_analyzer_has_vehicle_fields(self):
        """Document analyzer should have vehicle info fields."""
        from setup_automotive_analyzers import AUTO_CLAIMS_DOC_ANALYZER_SCHEMA
        
        fields = AUTO_CLAIMS_DOC_ANALYZER_SCHEMA["fields"]
        
        assert "VehicleVIN" in fields
        assert "VehicleMake" in fields
        assert "VehicleModel" in fields
        assert "VehicleYear" in fields

    def test_doc_analyzer_has_repair_estimate_fields(self):
        """Document analyzer should have repair estimate fields."""
        from setup_automotive_analyzers import AUTO_CLAIMS_DOC_ANALYZER_SCHEMA
        
        fields = AUTO_CLAIMS_DOC_ANALYZER_SCHEMA["fields"]
        
        assert "EstimateTotal" in fields
        assert "LaborCost" in fields
        assert "PartsCost" in fields
        assert "RepairLineItems" in fields

    def test_image_analyzer_schema_valid(self):
        """autoClaimsImageAnalyzer schema should be valid."""
        from setup_automotive_analyzers import AUTO_CLAIMS_IMAGE_ANALYZER_SCHEMA
        
        assert AUTO_CLAIMS_IMAGE_ANALYZER_SCHEMA is not None
        assert "name" in AUTO_CLAIMS_IMAGE_ANALYZER_SCHEMA
        assert "fields" in AUTO_CLAIMS_IMAGE_ANALYZER_SCHEMA
        assert len(AUTO_CLAIMS_IMAGE_ANALYZER_SCHEMA["fields"]) > 0

    def test_image_analyzer_extends_prebuilt_image(self):
        """Image analyzer should extend prebuilt-image."""
        from setup_automotive_analyzers import get_analyzer_configs
        
        configs = get_analyzer_configs()
        image_config = configs.get("autoClaimsImageAnalyzer")
        
        assert image_config is not None
        assert image_config["baseAnalyzerId"] == "prebuilt-image"

    def test_image_analyzer_has_damage_fields(self):
        """Image analyzer should have damage detection fields."""
        from setup_automotive_analyzers import AUTO_CLAIMS_IMAGE_ANALYZER_SCHEMA
        
        fields = AUTO_CLAIMS_IMAGE_ANALYZER_SCHEMA["fields"]
        
        assert "DamageDetected" in fields
        assert "DamageAreas" in fields
        assert "OverallDamageSeverity" in fields
        
        # DamageAreas should be an array with proper structure
        damage_areas = fields["DamageAreas"]
        assert damage_areas["type"] == "array"
        assert "items" in damage_areas

    def test_video_analyzer_schema_valid(self):
        """autoClaimsVideoAnalyzer schema should be valid."""
        from setup_automotive_analyzers import AUTO_CLAIMS_VIDEO_ANALYZER_SCHEMA
        
        assert AUTO_CLAIMS_VIDEO_ANALYZER_SCHEMA is not None
        assert "name" in AUTO_CLAIMS_VIDEO_ANALYZER_SCHEMA
        assert "fields" in AUTO_CLAIMS_VIDEO_ANALYZER_SCHEMA
        assert len(AUTO_CLAIMS_VIDEO_ANALYZER_SCHEMA["fields"]) > 0

    def test_video_analyzer_extends_prebuilt_video(self):
        """Video analyzer should extend prebuilt-video."""
        from setup_automotive_analyzers import get_analyzer_configs
        
        configs = get_analyzer_configs()
        video_config = configs.get("autoClaimsVideoAnalyzer")
        
        assert video_config is not None
        assert video_config["baseAnalyzerId"] == "prebuilt-video"

    def test_video_analyzer_has_incident_fields(self):
        """Video analyzer should have incident analysis fields."""
        from setup_automotive_analyzers import AUTO_CLAIMS_VIDEO_ANALYZER_SCHEMA
        
        fields = AUTO_CLAIMS_VIDEO_ANALYZER_SCHEMA["fields"]
        
        assert "IncidentDetected" in fields
        assert "ImpactTimestamp" in fields
        assert "IncidentType" in fields
        assert "VideoSegments" in fields
        assert "Transcript" in fields

    def test_all_analyzers_have_confidence_enabled(self):
        """All analyzers should have estimateFieldSourceAndConfidence enabled."""
        from setup_automotive_analyzers import get_analyzer_configs
        
        configs = get_analyzer_configs()
        
        for analyzer_id, config in configs.items():
            assert config["config"].get("estimateFieldSourceAndConfidence") is True, \
                f"{analyzer_id} should have confidence scoring enabled"


class TestAnalyzerDeployment:
    """Tests for analyzer deployment operations."""

    def test_get_analyzer_configs_returns_all_three(self):
        """get_analyzer_configs() should return all three analyzer configs."""
        from setup_automotive_analyzers import get_analyzer_configs
        
        configs = get_analyzer_configs()
        
        assert len(configs) == 3
        assert "autoClaimsDocAnalyzer" in configs
        assert "autoClaimsImageAnalyzer" in configs
        assert "autoClaimsVideoAnalyzer" in configs

    def test_analyzer_configs_have_required_fields(self):
        """Each analyzer config should have required fields."""
        from setup_automotive_analyzers import get_analyzer_configs
        
        configs = get_analyzer_configs()
        
        for analyzer_id, config in configs.items():
            assert "description" in config, f"{analyzer_id} missing description"
            assert "baseAnalyzerId" in config, f"{analyzer_id} missing baseAnalyzerId"
            assert "fieldSchema" in config, f"{analyzer_id} missing fieldSchema"
            assert "config" in config, f"{analyzer_id} missing config"

    @pytest.mark.integration
    def test_create_analyzer_success(self):
        """create_analyzer() should create analyzer in Azure CU."""
        # This test requires Azure connection - skip in unit tests
        pytest.skip("Integration test - requires Azure connection (T031)")

    @pytest.mark.integration
    def test_get_analyzer_returns_existing(self):
        """get_analyzer() should return analyzer if it exists."""
        # This test requires Azure connection - skip in unit tests
        pytest.skip("Integration test - requires Azure connection (T032)")

    @pytest.mark.integration
    def test_get_analyzer_returns_none_if_missing(self):
        """get_analyzer() should return None if analyzer doesn't exist."""
        # This test requires Azure connection - skip in unit tests
        pytest.skip("Integration test - requires Azure connection (T032)")

    @pytest.mark.integration
    def test_update_analyzer_success(self):
        """update_analyzer() should update existing analyzer."""
        # This test requires Azure connection - skip in unit tests
        pytest.skip("Integration test - requires Azure connection (T033)")

    @pytest.mark.integration
    def test_idempotent_deployment(self):
        """Deployment should be idempotent (create if not exists, update if changed)."""
        # This test requires Azure connection - skip in unit tests
        pytest.skip("Integration test - requires Azure connection (T034)")

    @pytest.mark.integration
    def test_verification_with_sample_content(self):
        """Verification should test each analyzer with sample content."""
        # This test requires Azure connection - skip in unit tests
        pytest.skip("Integration test - requires Azure connection (T035)")
