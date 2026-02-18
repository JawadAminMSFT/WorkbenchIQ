"""
Repository for Automotive Claims Media Data

Provides database persistence for processed claim media data including
damage areas, keyframes, repair items, and aggregated results.
"""

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from ..database import get_pool
from ..utils import setup_logging
from .processor import ProcessingResult, ProcessingStatus, BatchResult
from .aggregator import AggregatedResult, DamageSummary
from .extractors import DamageArea, VideoData, DocumentFields

# Import ClaimAssessment for type checking, avoid circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..claims.engine import ClaimAssessment

logger = setup_logging()


class ClaimsMediaRepository:
    """
    Repository for persisting automotive claims media data.
    
    Handles storage of:
    - Processed media files and their results
    - Extracted damage areas from images
    - Video keyframes and segments
    - Repair estimate line items
    - Aggregated claim results
    
    Example:
        repo = ClaimsMediaRepository()
        await repo.save_processing_result(claim_id, result)
    """
    
    # SQL for creating tables if they don't exist
    CREATE_TABLES_SQL = """
    -- Claim media files
    CREATE TABLE IF NOT EXISTS claim_media (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        claim_id VARCHAR(255) NOT NULL,
        file_id VARCHAR(255) NOT NULL,
        filename VARCHAR(512) NOT NULL,
        media_type VARCHAR(50) NOT NULL,
        analyzer_id VARCHAR(255),
        status VARCHAR(50) NOT NULL,
        error_message TEXT,
        processing_time_seconds FLOAT,
        raw_result JSONB,
        extracted_data JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(claim_id, file_id)
    );
    
    CREATE INDEX IF NOT EXISTS idx_claim_media_claim_id ON claim_media(claim_id);
    
    -- Damage areas from images
    CREATE TABLE IF NOT EXISTS claim_damage_areas (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        claim_id VARCHAR(255) NOT NULL,
        media_id UUID REFERENCES claim_media(id) ON DELETE CASCADE,
        component VARCHAR(255),
        damage_type VARCHAR(255),
        severity VARCHAR(50),
        confidence FLOAT,
        bounding_box JSONB,
        description TEXT,
        estimated_cost FLOAT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_damage_areas_claim_id ON claim_damage_areas(claim_id);
    
    -- Video keyframes
    CREATE TABLE IF NOT EXISTS claim_keyframes (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        claim_id VARCHAR(255) NOT NULL,
        media_id UUID REFERENCES claim_media(id) ON DELETE CASCADE,
        timestamp_seconds FLOAT NOT NULL,
        frame_data BYTEA,
        frame_url TEXT,
        description TEXT,
        objects_detected JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_keyframes_claim_id ON claim_keyframes(claim_id);
    
    -- Video segments
    CREATE TABLE IF NOT EXISTS claim_video_segments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        claim_id VARCHAR(255) NOT NULL,
        media_id UUID REFERENCES claim_media(id) ON DELETE CASCADE,
        start_time FLOAT NOT NULL,
        end_time FLOAT NOT NULL,
        event_type VARCHAR(100),
        description TEXT,
        confidence FLOAT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_video_segments_claim_id ON claim_video_segments(claim_id);
    
    -- Repair estimate line items
    CREATE TABLE IF NOT EXISTS claim_repair_items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        claim_id VARCHAR(255) NOT NULL,
        media_id UUID REFERENCES claim_media(id) ON DELETE CASCADE,
        item_description VARCHAR(512) NOT NULL,
        item_type VARCHAR(50),
        quantity INT DEFAULT 1,
        unit_price FLOAT,
        total_price FLOAT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_repair_items_claim_id ON claim_repair_items(claim_id);
    
    -- Aggregated claim summaries
    CREATE TABLE IF NOT EXISTS claim_summaries (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        claim_id VARCHAR(255) NOT NULL UNIQUE,
        vehicle_info JSONB,
        damage_summary JSONB,
        incident_info JSONB,
        repair_estimate JSONB,
        parties JSONB,
        source_files JSONB,
        conflicts_detected INT DEFAULT 0,
        confidence_score FLOAT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Claim policy assessments
    CREATE TABLE IF NOT EXISTS claim_assessments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        application_id VARCHAR(255) NOT NULL UNIQUE,
        assessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        
        -- Individual assessments stored as JSON
        damage_assessment JSONB,
        liability_assessment JSONB,
        fraud_assessment JSONB,
        payout_assessment JSONB,
        
        -- Overall recommendation
        overall_recommendation VARCHAR(50),
        requires_adjuster_review BOOLEAN DEFAULT false,
        confidence_score FLOAT,
        
        -- All policy citations
        policy_citations JSONB,
        
        -- Adjuster decision
        adjuster_decision VARCHAR(50),
        adjuster_notes TEXT,
        decided_at TIMESTAMP WITH TIME ZONE,
        
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_assessments_app_id ON claim_assessments(application_id);
    CREATE INDEX IF NOT EXISTS idx_assessments_recommendation ON claim_assessments(overall_recommendation);
    """
    
    def __init__(self, pool=None):
        """
        Initialize the repository.
        
        Args:
            pool: Optional database connection pool. If None, uses default pool.
        """
        self._pool = pool
    
    @property
    def pool(self):
        """Get the database connection pool."""
        if self._pool is None:
            self._pool = get_pool()
        return self._pool
    
    async def initialize_tables(self) -> None:
        """Create database tables if they don't exist."""
        async with self.pool.connection() as conn:
            await conn.execute(self.CREATE_TABLES_SQL)
            logger.info("Claim media tables initialized")
    
    async def save_processing_result(
        self,
        claim_id: str,
        result: ProcessingResult,
    ) -> str:
        """
        Save a processing result to the database.
        
        Args:
            claim_id: The claim identifier
            result: The processing result to save
            
        Returns:
            The media record ID
        """
        # Serialize extracted data
        extracted_json = None
        if result.extracted_data:
            if hasattr(result.extracted_data, "__dataclass_fields__"):
                extracted_json = asdict(result.extracted_data)
            elif isinstance(result.extracted_data, list):
                extracted_json = [asdict(item) for item in result.extracted_data]
            else:
                extracted_json = result.extracted_data
        
        async with self.pool.connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO claim_media 
                    (claim_id, file_id, filename, media_type, analyzer_id, 
                     status, error_message, processing_time_seconds, 
                     raw_result, extracted_data)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (claim_id, file_id) DO UPDATE SET
                    filename = EXCLUDED.filename,
                    media_type = EXCLUDED.media_type,
                    analyzer_id = EXCLUDED.analyzer_id,
                    status = EXCLUDED.status,
                    error_message = EXCLUDED.error_message,
                    processing_time_seconds = EXCLUDED.processing_time_seconds,
                    raw_result = EXCLUDED.raw_result,
                    extracted_data = EXCLUDED.extracted_data
                RETURNING id
                """,
                claim_id,
                result.file_id,
                result.filename,
                result.media_type,
                result.analyzer_id,
                result.status.value,
                result.error_message,
                result.processing_time_seconds,
                json.dumps(result.raw_result) if result.raw_result else None,
                json.dumps(extracted_json) if extracted_json else None,
            )
            
            media_id = str(row["id"])
            
            # Save related data based on extracted data type
            if result.status == ProcessingStatus.COMPLETED and result.extracted_data:
                if isinstance(result.extracted_data, list):
                    # Damage areas from images
                    await self._save_damage_areas(
                        conn, claim_id, media_id, result.extracted_data
                    )
                elif isinstance(result.extracted_data, VideoData):
                    # Video data
                    await self._save_video_data(
                        conn, claim_id, media_id, result.extracted_data
                    )
                elif isinstance(result.extracted_data, DocumentFields):
                    # Document data (repair items)
                    await self._save_document_data(
                        conn, claim_id, media_id, result.extracted_data
                    )
            
            return media_id
    
    async def save_batch_result(
        self,
        claim_id: str,
        batch: BatchResult,
    ) -> List[str]:
        """
        Save all results from a batch processing operation.
        
        Args:
            claim_id: The claim identifier
            batch: The batch processing result
            
        Returns:
            List of media record IDs
        """
        media_ids = []
        for result in batch.results:
            media_id = await self.save_processing_result(claim_id, result)
            media_ids.append(media_id)
        return media_ids
    
    async def save_aggregated_result(
        self,
        aggregated: AggregatedResult,
    ) -> str:
        """
        Save an aggregated result to the database.
        
        Args:
            aggregated: The aggregated result to save
            
        Returns:
            The summary record ID
        """
        claim_id = aggregated.claim_id or str(uuid4())
        
        # Serialize vehicle info
        vehicle_json = {}
        for field_name in ["vin", "make", "model", "year", "color", "license_plate"]:
            field = getattr(aggregated.vehicle, field_name)
            if field.value:
                vehicle_json[field_name] = field.value
        
        # Serialize damage summary
        damage_json = {
            "overall_severity": aggregated.damage.overall_severity,
            "severity_score": aggregated.damage.severity_score,
            "total_estimated_cost": aggregated.damage.total_estimated_cost,
            "damaged_components": list(aggregated.damage.damaged_components),
        }
        
        # Serialize incident info
        incident_json = {}
        for field_name in ["date", "time", "location", "description", 
                          "weather_conditions", "fault_determination"]:
            field = getattr(aggregated.incident, field_name)
            if field.value:
                incident_json[field_name] = field.value
        
        async with self.pool.connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO claim_summaries 
                    (claim_id, vehicle_info, damage_summary, incident_info,
                     repair_estimate, parties, source_files, 
                     conflicts_detected, confidence_score)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (claim_id) DO UPDATE SET
                    vehicle_info = EXCLUDED.vehicle_info,
                    damage_summary = EXCLUDED.damage_summary,
                    incident_info = EXCLUDED.incident_info,
                    repair_estimate = EXCLUDED.repair_estimate,
                    parties = EXCLUDED.parties,
                    source_files = EXCLUDED.source_files,
                    conflicts_detected = EXCLUDED.conflicts_detected,
                    confidence_score = EXCLUDED.confidence_score,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                claim_id,
                json.dumps(vehicle_json),
                json.dumps(damage_json),
                json.dumps(incident_json),
                json.dumps(aggregated.repair_estimate) if aggregated.repair_estimate else None,
                json.dumps(aggregated.parties),
                json.dumps(aggregated.source_files),
                aggregated.conflicts_detected,
                aggregated.confidence_score,
            )
            
            return str(row["id"])
    
    async def get_claim_media(
        self,
        claim_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all media files for a claim.
        
        Args:
            claim_id: The claim identifier
            
        Returns:
            List of media records
        """
        async with self.pool.connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, file_id, filename, media_type, analyzer_id,
                       status, error_message, processing_time_seconds,
                       extracted_data, created_at
                FROM claim_media
                WHERE claim_id = $1
                ORDER BY created_at
                """,
                claim_id,
            )
            
            return [dict(row) for row in rows]
    
    async def get_claim_summary(
        self,
        claim_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the aggregated summary for a claim.
        
        Args:
            claim_id: The claim identifier
            
        Returns:
            Summary record or None if not found
        """
        async with self.pool.connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM claim_summaries
                WHERE claim_id = $1
                """,
                claim_id,
            )
            
            return dict(row) if row else None
    
    async def get_damage_areas(
        self,
        claim_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all damage areas for a claim.
        
        Args:
            claim_id: The claim identifier
            
        Returns:
            List of damage area records
        """
        async with self.pool.connection() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM claim_damage_areas
                WHERE claim_id = $1
                ORDER BY severity DESC, confidence DESC
                """,
                claim_id,
            )
            
            return [dict(row) for row in rows]
    
    async def get_keyframes(
        self,
        claim_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all video keyframes for a claim.
        
        Args:
            claim_id: The claim identifier
            
        Returns:
            List of keyframe records
        """
        async with self.pool.connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, media_id, timestamp_seconds, frame_url,
                       description, objects_detected, created_at
                FROM claim_keyframes
                WHERE claim_id = $1
                ORDER BY timestamp_seconds
                """,
                claim_id,
            )
            
            return [dict(row) for row in rows]
    
    async def _save_damage_areas(
        self,
        conn,
        claim_id: str,
        media_id: str,
        damage_areas: List[DamageArea],
    ) -> None:
        """Save damage areas to database."""
        for area in damage_areas:
            await conn.execute(
                """
                INSERT INTO claim_damage_areas
                    (claim_id, media_id, component, damage_type, severity,
                     confidence, bounding_box, description, estimated_cost)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                claim_id,
                media_id,
                area.component,
                area.damage_type,
                area.severity,
                area.confidence,
                json.dumps(area.bounding_box) if area.bounding_box else None,
                area.description,
                area.estimated_cost,
            )
    
    async def _save_video_data(
        self,
        conn,
        claim_id: str,
        media_id: str,
        video_data: VideoData,
    ) -> None:
        """Save video data (keyframes, segments) to database."""
        # Save keyframes
        for keyframe in video_data.keyframes:
            await conn.execute(
                """
                INSERT INTO claim_keyframes
                    (claim_id, media_id, timestamp_seconds, frame_url,
                     description, objects_detected)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                claim_id,
                media_id,
                keyframe.timestamp,
                keyframe.frame_url,
                keyframe.description,
                json.dumps(keyframe.objects_detected) if keyframe.objects_detected else None,
            )
        
        # Save segments
        for segment in video_data.segments:
            await conn.execute(
                """
                INSERT INTO claim_video_segments
                    (claim_id, media_id, start_time, end_time,
                     event_type, description, confidence)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                claim_id,
                media_id,
                segment.start_time,
                segment.end_time,
                segment.event_type,
                segment.description,
                segment.confidence,
            )
    
    async def _save_document_data(
        self,
        conn,
        claim_id: str,
        media_id: str,
        doc_data: DocumentFields,
    ) -> None:
        """Save document data (repair items) to database."""
        if doc_data.repair_estimate and doc_data.repair_estimate.line_items:
            for item in doc_data.repair_estimate.line_items:
                await conn.execute(
                    """
                    INSERT INTO claim_repair_items
                        (claim_id, media_id, item_description, item_type,
                         quantity, unit_price, total_price)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    claim_id,
                    media_id,
                    item.get("description", "Unknown"),
                    item.get("type", "part"),
                    item.get("quantity", 1),
                    item.get("unit_price"),
                    item.get("total_price"),
                )
    
    # ============================================================
    # Claim Assessment Persistence Methods (Phase 5)
    # ============================================================
    
    async def save_claim_assessment(
        self,
        assessment: "ClaimAssessment",
    ) -> str:
        """
        Save a claim policy assessment to the database.
        
        Args:
            assessment: The ClaimAssessment to save
            
        Returns:
            The assessment record ID
        """
        # Convert dataclass fields to JSON-serializable dicts
        damage_json = None
        if assessment.damage:
            damage_json = {
                "severity": assessment.damage.severity,
                "estimated_repair_range": list(assessment.damage.estimated_repair_range),
                "requires_senior_review": assessment.damage.requires_senior_review,
                "requires_frame_inspection": assessment.damage.requires_frame_inspection,
                "is_total_loss": assessment.damage.is_total_loss,
                "damage_areas": assessment.damage.damage_areas,
                "citations": [asdict(c) for c in assessment.damage.citations],
                "rationale": assessment.damage.rationale,
            }
        
        liability_json = None
        if assessment.liability:
            liability_json = {
                "determination": assessment.liability.determination,
                "insured_fault_percentage": assessment.liability.insured_fault_percentage,
                "other_party_fault_percentage": assessment.liability.other_party_fault_percentage,
                "requires_investigation": assessment.liability.requires_investigation,
                "subrogation_potential": assessment.liability.subrogation_potential,
                "citations": [asdict(c) for c in assessment.liability.citations],
                "rationale": assessment.liability.rationale,
            }
        
        fraud_json = None
        if assessment.fraud:
            fraud_json = {
                "risk_level": assessment.fraud.risk_level,
                "indicators": assessment.fraud.indicators,
                "requires_siu_referral": assessment.fraud.requires_siu_referral,
                "requires_euo": assessment.fraud.requires_euo,
                "citations": [asdict(c) for c in assessment.fraud.citations],
                "rationale": assessment.fraud.rationale,
            }
        
        payout_json = None
        if assessment.payout:
            payout_json = {
                "estimate_status": assessment.payout.estimate_status,
                "original_estimate": assessment.payout.original_estimate,
                "recommended_payout": assessment.payout.recommended_payout,
                "adjustments": assessment.payout.adjustments,
                "requires_independent_appraisal": assessment.payout.requires_independent_appraisal,
                "citations": [asdict(c) for c in assessment.payout.citations],
                "rationale": assessment.payout.rationale,
            }
        
        citations_json = [asdict(c) for c in assessment.all_citations]
        
        async with self.pool.connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO claim_assessments
                    (application_id, assessed_at, damage_assessment, 
                     liability_assessment, fraud_assessment, payout_assessment,
                     overall_recommendation, requires_adjuster_review, 
                     confidence_score, policy_citations,
                     adjuster_decision, adjuster_notes, decided_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (application_id) DO UPDATE SET
                    assessed_at = EXCLUDED.assessed_at,
                    damage_assessment = EXCLUDED.damage_assessment,
                    liability_assessment = EXCLUDED.liability_assessment,
                    fraud_assessment = EXCLUDED.fraud_assessment,
                    payout_assessment = EXCLUDED.payout_assessment,
                    overall_recommendation = EXCLUDED.overall_recommendation,
                    requires_adjuster_review = EXCLUDED.requires_adjuster_review,
                    confidence_score = EXCLUDED.confidence_score,
                    policy_citations = EXCLUDED.policy_citations,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                assessment.application_id,
                assessment.assessed_at,
                json.dumps(damage_json) if damage_json else None,
                json.dumps(liability_json) if liability_json else None,
                json.dumps(fraud_json) if fraud_json else None,
                json.dumps(payout_json) if payout_json else None,
                assessment.overall_recommendation,
                assessment.requires_adjuster_review,
                assessment.confidence_score,
                json.dumps(citations_json),
                assessment.adjuster_decision,
                assessment.adjuster_notes,
                assessment.decided_at,
            )
            
            assessment_id = str(row["id"])
            logger.info(
                f"Saved claim assessment {assessment_id} for {assessment.application_id}"
            )
            return assessment_id
    
    async def get_claim_assessment(
        self,
        application_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a claim assessment by application ID.
        
        Args:
            application_id: The application/claim identifier
            
        Returns:
            Dictionary with assessment data or None if not found
        """
        async with self.pool.connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, application_id, assessed_at,
                       damage_assessment, liability_assessment,
                       fraud_assessment, payout_assessment,
                       overall_recommendation, requires_adjuster_review,
                       confidence_score, policy_citations,
                       adjuster_decision, adjuster_notes, decided_at,
                       created_at, updated_at
                FROM claim_assessments
                WHERE application_id = $1
                """,
                application_id,
            )
            
            if not row:
                return None
            
            return {
                "id": str(row["id"]),
                "application_id": row["application_id"],
                "assessed_at": row["assessed_at"].isoformat() if row["assessed_at"] else None,
                "damage_assessment": json.loads(row["damage_assessment"]) if row["damage_assessment"] else None,
                "liability_assessment": json.loads(row["liability_assessment"]) if row["liability_assessment"] else None,
                "fraud_assessment": json.loads(row["fraud_assessment"]) if row["fraud_assessment"] else None,
                "payout_assessment": json.loads(row["payout_assessment"]) if row["payout_assessment"] else None,
                "overall_recommendation": row["overall_recommendation"],
                "requires_adjuster_review": row["requires_adjuster_review"],
                "confidence_score": row["confidence_score"],
                "policy_citations": json.loads(row["policy_citations"]) if row["policy_citations"] else [],
                "adjuster_decision": row["adjuster_decision"],
                "adjuster_notes": row["adjuster_notes"],
                "decided_at": row["decided_at"].isoformat() if row["decided_at"] else None,
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            }
    
    async def update_adjuster_decision(
        self,
        claim_id: str,
        decision: str,
        approved_amount: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Update the adjuster's decision on a claim assessment.
        
        Args:
            claim_id: The claim/application identifier
            decision: The adjuster's decision (approve, deny, adjust, investigate)
            approved_amount: Optional approved amount for the claim
            notes: Optional adjuster notes
            
        Returns:
            True if the assessment was updated, False if not found
        """
        async with self.pool.connection() as conn:
            result = await conn.execute(
                """
                UPDATE claim_assessments
                SET adjuster_decision = $2,
                    adjuster_notes = $3,
                    approved_amount = COALESCE($4, approved_amount),
                    decided_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE application_id = $1
                """,
                claim_id,
                decision,
                notes,
                approved_amount,
            )
            
            # Check if any rows were updated
            rows_affected = int(result.split()[-1]) if result else 0
            if rows_affected > 0:
                logger.info(
                    f"Updated adjuster decision for {claim_id}: {decision}"
                )
                return True
            return False
    
    async def list_pending_assessments(
        self,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        List assessments pending adjuster review.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of assessment summaries
        """
        async with self.pool.connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, application_id, assessed_at,
                       overall_recommendation, requires_adjuster_review,
                       confidence_score, adjuster_decision
                FROM claim_assessments
                WHERE requires_adjuster_review = true
                  AND adjuster_decision IS NULL
                ORDER BY assessed_at DESC
                LIMIT $1
                """,
                limit,
            )
            
            return [
                {
                    "id": str(row["id"]),
                    "application_id": row["application_id"],
                    "assessed_at": row["assessed_at"].isoformat() if row["assessed_at"] else None,
                    "overall_recommendation": row["overall_recommendation"],
                    "requires_adjuster_review": row["requires_adjuster_review"],
                    "confidence_score": row["confidence_score"],
                }
                for row in rows
            ]


# Convenience function
async def save_claim_media(
    claim_id: str,
    batch: BatchResult,
    aggregated: Optional[AggregatedResult] = None,
) -> Tuple[List[str], Optional[str]]:
    """
    Save claim media processing results.
    
    Args:
        claim_id: The claim identifier
        batch: Batch processing results
        aggregated: Optional aggregated result
        
    Returns:
        Tuple of (media_ids, summary_id)
    """
    repo = ClaimsMediaRepository()
    
    media_ids = await repo.save_batch_result(claim_id, batch)
    
    summary_id = None
    if aggregated:
        summary_id = await repo.save_aggregated_result(aggregated)
    
    return media_ids, summary_id


__all__ = [
    "ClaimsMediaRepository",
    "save_claim_media",
]
