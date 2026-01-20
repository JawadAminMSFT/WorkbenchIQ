"""
Multimodal Processing Pipeline for Automotive Claims

Orchestrates the parallel processing of multiple media files (documents,
images, videos) through Azure Content Understanding, with progress tracking
and retry logic.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from ..config import AutomotiveClaimsSettings, ContentUnderstandingSettings
from ..content_understanding_client import (
    analyze_document,
    analyze_image,
    analyze_video,
    ContentUnderstandingError,
)
from ..utils import setup_logging
from . import MEDIA_TYPE_DOCUMENT, MEDIA_TYPE_IMAGE, MEDIA_TYPE_VIDEO
from .router import AnalyzerRouter, FileSizeError, UnsupportedMediaTypeError
from .extractors import (
    extract_document_fields,
    extract_damage_areas,
    extract_video_data,
    DocumentFields,
    DamageArea,
    VideoData,
)

logger = setup_logging()


class ProcessingStatus(str, Enum):
    """Status of a file processing operation."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class FileInfo:
    """Information about a file to be processed."""
    file_id: str
    filename: str
    file_bytes: bytes
    content_type: Optional[str] = None
    claim_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Result of processing a single file."""
    file_id: str
    filename: str
    media_type: str
    status: ProcessingStatus
    analyzer_id: Optional[str] = None
    raw_result: Optional[Dict[str, Any]] = None
    extracted_data: Optional[Union[DocumentFields, List[DamageArea], VideoData]] = None
    error_message: Optional[str] = None
    processing_time_seconds: float = 0.0
    retry_count: int = 0


@dataclass
class BatchResult:
    """Result of processing a batch of files."""
    total_files: int
    completed: int
    failed: int
    skipped: int
    results: List[ProcessingResult] = field(default_factory=list)
    total_time_seconds: float = 0.0


# Type alias for progress callback
ProgressCallback = Callable[[str, int, int, str], None]  # (file_id, current, total, status)


class MultimodalProcessor:
    """
    Processes multiple media files through Azure Content Understanding.
    
    Features:
    - Parallel processing with configurable concurrency
    - Automatic media type detection and analyzer routing
    - Progress tracking via callbacks
    - Retry logic with exponential backoff
    - Structured extraction of results
    
    Example:
        processor = MultimodalProcessor(auto_settings, cu_settings)
        results = processor.process_files(files, progress_callback=update_ui)
    """
    
    def __init__(
        self,
        auto_settings: Optional[AutomotiveClaimsSettings] = None,
        cu_settings: Optional[ContentUnderstandingSettings] = None,
        max_workers: int = 4,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
    ):
        """
        Initialize the multimodal processor.
        
        Args:
            auto_settings: Automotive claims settings (loads from env if None)
            cu_settings: Content Understanding settings (loads from env if None)
            max_workers: Maximum concurrent processing threads
            max_retries: Maximum retry attempts for failed analyses
            retry_backoff: Backoff multiplier for retries (seconds)
        """
        self._auto_settings = auto_settings
        self._cu_settings = cu_settings
        self._max_workers = max_workers
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff
        self._router = AnalyzerRouter(auto_settings)
    
    @property
    def auto_settings(self) -> AutomotiveClaimsSettings:
        """Get automotive claims settings."""
        if self._auto_settings is None:
            self._auto_settings = AutomotiveClaimsSettings.from_env()
        return self._auto_settings
    
    @property
    def cu_settings(self) -> ContentUnderstandingSettings:
        """Get Content Understanding settings."""
        if self._cu_settings is None:
            from ..config import load_settings
            settings = load_settings()
            self._cu_settings = settings.content_understanding
        return self._cu_settings
    
    def process_file(
        self,
        file_info: FileInfo,
        use_fallback_analyzer: bool = False,
    ) -> ProcessingResult:
        """
        Process a single file through Content Understanding.
        
        Args:
            file_info: Information about the file to process
            use_fallback_analyzer: Use prebuilt fallback analyzers
            
        Returns:
            ProcessingResult with status and extracted data
        """
        start_time = time.time()
        
        try:
            # Route the file to appropriate analyzer
            routing = self._router.route_file(
                file_info.file_bytes,
                file_info.filename,
                file_info.content_type,
                validate_size=True,
                use_fallback=use_fallback_analyzer,
            )
            
            media_type = routing.media_type
            analyzer_id = routing.analyzer_id
            
            logger.info(
                "Processing %s as %s with analyzer %s",
                file_info.filename, media_type, analyzer_id
            )
            
            # Call appropriate analyze function with retries
            raw_result = self._analyze_with_retry(
                file_info, media_type, analyzer_id
            )
            
            # Extract structured data based on media type
            extracted_data = self._extract_data(raw_result, media_type)
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                file_id=file_info.file_id,
                filename=file_info.filename,
                media_type=media_type,
                status=ProcessingStatus.COMPLETED,
                analyzer_id=analyzer_id,
                raw_result=raw_result,
                extracted_data=extracted_data,
                processing_time_seconds=processing_time,
            )
            
        except FileSizeError as e:
            logger.warning("File size error for %s: %s", file_info.filename, e)
            return ProcessingResult(
                file_id=file_info.file_id,
                filename=file_info.filename,
                media_type="unknown",
                status=ProcessingStatus.SKIPPED,
                error_message=str(e),
                processing_time_seconds=time.time() - start_time,
            )
            
        except UnsupportedMediaTypeError as e:
            logger.warning("Unsupported media type for %s: %s", file_info.filename, e)
            return ProcessingResult(
                file_id=file_info.file_id,
                filename=file_info.filename,
                media_type="unknown",
                status=ProcessingStatus.SKIPPED,
                error_message=str(e),
                processing_time_seconds=time.time() - start_time,
            )
            
        except Exception as e:
            logger.error("Failed to process %s: %s", file_info.filename, e)
            return ProcessingResult(
                file_id=file_info.file_id,
                filename=file_info.filename,
                media_type="unknown",
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                processing_time_seconds=time.time() - start_time,
            )
    
    def process_files(
        self,
        files: List[FileInfo],
        progress_callback: Optional[ProgressCallback] = None,
        use_fallback_analyzer: bool = False,
    ) -> BatchResult:
        """
        Process multiple files in parallel.
        
        Args:
            files: List of files to process
            progress_callback: Optional callback for progress updates
            use_fallback_analyzer: Use prebuilt fallback analyzers
            
        Returns:
            BatchResult with all processing results
        """
        start_time = time.time()
        results: List[ProcessingResult] = []
        total_files = len(files)
        
        if total_files == 0:
            return BatchResult(
                total_files=0,
                completed=0,
                failed=0,
                skipped=0,
                results=[],
                total_time_seconds=0.0,
            )
        
        # Process files in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(
                    self.process_file, file_info, use_fallback_analyzer
                ): file_info
                for file_info in files
            }
            
            # Collect results as they complete
            completed_count = 0
            for future in as_completed(future_to_file):
                file_info = future_to_file[future]
                completed_count += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Call progress callback
                    if progress_callback:
                        progress_callback(
                            result.file_id,
                            completed_count,
                            total_files,
                            result.status.value,
                        )
                        
                except Exception as e:
                    logger.error("Unexpected error processing %s: %s", file_info.filename, e)
                    results.append(ProcessingResult(
                        file_id=file_info.file_id,
                        filename=file_info.filename,
                        media_type="unknown",
                        status=ProcessingStatus.FAILED,
                        error_message=str(e),
                    ))
                    
                    if progress_callback:
                        progress_callback(
                            file_info.file_id,
                            completed_count,
                            total_files,
                            "failed",
                        )
        
        # Calculate summary
        completed = sum(1 for r in results if r.status == ProcessingStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == ProcessingStatus.FAILED)
        skipped = sum(1 for r in results if r.status == ProcessingStatus.SKIPPED)
        
        return BatchResult(
            total_files=total_files,
            completed=completed,
            failed=failed,
            skipped=skipped,
            results=results,
            total_time_seconds=time.time() - start_time,
        )
    
    def _analyze_with_retry(
        self,
        file_info: FileInfo,
        media_type: str,
        analyzer_id: str,
    ) -> Dict[str, Any]:
        """Analyze a file with retry logic."""
        last_error: Optional[Exception] = None
        
        for attempt in range(1, self._max_retries + 1):
            try:
                if media_type == MEDIA_TYPE_DOCUMENT:
                    return analyze_document(
                        settings=self.cu_settings,
                        file_path="",
                        file_bytes=file_info.file_bytes,
                        output_markdown=True,
                    )
                elif media_type == MEDIA_TYPE_IMAGE:
                    return analyze_image(
                        settings=self.cu_settings,
                        file_bytes=file_info.file_bytes,
                        analyzer_id=analyzer_id,
                    )
                elif media_type == MEDIA_TYPE_VIDEO:
                    return analyze_video(
                        settings=self.cu_settings,
                        file_bytes=file_info.file_bytes,
                        analyzer_id=analyzer_id,
                    )
                else:
                    raise ValueError(f"Unknown media type: {media_type}")
                    
            except ContentUnderstandingError as e:
                last_error = e
                logger.warning(
                    "Attempt %d/%d failed for %s: %s",
                    attempt, self._max_retries, file_info.filename, e
                )
                
                if attempt < self._max_retries:
                    sleep_time = self._retry_backoff ** attempt
                    time.sleep(sleep_time)
        
        raise last_error or ContentUnderstandingError("Analysis failed after retries")
    
    def _extract_data(
        self,
        raw_result: Dict[str, Any],
        media_type: str,
    ) -> Optional[Union[DocumentFields, List[DamageArea], VideoData]]:
        """Extract structured data from raw result based on media type."""
        try:
            if media_type == MEDIA_TYPE_DOCUMENT:
                return extract_document_fields(raw_result)
            elif media_type == MEDIA_TYPE_IMAGE:
                # For images, return the full ImageAnalysis but the interface
                # expects List[DamageArea] for compatibility
                from .extractors.image_extractor import ImageExtractor
                extractor = ImageExtractor()
                analysis = extractor.extract(raw_result)
                return analysis.damage_areas if analysis.damage_areas else []
            elif media_type == MEDIA_TYPE_VIDEO:
                return extract_video_data(raw_result)
            else:
                return None
        except Exception as e:
            logger.warning("Failed to extract data from result: %s", e)
            return None


# Convenience function for simple usage
def process_claim_media(
    files: List[FileInfo],
    progress_callback: Optional[ProgressCallback] = None,
) -> BatchResult:
    """
    Process claim media files through Content Understanding.
    
    Convenience function that creates a processor and processes files.
    
    Args:
        files: List of files to process
        progress_callback: Optional callback for progress updates
        
    Returns:
        BatchResult with all processing results
    """
    processor = MultimodalProcessor()
    return processor.process_files(files, progress_callback)


__all__ = [
    "MultimodalProcessor",
    "FileInfo",
    "ProcessingResult",
    "BatchResult",
    "ProcessingStatus",
    "ProgressCallback",
    "process_claim_media",
]
