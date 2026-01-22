"""
Tests for Phase 2: Multimodal Router & MIME Detection
Feature: 007-automotive-claims-multimodal

Tests cover:
- MIME type detection for documents, images, videos
- File extension fallback detection
- Analyzer routing based on media type
- File size validation
"""
import pytest

from app.multimodal import (
    MimeDetector,
    MediaType,
    detect_media_type,
    AnalyzerRouter,
    FileSizeError,
    UnsupportedMediaTypeError,
    MEDIA_TYPE_DOCUMENT,
    MEDIA_TYPE_IMAGE,
    MEDIA_TYPE_VIDEO,
)
from app.config import AutomotiveClaimsSettings


# Test file signatures (magic bytes)
PDF_MAGIC = b"%PDF-1.4 test content"
JPEG_MAGIC = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01test"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
MP4_MAGIC = b"\x00\x00\x00\x1cftypisom\x00\x00\x02\x00"
MOV_MAGIC = b"\x00\x00\x00\x14ftypqt  \x00\x00\x00\x00"


class TestMimeDetector:
    """Tests for MimeDetector class."""

    def test_detect_pdf_as_document(self):
        """PDF files should be detected as document type."""
        detector = MimeDetector()
        result = detector.detect(PDF_MAGIC, "claim.pdf")
        
        assert result.media_type == MediaType.DOCUMENT
        assert result.confidence > 0.8

    def test_detect_docx_as_document(self):
        """DOCX files should be detected as document type."""
        # DOCX starts with PK (ZIP) and contains word/
        docx_bytes = b"PK\x03\x04" + b"\x00" * 100 + b"word/" + b"\x00" * 100
        detector = MimeDetector()
        result = detector.detect(docx_bytes, "report.docx")
        
        assert result.media_type == MediaType.DOCUMENT

    def test_detect_jpeg_as_image(self):
        """JPEG files should be detected as image type."""
        detector = MimeDetector()
        result = detector.detect(JPEG_MAGIC, "damage_photo.jpg")
        
        assert result.media_type == MediaType.IMAGE
        assert result.confidence > 0.8

    def test_detect_png_as_image(self):
        """PNG files should be detected as image type."""
        detector = MimeDetector()
        result = detector.detect(PNG_MAGIC, "screenshot.png")
        
        assert result.media_type == MediaType.IMAGE
        assert result.confidence > 0.8

    def test_detect_mp4_as_video(self):
        """MP4 files should be detected as video type."""
        detector = MimeDetector()
        result = detector.detect(MP4_MAGIC, "dashcam.mp4")
        
        assert result.media_type == MediaType.VIDEO
        assert result.confidence > 0.8

    def test_detect_mov_as_video(self):
        """MOV files should be detected as video type."""
        detector = MimeDetector()
        result = detector.detect(MOV_MAGIC, "incident.mov")
        
        assert result.media_type == MediaType.VIDEO
        assert result.confidence > 0.8

    def test_extension_fallback_for_unknown_mime(self):
        """Should fall back to extension-based detection for unknown MIME types."""
        # Unknown binary content but with known extension
        unknown_bytes = b"\x00\x01\x02\x03\x04\x05\x06\x07"
        detector = MimeDetector()
        result = detector.detect(unknown_bytes, "document.pdf")
        
        assert result.media_type == MediaType.DOCUMENT
        assert result.detection_method == "extension"

    def test_convenience_function(self):
        """detect_media_type() convenience function should work."""
        media_type = detect_media_type(JPEG_MAGIC, "photo.jpg")
        assert media_type == MEDIA_TYPE_IMAGE


class TestAnalyzerRouter:
    """Tests for AnalyzerRouter class."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return AutomotiveClaimsSettings(
            enabled=True,
            doc_analyzer="autoClaimsDocAnalyzer",
            image_analyzer="autoClaimsImageAnalyzer",
            video_analyzer="autoClaimsVideoAnalyzer",
            policies_path="prompts/automotive-claims-policies.json",
            video_max_duration_minutes=30,
            image_max_size_mb=20,
        )

    def test_router_selects_document_analyzer(self, settings):
        """Document media type should route to document analyzer."""
        router = AnalyzerRouter(settings)
        analyzer_id = router.get_analyzer_id(MEDIA_TYPE_DOCUMENT)
        
        assert analyzer_id == "autoClaimsDocAnalyzer"

    def test_router_selects_image_analyzer(self, settings):
        """Image media type should route to image analyzer."""
        router = AnalyzerRouter(settings)
        analyzer_id = router.get_analyzer_id(MEDIA_TYPE_IMAGE)
        
        assert analyzer_id == "autoClaimsImageAnalyzer"

    def test_router_selects_video_analyzer(self, settings):
        """Video media type should route to video analyzer."""
        router = AnalyzerRouter(settings)
        analyzer_id = router.get_analyzer_id(MEDIA_TYPE_VIDEO)
        
        assert analyzer_id == "autoClaimsVideoAnalyzer"

    def test_router_uses_fallback_analyzers(self, settings):
        """Should use prebuilt fallback if custom analyzer not configured."""
        router = AnalyzerRouter(settings)
        
        doc_fallback = router.get_analyzer_id(MEDIA_TYPE_DOCUMENT, use_fallback=True)
        image_fallback = router.get_analyzer_id(MEDIA_TYPE_IMAGE, use_fallback=True)
        video_fallback = router.get_analyzer_id(MEDIA_TYPE_VIDEO, use_fallback=True)
        
        assert doc_fallback == "prebuilt-document"
        assert image_fallback == "prebuilt-image"
        assert video_fallback == "prebuilt-video"

    def test_route_file_returns_media_type_and_analyzer(self, settings):
        """route_file() should return RoutingResult with media_type and analyzer_id."""
        router = AnalyzerRouter(settings)
        result = router.route_file(JPEG_MAGIC, "damage.jpg", validate_size=False)
        
        assert result.media_type == MEDIA_TYPE_IMAGE
        assert result.analyzer_id == "autoClaimsImageAnalyzer"
        assert result.is_custom_analyzer is True

    def test_validates_image_size_limit(self, settings):
        """Should reject images exceeding size limit."""
        # Create oversized image (25 MB when limit is 20 MB)
        settings.image_max_size_mb = 20
        oversized_image = JPEG_MAGIC + b"\x00" * (25 * 1024 * 1024)
        
        router = AnalyzerRouter(settings)
        
        with pytest.raises(FileSizeError) as exc_info:
            router.route_file(oversized_image, "huge.jpg")
        
        assert "exceeds limit" in str(exc_info.value)

    def test_validates_video_size_limit(self):
        """Should reject videos exceeding size/duration limits."""
        # Note: We test size limit, duration would require actual video parsing
        settings = AutomotiveClaimsSettings(
            enabled=True,
            doc_analyzer="doc",
            image_analyzer="img",
            video_analyzer="vid",
        )
        
        # Create 600 MB video (over 500 MB limit)
        oversized_video = MP4_MAGIC + b"\x00" * (600 * 1024 * 1024)
        
        router = AnalyzerRouter(settings)
        
        with pytest.raises(FileSizeError) as exc_info:
            router.route_file(oversized_video, "huge.mp4")
        
        assert "exceeds limit" in str(exc_info.value)

    def test_raises_for_unsupported_type(self, settings):
        """Should raise UnsupportedMediaTypeError for unknown files."""
        router = AnalyzerRouter(settings)
        unknown_bytes = b"\x00\x01\x02\x03"
        
        with pytest.raises(UnsupportedMediaTypeError):
            router.route_file(unknown_bytes, "mystery.xyz")


class TestContentUnderstandingExtensions:
    """Tests for CU client extensions."""

    def test_analyze_image_function_exists(self):
        """analyze_image() function should exist in content_understanding_client."""
        from app.content_understanding_client import analyze_image
        assert callable(analyze_image)

    def test_analyze_video_function_exists(self):
        """analyze_video() function should exist in content_understanding_client."""
        from app.content_understanding_client import analyze_video
        assert callable(analyze_video)

    def test_extract_keyframes_function_exists(self):
        """extract_video_keyframes() function should exist."""
        from app.content_understanding_client import extract_video_keyframes
        assert callable(extract_video_keyframes)

    def test_extract_transcript_function_exists(self):
        """extract_video_transcript() function should exist."""
        from app.content_understanding_client import extract_video_transcript
        assert callable(extract_video_transcript)

    def test_extract_segments_function_exists(self):
        """extract_video_segments() function should exist."""
        from app.content_understanding_client import extract_video_segments
        assert callable(extract_video_segments)

    def test_extract_keyframes_from_video_response(self):
        """Should extract keyframe URLs from CU video response."""
        from app.content_understanding_client import extract_video_keyframes
        
        mock_response = {
            "result": {
                "contents": [{
                    "kind": "audioVisual",
                    "segments": [{
                        "id": 1,
                        "keyframes": [
                            {"timestamp": "0:00:05", "url": "https://example.com/kf1.jpg", "description": "Impact"},
                            {"timestamp": "0:00:10", "url": "https://example.com/kf2.jpg", "description": "Aftermath"},
                        ]
                    }]
                }]
            }
        }
        
        keyframes = extract_video_keyframes(mock_response)
        
        assert len(keyframes) == 2
        assert keyframes[0]["timestamp"] == "0:00:05"
        assert keyframes[0]["url"] == "https://example.com/kf1.jpg"

    def test_extract_transcript_from_video_response(self):
        """Should extract transcript from CU video response."""
        from app.content_understanding_client import extract_video_transcript
        
        mock_response = {
            "result": {
                "contents": [{
                    "kind": "audioVisual",
                    "segments": [
                        {"startTime": "0:00:00", "speech": "He ran a red light."},
                        {"startTime": "0:00:05", "speech": "I tried to brake but couldn't stop."},
                    ]
                }]
            }
        }
        
        transcript = extract_video_transcript(mock_response)
        
        assert "He ran a red light" in transcript
        assert "tried to brake" in transcript

    def test_extract_segments_from_video_response(self):
        """Should extract segments/chapters from CU video response."""
        from app.content_understanding_client import extract_video_segments
        
        mock_response = {
            "result": {
                "contents": [{
                    "kind": "audioVisual",
                    "segments": [
                        {"id": 1, "startTime": "0:00:00", "endTime": "0:00:10", "label": "Pre-incident"},
                        {"id": 2, "startTime": "0:00:10", "endTime": "0:00:15", "label": "Impact"},
                        {"id": 3, "startTime": "0:00:15", "endTime": "0:00:30", "label": "Post-incident"},
                    ]
                }]
            }
        }
        
        segments = extract_video_segments(mock_response)
        
        assert len(segments) == 3
        assert segments[0]["label"] == "Pre-incident"
        assert segments[1]["label"] == "Impact"
        assert segments[2]["label"] == "Post-incident"
