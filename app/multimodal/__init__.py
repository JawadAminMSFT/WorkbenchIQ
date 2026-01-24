"""
Multimodal Processing Package for Automotive Claims

This package handles the processing of multiple media types (documents, images, videos)
for automotive insurance claims using Azure Content Understanding.

Modules:
- mime_detector: Detects file MIME types and classifies media
- router: Routes files to appropriate Azure CU analyzers
- processor: Orchestrates parallel processing of multiple files
- aggregator: Aggregates results from multiple media sources
- repository: Database operations for claim media data

Extractors:
- extractors.document_extractor: Extracts fields from document analysis
- extractors.image_extractor: Extracts damage areas from image analysis
- extractors.video_extractor: Extracts segments/keyframes from video analysis
"""

# Media type constants
MEDIA_TYPE_DOCUMENT = "document"
MEDIA_TYPE_IMAGE = "image"
MEDIA_TYPE_VIDEO = "video"

# Import classes after constants are defined (they depend on these constants)
from .mime_detector import (
    MimeDetector,
    MediaType,
    DetectionResult,
    detect_media_type,
    DOCUMENT_MIME_TYPES,
    IMAGE_MIME_TYPES,
    VIDEO_MIME_TYPES,
)
from .router import (
    AnalyzerRouter,
    RoutingResult,
    FileSizeError,
    UnsupportedMediaTypeError,
    route_file,
    FALLBACK_DOC_ANALYZER,
    FALLBACK_IMAGE_ANALYZER,
    FALLBACK_VIDEO_ANALYZER,
)
from .processor import (
    MultimodalProcessor,
    FileInfo,
    ProcessingResult,
    BatchResult,
    ProcessingStatus,
    ProgressCallback,
    process_claim_media,
)
from .aggregator import (
    ResultAggregator,
    AggregatedResult,
    VehicleSummary,
    DamageSummary,
    IncidentSummary,
    AggregatedField,
    SourceAttribution,
    ConfidenceLevel,
    aggregate_claim_results,
)
from .repository import (
    ClaimsMediaRepository,
    save_claim_media,
)

# Public exports
__all__ = [
    # Constants
    "MEDIA_TYPE_DOCUMENT",
    "MEDIA_TYPE_IMAGE",
    "MEDIA_TYPE_VIDEO",
    # MIME Detection
    "MimeDetector",
    "MediaType",
    "DetectionResult",
    "detect_media_type",
    "DOCUMENT_MIME_TYPES",
    "IMAGE_MIME_TYPES",
    "VIDEO_MIME_TYPES",
    # Analyzer Routing
    "AnalyzerRouter",
    "RoutingResult",
    "FileSizeError",
    "UnsupportedMediaTypeError",
    "route_file",
    "FALLBACK_DOC_ANALYZER",
    "FALLBACK_IMAGE_ANALYZER",
    "FALLBACK_VIDEO_ANALYZER",
    # Processing Pipeline
    "MultimodalProcessor",
    "FileInfo",
    "ProcessingResult",
    "BatchResult",
    "ProcessingStatus",
    "ProgressCallback",
    "process_claim_media",
    # Result Aggregation
    "ResultAggregator",
    "AggregatedResult",
    "VehicleSummary",
    "DamageSummary",
    "IncidentSummary",
    "AggregatedField",
    "SourceAttribution",
    "ConfidenceLevel",
    "aggregate_claim_results",
    # Repository
    "ClaimsMediaRepository",
    "save_claim_media",
]
