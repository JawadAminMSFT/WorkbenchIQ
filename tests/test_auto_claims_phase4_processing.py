"""
Tests for Phase 4: Multimodal Processing Pipeline
Feature: 007-automotive-claims-multimodal

Tests cover:
- Single file processing (with mocks)
- Parallel file processing
- Result extraction (document, image, video)
- Result aggregation and conflict resolution
- Database persistence
"""
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import asdict

from app.multimodal import (
    MEDIA_TYPE_DOCUMENT,
    MEDIA_TYPE_IMAGE,
    MEDIA_TYPE_VIDEO,
)
from app.multimodal.processor import (
    MultimodalProcessor,
    FileInfo,
    ProcessingResult,
    BatchResult,
    ProcessingStatus,
)
from app.multimodal.extractors import (
    DocumentExtractor,
    ImageExtractor,
    VideoExtractor,
    extract_document_fields,
    extract_damage_areas,
    extract_video_data,
    DocumentFields,
    DamageArea,
    VideoData,
)
from app.multimodal.aggregator import (
    ResultAggregator,
    AggregatedResult,
    AggregatedField,
    SourceAttribution,
    ConfidenceLevel,
)
from app.claims import SEVERITY_MODERATE, SEVERITY_HEAVY, SEVERITY_MINIMAL


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_document_cu_response():
    """Sample Azure CU response for a document."""
    return {
        "result": {
            "contents": [
                {"markdown": "# Repair Estimate\nVehicle: 2022 Honda Accord\nVIN: 1HGBH41JXMN123456"}
            ],
            "fields": {
                "VehicleMake": {"content": "Honda", "confidence": 0.95},
                "VehicleModel": {"content": "Accord", "confidence": 0.95},
                "VehicleYear": {"content": "2022", "confidence": 0.95},
                "VehicleVIN": {"content": "1HGBH41JXMN123456", "confidence": 0.98},
                "DateOfLoss": {"content": "2024-01-15", "confidence": 0.90},
                "IncidentLocation": {"content": "123 Main St, Springfield", "confidence": 0.85},
                "EstimateTotal": {"content": "4500.00", "confidence": 0.92},
            }
        }
    }


@pytest.fixture
def sample_image_cu_response():
    """Sample Azure CU response for an image."""
    return {
        "result": {
            "contents": [
                {"markdown": "Vehicle image showing front-end damage"}
            ],
            "fields": {
                "damage_detected": {"content": "true", "confidence": 0.98},
                "damage_severity": {"content": "moderate", "confidence": 0.85},
                "damaged_components": {
                    "content": "front bumper, hood, headlight",
                    "confidence": 0.88
                },
                "damage_areas": {
                    "valueArray": [
                        {
                            "component": "front bumper",
                            "damage_type": "dent",
                            "severity": "moderate",
                            "confidence": 0.87,
                        },
                        {
                            "component": "hood",
                            "damage_type": "scratch",
                            "severity": "minor",
                            "confidence": 0.82,
                        }
                    ]
                }
            }
        }
    }


@pytest.fixture
def sample_video_cu_response():
    """Sample Azure CU response for a video."""
    return {
        "result": {
            "contents": [
                {"markdown": "Dashcam footage showing collision"}
            ],
            "fields": {
                "incident_detected": {"content": "true", "confidence": 0.95},
                "incident_timestamp": {"content": "00:15.500", "confidence": 0.92},
                "transcript": {"content": "Audio transcript here...", "confidence": 0.75},
            },
            "segments": [
                {
                    "start_time": 0.0,
                    "end_time": 10.0,
                    "event_type": "normal_driving",
                    "description": "Normal driving conditions",
                    "confidence": 0.90,
                },
                {
                    "start_time": 10.0,
                    "end_time": 18.0,
                    "event_type": "collision",
                    "description": "Vehicle collision detected",
                    "confidence": 0.95,
                }
            ],
            "keyframes": [
                {
                    "timestamp": 15.5,
                    "description": "Impact moment",
                    "objects_detected": ["vehicle", "debris"],
                }
            ]
        }
    }


# ============================================================================
# TestDocumentExtractor
# ============================================================================

class TestDocumentExtractor:
    """Tests for document field extraction."""

    def test_extract_vehicle_info_from_document(self, sample_document_cu_response):
        """Should extract vehicle info fields from document CU result."""
        extractor = DocumentExtractor()
        result = extractor.extract(sample_document_cu_response)
        
        assert isinstance(result, DocumentFields)
        assert result.vehicle is not None
        assert result.vehicle.make == "Honda"
        assert result.vehicle.model == "Accord"
        assert result.vehicle.year == 2022  # Year is int
        assert result.vehicle.vin == "1HGBH41JXMN123456"

    def test_extract_incident_info_from_document(self, sample_document_cu_response):
        """Should extract incident info from document CU result."""
        extractor = DocumentExtractor()
        result = extractor.extract(sample_document_cu_response)
        
        assert result.incident is not None
        assert result.incident.date_of_loss == "2024-01-15"
        assert result.incident.location == "123 Main St, Springfield"

    def test_convenience_function_extract_document_fields(self, sample_document_cu_response):
        """Convenience function should work the same as extractor class."""
        result = extract_document_fields(sample_document_cu_response)
        
        assert isinstance(result, DocumentFields)
        assert result.vehicle is not None

    def test_handles_missing_fields_gracefully(self):
        """Should handle missing fields without raising exceptions."""
        empty_response = {"result": {"fields": {}}}
        result = extract_document_fields(empty_response)
        
        assert isinstance(result, DocumentFields)
        # Vehicle info should be None or have None fields
        assert result.vehicle is None or result.vehicle.vin is None


# ============================================================================
# TestImageExtractor
# ============================================================================

class TestImageExtractor:
    """Tests for image damage extraction."""

    def test_extract_damage_areas_from_image(self, sample_image_cu_response):
        """Should extract damage areas from image CU result."""
        extractor = ImageExtractor()
        result = extractor.extract(sample_image_cu_response)
        
        assert result.damage_detected is True
        assert len(result.damage_areas) >= 1

    def test_damage_area_has_location(self, sample_image_cu_response):
        """Damage area should include component/location info."""
        extractor = ImageExtractor()
        result = extractor.extract(sample_image_cu_response)
        
        if result.damage_areas:
            area = result.damage_areas[0]
            assert area.component is not None

    def test_damage_area_has_severity(self, sample_image_cu_response):
        """Damage area should include severity rating."""
        extractor = ImageExtractor()
        result = extractor.extract(sample_image_cu_response)
        
        if result.damage_areas:
            area = result.damage_areas[0]
            assert area.severity is not None

    def test_damage_area_has_confidence(self, sample_image_cu_response):
        """Damage area should include confidence score."""
        extractor = ImageExtractor()
        result = extractor.extract(sample_image_cu_response)
        
        if result.damage_areas:
            area = result.damage_areas[0]
            assert area.confidence is not None
            assert 0.0 <= area.confidence <= 1.0

    def test_convenience_function_extract_damage_areas(self, sample_image_cu_response):
        """Convenience function should extract damage areas list."""
        result = extract_damage_areas(sample_image_cu_response)
        
        assert isinstance(result, list)


# ============================================================================
# TestVideoExtractor
# ============================================================================

class TestVideoExtractor:
    """Tests for video content extraction."""

    def test_extract_segments_from_video(self, sample_video_cu_response):
        """Should extract segments from video CU result."""
        extractor = VideoExtractor()
        result = extractor.extract(sample_video_cu_response)
        
        assert isinstance(result, VideoData)
        assert len(result.segments) >= 1

    def test_extract_keyframes_from_video(self, sample_video_cu_response):
        """Should extract keyframes from video CU result."""
        extractor = VideoExtractor()
        result = extractor.extract(sample_video_cu_response)
        
        assert len(result.keyframes) >= 1
        keyframe = result.keyframes[0]
        assert keyframe.timestamp == 15.5

    def test_segment_has_event_type(self, sample_video_cu_response):
        """Video segment should include event type."""
        extractor = VideoExtractor()
        result = extractor.extract(sample_video_cu_response)
        
        if result.segments:
            segment = result.segments[0]
            assert segment.event_type is not None

    def test_convenience_function_extract_video_data(self, sample_video_cu_response):
        """Convenience function should work the same."""
        result = extract_video_data(sample_video_cu_response)
        
        assert isinstance(result, VideoData)


# ============================================================================
# TestResultAggregator
# ============================================================================

class TestResultAggregator:
    """Tests for result aggregation."""

    @pytest.fixture
    def document_processing_result(self, sample_document_cu_response):
        """Create a document processing result."""
        doc_fields = extract_document_fields(sample_document_cu_response)
        return ProcessingResult(
            file_id="doc-001",
            filename="repair_estimate.pdf",
            media_type=MEDIA_TYPE_DOCUMENT,
            status=ProcessingStatus.COMPLETED,
            analyzer_id="autoClaimsDocAnalyzer",
            raw_result=sample_document_cu_response,
            extracted_data=doc_fields,
        )

    @pytest.fixture
    def image_processing_result(self, sample_image_cu_response):
        """Create an image processing result."""
        damage_areas = extract_damage_areas(sample_image_cu_response)
        return ProcessingResult(
            file_id="img-001",
            filename="damage_photo.jpg",
            media_type=MEDIA_TYPE_IMAGE,
            status=ProcessingStatus.COMPLETED,
            analyzer_id="autoClaimsImageAnalyzer",
            raw_result=sample_image_cu_response,
            extracted_data=damage_areas,
        )

    @pytest.fixture
    def video_processing_result(self, sample_video_cu_response):
        """Create a video processing result."""
        video_data = extract_video_data(sample_video_cu_response)
        return ProcessingResult(
            file_id="vid-001",
            filename="dashcam.mp4",
            media_type=MEDIA_TYPE_VIDEO,
            status=ProcessingStatus.COMPLETED,
            analyzer_id="autoClaimsVideoAnalyzer",
            raw_result=sample_video_cu_response,
            extracted_data=video_data,
        )

    def test_aggregate_results_merges_fields(
        self, document_processing_result, image_processing_result
    ):
        """Should merge fields from all media sources."""
        aggregator = ResultAggregator()
        results = [document_processing_result, image_processing_result]
        
        aggregated = aggregator.aggregate(results, claim_id="CLM-001")
        
        assert isinstance(aggregated, AggregatedResult)
        assert aggregated.claim_id == "CLM-001"
        # Vehicle info should come from document
        assert aggregated.vehicle.make.value == "Honda"
        # Damage info should come from image
        assert len(aggregated.damage.damage_areas) >= 1

    def test_source_attribution_tracking(self, document_processing_result):
        """Should track source attribution for each field value."""
        aggregator = ResultAggregator()
        results = [document_processing_result]
        
        aggregated = aggregator.aggregate(results)
        
        # Check source is tracked
        if aggregated.vehicle.make.value:
            assert len(aggregated.vehicle.make.sources) >= 1
            source = aggregated.vehicle.make.sources[0]
            assert source.media_type == MEDIA_TYPE_DOCUMENT
            assert source.filename == "repair_estimate.pdf"

    def test_overall_damage_severity_calculation(self, image_processing_result):
        """Should calculate overall severity from individual damage areas."""
        aggregator = ResultAggregator()
        results = [image_processing_result]
        
        aggregated = aggregator.aggregate(results)
        
        # Should have calculated overall severity
        assert aggregated.damage.overall_severity is not None
        assert 0.0 <= aggregated.damage.severity_score <= 1.0

    def test_empty_results_returns_empty_aggregation(self):
        """Should return empty result when no results provided."""
        aggregator = ResultAggregator()
        aggregated = aggregator.aggregate([])
        
        assert aggregated.vehicle.vin.value is None
        assert aggregated.damage.overall_severity == SEVERITY_MINIMAL

    def test_failed_results_are_filtered(self, document_processing_result):
        """Should filter out failed processing results."""
        failed_result = ProcessingResult(
            file_id="failed-001",
            filename="corrupt.pdf",
            media_type=MEDIA_TYPE_DOCUMENT,
            status=ProcessingStatus.FAILED,
            error_message="File corrupted",
        )
        
        aggregator = ResultAggregator()
        results = [failed_result, document_processing_result]
        
        aggregated = aggregator.aggregate(results)
        
        # Only the successful result should be included
        assert len(aggregated.source_files) == 1
        assert "repair_estimate.pdf" in aggregated.source_files


# ============================================================================
# TestMultimodalProcessor (Unit Tests with Mocks)
# ============================================================================

class TestMultimodalProcessor:
    """Tests for MultimodalProcessor class."""

    @pytest.fixture
    def mock_cu_settings(self):
        """Mock Content Understanding settings."""
        settings = MagicMock()
        settings.endpoint = "https://test.cognitiveservices.azure.com"
        settings.key = "test-key"
        return settings

    @pytest.fixture
    def mock_auto_settings(self):
        """Mock Automotive Claims settings."""
        settings = MagicMock()
        settings.doc_analyzer_id = "autoClaimsDocAnalyzer"
        settings.image_analyzer_id = "autoClaimsImageAnalyzer"
        settings.video_analyzer_id = "autoClaimsVideoAnalyzer"
        settings.max_doc_size_mb = 20
        settings.max_image_size_mb = 20
        settings.max_video_size_mb = 200
        return settings

    def test_processor_initialization(self, mock_auto_settings, mock_cu_settings):
        """Should initialize processor with settings."""
        processor = MultimodalProcessor(
            auto_settings=mock_auto_settings,
            cu_settings=mock_cu_settings,
        )
        
        assert processor._max_workers == 4  # default
        assert processor._max_retries == 3  # default

    def test_processor_custom_worker_count(self, mock_auto_settings, mock_cu_settings):
        """Should accept custom worker count."""
        processor = MultimodalProcessor(
            auto_settings=mock_auto_settings,
            cu_settings=mock_cu_settings,
            max_workers=8,
        )
        
        assert processor._max_workers == 8

    def test_batch_result_structure(self):
        """BatchResult should have correct structure."""
        result = BatchResult(
            total_files=3,
            completed=2,
            failed=1,
            skipped=0,
            results=[],
            total_time_seconds=5.5,
        )
        
        assert result.total_files == 3
        assert result.completed == 2
        assert result.failed == 1

    def test_file_info_structure(self):
        """FileInfo should have correct structure."""
        file_info = FileInfo(
            file_id="test-001",
            filename="test.pdf",
            file_bytes=b"test content",
            content_type="application/pdf",
            claim_id="CLM-001",
        )
        
        assert file_info.file_id == "test-001"
        assert file_info.claim_id == "CLM-001"

    def test_processing_status_values(self):
        """ProcessingStatus enum should have expected values."""
        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.PROCESSING.value == "processing"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"
        assert ProcessingStatus.SKIPPED.value == "skipped"

    def test_empty_batch_returns_zero_counts(self, mock_auto_settings, mock_cu_settings):
        """Processing empty list should return zero counts."""
        processor = MultimodalProcessor(
            auto_settings=mock_auto_settings,
            cu_settings=mock_cu_settings,
        )
        
        result = processor.process_files([])
        
        assert result.total_files == 0
        assert result.completed == 0
        assert result.failed == 0


# ============================================================================
# TestMultimodalRepository (Integration Tests)
# ============================================================================

class TestMultimodalRepository:
    """Tests for database persistence."""

    @pytest.mark.integration
    def test_save_claim_media(self):
        """Should save claim media to claim_media table."""
        # Integration test - requires database
        pytest.skip("Integration test - requires PostgreSQL")

    @pytest.mark.integration
    def test_save_keyframes(self):
        """Should save keyframes to claim_keyframes table."""
        pytest.skip("Integration test - requires PostgreSQL")

    @pytest.mark.integration
    def test_save_damage_areas(self):
        """Should save damage areas to claim_damage_areas table."""
        pytest.skip("Integration test - requires PostgreSQL")

    @pytest.mark.integration
    def test_save_repair_items(self):
        """Should save repair items to claim_repair_items table."""
        pytest.skip("Integration test - requires PostgreSQL")

    def test_repository_has_create_tables_sql(self):
        """Repository should have SQL for creating tables."""
        from app.multimodal.repository import ClaimsMediaRepository
        
        repo = ClaimsMediaRepository()
        
        assert "claim_media" in repo.CREATE_TABLES_SQL
        assert "claim_damage_areas" in repo.CREATE_TABLES_SQL
        assert "claim_keyframes" in repo.CREATE_TABLES_SQL
        assert "claim_repair_items" in repo.CREATE_TABLES_SQL
        assert "claim_summaries" in repo.CREATE_TABLES_SQL
