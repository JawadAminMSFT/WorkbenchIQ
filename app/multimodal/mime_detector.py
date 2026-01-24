"""
MIME Type Detection for Multimodal Content

This module provides file type detection for the automotive claims multimodal
processing pipeline. It detects whether uploaded content is a document, image,
or video based on MIME type and file extension.
"""

import mimetypes
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

from . import MEDIA_TYPE_DOCUMENT, MEDIA_TYPE_IMAGE, MEDIA_TYPE_VIDEO


class MediaType(str, Enum):
    """Supported media types for multimodal processing."""
    DOCUMENT = MEDIA_TYPE_DOCUMENT
    IMAGE = MEDIA_TYPE_IMAGE
    VIDEO = MEDIA_TYPE_VIDEO
    UNKNOWN = "unknown"


# MIME type to media type mappings
# Documents: PDFs, Word documents, text files
DOCUMENT_MIME_TYPES = frozenset({
    # PDF
    "application/pdf",
    # Microsoft Word
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    # Microsoft Excel (repair estimates often in spreadsheets)
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    # Text files
    "text/plain",
    "text/csv",
    # Rich text
    "application/rtf",
    "text/rtf",
})

# Images: Common image formats supported by Azure Content Understanding
IMAGE_MIME_TYPES = frozenset({
    "image/jpeg",
    "image/jpg",  # Non-standard but common
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/tiff",
    "image/heic",
    "image/heif",
})

# Videos: Common video formats supported by Azure Content Understanding
VIDEO_MIME_TYPES = frozenset({
    "video/mp4",
    "video/quicktime",  # .mov files
    "video/x-msvideo",  # .avi files
    "video/webm",
    "video/x-ms-wmv",
    "video/mpeg",
    "video/3gpp",
    "video/x-matroska",  # .mkv files
})

# File extension to media type mappings (fallback)
EXTENSION_TO_MEDIA_TYPE = {
    # Documents
    ".pdf": MediaType.DOCUMENT,
    ".doc": MediaType.DOCUMENT,
    ".docx": MediaType.DOCUMENT,
    ".xls": MediaType.DOCUMENT,
    ".xlsx": MediaType.DOCUMENT,
    ".txt": MediaType.DOCUMENT,
    ".csv": MediaType.DOCUMENT,
    ".rtf": MediaType.DOCUMENT,
    # Images
    ".jpg": MediaType.IMAGE,
    ".jpeg": MediaType.IMAGE,
    ".png": MediaType.IMAGE,
    ".gif": MediaType.IMAGE,
    ".webp": MediaType.IMAGE,
    ".bmp": MediaType.IMAGE,
    ".tiff": MediaType.IMAGE,
    ".tif": MediaType.IMAGE,
    ".heic": MediaType.IMAGE,
    ".heif": MediaType.IMAGE,
    # Videos
    ".mp4": MediaType.VIDEO,
    ".mov": MediaType.VIDEO,
    ".avi": MediaType.VIDEO,
    ".webm": MediaType.VIDEO,
    ".wmv": MediaType.VIDEO,
    ".mpeg": MediaType.VIDEO,
    ".mpg": MediaType.VIDEO,
    ".3gp": MediaType.VIDEO,
    ".mkv": MediaType.VIDEO,
}

# Magic bytes (file signatures) for common formats
# Format: (offset, signature_bytes, media_type)
MAGIC_SIGNATURES = [
    # PDF
    (0, b"%PDF", MediaType.DOCUMENT),
    # JPEG
    (0, b"\xff\xd8\xff", MediaType.IMAGE),
    # PNG
    (0, b"\x89PNG\r\n\x1a\n", MediaType.IMAGE),
    # GIF
    (0, b"GIF87a", MediaType.IMAGE),
    (0, b"GIF89a", MediaType.IMAGE),
    # WebP
    (8, b"WEBP", MediaType.IMAGE),
    # BMP
    (0, b"BM", MediaType.IMAGE),
    # TIFF (little-endian)
    (0, b"II\x2a\x00", MediaType.IMAGE),
    # TIFF (big-endian)
    (0, b"MM\x00\x2a", MediaType.IMAGE),
    # MP4 / MOV (ftyp box)
    (4, b"ftyp", MediaType.VIDEO),
    # AVI
    (0, b"RIFF", MediaType.VIDEO),  # Note: RIFF is also used by WAV, but we check context
    # WebM/MKV
    (0, b"\x1a\x45\xdf\xa3", MediaType.VIDEO),
    # MPEG
    (0, b"\x00\x00\x01\xba", MediaType.VIDEO),
    (0, b"\x00\x00\x01\xb3", MediaType.VIDEO),
    # DOCX/XLSX (ZIP-based formats - need additional check)
    (0, b"PK\x03\x04", MediaType.DOCUMENT),  # ZIP signature
]


@dataclass
class DetectionResult:
    """Result of MIME type detection."""
    media_type: MediaType
    mime_type: Optional[str]
    confidence: float  # 0.0 to 1.0
    detection_method: str  # "magic", "mime", "extension", "fallback"


class MimeDetector:
    """
    Detects media type (document, image, video) from file content and metadata.
    
    Detection strategy (in order of preference):
    1. Magic bytes (file signature) - most reliable
    2. MIME type from content-type header if available
    3. File extension fallback
    
    Example:
        detector = MimeDetector()
        result = detector.detect(file_bytes, "claim_photo.jpg")
        print(result.media_type)  # MediaType.IMAGE
    """
    
    def __init__(self):
        """Initialize the MIME detector."""
        # Ensure mimetypes database is initialized
        mimetypes.init()
    
    def detect(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
    ) -> DetectionResult:
        """
        Detect the media type of a file.
        
        Args:
            file_bytes: Raw file content (at least first 16 bytes needed)
            filename: Original filename with extension
            content_type: Optional MIME type from HTTP Content-Type header
            
        Returns:
            DetectionResult with media_type, mime_type, confidence, and method
        """
        # Strategy 1: Check magic bytes first (most reliable)
        magic_result = self._detect_from_magic(file_bytes)
        if magic_result and magic_result.media_type != MediaType.UNKNOWN:
            return magic_result
        
        # Strategy 2: Check provided content-type
        if content_type:
            mime_result = self._detect_from_mime(content_type)
            if mime_result.media_type != MediaType.UNKNOWN:
                return mime_result
        
        # Strategy 3: Check file extension
        ext_result = self._detect_from_extension(filename)
        if ext_result.media_type != MediaType.UNKNOWN:
            return ext_result
        
        # Strategy 4: Try to guess MIME type from filename
        guessed_mime, _ = mimetypes.guess_type(filename)
        if guessed_mime:
            mime_result = self._detect_from_mime(guessed_mime)
            if mime_result.media_type != MediaType.UNKNOWN:
                mime_result.detection_method = "guessed_mime"
                return mime_result
        
        # Fallback: Unknown
        return DetectionResult(
            media_type=MediaType.UNKNOWN,
            mime_type=None,
            confidence=0.0,
            detection_method="fallback",
        )
    
    def detect_media_type(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Simplified detection returning just the media type string.
        
        Args:
            file_bytes: Raw file content
            filename: Original filename with extension
            content_type: Optional MIME type from HTTP header
            
        Returns:
            Media type string: "document", "image", "video", or "unknown"
        """
        result = self.detect(file_bytes, filename, content_type)
        return result.media_type.value
    
    def _detect_from_magic(self, file_bytes: bytes) -> Optional[DetectionResult]:
        """Detect media type from magic bytes (file signature)."""
        if not file_bytes or len(file_bytes) < 4:
            return None
        
        for offset, signature, media_type in MAGIC_SIGNATURES:
            if len(file_bytes) >= offset + len(signature):
                if file_bytes[offset:offset + len(signature)] == signature:
                    # Special handling for ZIP-based formats (DOCX, XLSX)
                    if signature == b"PK\x03\x04":
                        # Check if it's an Office document by looking for specific markers
                        if b"word/" in file_bytes[:1000] or b"xl/" in file_bytes[:1000]:
                            return DetectionResult(
                                media_type=MediaType.DOCUMENT,
                                mime_type="application/vnd.openxmlformats-officedocument",
                                confidence=0.9,
                                detection_method="magic",
                            )
                        # Could be other ZIP file - lower confidence
                        continue
                    
                    # Special handling for RIFF (could be AVI or WAV)
                    if signature == b"RIFF" and len(file_bytes) >= 12:
                        if file_bytes[8:12] == b"AVI ":
                            return DetectionResult(
                                media_type=MediaType.VIDEO,
                                mime_type="video/x-msvideo",
                                confidence=0.95,
                                detection_method="magic",
                            )
                        # Not AVI, skip
                        continue
                    
                    return DetectionResult(
                        media_type=media_type,
                        mime_type=None,  # We know the type but not exact MIME
                        confidence=0.95,
                        detection_method="magic",
                    )
        
        return None
    
    def _detect_from_mime(self, mime_type: str) -> DetectionResult:
        """Detect media type from MIME type string."""
        mime_lower = mime_type.lower().split(";")[0].strip()
        
        if mime_lower in DOCUMENT_MIME_TYPES:
            return DetectionResult(
                media_type=MediaType.DOCUMENT,
                mime_type=mime_lower,
                confidence=0.9,
                detection_method="mime",
            )
        
        if mime_lower in IMAGE_MIME_TYPES:
            return DetectionResult(
                media_type=MediaType.IMAGE,
                mime_type=mime_lower,
                confidence=0.9,
                detection_method="mime",
            )
        
        if mime_lower in VIDEO_MIME_TYPES:
            return DetectionResult(
                media_type=MediaType.VIDEO,
                mime_type=mime_lower,
                confidence=0.9,
                detection_method="mime",
            )
        
        # Check MIME type prefix as fallback
        if mime_lower.startswith("image/"):
            return DetectionResult(
                media_type=MediaType.IMAGE,
                mime_type=mime_lower,
                confidence=0.7,
                detection_method="mime_prefix",
            )
        
        if mime_lower.startswith("video/"):
            return DetectionResult(
                media_type=MediaType.VIDEO,
                mime_type=mime_lower,
                confidence=0.7,
                detection_method="mime_prefix",
            )
        
        if mime_lower.startswith("text/") or mime_lower.startswith("application/"):
            # Many document types start with these
            return DetectionResult(
                media_type=MediaType.DOCUMENT,
                mime_type=mime_lower,
                confidence=0.5,
                detection_method="mime_prefix",
            )
        
        return DetectionResult(
            media_type=MediaType.UNKNOWN,
            mime_type=mime_lower,
            confidence=0.0,
            detection_method="mime",
        )
    
    def _detect_from_extension(self, filename: str) -> DetectionResult:
        """Detect media type from file extension."""
        if not filename:
            return DetectionResult(
                media_type=MediaType.UNKNOWN,
                mime_type=None,
                confidence=0.0,
                detection_method="extension",
            )
        
        ext = Path(filename).suffix.lower()
        
        if ext in EXTENSION_TO_MEDIA_TYPE:
            media_type = EXTENSION_TO_MEDIA_TYPE[ext]
            # Try to get MIME type from extension
            guessed_mime, _ = mimetypes.guess_type(filename)
            
            return DetectionResult(
                media_type=media_type,
                mime_type=guessed_mime,
                confidence=0.8,
                detection_method="extension",
            )
        
        return DetectionResult(
            media_type=MediaType.UNKNOWN,
            mime_type=None,
            confidence=0.0,
            detection_method="extension",
        )


# Module-level convenience function
def detect_media_type(
    file_bytes: bytes,
    filename: str,
    content_type: Optional[str] = None,
) -> str:
    """
    Detect the media type of a file.
    
    Convenience function that creates a MimeDetector and returns just the type.
    
    Args:
        file_bytes: Raw file content
        filename: Original filename with extension
        content_type: Optional MIME type from HTTP header
        
    Returns:
        Media type string: "document", "image", "video", or "unknown"
    """
    detector = MimeDetector()
    return detector.detect_media_type(file_bytes, filename, content_type)


__all__ = [
    "MimeDetector",
    "MediaType",
    "DetectionResult",
    "detect_media_type",
    "DOCUMENT_MIME_TYPES",
    "IMAGE_MIME_TYPES",
    "VIDEO_MIME_TYPES",
]
