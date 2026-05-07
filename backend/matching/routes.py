from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from db.models import (
    Evaluation, EvaluationCreate, EvaluationMatrixResponse,
    ReviewQueueResponse, AuditTrailResponse, DashboardStats,
    Bidder, Criterion, ReviewItem, AuditLog, ReviewItemUpdate
)
from db.database import Database
from datetime import datetime
import uuid
import json

router = APIRouter(tags=["evaluations"])


# ─────────────────────────────────────────────────────────────────────────────
# NEW: Trigger the matching + evaluation pipeline
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/matching/run/{tender_id}")
async def run_matching(tender_id: str, background_tasks: BackgroundTasks):
    """
    Trigger Stage 3 matching & evaluation for all bidders in a tender.

    What this does:
      1. Loads all criteria from the database for this tender
      2. For each bidder, loads their FAISS index from disk
         (produced by the bidder ingestion pipeline)
      3. Runs retrieval → regex/LLM extraction → logprob scoring → verdict
      4. Writes every result to the evaluations table
      5. Auto-populates the review_queue for any REVIEW verdicts
      6. Updates tender status to evaluation_in_progress / evaluation_complete

    Runs in the background so the HTTP response returns immediately.
    Poll GET /api/tenders/{tender_id} and check status field to know when done.

    Prerequisites:
      - Tender must have criteria (run tender upload first)
      - Bidders must be registered and their FAISS indexes must exist at
        data/bidder_indexes/{bidder_id}/faiss.index
        data/bidder_indexes/{bidder_id}/pages.json
    """
    # Validate tender exists before handing off to background
    try:
        with Database.get_cursor() as cursor:
            cursor.execute("SELECT id, status FROM tenders WHERE id = %s", (tender_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Tender not found")

            cursor.execute("SELECT COUNT(*) as c FROM criteria WHERE tender_id = %s", (tender_id,))
            criteria_count = cursor.fetchone()["c"]
            if criteria_count == 0:
                raise HTTPException(
                    status_code=400,
                    detail="No criteria found for this tender. Upload the tender PDF first."
                )

            cursor.execute("SELECT COUNT(*) as c FROM bidders WHERE tender_id = %s", (tender_id,))
            bidder_count = cursor.fetchone()["c"]
            if bidder_count == 0:
                raise HTTPException(
                    status_code=400,
                    detail="No bidders found for this tender. Add bidders first."
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Import here to avoid circular imports and slow startup
    from matching.engine import run_evaluation_for_tender

    # Run in background — evaluation can take minutes for 30+ bidders
    background_tasks.add_task(run_evaluation_for_tender, tender_id)

    return {
        "message": "Evaluation started in background",
        "tender_id": tender_id,
        "criteria_count": criteria_count,
        "bidder_count": bidder_count,
        "poll": f"GET /api/tenders/{tender_id} — watch the 'status' field",
    }


@router.post("/matching/run/{tender_id}/sync")
async def run_matching_sync(tender_id: str):
    """
    Same as /matching/run/{tender_id} but waits for completion and
    returns the full summary. Use this for small tenders or testing.
    For production with 30+ bidders, use the async version above.
    """
    try:
        with Database.get_cursor() as cursor:
            cursor.execute("SELECT id FROM tenders WHERE id = %s", (tender_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Tender not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    from matching.engine import run_evaluation_for_tender
    try:
        result = run_evaluation_for_tender(tender_id)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Existing routes (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/evaluations/matrix/{tender_id}", response_model=EvaluationMatrixResponse)
async def get_evaluation_matrix(tender_id: str):
    """Get evaluation matrix for a tender"""
    try:
        with Database.get_cursor() as cursor:
            cursor.execute("SELECT * FROM evaluations WHERE tender_id = %s", (tender_id,))
            eval_rows = cursor.fetchall()
            evaluations = [Evaluation(**dict(row)) for row in eval_rows]

            cursor.execute("SELECT * FROM bidders WHERE tender_id = %s", (tender_id,))
            bidder_rows = cursor.fetchall()
            bidders = [Bidder(**dict(row)) for row in bidder_rows]

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
    """Get review queue for a tender with full details"""
    try:
        with Database.get_cursor() as cursor:
            # Join with evaluations, criteria, and bidders to get full details
            query = """
                SELECT 
                    rq.*,
                    e.extracted_value,
                    e.confidence,
                    e.signals,
                    c.field as criterion,
                    b.name as bidder
                FROM review_queue rq
                JOIN evaluations e ON rq.evaluation_id = e.id
                JOIN criteria c ON e.criterion_id = c.id
                JOIN bidders b ON e.bidder_id = b.id
                WHERE rq.tender_id = %s
            """
            
            if status:
                query += " AND rq.status = %s"
                cursor.execute(query + " ORDER BY rq.created_at DESC", (tender_id, status))
            else:
                cursor.execute(query + " ORDER BY rq.created_at DESC", (tender_id,))

            rows = cursor.fetchall()
            items = []
            for row in rows:
                row_dict = dict(row)
                # Parse signals JSON if it's a string
                if isinstance(row_dict.get('signals'), str):
                    import json
                    row_dict['signals'] = json.loads(row_dict['signals'])
                items.append(ReviewItem(**row_dict))
            
            return ReviewQueueResponse(items=items, total=len(items))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/review-queue/{review_id}")
async def update_review_item(review_id: str, update_data: ReviewItemUpdate):
    """Update a review item (confirm/override) and update the evaluation verdict"""
    try:
        with Database.get_cursor() as cursor:
            now = datetime.utcnow()
            status = update_data.status
            officer = update_data.officer
            reason = update_data.reason

            # Get the review item to find the evaluation_id
            cursor.execute("""
                SELECT * FROM review_queue WHERE id = %s
            """, (review_id,))
            review_row = cursor.fetchone()
            
            if not review_row:
                raise HTTPException(status_code=404, detail="Review item not found")
            
            review_data = dict(review_row)
            evaluation_id = review_data["evaluation_id"]
            
            # Update review queue status
            cursor.execute("""
                UPDATE review_queue
                SET status = %s, reviewed_by = %s, reviewed_at = %s
                WHERE id = %s
            """, (status, officer, now, review_id))

            # Update the evaluation verdict based on officer decision
            new_verdict = None
            if status == "confirmed":
                new_verdict = "PASS"
            elif status == "overridden":
                new_verdict = "FAIL"
            
            if new_verdict:
                cursor.execute("""
                    UPDATE evaluations
                    SET verdict = %s, confidence = 1.0
                    WHERE id = %s
                """, (new_verdict, evaluation_id))

            # Log the action
            action = "REVIEW_CONFIRMED" if status == "confirmed" else "REVIEW_OVERRIDE"
            cursor.execute("""
                INSERT INTO audit_logs (id, tender_id, action, officer, detail, version, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()), review_data["tender_id"], action, officer,
                reason or f"Review item {status} - verdict changed to {new_verdict}", "1.0", now
            ))

            return {"message": "Review item and evaluation updated successfully", "new_verdict": new_verdict}
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
            cursor.execute("""
                SELECT COUNT(*) as count FROM tenders
                WHERE status IN ('awaiting_bids', 'evaluation_in_progress', 'evaluation_complete')
            """)
            active_tenders = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM review_queue WHERE status = 'pending'")
            pending_reviews = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM bidders")
            bidders = cursor.fetchone()["count"]

            cursor.execute("SELECT verdict, COUNT(*) as count FROM evaluations GROUP BY verdict")
            verdict_rows = cursor.fetchall()

            if verdict_rows:
                pass_count  = sum(r["count"] for r in verdict_rows if r["verdict"] == "PASS")
                total_count = sum(r["count"] for r in verdict_rows)
                compliance_rate = int((pass_count / total_count) * 100) if total_count > 0 else 0
            else:
                compliance_rate = 0

            return DashboardStats(
                active_tenders=active_tenders,
                pending_reviews=pending_reviews,
                bidders_evaluated=bidders,
                compliance_rate=compliance_rate,
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
