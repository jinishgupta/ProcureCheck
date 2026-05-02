from fastapi import APIRouter, HTTPException
from typing import Optional
from app.models import (
    Evaluation, EvaluationCreate, EvaluationMatrixResponse,
    ReviewQueueResponse, AuditTrailResponse, DashboardStats
)
from app.database import get_db
from datetime import datetime
import uuid

router = APIRouter(tags=["evaluations"])


@router.get("/evaluations/matrix/{tender_id}", response_model=EvaluationMatrixResponse)
async def get_evaluation_matrix(tender_id: str):
    """Get evaluation matrix for a tender"""
    try:
        db = get_db()
        
        # Get evaluations
        eval_response = db.table("evaluations").select("*").eq("tender_id", tender_id).execute()
        evaluations = [Evaluation(**item) for item in eval_response.data]
        
        # Get bidders
        bidder_response = db.table("bidders").select("*").eq("tender_id", tender_id).execute()
        from app.models import Bidder
        bidders = [Bidder(**item) for item in bidder_response.data]
        
        # Get criteria
        criteria_response = db.table("criteria").select("*").eq("tender_id", tender_id).execute()
        from app.models import Criterion
        criteria = [Criterion(**item) for item in criteria_response.data]
        
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
        db = get_db()
        
        evaluation_data = {
            "id": str(uuid.uuid4()),
            **evaluation.model_dump(),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        response = db.table("evaluations").insert(evaluation_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create evaluation")
        
        # If confidence < 0.9, add to review queue
        if evaluation.confidence < 0.9:
            from app.models import ReviewItemCreate
            review_data = {
                "id": str(uuid.uuid4()),
                "tender_id": evaluation.tender_id,
                "evaluation_id": response.data[0]["id"],
                "urgency": "high" if evaluation.confidence < 0.7 else "medium",
                "reason": f"Confidence {evaluation.confidence:.2%} below threshold",
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
            }
            db.table("review_queue").insert(review_data).execute()
        
        return Evaluation(**response.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review-queue/{tender_id}", response_model=ReviewQueueResponse)
async def get_review_queue(tender_id: str, status: Optional[str] = "pending"):
    """Get review queue for a tender"""
    try:
        db = get_db()
        
        query = db.table("review_queue").select("*").eq("tender_id", tender_id)
        
        if status:
            query = query.eq("status", status)
        
        response = query.order("created_at", desc=True).execute()
        
        from app.models import ReviewItem
        items = [ReviewItem(**item) for item in response.data]
        
        return ReviewQueueResponse(items=items, total=len(items))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/review-queue/{review_id}")
async def update_review_item(review_id: str, status: str, officer: str, reason: Optional[str] = None):
    """Update a review item (confirm/override)"""
    try:
        db = get_db()
        
        update_data = {
            "status": status,
            "reviewed_by": officer,
            "reviewed_at": datetime.utcnow().isoformat(),
        }
        
        response = db.table("review_queue").update(update_data).eq("id", review_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Review item not found")
        
        # Create audit log
        review_data = response.data[0]
        action = "REVIEW_CONFIRMED" if status == "confirmed" else "REVIEW_OVERRIDE"
        audit_data = {
            "id": str(uuid.uuid4()),
            "tender_id": review_data["tender_id"],
            "action": action,
            "officer": officer,
            "detail": reason or f"Review item {status}",
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
        }
        db.table("audit_logs").insert(audit_data).execute()
        
        return {"message": "Review item updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-trail/{tender_id}", response_model=AuditTrailResponse)
async def get_audit_trail(tender_id: str, action: Optional[str] = None):
    """Get audit trail for a tender"""
    try:
        db = get_db()
        
        query = db.table("audit_logs").select("*").eq("tender_id", tender_id)
        
        if action:
            query = query.eq("action", action)
        
        response = query.order("timestamp", desc=True).execute()
        
        from app.models import AuditLog
        logs = [AuditLog(**item) for item in response.data]
        
        return AuditTrailResponse(logs=logs, total=len(logs))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        db = get_db()
        
        # Count active tenders
        active_tenders = db.table("tenders").select("id", count="exact").in_(
            "status", ["awaiting_bids", "evaluation_in_progress", "evaluation_complete"]
        ).execute()
        
        # Count pending reviews
        pending_reviews = db.table("review_queue").select("id", count="exact").eq("status", "pending").execute()
        
        # Count total bidders
        bidders = db.table("bidders").select("id", count="exact").execute()
        
        # Calculate compliance rate (simplified)
        evaluations = db.table("evaluations").select("verdict", count="exact").execute()
        if evaluations.data:
            pass_count = len([e for e in evaluations.data if e.get("verdict") == "PASS"])
            total_count = len(evaluations.data)
            compliance_rate = int((pass_count / total_count) * 100) if total_count > 0 else 0
        else:
            compliance_rate = 0
        
        return DashboardStats(
            active_tenders=len(active_tenders.data) if active_tenders.data else 0,
            pending_reviews=len(pending_reviews.data) if pending_reviews.data else 0,
            bidders_evaluated=len(bidders.data) if bidders.data else 0,
            compliance_rate=compliance_rate
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
