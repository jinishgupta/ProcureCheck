from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from app.models import (
    Tender, TenderCreate, TenderUpdate, TenderListResponse,
    TenderStatus
)
from app.database import get_db
from datetime import datetime
import uuid

router = APIRouter(prefix="/tenders", tags=["tenders"])


@router.get("/", response_model=TenderListResponse)
async def get_tenders():
    """Get all tenders"""
    try:
        db = get_db()
        response = db.table("tenders").select("*").order("created_at", desc=True).execute()
        
        tenders = []
        for tender_data in response.data:
            # Get counts
            bidders_count = db.table("bidders").select("id", count="exact").eq("tender_id", tender_data["id"]).execute()
            reviews_count = db.table("review_queue").select("id", count="exact").eq("tender_id", tender_data["id"]).eq("status", "pending").execute()
            
            tender_data["bidders_count"] = len(bidders_count.data) if bidders_count.data else 0
            tender_data["pending_reviews"] = len(reviews_count.data) if reviews_count.data else 0
            
            tenders.append(Tender(**tender_data))
        
        return TenderListResponse(tenders=tenders, total=len(tenders))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tender_id}", response_model=Tender)
async def get_tender(tender_id: str):
    """Get a specific tender"""
    try:
        db = get_db()
        response = db.table("tenders").select("*").eq("id", tender_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Tender not found")
        
        tender_data = response.data[0]
        
        # Get counts
        bidders_count = db.table("bidders").select("id", count="exact").eq("tender_id", tender_id).execute()
        reviews_count = db.table("review_queue").select("id", count="exact").eq("tender_id", tender_id).eq("status", "pending").execute()
        
        tender_data["bidders_count"] = len(bidders_count.data) if bidders_count.data else 0
        tender_data["pending_reviews"] = len(reviews_count.data) if reviews_count.data else 0
        
        return Tender(**tender_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Tender)
async def create_tender(tender: TenderCreate):
    """Create a new tender"""
    try:
        db = get_db()
        
        tender_data = {
            "id": str(uuid.uuid4()),
            **tender.model_dump(),
            "status": TenderStatus.DRAFT.value,
            "total_pages": 0,
            "extracted_criteria_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        response = db.table("tenders").insert(tender_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create tender")
        
        result = response.data[0]
        result["bidders_count"] = 0
        result["pending_reviews"] = 0
        
        # Create audit log
        audit_data = {
            "id": str(uuid.uuid4()),
            "tender_id": result["id"],
            "action": "TENDER_CREATED",
            "officer": "System",
            "detail": f"Tender '{tender.title}' created",
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
        }
        db.table("audit_logs").insert(audit_data).execute()
        
        return Tender(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{tender_id}", response_model=Tender)
async def update_tender(tender_id: str, tender_update: TenderUpdate):
    """Update a tender"""
    try:
        db = get_db()
        
        # Check if tender exists
        existing = db.table("tenders").select("*").eq("id", tender_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Tender not found")
        
        # Update only provided fields
        update_data = {
            k: v for k, v in tender_update.model_dump(exclude_unset=True).items()
            if v is not None
        }
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        response = db.table("tenders").update(update_data).eq("id", tender_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to update tender")
        
        result = response.data[0]
        
        # Get counts
        bidders_count = db.table("bidders").select("id", count="exact").eq("tender_id", tender_id).execute()
        reviews_count = db.table("review_queue").select("id", count="exact").eq("tender_id", tender_id).eq("status", "pending").execute()
        
        result["bidders_count"] = len(bidders_count.data) if bidders_count.data else 0
        result["pending_reviews"] = len(reviews_count.data) if reviews_count.data else 0
        
        return Tender(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{tender_id}")
async def delete_tender(tender_id: str):
    """Delete a tender"""
    try:
        db = get_db()
        
        # Check if tender exists
        existing = db.table("tenders").select("id").eq("id", tender_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Tender not found")
        
        # Delete tender (cascade will handle related records)
        db.table("tenders").delete().eq("id", tender_id).execute()
        
        return {"message": "Tender deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tender_id}/upload")
async def upload_tender_document(tender_id: str, file: UploadFile = File(...)):
    """Upload tender document (placeholder for future processing)"""
    try:
        db = get_db()
        
        # Check if tender exists
        existing = db.table("tenders").select("id").eq("id", tender_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Tender not found")
        
        # TODO: Implement actual file processing
        # For now, just update status
        update_data = {
            "status": TenderStatus.CRITERIA_EXTRACTED.value,
            "updated_at": datetime.utcnow().isoformat(),
        }
        db.table("tenders").update(update_data).eq("id", tender_id).execute()
        
        # Create audit log
        audit_data = {
            "id": str(uuid.uuid4()),
            "tender_id": tender_id,
            "action": "TENDER_UPLOADED",
            "officer": "System",
            "detail": f"Tender document '{file.filename}' uploaded",
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
        }
        db.table("audit_logs").insert(audit_data).execute()
        
        return {"message": "File uploaded successfully", "filename": file.filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
