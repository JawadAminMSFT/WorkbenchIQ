"""
Analyzer Router for Multimodal Content

This module routes files to the appropriate Azure Content Understanding analyzer
based on their media type (document, image, video).
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from ..config import AutomotiveClaimsSettings
from . import MEDIA_TYPE_DOCUMENT, MEDIA_TYPE_IMAGE, MEDIA_TYPE_VIDEO
from .mime_detector import MimeDetector, MediaType, DetectionResult


# Fallback analyzer IDs (prebuilt Azure CU analyzers)
FALLBACK_DOC_ANALYZER = "prebuilt-document"
FALLBACK_IMAGE_ANALYZER = "prebuilt-image"
FALLBACK_VIDEO_ANALYZER = "prebuilt-video"

# Default file size limits (in bytes)
DEFAULT_IMAGE_MAX_SIZE_MB = 20  # 20 MB
DEFAULT_VIDEO_MAX_SIZE_MB = 500  # 500 MB (Azure CU limit)
DEFAULT_VIDEO_MAX_DURATION_MINUTES = 30  # 30 minutes


class FileSizeError(Exception):
    """Raised when a file exceeds the allowed size limit."""
    pass


class UnsupportedMediaTypeError(Exception):
    """Raised when a file has an unsupported media type."""
    pass


@dataclass
class RoutingResult:
    """Result of file routing decision."""
    media_type: str
    analyzer_id: str
    is_custom_analyzer: bool
    file_size_bytes: int
    detection_confidence: float


class AnalyzerRouter:
    """
    Routes files to appropriate Azure Content Understanding analyzers.
    
    The router determines the correct analyzer based on:
    1. Media type detection (document, image, video)
    2. Configuration settings (custom vs prebuilt analyzers)
    3. File size validation
    
    Example:
        router = AnalyzerRouter(settings)
        result = router.route_file(file_bytes, "damage_photo.jpg")
        print(result.analyzer_id)  # "autoClaimsImageAnalyzer"
    """
    
    def __init__(
        self,
        settings: Optional[AutomotiveClaimsSettings] = None,
        mime_detector: Optional[MimeDetector] = None,
    ):
        """
        Initialize the analyzer router.
        
        Args:
            settings: Automotive claims settings with analyzer IDs
            mime_detector: Optional custom MimeDetector instance
        """
        self._settings = settings
        self._detector = mime_detector or MimeDetector()
    
    @property
    def settings(self) -> AutomotiveClaimsSettings:
        """Get settings, loading from env if not provided."""
        if self._settings is None:
            self._settings = AutomotiveClaimsSettings.from_env()
        return self._settings
    
    def get_analyzer_id(
        self,
        media_type: str,
        use_fallback: bool = False,
    ) -> str:
        """
        Get the analyzer ID for a given media type.
        
        Args:
            media_type: The media type ("document", "image", "video")
            use_fallback: Force use of prebuilt fallback analyzers
            
        Returns:
            Analyzer ID string
            
        Raises:
            UnsupportedMediaTypeError: If media type is not supported
        """
        settings = self.settings
        
        if media_type == MEDIA_TYPE_DOCUMENT:
            if use_fallback or not settings.doc_analyzer:
                return FALLBACK_DOC_ANALYZER
            return settings.doc_analyzer
        
        if media_type == MEDIA_TYPE_IMAGE:
            if use_fallback or not settings.image_analyzer:
                return FALLBACK_IMAGE_ANALYZER
            return settings.image_analyzer
        
        if media_type == MEDIA_TYPE_VIDEO:
            if use_fallback or not settings.video_analyzer:
                return FALLBACK_VIDEO_ANALYZER
            return settings.video_analyzer
        
        raise UnsupportedMediaTypeError(
            f"Unsupported media type: {media_type}. "
            f"Supported types: {MEDIA_TYPE_DOCUMENT}, {MEDIA_TYPE_IMAGE}, {MEDIA_TYPE_VIDEO}"
        )
    
    def validate_file_size(
        self,
        file_bytes: bytes,
        media_type: str,
    ) -> None:
        """
        Validate that a file is within size limits.
        
        Args:
            file_bytes: The file content
            media_type: The detected media type
            
        Raises:
            FileSizeError: If file exceeds size limit for its type
        """
        file_size_bytes = len(file_bytes)
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        settings = self.settings
        
        if media_type == MEDIA_TYPE_IMAGE:
            max_size_mb = settings.image_max_size_mb or DEFAULT_IMAGE_MAX_SIZE_MB
            if file_size_mb > max_size_mb:
                raise FileSizeError(
                    f"Image file size ({file_size_mb:.1f} MB) exceeds limit of {max_size_mb} MB"
                )
        
        if media_type == MEDIA_TYPE_VIDEO:
            max_size_mb = DEFAULT_VIDEO_MAX_SIZE_MB  # Video size limit not configurable
            if file_size_mb > max_size_mb:
                raise FileSizeError(
                    f"Video file size ({file_size_mb:.1f} MB) exceeds limit of {max_size_mb} MB"
                )
        
        # Documents don't have strict size limits (Azure CU handles large docs)
    
    def route_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
        validate_size: bool = True,
        use_fallback: bool = False,
    ) -> RoutingResult:
        """
        Route a file to the appropriate analyzer.
        
        This is the main entry point for file routing. It:
        1. Detects the media type from file content
        2. Validates file size if enabled
        3. Selects the appropriate analyzer
        
        Args:
            file_bytes: Raw file content
            filename: Original filename with extension
            content_type: Optional MIME type from HTTP header
            validate_size: Whether to check file size limits
            use_fallback: Force use of prebuilt fallback analyzers
            
        Returns:
            RoutingResult with media_type, analyzer_id, and metadata
            
        Raises:
            FileSizeError: If file exceeds size limit
            UnsupportedMediaTypeError: If media type cannot be determined
        """
        # Detect media type
        detection = self._detector.detect(file_bytes, filename, content_type)
        
        if detection.media_type == MediaType.UNKNOWN:
            raise UnsupportedMediaTypeError(
                f"Could not determine media type for file: {filename}. "
                "Supported formats: PDF, DOCX, JPEG, PNG, MP4, MOV, etc."
            )
        
        media_type = detection.media_type.value
        
        # Validate file size
        if validate_size:
            self.validate_file_size(file_bytes, media_type)
        
        # Get analyzer ID
        analyzer_id = self.get_analyzer_id(media_type, use_fallback)
        
        # Determine if using custom analyzer
        settings = self.settings
        is_custom = False
        if media_type == MEDIA_TYPE_DOCUMENT:
            is_custom = analyzer_id == settings.doc_analyzer
        elif media_type == MEDIA_TYPE_IMAGE:
            is_custom = analyzer_id == settings.image_analyzer
        elif media_type == MEDIA_TYPE_VIDEO:
            is_custom = analyzer_id == settings.video_analyzer
        
        return RoutingResult(
            media_type=media_type,
            analyzer_id=analyzer_id,
            is_custom_analyzer=is_custom,
            file_size_bytes=len(file_bytes),
            detection_confidence=detection.confidence,
        )


# Module-level convenience function
def route_file(
    file_bytes: bytes,
    filename: str,
    settings: Optional[AutomotiveClaimsSettings] = None,
    content_type: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Route a file to the appropriate analyzer.
    
    Convenience function that returns just (media_type, analyzer_id).
    
    Args:
        file_bytes: Raw file content
        filename: Original filename with extension
        settings: Optional settings (loads from env if not provided)
        content_type: Optional MIME type from HTTP header
        
    Returns:
        Tuple of (media_type, analyzer_id)
    """
    router = AnalyzerRouter(settings)
    result = router.route_file(file_bytes, filename, content_type)
    return (result.media_type, result.analyzer_id)


__all__ = [
    "AnalyzerRouter",
    "RoutingResult",
    "FileSizeError",
    "UnsupportedMediaTypeError",
    "route_file",
    "FALLBACK_DOC_ANALYZER",
    "FALLBACK_IMAGE_ANALYZER",
    "FALLBACK_VIDEO_ANALYZER",
]
