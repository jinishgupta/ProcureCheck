from fastapi import APIRouter, HTTPException
from typing import Optional
from db.models import (
    Evaluation, EvaluationCreate, EvaluationMatrixResponse,
    ReviewQueueResponse, AuditTrailResponse, DashboardStats,
    Bidder, Criterion, ReviewItem, AuditLog
)
from db.database import Database
from datetime import datetime
import uuid
import json

router = APIRouter(tags=["evaluations"])


@router.get("/evaluations/matrix/{tender_id}", response_model=EvaluationMatrixResponse)
async def get_evaluation_matrix(tender_id: str):
    """Get evaluation matrix for a tender"""
    try:
        with Database.get_cursor() as cursor:
            # Get evaluations
            cursor.execute("SELECT * FROM evaluations WHERE tender_id = %s", (tender_id,))
            eval_rows = cursor.fetchall()
            evaluations = [Evaluation(**dict(row)) for row in eval_rows]
            
            # Get bidders
            cursor.execute("SELECT * FROM bidders WHERE tender_id = %s", (tender_id,))
            bidder_rows = cursor.fetchall()
            bidders = [Bidder(**dict(row)) for row in bidder_rows]
            
            # Get criteria
            cursor.execute("SELECT * FROM criteria WHERE tender_id = %s", (tender_id,))
            criteria_rows = cursor.fetchall()
            criteria = [Criterion(**dict(row)) for row in criteria_rows]
            
            return EvaluationMatrixResponse(
                evaluations=evaluations,
                bidders=bidders,
                criteria=criteria
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluations/", response_model=Evaluation)
async def create_evaluation(evaluation: EvaluationCreate):
    """Create a new evaluation"""
    try:
        with Database.get_cursor() as cursor:
            evaluation_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            # Convert signals to JSON
            signals_json = json.dumps(evaluation.signals.model_dump())
            
            cursor.execute("""
                INSERT INTO evaluations (
                    id, tender_id, bidder_id, criterion_id, verdict, confidence,
                    extracted_value, method, source_page, signals, explanation, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                evaluation_id, evaluation.tender_id, evaluation.bidder_id,
                evaluation.criterion_id, evaluation.verdict.value, evaluation.confidence,
                evaluation.extracted_value, evaluation.method.value, evaluation.source_page,
                signals_json, evaluation.explanation, now
            ))
            
            row = cursor.fetchone()
            
            # If confidence < 0.9, add to review queue
            if evaluation.confidence < 0.9:
                urgency = "high" if evaluation.confidence < 0.7 else "medium"
                cursor.execute("""
                    INSERT INTO review_queue (
                        id, tender_id, evaluation_id, urgency, reason, status, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(uuid.uuid4()), evaluation.tender_id, evaluation_id,
                    urgency, f"Confidence {evaluation.confidence:.2%} below threshold",
                    "pending", now
                ))
            
            return Evaluation(**dict(row))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review-queue/{tender_id}", response_model=ReviewQueueResponse)
async def get_review_queue(tender_id: str, status: Optional[str] = "pending"):
    """Get review queue for a tender"""
    try:
        with Database.get_cursor() as cursor:
            if status:
                cursor.execute("""
                    SELECT * FROM review_queue
                    WHERE tender_id = %s AND status = %s
                    ORDER BY created_at DESC
                """, (tender_id, status))
            else:
                cursor.execute("""
                    SELECT * FROM review_queue
                    WHERE tender_id = %s
                    ORDER BY created_at DESC
                """, (tender_id,))
            
            rows = cursor.fetchall()
            items = [ReviewItem(**dict(row)) for row in rows]
            
            return ReviewQueueResponse(items=items, total=len(items))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/review-queue/{review_id}")
async def update_review_item(review_id: str, status: str, officer: str, reason: Optional[str] = None):
    """Update a review item (confirm/override)"""
    try:
        with Database.get_cursor() as cursor:
            now = datetime.utcnow()
            
            cursor.execute("""
                UPDATE review_queue
                SET status = %s, reviewed_by = %s, reviewed_at = %s
                WHERE id = %s
                RETURNING *
            """, (status, officer, now, review_id))
            
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Review item not found")
            
            review_data = dict(row)
            
            # Create audit log
            action = "REVIEW_CONFIRMED" if status == "confirmed" else "REVIEW_OVERRIDE"
            cursor.execute("""
                INSERT INTO audit_logs (id, tender_id, action, officer, detail, version, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()), review_data["tender_id"], action, officer,
                reason or f"Review item {status}", "1.0", now
            ))
            
            return {"message": "Review item updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-trail/{tender_id}", response_model=AuditTrailResponse)
async def get_audit_trail(tender_id: str, action: Optional[str] = None):
    """Get audit trail for a tender"""
    try:
        with Database.get_cursor() as cursor:
            if action:
                cursor.execute("""
                    SELECT * FROM audit_logs
                    WHERE tender_id = %s AND action = %s
                    ORDER BY timestamp DESC
                """, (tender_id, action))
            else:
                cursor.execute("""
                    SELECT * FROM audit_logs
                    WHERE tender_id = %s
                    ORDER BY timestamp DESC
                """, (tender_id,))
            
            rows = cursor.fetchall()
            logs = [AuditLog(**dict(row)) for row in rows]
            
            return AuditTrailResponse(logs=logs, total=len(logs))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        with Database.get_cursor() as cursor:
            # Count active tenders
            cursor.execute("""
                SELECT COUNT(*) as count FROM tenders
                WHERE status IN ('awaiting_bids', 'evaluation_in_progress', 'evaluation_complete')
            """)
            active_tenders = cursor.fetchone()['count']
            
            # Count pending reviews
            cursor.execute("""
                SELECT COUNT(*) as count FROM review_queue
                WHERE status = 'pending'
            """)
            pending_reviews = cursor.fetchone()['count']
            
            # Count total bidders
            cursor.execute("SELECT COUNT(*) as count FROM bidders")
            bidders = cursor.fetchone()['count']
            
            # Calculate compliance rate
            cursor.execute("""
                SELECT verdict, COUNT(*) as count
                FROM evaluations
                GROUP BY verdict
            """)
            verdict_rows = cursor.fetchall()
            
            if verdict_rows:
                pass_count = sum(row['count'] for row in verdict_rows if row['verdict'] == 'PASS')
                total_count = sum(row['count'] for row in verdict_rows)
                compliance_rate = int((pass_count / total_count) * 100) if total_count > 0 else 0
            else:
                compliance_rate = 0
            
            return DashboardStats(
                active_tenders=active_tenders,
                pending_reviews=pending_reviews,
                bidders_evaluated=bidders,
                compliance_rate=compliance_rate
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
