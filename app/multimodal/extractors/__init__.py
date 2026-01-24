"""
Extractors Package for Multimodal Content

This package contains specialized extractors for different media types
that parse Azure Content Understanding responses and return structured data.
"""

from .document_extractor import (
    DocumentExtractor,
    extract_document_fields,
    DocumentFields,
)
from .image_extractor import (
    ImageExtractor,
    extract_damage_areas,
    DamageArea,
)
from .video_extractor import (
    VideoExtractor,
    extract_video_data,
    VideoData,
    VideoSegment,
    Keyframe,
)

__all__ = [
    # Document extraction
    "DocumentExtractor",
    "extract_document_fields",
    "DocumentFields",
    # Image extraction
    "ImageExtractor",
    "extract_damage_areas",
    "DamageArea",
    # Video extraction
    "VideoExtractor",
    "extract_video_data",
    "VideoData",
    "VideoSegment",
    "Keyframe",
]
